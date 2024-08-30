"""Access to a XiaoTU account."""

from dataclasses import dataclass, field
import datetime

# import json
import logging

from .dao import BaseDevice, LockDevice

VALID_UNTIL_OFFSET = datetime.timedelta(seconds=10)

_LOGGER = logging.getLogger(__name__)


@dataclass
class XiaoTuAccount:
    """Create a new connection to the XiaoTu web service."""

    devices: list[BaseDevice] = field(default_factory=list, init=False)

    def __init__(self, config: dict) -> None:
        """Initialize the account."""

        self.devices = []
        self.fetched_at = None
        self.config = {
            **config,
            "refresh_token": "",
            "access_token": "",
        }

        # Debug
        self.add_device({"id": "1", "type": "lock", "name": "Lock 001"})

    async def _init_devices(self) -> None:
        """Initialize devices from servers."""
        _LOGGER.debug("Init device list")

        self.fetched_at = datetime.datetime.now(datetime.UTC)

    async def get_devices(self, force_init: bool = False) -> None:
        """Retrieve device data from servers."""
        _LOGGER.debug("Getting device list")

        if len(self.devices) == 0 or force_init:
            await self._init_devices()

        # error_count = 0
        # for device in self.devices:
        #     # Get the detailed device state
        #     try:
        #         await device.get_device_state()
        #     except (XiaoTuAPIError, json.JSONDecodeError) as ex:
        #         # We don't want to fail completely if one device fails, but we want to know about it
        #         error_count += 1

        #         # If it's a XiaoTuQuotaError or XiaoTuAuthError, we want to raise it
        #         if isinstance(ex, (XiaoTuQuotaError, XiaoTuAuthError)):
        #             raise ex  # noqa: TRY201

        #         # Always log the error
        #         _LOGGER.error(
        #             "Unable to get details for device %s - (%s) %s",
        #             device.id,
        #             type(ex).__name__,
        #             ex,
        #         )

        #         # If all devices fail, we want to raise an exception
        #         if error_count == len(self.devices):
        #             raise ex  # noqa: TRY201

    def add_device(
        self,
        data: dict,
        fetched_at: datetime.datetime | None = None,
    ) -> None:
        """Add a device."""

        existing_device = self.get_device(data["id"])

        # If device already exists, just update it's state
        if existing_device:
            existing_device.update_state(data)
        else:
            clssMap = {
                "lock": LockDevice,
                "device": BaseDevice,
            }

            Cls = clssMap.get(data["type"], BaseDevice)
            self.devices.append(Cls(data))

    def get_device(self, id: str) -> BaseDevice | None:
        """Get device with given id.

        The search is NOT case sensitive.
        :param id: ID of the device you want to get.
        :return: Returns None if no device is found.
        """
        for device in self.devices:
            if device.id.upper() == id.upper():
                return device
        return None

    def set_token(
        self,
        refresh_token: str,
        access_token: str | None = None,
    ) -> None:
        """Overwrite the current value of the XiaoTu tokens."""
        self.config["refresh_token"] = refresh_token

        if access_token:
            self.config["access_token"] = access_token

    @property
    def refresh_token(self) -> str | None:
        """Returns the current refresh_token."""
        return self.config["refresh_token"]
