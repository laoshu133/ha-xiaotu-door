"""Models state and remote services of one entity."""

import datetime
import logging
from typing import TYPE_CHECKING

# from typing import Dict, List, Optional, Tuple, Type, Union
from .base_device import BaseDeivce

if TYPE_CHECKING:
    from .account import XiaoTuAccount

_LOGGER = logging.getLogger(__name__)


class DeviceZone:
    """Models state and remote services of entity."""

    def __init__(
        self,
        account: "XiaoTuAccount",
        base_data: dict,
    ) -> None:
        """Initialize a device model."""
        self.account = account
        self.fetched_at = None
        self.devices = []
        self.data = {}

        # Debug
        self.add_device({"id": "1", "name": "Device 1", "brand_name": "XiaoTu"})

    async def get_devices(self) -> None:
        """Fetch devices."""
        await self.fetch_state()

    def get_device(self, id: str) -> BaseDeivce:
        """Get a device by id."""
        for device in self.devices:
            if device.id == id:
                return device

        return None

    def add_device(self, base_data: dict) -> None:
        """Add a device to the zone."""
        self.devices.append(BaseDeivce(self, base_data))

    async def fetch_state(self) -> None:
        """Retrieve data from servers."""

        new_data = {"a": 1, "b": 2}

        self.update_state(new_data)

    def update_state(
        self,
        data: dict | list[dict],
    ) -> None:
        """Update the state."""
        fetched_at = datetime.datetime.now(datetime.UTC)

        data["fetched_at"] = fetched_at
        self.data = data

        # update_entities: List[Tuple[Type[VehicleDataBase], str]] = [
        #     (FuelAndBattery, "fuel_and_battery"),
        #     (VehicleLocation, "vehicle_location"),
        #     (DoorsAndWindows, "doors_and_windows"),
        #     (ConditionBasedServiceReport, "condition_based_services"),
        #     (CheckControlMessageReport, "check_control_messages"),
        #     (Headunit, "headunit"),
        #     (Climate, "climate"),
        #     (ChargingProfile, "charging_profile"),
        #     (Tires, "tires"),
        # ]
        # for cls, vehicle_attribute in update_entities:
        #     try:
        #         if getattr(self, vehicle_attribute) is None:
        #             setattr(
        #                 self, vehicle_attribute, cls.from_vehicle_data(vehicle_data)
        #             )
        #         else:
        #             curr_attr: VehicleDataBase = getattr(self, vehicle_attribute)
        #             curr_attr.update_from_vehicle_data(vehicle_data)
        #     except (KeyError, TypeError) as ex:
        #         _LOGGER.warning(
        #             "Unable to update %s - (%s) %s",
        #             vehicle_attribute,
        #             type(ex).__name__,
        #             ex,
        #         )

    # # # # # # # # # # # # # # #
    # Generic attributes
    # # # # # # # # # # # # # # #

    @property
    def brand_name(self) -> str:
        """Get the brand name."""
        return self.data["brand_name"]

    @property
    def name(self) -> str:
        """Get the name of the model."""
        return self.data["name"]

    @property
    def id(self) -> str:
        """Get the id of the model."""
        return self.data["id"]
