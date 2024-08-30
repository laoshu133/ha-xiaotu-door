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

        [setattr(self, k, v) for k, v in data.items()]

    async def push_state(self, entity, data: dict) -> None:
        """Push state to server."""

        _LOGGER.info(1111)

        await asyncio.sleep(3)

        self.set_state(data)

        _LOGGER.info(22222)
        _LOGGER.info(self)

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

    def __init__(self, base_data: dict) -> None:
        """Initialize Device."""
        super().__init__(base_data)

        self.is_locked = True
