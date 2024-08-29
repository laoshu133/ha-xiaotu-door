"""The XiaoTu Door integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN
from .coordinator import XiaoTuCoordinator

PLATFORMS: list[Platform] = [Platform.LOCK]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up XiaoTu Door from a config entry."""

    # _LOGGER.info(entry)
    _LOGGER.info(f"{DOMAIN}: {entry.entry_id}")  # noqa: G004

    # Set up one data coordinator per account/config entry
    coordinator = XiaoTuCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.coordinator = coordinator

    # Set up all platforms except notify
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Clean up devices which are not assigned to the account anymore
    account_devices = {(DOMAIN, v.vin) for v in coordinator.account.devices}
    device_registry = dr.async_get(hass)
    device_entries = dr.async_entries_for_config_entry(
        device_registry, config_entry_id=entry.entry_id
    )
    for device in device_entries:
        if not device.identifiers.intersection(account_devices):
            device_registry.async_update_device(
                device.id, remove_config_entry_id=entry.entry_id
            )

    # # Initialize the service
    # entry.service = XiaoTuService(entry.data)

    # await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
