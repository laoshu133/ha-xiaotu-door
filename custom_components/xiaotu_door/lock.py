"""Platform for xiaotu lock integration."""

from __future__ import annotations

import logging

from homeassistant.components.lock import LockEntity
from homeassistant.core import HomeAssistant, callback

from .coordinator import XiaoTuCoordinator
from .dao import DaoEntity, XiaoTuDevice
from .entity import BaseEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    """Perform the setup for XiaoTu Door devices."""
    coordinator = config_entry.coordinator

    entities = [
        XiaoTuDoorLock(coordinator, device, daoEntity)
        for device in coordinator.account.devices
        if device.type == "village"
        for daoEntity in await device.get_entities()
        if daoEntity.type == "lock"
    ]

    _LOGGER.info("Lock.setup: %s", entities)

    async_add_entities(entities)


class XiaoTuDoorLock(BaseEntity, LockEntity):
    """A XiaoTu Door Lock."""

    device: XiaoTuDevice
    _attr_translation_key = "lock"

    def __init__(
        self,
        coordinator: XiaoTuCoordinator,
        device: XiaoTuDevice,
        daoEntity: DaoEntity,
    ) -> None:
        """Initialize the lock."""
        super().__init__(coordinator, device, daoEntity)

        self._attr_is_locked = self.get_locked_state()

    def get_locked_state(self) -> bool:
        """Get lock locked state."""
        return self.daoEntity.get("isOpen", "2") == "2"

    async def async_lock(self, **kwargs) -> None:
        """Lock the door."""

        # Locking the door
        self._attr_is_locking = True
        self.async_write_ha_state()

        await self.device.push_entity_state(self, {"is_locked": True})

    async def async_unlock(self, **kwargs) -> None:
        """Unlock the door."""

        # Unlocking the door
        self._attr_is_unlocking = True
        self.async_write_ha_state()

        await self.device.push_entity_state(self, {"is_locked": False})

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.info("Updating lock data of %s", self.daoEntity.name)

        # Update the HA state
        is_locked = self.get_locked_state()
        if self._attr_is_locked != is_locked:
            self._attr_is_locked = is_locked

        # Reset ing state
        self._attr_is_unlocking = False
        self._attr_is_locking = False

        # self.async_write_ha_state
        super()._handle_coordinator_update()
