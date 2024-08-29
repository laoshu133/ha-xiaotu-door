"""Support for XiaoTu service."""

import asyncio
import logging

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.components.lock import LockEntity
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)


class XiaoTuService:
    """Service handles XiaoTu door."""

    def __init__(self, config: dict) -> None:
        """Initialize."""
        self.host = config[CONF_HOST]
        self.username = config[CONF_USERNAME]
        self.password = config[CONF_PASSWORD]
        self.user = None

    async def authenticate(self):
        """Test if we can authenticate with the host."""

        # user = await self._authenticate()
        auth_data = {
            "code": "success",
            "msg": "",
            "data": {"uid": 1, "username": "test"},
        }

        if auth_data["code"] != "success":
            raise ResError(auth_data["code"], auth_data["msg"], auth_data["data"])

        self.user = auth_data["data"]

        return self.user

    async def get_devices(self, type: str):
        """Get devices."""

        devices = [
            Lock(is_locked=True, unique_id="lock_1"),
            Lock(is_locked=False, unique_id="lock_2"),
        ]

        # filter devices by type
        return [device for device in devices if device.type == type]


class Lock:
    """A XiaoTu lock device."""

    def __init__(self, is_locked=False, unique_id=None) -> None:
        """Initialize the device."""
        self.type = "lock"
        self.unique_id = unique_id
        self.is_locked = is_locked
        self._timer = None

    def lock(self, **kwargs):
        """Lock the lock."""
        self.is_locked = True

    def unlock(self, lockEntity: LockEntity):
        """Unlock the lock."""

        # reset the lock status after 5 seconds
        if self._timer:
            self._timer.cancel()
        self._timer = asyncio.create_task(self.reset_lock_state(lockEntity))

        self.is_locked = False

    async def reset_lock_state(self, lockEntity: LockEntity):
        """Reset the lock state."""
        await asyncio.sleep(2)
        lockEntity.lock()


class ResError(HomeAssistantError):
    """Error to indicate a request failed."""

    def __init__(self, code: str, message: str, data: dict) -> None:
        """Initialize."""
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data
