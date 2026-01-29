"""Protocol implementations for common object behaviors.
"""
from typing import Any, Optional
from pyrox.interfaces import (
    IConfigurable,
    IAuthored,
    IVersioned,
    IHasId,
    INameable,
    IDescribable,
    IRefreshable,
    IResettable,
    IBuildable,
    IRunnable,
    ICoreMixin,
    ICoreRunnableMixin,
    IHasFileLocation,
    IHasDictMetaData,
    ISupportsItemAccess,
)


class Configurable(IConfigurable):
    """Denotes object is 'configurable' and supports configuration.

    This class provides a foundation for objects that can be configured
    with a dictionary of settings, implementing the IConfigurable protocol.
    """

    def __init__(
        self,
        config: Optional[dict[str, Any]] = None
    ):
        if config is not None:
            self._config: dict[str, Any] = config
        else:
            self._config: dict[str, Any] = dict()

    def configure(self, config: dict) -> None:
        pass

    def get_config(self) -> dict[str, Any]:
        """Get the configuration of this object.

        Returns:
            dict: The configuration of this object.
        """
        return self._config

    def set_config(self, config: dict[str, Any]) -> None:
        """Set the configuration of this object.

        Args:
            config (dict): The configuration to set.
        """
        self._config = config


class Authored(IAuthored):
    """Denotes object is 'authored' and supports getting author information.

    This class provides a foundation for objects that have author information,
    implementing the IAuthored protocol.
    """

    def __init__(
        self,
        author: str = ""
    ) -> None:
        self._author: str = author

    def get_author(self) -> str:
        """Get the author of this object.

        Returns:
            str: The author of this object.
        """
        return self._author

    def set_author(self, author: str) -> None:
        """Set the author of this object.

        Args:
            author (str): The author to set.
        """
        self._author = author


class Versioned(IVersioned):
    """Denotes object is 'versioned' and supports getting version information.

    This class provides a foundation for objects that have version information,
    implementing the IVersioned protocol.
    """

    def __init__(
        self,
        version: str = ""
    ) -> None:
        self._version: str = version

    def get_version(self) -> str:
        """Get the version of this object.

        Returns:
            str: The version of this object.
        """
        return self._version

    def set_version(self, version: str) -> None:
        """Set the version of this object.

        Args:
            version (str): The version to set.
        """
        self._version = version


class HasId(IHasId):
    """Denotes object has an identifier.

    This class provides a foundation for objects that have an ID property,
    implementing the IHasId protocol.
    """

    def __init__(
        self,
        id: str = ""
    ):
        self._id: str = id

    def get_id(self) -> str:
        """Get the ID of this object.

        Returns:
            str: The ID of this object.
        """
        return self._id

    def set_id(self, id: str) -> None:
        """Set the ID of this object.

        Args:
            id (str): The ID to set.
        """
        self._id = id


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


class CoreMixin(
    ICoreMixin,
    HasId,
    Nameable,
    Describable,
):
    """Mixin class that acts as a core mixin with name and description.
    """

    def __init__(
        self,
        id: str = "",
        name: str = "",
        description: str = ""
    ):
        HasId.__init__(self, id)
        Nameable.__init__(self, name)
        Describable.__init__(self, description)


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

        Nameable.__init__(self, name)
        Describable.__init__(self, description)
        Runnable.__init__(self)
        Buildable.__init__(self)


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
    'Configurable',
    'Authored',
    'Versioned',
    'HasId',
    'Nameable',
    'Describable',
    'Refreshable',
    'Resettable',
    'Buildable',
    'Runnable',
    'CoreMixin',
    'CoreRunnableMixin',
    'HasFileLocation',
    'HasMetaDictData',
    'SupportsItemAccess',
)
