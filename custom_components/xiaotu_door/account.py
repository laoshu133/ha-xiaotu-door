"""Access to a XiaoTU account."""

from base64 import b64decode
from dataclasses import dataclass, field

# import json
import logging

from .api import API, APIConfiguration
from .dao import BaseDevice, LockDevice
from .utils import get_now

_LOGGER = logging.getLogger(__name__)


@dataclass
class XiaoTuUser:
    """XiaoTu user data."""

    userId: str = ""  # noqa: N815
    name: str = ""
    mobile: str = ""
    province: str = ""
    city: str = ""
    district: str = ""
    villageId: str = ""  # noqa: N815
    villageName: str = ""  # noqa: N815
    villageMobile: str = ""  # noqa: N815
    building: str = ""
    houseId: str = ""  # noqa: N815
    fetched_at = None


@dataclass
class XiaoTuAccount:
    """Create a new connection to the XiaoTu web service."""

    devices: list[BaseDevice] = field(default_factory=list, init=False)

    def __init__(self, config: dict) -> None:
        """Initialize the account."""

        _LOGGER.info("XiaoTuAccount.config: %s", config)
        api_config = APIConfiguration(**config)

        self.api_config = api_config
        self.api = API(self.api_config)
        self.user = XiaoTuUser()
        self.devices = []
        self.fetched_at = None

    async def get_user(self) -> XiaoTuUser:
        """Get the user info."""

        user = self.user
        if not user.userId:
            auth = await self.api.get_auth()

            res = await self.api.post(
                "/userClient/cuserV2/getUserInfoV2", data=auth.toJSON()
            )
            ret = res.json()["result"]

            for key in ret:
                if hasattr(user, key):
                    setattr(user, key, ret[key])

            # Decode mobile
            user.mobile = b64decode(user.mobile).decode()

        # Get village info
        # POST /userClient/cuserV2/getUserVillageV2

        return user

    async def _init_devices(self) -> None:
        """Initialize devices from servers."""
        _LOGGER.debug("Init device list")

        devices = self.devices
        if len(devices) == 0:
            auth = await self.api.get_auth()
            params = {
                "tokenId": auth.token_id,
            }

            res = await self.api.get(
                "/wap/door/getDoor",
                params=params,
                headers={
                    "tokenId": auth.token_id,
                },
            )
            ret = res.json()["result"]

            for info in ret:
                # Filter doorType is door and status is 0
                if info["doorType"] != "door" and info["status"] != "0":
                    continue

                # Override type
                info["_type"] = info["type"]
                info["type"] = "lock"

                self.add_device(info)

        self.fetched_at = get_now()

    async def get_devices(self, force_init: bool = False) -> list[BaseDevice]:
        """Retrieve device data from servers."""
        _LOGGER.debug("Getting device list")

        if len(self.devices) == 0 or force_init:
            await self._init_devices()

        return self.devices

    def add_device(self, data: dict) -> BaseDevice:
        """Add a device."""

        device = self.get_device(data["id"])

        # If device already exists, just update it's state
        if device:
            device.update_state(data)
        else:
            clssMap = {
                "lock": LockDevice,
                "device": BaseDevice,
            }

            Cls = clssMap.get(data["type"], BaseDevice)
            device = Cls(data)

            self.devices.append(device)

        return device

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
