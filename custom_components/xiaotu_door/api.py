"""Generic API management."""

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
import datetime
from hashlib import md5
import inspect
import logging
import math
from typing import collections
from uuid import uuid4

import httpx

from .const import AUTH_VALID_OFFSET, DEFAULT_API_HOST, HTTPX_TIMEOUT, X_USER_AGENT
from .utils import (
    RESPONSE_STORE,
    APIError,
    AuthError,
    anonymize_response,
    get_now,
    handle_httpstatuserror,
)

from homeassistant.const import CONF_HOST

EXPIRES_AT_OFFSET = datetime.timedelta(seconds=HTTPX_TIMEOUT * 2)

_LOGGER = logging.getLogger(__name__)


@dataclass
class APIAuth:
    """API authentication data."""

    client_id: str = ""
    token_id: str = ""
    fetched_at = None

    @property
    def uuidString(self) -> str:
        """Generate a UUID string from the client ID."""
        return md5(self.client_id)

    def toJSON(self):
        """Convert to JSON."""

        return {
            "clientId": self.client_id,
            "tokenId": self.token_id,
            "version": "2",
            "net": "-1",
            "os": "4",
        }


@dataclass
class APIConfiguration:
    """Stores global settings for API."""

    host: str = DEFAULT_API_HOST
    init_token: dict[str, str] | None = None
    username: str = ""
    password: str = ""

    auth: APIAuth = field(default_factory=APIAuth)

    proxy_config: dict | None = None

    timeout: float = HTTPX_TIMEOUT
    log_responses: bool = False

    def set_log_responses(self, log_responses: bool) -> None:
        """Set if responses are logged and clear response store."""

        self.log_responses = log_responses
        RESPONSE_STORE.clear()


class API:
    """Async XiaoTu API with lazy, executor-backed client construction."""

    def __init__(self, config: APIConfiguration, *args, **kwargs) -> None:
        """Initialize the API."""

        self.config = config
        self._client: httpx.AsyncClient | None = None
        self._client_args = args
        self._client_kwargs = self._build_client_kwargs(kwargs)
        self._client_lock: asyncio.Lock | None = None
        self._closed = False

        # Make sure we have an auth
        if not config.auth:
            config.auth = APIAuth()

        # init token
        auth = config.auth
        init_token = config.init_token
        if init_token:
            auth.client_id = config.password
            auth.token_id = init_token.get("token_id", "")
            auth.fetched_at = datetime.datetime.fromisoformat(
                init_token.get("fetched_at")
            )

        _LOGGER.info("API.init_auth: %s", auth.toJSON())

    def _build_client_kwargs(self, kwargs: dict) -> dict:
        """Build AsyncClient arguments without constructing the client."""

        # Proxy config
        proxy_config = self.config.proxy_config or {}
        if proxy_config.get("url"):
            proxy_url = proxy_config["url"]
            if "proxy" in inspect.signature(httpx.AsyncClient).parameters:
                kwargs["proxy"] = proxy_url
            else:
                kwargs["proxies"] = {
                    "http://": proxy_url,
                    "https://": proxy_url,
                }
        if proxy_config.get("ca_path"):
            kwargs["verify"] = proxy_config["ca_path"]

        # Increase timeout
        kwargs["timeout"] = self.config.timeout

        # Set default values
        kwargs["base_url"] = kwargs.get("base_url") or getattr(self.config, CONF_HOST)
        kwargs["headers"] = self.generate_header(kwargs.get("headers"), kwargs)

        # Register event hooks
        kwargs["event_hooks"] = defaultdict(list, **kwargs.get("event_hooks", {}))

        # Event hook for logging content
        async def log_response(response: httpx.Response):
            await response.aread()
            RESPONSE_STORE.append(anonymize_response(response))

        if self.config.log_responses:
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
            json_code = int(json_data["code"]) or 200
            if json_code != 200:
                if json_code == 301:
                    # Reset token_id on Unauthorized
                    self.config.auth.token_id = ""

                    raise AuthError(
                        response=response, request=None, message="Unauthorized"
                    )
                else:
                    raise APIError(
                        response=response, request=None, message=json_data["desc"]
                    )

        kwargs["event_hooks"]["response"].append(raise_for_status_event_handler)

        return kwargs

    def _get_client_lock(self) -> asyncio.Lock:
        """Return the lock used to serialize lazy client construction."""

        if self._client_lock is None:
            self._client_lock = asyncio.Lock()
        return self._client_lock

    async def _async_get_client(self) -> httpx.AsyncClient:
        """Construct the HTTP client away from the Home Assistant event loop."""

        if self._closed:
            raise RuntimeError("XiaoTu API client is closed")

        async with self._get_client_lock():
            if self._closed:
                raise RuntimeError("XiaoTu API client is closed")
            if self._client is None:
                client = await asyncio.to_thread(
                    httpx.AsyncClient,
                    *self._client_args,
                    **self._client_kwargs,
                )
                if self._closed:
                    await client.aclose()
                    raise RuntimeError("XiaoTu API client is closed")
                self._client = client

        client = self._client
        if client is None:
            raise RuntimeError("XiaoTu API client was not initialized")
        return client

    async def request(self, *args, **kwargs) -> httpx.Response:
        """Send a request using the lazily initialized client."""

        client = await self._async_get_client()
        return await client.request(*args, **kwargs)

    async def get(self, *args, **kwargs) -> httpx.Response:
        """Send a GET request."""

        client = await self._async_get_client()
        return await client.get(*args, **kwargs)

    async def post(self, *args, **kwargs) -> httpx.Response:
        """Send a POST request."""

        client = await self._async_get_client()
        return await client.post(*args, **kwargs)

    async def aclose(self) -> None:
        """Close the HTTP client and release its resources."""

        async with self._get_client_lock():
            self._closed = True
            client = self._client
            self._client = None
            if client is not None:
                await client.aclose()

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

    async def get_auth(self) -> APIAuth:
        """Get the authentication data."""

        auth = self.auth

        if (
            not auth.token_id
            or not auth.fetched_at
            or auth.fetched_at + AUTH_VALID_OFFSET < get_now()
        ):
            # Update auth
            auth.client_id = self.config.password

            data = {
                **auth.toJSON(),
                "openid": self.config.username,
            }

            res = await self.post("/userClient/clientV2/loginByOpenId", data=data)

            ret = res.json()["result"]
            auth.token_id = ret.get("tokenId", ret.get("access_token", ""))
            auth.fetched_at = get_now()

        return auth

    @property
    def auth(self) -> APIAuth:
        """Returns the current auth."""
        return self.config.auth
