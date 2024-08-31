"""DAO."""

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .entity import BaseEntity

_LOGGER = logging.getLogger(__name__)


class Device:
    """Base Device."""

    def __init__(self, base_data: dict) -> None:
        """Initialize entity."""

        self.id = ""
        self.type: str = "unknown"
        self.name: str = ""
        self.model: str = ""
        self.brand_name: str = ""
        self.alias: str = ""
        self.fetched_at = None

        self.set_state(base_data)

    def set_state(self, data: dict) -> None:
        """Update the state."""

        for key in data:
            if hasattr(self, key):
                setattr(self, key, data[key])

    async def push_state(self, entity, data: dict) -> None:
        """Push state to server."""

        # Simulate a push to the server
        await asyncio.sleep(1)

        self.set_state(data)

        # Always update the listeners to get the latest state
        if entity.coordinator:
            entity.coordinator.async_update_listeners()

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


class LockDevice(BaseDevice):
    """Lock Device."""

    id: str = ""
    doorId: str = ""  # noqa: N815
    doorType: str = ""  # noqa: N815
    name: str = ""
    address: str = ""
    image: str = ""
    uCode: str = ""  # noqa: N815

    def __init__(self, base_data: dict) -> None:
        """Initialize Device."""
        super().__init__(base_data)

        self.is_locked = True

    def set_state(self, data: dict) -> None:
        """Update the state."""

        super().set_state(data)

        self.is_locked = data.get("isOpen", "2") == "2"

        img_map = data.get("imageItem", {})
        self.image = img_map.get("originalImage", "")

    async def push_state(self, entity, data: dict) -> None:
        """Push state to server."""

        account = entity.coordinator.account
        auth = await account.get_auth()

        # Open the door
        params = {
            "clientId": auth.client_id,
            "doorId": self.doorId,
            "longitude": "",
            "latitude": "",
        }
        await account.api.get(
            "/wap/door/openDoorNew", params=params, headers={"tokenId": auth.token_id}
        )

        # Delay to simulate the door opening
        await asyncio.sleep(1)

        self.set_state(data)

        # Always update the listeners to get the latest state
        if entity.coordinator:
            entity.coordinator.async_update_listeners()
