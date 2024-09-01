"""DAO."""

import asyncio
from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING

from .utils import AuthError, get_now

if TYPE_CHECKING:
    from .entity import BaseEntity

_LOGGER = logging.getLogger(__name__)


@dataclass
class DaoEntity:
    """Base Entity for DAO."""

    data: dict

    def __init__(self, data: dict) -> None:
        """Initialize entity."""
        self.data = {}

        self.update(data)

    def get(self, key: str, default_val=""):
        """Get value by key."""
        return self.data.get(key, default_val)

    def update(self, data: dict) -> None:
        """Update the state."""
        self.data.update(data)

    @property
    def id(self) -> str:
        """Get id of the entity."""
        return self.data.get("id", "")

    @property
    def type(self) -> str:
        """Get type of the entity."""
        return self.data.get("type", "")

    @property
    def name(self) -> str:
        """Get name of the entity."""
        return self.data.get("name", "")


class BaseDevice:
    """Base Device."""

    def __init__(self, account, base_data: dict) -> None:
        """Initialize entity."""

        self.account = account
        self.entities: list[DaoEntity] = []
        self.fetched_at = None

        self.id = ""
        self.type: str = "unknown"
        self.name: str = ""
        self.brand_name: str = ""

        self.update_state(base_data)

    async def _init_entities(self) -> None:
        """Initialize entities from servers."""
        _LOGGER.debug("Init entity list")

        entities = self.entities
        if len(entities) == 0:
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

                self.add_entity(info)

        self.fetched_at = get_now()

    async def get_entities(self, force_init: bool = False) -> list[DaoEntity]:
        """Retrieve entity data from servers."""

        if len(self.entities) == 0 or force_init:
            await self._init_entities()

        return self.entities

    def _add_entity(self, data: dict) -> DaoEntity:
        """Add a entity."""

        entity = DaoEntity(data)
        self.entities.append(entity)
        return entity

    def add_entity(self, data: dict) -> DaoEntity:
        """Add a entity."""

        entity = self.get_entity(data["id"])

        # If entity already exists, just update it's state
        if entity:
            entity.update_state(data)
        else:
            entity = self._add_entity(data)

        return entity

    def get_entity(self, id: str) -> DaoEntity | None:
        """Get DaoEntity with given id.

        The search is NOT case sensitive.
        :param id: ID of the entity you want to get.
        :return: Returns None if no entity is found.
        """
        for entity in self.entities:
            if entity.id.upper() == id.upper():
                return entity
        return None

    def _update_entity(self, entity: DaoEntity, data: dict) -> None:
        """Update entity with given data."""
        entity.update(data)

    def update_entity(self, idOrEntity: str | DaoEntity, data: dict) -> None:
        """Update entity with given data."""
        entity = (
            idOrEntity
            if isinstance(idOrEntity, DaoEntity)
            else self.get_entity(idOrEntity)
        )
        if entity:
            self._update_entity(entity, data)

    async def _push_entity_state(self, entity, data: dict) -> None:
        """Push state to server."""
        account = entity.coordinator.account
        await account.get_entities()

    async def push_entity_state(self, entity, data: dict) -> None:
        """Push state to server."""

        try:
            try:
                await self._push_entity_state(entity, data)
            except AuthError:
                # Try again when the authorization expires
                await self._push_entity_state(entity, data)

            # Always delay for a few seconds
            await asyncio.sleep(0.6)
        finally:
            self.update_state(data)

            # Always update the listeners to get the latest state
            if entity.coordinator:
                entity.coordinator.async_update_listeners()

    async def push_state(self, entity, data: dict) -> None:
        """Push state to server."""

        # Simulate a push to the server
        await asyncio.sleep(0.8)

        self.update_state(data)

        # Always update the listeners to get the latest state
        if entity.coordinator:
            entity.coordinator.async_update_listeners()

    def update_state(self, data: dict) -> None:
        """Update the state."""

        for key in data:
            if hasattr(self, key):
                setattr(self, key, data[key])

    @property
    def api(self) -> str:
        """Get a api of the device."""
        return self.account.api

    @property
    def serial_number(self) -> str:
        """Get a serial number of the device."""
        return self.account.user.userId


class XiaoTuDevice(BaseDevice):
    """XiaoTu Device."""

    def __init__(self, account, base_data: dict) -> None:
        """Initialize Device."""
        super().__init__(account, base_data)

        self.brand_name = "XiaoTu"

    def _update_entity(self, entity: DaoEntity, data: dict) -> None:
        """Update entity with given data."""
        super()._update_entity(data)

        # self.is_locked = data.get("isOpen", "2") == "2"

        img_map = data.get("imageItem", {})
        self.data.update(
            {"image": img_map.get("originalImage", self.data.get("image"))}
        )

    async def _push_entity_state(self, entity, data: dict) -> None:
        """Push state to server."""
        account = entity.coordinator.account
        auth = await account.api.get_auth()

        # Open the door
        if not data.get("is_locked"):
            params = {
                "clientId": auth.client_id,
                "doorId": entity.daoEntity.get("doorId"),
                "longitude": "",
                "latitude": "",
            }

            _LOGGER.info("XiaoTuDevice._push_entity_state: %s", params)

            await account.api.get(
                "/wap/door/openDoorNew",
                params=params,
                headers={"tokenId": auth.token_id},
            )

        # Close the door
        # Do nothing
