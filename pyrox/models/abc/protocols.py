"""Protocol implementations for common object behaviors.
"""
from typing import Any, Optional, Union
from pyrox.interfaces import (
    IBuildable,
    IRunnable,
    INameable,
    IDescribable,
    IRefreshable,
    IResettable,
    ICoreRunnableMixin,
    IHasFileLocation,
    IHasDictMetaData,
    ISupportsItemAccess,
)


class Nameable(INameable):
    """Denotes object is 'nameable' and supports getting and setting name.

    This class provides a foundation for objects that have a name property,
    implementing the INameable protocol.
    """

    def __init__(
        self,
        name: str = ""
    ):
        self._name: str = name

    def get_name(self) -> str:
        """Get the name of this object.

        Returns:
            str: The name of this object.
        """
        return self._name

    def set_name(self, name: str) -> None:
        """Set the name of this object.

        Args:
            name (str): The name to set.
        """
        self._name = name


class Describable(IDescribable):
    """Denotes object is 'describable' and supports getting and setting description.

    This class provides a foundation for objects that have a description property,
    implementing the IDescribable protocol.
    """

    def __init__(
        self,
        description: str = ""
    ):
        self._description: str = description

    def get_description(self) -> str:
        """Get the description of this object.

        Returns:
            str: The description of this object.
        """
        return self._description

    def set_description(self, description: str) -> None:
        """Set the description of this object.

        Args:
            description (str): The description to set.
        """
        self._description = description


class Refreshable(IRefreshable):
    """Denotes object is 'refreshable' and supports refresh method.

    This class provides a foundation for objects that support refreshing,
    implementing the IRefreshable protocol.
    """

    def refresh(self) -> None:
        """Refresh this object.

        This method should be overridden by subclasses to implement
        specific refresh behavior.
        """
        ...


class Resettable(IResettable):
    """Denotes object is 'resettable' and supports reset method.

    This class provides a foundation for objects that support resetting,
    implementing the IResettable protocol.
    """

    def reset(self) -> None:
        """Reset this object.

        This method should be overridden by subclasses to implement
        specific reset behavior.
        """
        ...


class Buildable(IBuildable):
    """Denotes object is 'buildable' and supports build and refresh methods.

    This class provides a foundation for objects that have a build lifecycle,
    tracking whether the object has been built and providing methods for
    building and refreshing the object state.

    Attributes:
        built: Whether the object has previously been built.
    """

    def __init__(self):
        self._built: bool = False

    def build(self) -> None:
        """Build this object."""
        self._built = True

    def teardown(self) -> None:
        """Tear down this object."""
        self._built = False

    def refresh(self) -> None:
        """Refresh this object.

        This method should be overridden by subclasses to implement
        specific refresh behavior.
        """
        ...

    def is_built(self) -> bool:
        """Check if the object is built.

        Returns:
            bool: True if built, False otherwise.
        """
        return self._built


class Runnable(IRunnable):
    """Denotes object is 'runnable' and supports run method.

    This class extends Buildable to provide runtime state management,
    tracking whether the object is currently running and providing
    methods for starting and stopping execution.

    Attributes:
        running: Whether the object is currently in a running state.
    """

    def __init__(self):
        self._running: bool = False

    def run(self) -> int:
        """Start this object."""
        self._running = True
        return 0

    def stop(self, stop_code: int = 0) -> None:
        """Stop this object."""
        self._running = False

    def is_running(self) -> bool:
        """Check if the object is running.

        Returns:
            bool: True if running, False otherwise.
        """
        return self._running


class CoreRunnableMixin(
    ICoreRunnableMixin,
    Nameable,
    Describable,
    Runnable,
    Buildable,
):
    """Mixin class that acts as a core runnable with name and description.
    """

    def __init__(
        self,
        name: str = "",
        description: str = ""
    ):
        Buildable.__init__(self)
        Nameable.__init__(self, name)
        Describable.__init__(self, description)


class HasFileLocation(IHasFileLocation):
    """Denotes object supports file location access.

    This class provides a foundation for objects that have an associated
    file location, implementing the IHasFileLocation protocol.
    """

    def __init__(
        self,
        file_location: str = ""
    ):
        self._file_location: str = file_location

    def get_file_location(self) -> str:
        """Get the file location of this object.

        Returns:
            str: The file location of this object.
        """
        return self._file_location

    def set_file_location(self, location: str) -> None:
        """Set the file location of this object.

        Args:
            file_location (str): The file location to set.
        """
        self._file_location = location


class HasMetaDictData(IHasDictMetaData):
    """Denotes object supports meta data access.

    This class provides a foundation for objects that have associated
    meta data, implementing the IHasMetaData protocol.
    """

    def __init__(
        self,
        meta_data: Optional[dict[str, Any]] = None
    ):
        if meta_data is not None:
            self._meta_data: dict[str, Any] = meta_data
        else:
            self._meta_data: dict[str, Any] = dict()

    def get_metadata(self) -> dict[str, Any]:
        """Get the meta data of this object.

        Returns:
            dict[str, any]: The meta data of this object.
        """
        return self._meta_data

    def set_metadata(self, metadata: dict[str, Any]) -> None:
        """Set the meta data of this object.

        Args:
            meta_data (dict[str, any]): The meta data to set.
        """
        self._meta_data = metadata


class SupportsItemAccess(
    ISupportsItemAccess,
    HasMetaDictData
):
    """Denotes object supports item access via indexing.

    This class provides a foundation for objects that support item
    access through indexing, implementing the ISupportsItemAccess protocol.
    """

    def __getitem__(self, key: Any) -> Any:
        """Get an item by key.

        Args:
            key (Any): The key of the item to retrieve.

        Returns:
            Any: The item associated with the key.
        """
        return self.metadata[key]

    def __setitem__(self, key: Any, value: Any) -> None:
        """Set an item by key.

        Args:
            key (Any): The key of the item to set.
            value (Any): The value to associate with the key.
        """
        self.metadata[key] = value


__all__ = (
    'Nameable',
    'Describable',
    'Refreshable',
    'Resettable',
    'Buildable',
    'Runnable',
    'CoreRunnableMixin',
    'HasFileLocation',
    'HasMetaDictData',
    'SupportsItemAccess',
)
