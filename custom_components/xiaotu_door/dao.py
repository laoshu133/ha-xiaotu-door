"""DAO."""


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

        self.is_locked = True
