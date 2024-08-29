"""Base for all entities."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .base_device import BaseDeivce
from .const import DOMAIN
from .coordinator import XiaoTuCoordinator


class BaseEntity(CoordinatorEntity[XiaoTuCoordinator]):
    """Common base for all entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: XiaoTuCoordinator,
        device: BaseDeivce,
    ) -> None:
        """Initialize entity."""
        super().__init__(coordinator)

        self.device = device

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.id)},
            manufacturer=device.name,
            model=device.name,
            name=device.name,
            serial_number=device.id,
        )

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()
