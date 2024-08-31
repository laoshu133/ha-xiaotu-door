"""Coordinator for XiaoTu."""

from __future__ import annotations

import logging

from httpx import RequestError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .account import AUTH_VALID_OFFSET, XiaoTuAccount
from .const import DOMAIN
from .utils import APIError, AuthError

_LOGGER = logging.getLogger(__name__)


class XiaoTuCoordinator(DataUpdateCoordinator[None]):
    """Class to manage fetching XiaoTu data."""

    account: XiaoTuAccount

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize account-wide BMW data updater."""

        self.config_entry = entry
        self.account = XiaoTuAccount(entry.data)

        # Remove init token from entry data
        data = entry.data.copy()
        _LOGGER.info("XiaoTuCoordinator.clear: %s", data)
        data.pop("init_token", None)
        hass.config_entries.async_update_entry(self.config_entry, data=data)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=AUTH_VALID_OFFSET / 2,
        )

        # Default to false on init so _async_update_data logic works
        self.last_update_success = False

    async def _async_update_data(self) -> None:
        """Fetch data from XiaoTu."""
        # old_refresh_token = self.account.refresh_token

        try:
            await self.account.get_devices()
        except AuthError as err:
            # Clear refresh token and trigger reauth if previous update failed as well
            self._update_config_entry_refresh_token(None)
            raise ConfigEntryAuthFailed(err) from err
        except (APIError, RequestError) as err:
            raise UpdateFailed(err) from err

        # if self.account.refresh_token != old_refresh_token:
        #     self._update_config_entry_refresh_token(self.account.refresh_token)
        #     _LOGGER.debug(
        #         "xiaotu_connected: refresh token %s > %s",
        #         old_refresh_token,
        #         self.account.refresh_token,
        #     )

    def _update_config_entry_refresh_token(self, refresh_token: str | None) -> None:
        """Update or delete the refresh_token in the Config Entry."""
        # data = {
        #     **self.config_entry.data,
        #     CONF_REFRESH_TOKEN: refresh_token,
        # }
        # if not refresh_token:
        #     data.pop(CONF_REFRESH_TOKEN)
        # self.hass.config_entries.async_update_entry(self.config_entry, data=data)
