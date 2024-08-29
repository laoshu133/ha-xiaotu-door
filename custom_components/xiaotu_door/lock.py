"""Platform for xiaotu lock integration."""

from __future__ import annotations

import logging

from homeassistant.components.lock import LockEntity
from homeassistant.core import HomeAssistant, callback

from .base_device import BaseDeivce
from .coordinator import XiaoTuCoordinator
from .entity import BaseEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    """Perform the setup for XiaoTu Door devices."""
    coordinator = config_entry.coordinator

    entities = [
        XiaoTuDoorLock(coordinator, device)
        for zone in coordinator.account.zones
        for device in zone.devices
        if device.type == "lock"
    ]

    async_add_entities(entities)


class XiaoTuDoorLock(BaseEntity, LockEntity):
    """A XiaoTu Door Lock."""

    _attr_translation_key = "lock"

    def __init__(self, coordinator: XiaoTuCoordinator, device: BaseDeivce) -> None:
        """Initialize the lock."""
        super().__init__(coordinator, device)

        # self.name = "A XiaoTu Door Lock"
        self._attr_unique_id = f"{device.zone.id}_{device.id}"
        self._attr_is_locked = device.is_locked

    async def async_lock(self, **kwargs) -> None:
        """Lock the door."""
        _LOGGER.debug("%s: locking doors", self.device.name)

        # Optimistic state set here because it takes some time before the update callback response
        self._attr_is_locked = True
        self.async_write_ha_state()

        # Always update the listeners to get the latest state
        self.coordinator.async_update_listeners()

    async def async_unlock(self, **kwargs) -> None:
        """Unlock the door."""
        # Optimistic state set here because it takes some time before the update callback response
        self._attr_is_locked = False
        self.async_write_ha_state()

        # Always update the listeners to get the latest state
        self.coordinator.async_update_listeners()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug("Updating lock data of %s", self.device.name)

        # Update the HA state
        if self.device.is_locked != self._attr_is_locked:
            self._attr_is_locked = self.device.is_locked

        super()._handle_coordinator_update()
