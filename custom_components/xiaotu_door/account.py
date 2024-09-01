"""Access to a XiaoTu account."""

from base64 import b64decode
from dataclasses import dataclass, field

# import json
import logging

from .api import API, APIConfiguration
from .dao import XiaoTuDevice

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

    devices: list[XiaoTuDevice] = field(default_factory=list, init=False)

    def __init__(self, config: dict) -> None:
        """Initialize the account."""

        # Only for debugging
        # _LOGGER.info("XiaoTuAccount.config: %s", config)

        api_config = APIConfiguration(**config)

        self.api_config = api_config
        self.api = API(self.api_config)
        self.user = XiaoTuUser()

        self.devices = []
        self.devices_info_map = {}

        self.fetched_at = None

    async def get_user(self, force_init: bool = False) -> XiaoTuUser:
        """Get the user info."""

        user = self.user
        if not user.userId or force_init:
            auth = await self.api.get_auth()

            res = await self.api.post(
                "/userClient/cuserV2/getUserInfoV2", data=auth.toJSON(auth)
            )
            ret = res.json()["result"]

            for key in ret:
                if hasattr(user, key):
                    setattr(user, key, ret[key])

            # Decode mobile
            user.mobile = b64decode(user.mobile).decode()

        # Get village info
        # Only support 1 village/house now
        # POST /userClient/cuserV2/getUserVillageV2

        return user

    async def get_devices(self, force_init: bool = False) -> list[XiaoTuDevice]:
        """Retrieve device data from servers."""

        # Only support 1 village/house
        if len(self.devices) == 0 or force_init:
            user = await self.get_user(force_init=force_init)

            self.add_device(
                {"type": "village", "id": user.villageId, "name": user.villageName}
            )

        return self.devices

    def add_device(self, data: dict) -> XiaoTuDevice:
        """Add a device."""

        device = self.get_device(data["id"])

        # If device already exists, just update it's state
        if device:
            device.update_state(data)
        else:
            device = XiaoTuDevice(account=self, base_data=data)

            self.devices.append(device)

        return device

    def get_device(self, id: str) -> XiaoTuDevice | None:
        """Get device with given id."""
        return next((device for device in self.devices if device.id == id), None)
