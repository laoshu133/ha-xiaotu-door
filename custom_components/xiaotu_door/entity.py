"""Base for all entities."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import XiaoTuCoordinator
from .dao import BaseDevice


class BaseEntity(CoordinatorEntity[XiaoTuCoordinator]):
    """Common base for all entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: XiaoTuCoordinator,
        device: BaseDevice,
    ) -> None:
        """Initialize entity."""
        super().__init__(coordinator)

        self.device = device

        self._attr_name = ""
        self._attr_unique_id = f"{DOMAIN}_{device.type}_{device.id}"
        self._attr_device_info = DeviceInfo(
            manufacturer=device.brand_name,
            identifiers={(DOMAIN, device.id)},
            model={(DOMAIN, ".", device.type)},
            name=device.name,
            # serial_number=device.id,
        )

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()
