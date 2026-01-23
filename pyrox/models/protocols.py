from pyrox.interfaces import (
    IBuildable,
    IRunnable,
    INameable,
    IDescribable,
    IRefreshable,
    IResettable
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


class Runnable(
    IRunnable,
    Buildable
):
    """Denotes object is 'runnable' and supports run method.

    This class extends Buildable to provide runtime state management,
    tracking whether the object is currently running and providing
    methods for starting and stopping execution.

    Attributes:
        running: Whether the object is currently in a running state.
    """

    def __init__(self):
        Buildable.__init__(self)
        self._running: bool = False

    def run(self) -> int:
        """Start this object."""
        if self.built is False:
            self.build()
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


__all__ = (
    'Nameable',
    'Describable',
    'Refreshable',
    'Resettable',
    'Buildable',
    'Runnable',
)
