"""Base Device."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .device_zone import DeviceZone


class BaseDeivce:
    """Base Device."""

    def __init__(self, zone: "DeviceZone", base_data: dict) -> None:
        """Initialize entity."""

        self.zone = zone
        self.data = {**base_data}

    async def async_update(self, data: dict) -> None:
        """Update the state."""

        self.data = {**data}

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
