"""Protocols for common interfaces used across Pyrox."""
from abc import ABC, abstractmethod


class IConfigurable(ABC):
    """ABC for objects that support configuration."""

    @abstractmethod
    def configure(self, config: dict) -> None: ...
    @abstractmethod
    def get_config(self) -> dict: ...
    @abstractmethod
    def set_config(self, config: dict) -> None: ...

    @property
    @abstractmethod
    def config(self) -> dict: ...


class IAuthored(ABC):
    """ABC for objects that have an author."""

    @abstractmethod
    def get_author(self) -> str: ...
    @abstractmethod
    def set_author(self, author: str) -> None: ...

    @property
    @abstractmethod
    def author(self) -> str: ...


class IVersioned(ABC):
    """ABC for objects that have a version."""

    @abstractmethod
    def get_version(self) -> str: ...
    @abstractmethod
    def set_version(self, version: str) -> None: ...

    @property
    @abstractmethod
    def version(self) -> str: ...


class IHasId(ABC):
    """ABC for objects that have an ID."""

    @abstractmethod
    def get_id(self) -> str: ...
    @abstractmethod
    def set_id(self, id_: str) -> None: ...

    @property
    @abstractmethod
    def id_(self) -> str: ...


class INameable(ABC):
    """ABC for objects that have a name."""

    @abstractmethod
    def get_name(self) -> str: ...
    @abstractmethod
    def set_name(self, name: str) -> None: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @name.setter
    @abstractmethod
    def name(self, name: str) -> None: ...


class IDescribable(ABC):
    """ABC for objects that have a description."""

    @abstractmethod
    def get_description(self) -> str: ...
    @abstractmethod
    def set_description(self, description: str) -> None: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @description.setter
    @abstractmethod
    def description(self, description: str) -> None: ...


class IRefreshable(ABC):
    """ABC for objects that support refreshing."""

    @abstractmethod
    def refresh(self) -> None: ...


class IResettable(ABC):
    """ABC for objects that support resetting."""

    @abstractmethod
    def reset(self) -> None: ...


class IBuildable(ABC):
    """ABC for objects that support building."""

    @abstractmethod
    def build(self) -> None: ...
    @abstractmethod
    def teardown(self) -> None: ...
    @abstractmethod
    def is_built(self) -> bool: ...

    @property
    @abstractmethod
    def built(self) -> bool: ...


class IRunnable(ABC):
    """ABC for objects that support running."""

    @abstractmethod
    def run(self) -> int: ...
    @abstractmethod
    def quit(self, exit_code: int = 0) -> None: ...
    @abstractmethod
    def stop(self, stop_code: int = 0) -> None: ...
    @abstractmethod
    def is_running(self) -> bool: ...

    @property
    @abstractmethod
    def running(self) -> bool: ...


class IHasFileLocation(ABC):
    """ABC for objects that support file location."""

    @abstractmethod
    def get_file_location(self) -> str: ...
    @abstractmethod
    def set_file_location(self, location: str) -> None: ...

    @property
    @abstractmethod
    def file_location(self) -> str: ...

    @file_location.setter
    @abstractmethod
    def file_location(self, location: str) -> None: ...


class IHasDictMetaData(ABC):
    """ABC for objects that support metadata."""

    @abstractmethod
    def get_meta_data(self) -> dict[str, object]: ...
    @abstractmethod
    def set_meta_data(self, meta_data: dict[str, object]) -> None: ...

    @property
    @abstractmethod
    def meta_data(self) -> dict[str, object]: ...
    @meta_data.setter
    @abstractmethod
    def meta_data(self, meta_data: dict[str, object]) -> None: ...


class IHasProperties(ABC):
    """ABC for objects that support properties."""

    @abstractmethod
    def get_property(self, name: str) -> object: ...
    @abstractmethod
    def set_property(self, name: str, value: object) -> None: ...
    @abstractmethod
    def get_properties(self) -> dict[str, object]: ...
    @abstractmethod
    def set_properties(self, properties: dict[str, object]) -> None: ...

    @property
    @abstractmethod
    def properties(self) -> dict[str, object]: ...


__all__ = [
    "IConfigurable",
    "IAuthored",
    "IVersioned",
    "IHasId",
    "INameable",
    "IDescribable",
    "IRefreshable",
    "IResettable",
    "IBuildable",
    "IRunnable",
    "IHasFileLocation",
    "IHasDictMetaData",
    "IHasProperties",
]
