"""Protocols module for PLC interfaces."""
from abc import ABCMeta
from typing import (
    _ProtocolMeta,
    Protocol,
    runtime_checkable,
)


class IFactoryMixinProtocolMeta(_ProtocolMeta, ABCMeta):
    """Metaclass for factory mixin protocols."""
    pass


@runtime_checkable
class IConfigurable(Protocol):
    """Protocol for objects that support configuration."""

    @property
    def config(self) -> dict:
        """Get the current configuration of the object.

        Returns:
            dict: Current configuration settings.
        """
        return self.get_config()

    def configure(self, config: dict) -> None:
        """Configure the object with the given settings.

        Args:
            config (dict): Configuration settings.
        """
        ...

    def get_config(self) -> dict:
        """Get the current configuration of the object.

        Returns:
            dict: Current configuration settings.
        """
        ...


@runtime_checkable
class IAuthored(Protocol):
    """Protocol for objects that have an author."""

    @property
    def author(self) -> str:
        """Get the author of this object.

        Returns:
            str: The author of this object.
        """
        return self.get_author()

    def get_author(self) -> str:
        """Get the author of this object.

        Returns:
            str: The author of this object.
        """
        ...


@runtime_checkable
class IVersioned(Protocol):
    """Protocol for objects that have a version."""

    @property
    def version(self) -> str:
        """Get the version of this object.

        Returns:
            str: The version of this object.
        """
        return self.get_version()

    def get_version(self) -> str:
        """Get the version of this object.

        Returns:
            str: The version of this object.
        """
        ...


@runtime_checkable
class INameable(Protocol):
    """Protocol for objects that have a name."""

    @property
    def name(self) -> str:
        """Get the name of this object.

        Returns:
            str: The name of this object.
        """
        return self.get_name()

    @name.setter
    def name(self, name: str) -> None:
        """Set the name of this object.

        Args:
            name (str): The name to set.
        """
        self.set_name(name)

    def get_name(self) -> str:
        """Get the name of this object.

        Returns:
            str: The name of this object.
        """
        ...

    def set_name(self, name: str) -> None:
        """Set the name of this object.

        Args:
            name (str): The name to set.
        """
        ...


@runtime_checkable
class IDescribable(Protocol):
    """Protocol for objects that have a description."""

    @property
    def description(self) -> str:
        """Get the description of this object.

        Returns:
            str: The description of this object.
        """
        return self.get_description()

    @description.setter
    def description(self, description: str) -> None:
        """Set the description of this object.

        Args:
            description (str): The description to set.
        """
        self.set_description(description)

    def get_description(self) -> str:
        """Get the description of this object.

        Returns:
            str: The description of this object.
        """
        ...

    def set_description(self, description: str) -> None:
        """Set the description of this object.

        Args:
            description (str): The description to set.
        """
        ...


@runtime_checkable
class IRefreshable(Protocol):
    """Protocol for objects that support refreshing."""

    def refresh(self) -> None:
        """Refresh the object's state."""
        ...


@runtime_checkable
class IResettable(Protocol):
    """Protocol for objects that support resetting."""

    def reset(self) -> None:
        """Reset the object's state."""
        ...


@runtime_checkable
class IBuildable(Protocol):
    """Protocol for objects that support building."""

    @property
    def built(self) -> bool:
        """Check if the object is built.

        Returns:
            bool: True if built, False otherwise.
        """
        return self.is_built()

    def build(self) -> None:
        """Build or initialize the object."""
        ...

    def teardown(self) -> None:
        """Tear down or clean up the object."""
        ...

    def is_built(self) -> bool:
        """Check if the object is built.

        Returns:
            bool: True if built, False otherwise.
        """
        ...


@runtime_checkable
class IRunnable(Protocol):
    """Protocol for objects that support running."""

    @property
    def running(self) -> bool:
        """Check if the object is running.

        Returns:
            bool: True if running, False otherwise.
        """
        return self.is_running()

    def run(self) -> int:
        """Start running the object.

        Returns:
            int: Exit code when the run completes.
        """
        ...

    def quit(self, exit_code: int = 0) -> None:
        """Quit running the object."""
        self.stop(exit_code)

    def stop(self, stop_code: int = 0) -> None:
        """Stop running the object.

        Args:
            stop_code (int): The code indicating the reason for stopping.
        """
        ...

    def is_running(self) -> bool:
        """Check if the object is running.

        Returns:
            bool: True if running, False otherwise.
        """
        ...


__all__ = [
    "IConfigurable",
    "IAuthored",
    "IVersioned",
    "INameable",
    "IDescribable",
    "IRefreshable",
    "IResettable",
    "IBuildable",
    "IRunnable",

]
