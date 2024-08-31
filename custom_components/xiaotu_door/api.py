"""Generic API management."""

import asyncio
from collections import defaultdict
from dataclasses import dataclass
import datetime
from hashlib import md5
import logging
import math
from typing import collections
from uuid import uuid4

import httpx

from .const import DEFAULT_API_HOST, HTTPX_TIMEOUT, X_USER_AGENT
from .utils import RESPONSE_STORE, APIError, anonymize_response, handle_httpstatuserror

from homeassistant.const import CONF_HOST

EXPIRES_AT_OFFSET = datetime.timedelta(seconds=HTTPX_TIMEOUT * 2)

_LOGGER = logging.getLogger(__name__)


@dataclass
class APIConfiguration:
    """Stores global settings for API."""

    host: str = DEFAULT_API_HOST
    username: str = ""
    password: str = ""

    proxy_config: dict | None = None

    timeout: float = HTTPX_TIMEOUT
    log_responses: bool = False

    def set_log_responses(self, log_responses: bool) -> None:
        """Set if responses are logged and clear response store."""

        self.log_responses = log_responses
        RESPONSE_STORE.clear()


class API(httpx.AsyncClient):
    """Async HTTP API based on `httpx.AsyncClient`."""

    def __init__(self, config: APIConfiguration, *args, **kwargs) -> None:
        """Initialize the API."""

        self.config = config

        # Proxy config
        proxy_config = config.proxy_config or {}
        if proxy_config.get("url"):
            kwargs["proxies"] = {
                "http://": proxy_config.get("url"),
                "https://": proxy_config.get("url"),
            }
        if proxy_config.get("ca_path"):
            kwargs["verify"] = config.proxy_config["ca_path"]

        # Increase timeout
        kwargs["timeout"] = config.timeout

        # Set default values
        kwargs["base_url"] = kwargs.get("base_url") or getattr(config, CONF_HOST)
        kwargs["headers"] = self.generate_header(kwargs.get("headers"), kwargs)

        # Register event hooks
        kwargs["event_hooks"] = defaultdict(list, **kwargs.get("event_hooks", {}))

        # Event hook for logging content
        async def log_response(response: httpx.Response):
            await response.aread()
            RESPONSE_STORE.append(anonymize_response(response))

        if config.log_responses:
            kwargs["event_hooks"]["response"].append(log_response)

        # Event hook which calls raise_for_status on all requests
        async def raise_for_status_event_handler(response: httpx.Response):
            """Event handler that automatically raises HTTPStatusErrors when attached.

            Will only raise on 4xx/5xx errors but not 401/429 which are handled `self.auth`.
            """
            if response.is_error and response.status_code not in [401, 429]:
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as ex:
                    await handle_httpstatuserror(ex, log_handler=_LOGGER)

            # XiaoTu API
            await response.aread()
            json_data = response.json()
            if int(json_data["code"]) != 200:
                raise APIError(
                    response=response, request=None, message=json_data["desc"]
                )

        kwargs["event_hooks"]["response"].append(raise_for_status_event_handler)

        super().__init__(*args, **kwargs)

    def generate_header(self, data: dict | None, all_data: dict) -> dict[str, str]:
        """Generate a header for HTTP requests to the server."""

        headers = {
            "referer": "https://servicewechat.com/wxcc9f1fa2912a152f/64/page-frame.html",
            "user-agent": X_USER_AGENT,
            "xweb_xhr": "1",
        }

        if data:
            headers.update(data)

        return headers


class Authentication(httpx.Auth):
    """Authentication and Retry Handler for API."""

    def __init__(
        self,
        username: str,
        password: str,
        access_token: str | None = None,
        expires_at: datetime.datetime | None = None,
        refresh_token: str | None = None,
    ) -> None:
        """Initialize the authentication object."""
        self.username: str = username
        self.password: str = password
        self.access_token: str | None = access_token
        self.expires_at: datetime.datetime | None = expires_at
        self.refresh_token: str | None = refresh_token
        self.session_id: str = str(uuid4())
        self._lock: asyncio.Lock | None = None

    @property
    def login_lock(self) -> asyncio.Lock:
        """Make sure that there is a lock in the current event loop."""
        if not self._lock:
            self._lock = asyncio.Lock()
        return self._lock

    def sync_auth_flow(
        self, request: httpx.Request
    ) -> collections.abc.Generator[httpx.Request, httpx.Response, None]:
        """Sync auth flow."""
        raise RuntimeError("Cannot use a async authentication class with httpx.Client")

    async def async_auth_flow(
        self, request: httpx.Request
    ) -> collections.abc.AsyncGenerator[httpx.Request, httpx.Response]:
        """Async auth flow."""
        # Get an access token on first call
        async with self.login_lock:
            if not self.access_token:
                await self.login()
        request.headers["authorization"] = f"Bearer {self.access_token}"

        # Try getting a response
        response: httpx.Response = yield request

        # return directly if first response was successful
        if response.is_success:
            return

        await response.aread()

        # First check against 429 Too Many Requests and 403 Quota Exceeded
        retry_count = 0
        while (
            response.status_code == 429
            or (response.status_code == 403 and "quota" in response.text.lower())
        ) and retry_count < 3:
            # Quota errors can either be 429 Too Many Requests or 403 Quota Exceeded (instead of 403 Forbidden)
            wait_time = get_retry_wait_time(response)
            _LOGGER.debug("Sleeping %s seconds due to 429 Too Many Requests", wait_time)
            await asyncio.sleep(wait_time)
            response = yield request
            await response.aread()
            retry_count += 1

        # Handle 401 Unauthorized and try getting a new token
        if response.status_code == 401:
            async with self.login_lock:
                _LOGGER.debug("Received unauthorized response, refreshing token")
                await self.login()
            request.headers["authorization"] = f"Bearer {self.access_token}"
            response = yield request

        # Raise if request still was not successful
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as ex:
            await handle_httpstatuserror(ex, module="API", log_handler=_LOGGER)

    async def login(self) -> None:
        """Get a valid Auth token."""
        token_data = {}

        # Try logging in with refresh token first
        if self.refresh_token:
            token_data = await self._refresh_token()
        if not token_data:
            token_data = await self._login()
        token_data["expires_at"] = token_data["expires_at"] - EXPIRES_AT_OFFSET

        self.access_token = token_data["access_token"]
        self.expires_at = token_data["expires_at"]
        self.refresh_token = token_data["refresh_token"]

    async def _login(self):
        return await self._refresh_token()

    async def _refresh_token(self):
        ret = {"refresh_token": "", "access_token": ""}

        async with API() as client:
            _LOGGER.debug("Authenticating")

            # Get token
            response = await client.post(
                "/userClient/clientV2/loginByOpenId",
                # headers={"tokenId": ""},
                json={
                    "openid": self.username,
                    "uuidString": md5(self.password),
                    "clientId": self.password,
                    "version": 2,
                    "net": -1,
                    "os": 4,
                },
            )

            ret_json = response.json()["result"]

            ret["refresh_token"] = ret_json.get("refresh_token", "")
            ret["access_token"] = ret_json.get(
                "tokenId", ret_json.get("access_token", "")
            )

        return ret


class LoginRetry(httpx.Auth):
    """httpx.Auth used as workaround to retry & sleep on 429 Too Many Requests."""

    def sync_auth_flow(
        self, request: httpx.Request
    ) -> collections.abc.Generator[httpx.Request, httpx.Response, None]:
        """Sync auth flow."""
        raise RuntimeError("Cannot use a async authentication class with httpx.Client")

    async def async_auth_flow(
        self, request: httpx.Request
    ) -> collections.abc.AsyncGenerator[httpx.Request, httpx.Response]:
        """Async auth flow."""

        # Try getting a response
        response: httpx.Response = yield request

        for _ in range(3):
            if response.status_code == 429:
                await response.aread()
                wait_time = get_retry_wait_time(response)
                _LOGGER.debug(
                    "Sleeping %s seconds due to 429 Too Many Requests", wait_time
                )
                await asyncio.sleep(wait_time)
                response = yield request
        # Only checking for 429 errors, as all other errors are handled by the
        # response hook of LoginClient
        if response.status_code == 429:
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as ex:
                await handle_httpstatuserror(ex, module="AUTH", log_handler=_LOGGER)


def get_retry_wait_time(response: httpx.Response) -> int:
    """Get the wait time for the next retry from the response and multiply by 2."""
    try:
        response_wait_time = next(
            iter([int(i) for i in response.json().get("message", "") if i.isdigit()])
        )
    except Exception:  # noqa: BLE001
        response_wait_time = 2

    return math.ceil(response_wait_time * 2)
