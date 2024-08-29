"""DAO."""

# from typing import TYPE_CHECKING

# if TYPE_CHECKING:
#     from .device_zone import DeviceZone


class Device:
    """Base Device."""

    def __init__(self, base_data: dict) -> None:
        """Initialize entity."""

        self.id = ""
        self.name: str = ""
        self.model: str = ""
        self.brand_name: str = ""
        self.alias: str = ""
        self.zone_id: str = ""
        self.fetched_at = None

        self.update_state(base_data)

    def update_state(self, data: dict) -> None:
        """Update the state."""

        [setattr(self, k, v) for k, v in data.items()]

    # # # # # # # # # # # # # # #
    # Generic attributes
    # # # # # # # # # # # # # # #

    # @property
    # def name(self) -> str:
    #     """Get the name of the model."""
    #     return self.data["name"]

    # @property
    # def id(self) -> str:
    #     """Get the id of the model."""
    #     return self.data["id"]


class Zone:
    """Zone."""

    def __init__(
        self,
        base_data: dict,
    ) -> None:
        """Initialize a device model."""

        self.id = ""
        self.name: str = ""
        self.alias: str = ""
        self.account = None
        self.fetched_at = None
        self.devices: list[Device] = []

        self.update_state(base_data)

        # Debug
        self.add_device({"id": "1", "name": "Device 1"})

    def update_state(self, data: dict) -> None:
        """Update the state."""

        [setattr(self, k, v) for k, v in data.items()]

    async def get_devices(self) -> None:
        """Fetch devices."""
        await self.fetch_state()

    def get_device(self, id: str):
        """Get a device by id."""
        for device in self.devices:
            if device.id == id:
                return device

        return None

    def add_device(self, base_data: dict) -> None:
        """Add a device to the zone."""
        self.devices.append(Device(self, base_data))

    async def fetch_state(self) -> None:
        """Retrieve data from servers."""

        new_data = {"a": 1, "b": 2}

        self.update_state(new_data)

    # # # # # # # # # # # # # # #
    # Generic attributes
    # # # # # # # # # # # # # # #

    # @property
    # def name(self) -> str:
    #     """Get the name of the model."""
    #     return self.data["name"]

    # @property
    # def id(self) -> str:
    #     """Get the id of the model."""
    #     return self.data["id"]


class BaseDevice(Device):
    """Base Device."""

    def __init__(self, base_data: dict) -> None:
        """Initialize Base Device."""
        super().__init__(base_data)

        self.brand_name = "XiaoTu"


class Lock(BaseDevice):
    """Lock Device."""

    def __init__(self, base_data: dict) -> None:
        """Initialize Device."""
        super().__init__(base_data)

        self.model = "xiaotu_lock"
        self.is_locked = False
