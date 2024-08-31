"""Config flow for XiaoTu Door integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

# from homeassistant.core import HomeAssistant
from .account import XiaoTuAccount
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, "API Host", "https://wap.anjucloud.com"): str,
        vol.Required(CONF_USERNAME, "WeChat OpenId"): str,
        vol.Required(CONF_PASSWORD, "XiaoTu ClientId"): str,
    }
)


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for XiaoTu Door."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                # # For debugging
                # user_input["proxy_config"] = {
                #     "ca_path": "/workspaces/proxyman-ca.pem",
                #     "url": "http://172.16.3.33:8888",
                # }

                account = XiaoTuAccount(user_input)
                user = await account.get_user()

                # Add init token
                auth = account.api.auth
                user_input["init_token"] = {
                    "token_id": auth.token_id,
                    "fetched_at": auth.fetched_at.isoformat(),
                }
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                username = user_input[CONF_USERNAME]
                title = "XiaoTu Door - " + user.villageName

                await self.async_set_unique_id(username)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
