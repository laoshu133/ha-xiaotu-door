"""Base for all entities."""

from __future__ import annotations

import logging

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import XiaoTuCoordinator
from .dao import DaoEntity, XiaoTuDevice

_LOGGER = logging.getLogger(__name__)


class BaseEntity(CoordinatorEntity[XiaoTuCoordinator]):
    """Common base for all entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: XiaoTuCoordinator,
        device: XiaoTuDevice,
        daoEntity: DaoEntity,
    ) -> None:
        """Initialize entity."""
        super().__init__(coordinator)

        self.daoEntity = daoEntity
        self.device = device

        self._attr_name = daoEntity.name
        self._attr_unique_id = f"{DOMAIN}_{daoEntity.type}_{daoEntity.id}"

        self._attr_device_info = DeviceInfo(
            serial_number=device.serial_number,
            manufacturer=device.brand_name,
            identifiers={(DOMAIN, device.id)},
            model=f"{DOMAIN}.{device.type}",
            name=device.name,
        )

        # _LOGGER.info("Entity.setup_device_info: %s", self._attr_device_info)

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    # @property
    # def name(self):
    #     """Get name of the entity."""
    #     return "%s_%s" % (self._data_key, self._unique_id)
