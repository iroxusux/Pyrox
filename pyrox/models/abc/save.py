"""Save and load related abstract base classes.

These classes provide a structured way to implement saving and loading functionality
in other classes, supporting both generic file operations and JSON-specific operations.
"""
import json
from pathlib import Path
from typing import Any, Optional, Union
from pyrox.models.abc.meta import SupportsFileLocation

__all__ = (
    'SupportsLoading',
    'SupportsSaving',
    'SupportsJsonLoading',
    'SupportsJsonSaving',
)


class SupportsLoading(SupportsFileLocation):
    """A meta class for all classes to derive from to obtain loading capabilities.

    This class provides the foundation for objects that can load their state
    from external files, with customizable loading behavior and post-load callbacks.

    Attributes:
        load_path: Path to load the object from.
    """
    __slots__ = ()

    def load(self, path: Optional[Path] = None) -> Any:
        """Load the object from a file.

        Args:
            path: Path to load the object from. If not provided, uses the load_path attribute.

        Returns:
            Any: The loaded data.

        Raises:
            NotImplementedError: This method should be implemented in subclasses.
        """
        raise NotImplementedError("This method should be implemented in subclasses.")

    def on_loaded(self, data: Any) -> None:
        """Method to be called after the object has been loaded.

        This method can be overridden in subclasses to perform additional actions after loading.

        Args:
            data: Data that was loaded from the file.
        """
        ...


class SupportsSaving(SupportsFileLocation):
    """A meta class for all classes to derive from to obtain saving capabilities.

    This class provides the foundation for objects that can save their state
    to external files, with customizable saving behavior and pre-save callbacks.
    """

    def save(self, path: Optional[Path] = None, data: Optional[Any] = None) -> None:
        """Save the object to a file.

        Args:
            path: Path to save the object to. If not provided, uses the save_path attribute.
            data: Data to save. If not provided, uses the save_data_callback attribute.

        Raises:
            NotImplementedError: This method should be implemented in subclasses.
        """
        raise NotImplementedError("This method should be implemented in subclasses.")

    def on_saving(self) -> Any:
        """Method to be called to retrieve the save data of the object.
        """
        ...


class SupportsJsonSaving(SupportsSaving):
    """A meta class for all classes to derive from to obtain JSON saving capabilities.

    Attributes:
        save_path: Path to save the object to.
        save_data_callback: Callback to call when saving data.
    """

    def save_to_json(
        self,
        path: Optional[Union[Path, str]] = None,
        data: Optional[dict] = None
    ) -> None:
        """Save the object to a JSON file.

        Args:
            path: Path to save the object to. If not provided, uses the save_path attribute.
            data: Data to save. If not provided, uses the save_data_callback attribute.

        Raises:
            ValueError: If no path is provided for saving JSON data.
            IOError: If the file cannot be written.
        """
        path = path or self.file_location
        if not path:
            raise ValueError("No path provided for saving JSON data.")

        data = data or self.on_saving()

        if data is None:
            raise ValueError("No data provided for saving JSON.")

        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except (IOError, OSError) as e:
            raise IOError(f"Failed to save JSON to {path}: {e}")


class SupportsJsonLoading(SupportsLoading):
    """A meta class for all classes to derive from to obtain JSON loading capabilities."""

    def load_from_json(
        self,
        path: Optional[Union[Path, str]] = None
    ) -> Any:
        """Load the object from a JSON file.

        Args:
            path: Path to load the object from. If not provided, uses the load_path attribute.

        Returns:
            Any: Loaded data from the JSON file, or None if file doesn't exist.
        """
        if self.file_location is None and path is None:
            return None

        if isinstance(path, str):
            path = Path(path)

        if path is None and self.file_location is not None:
            path = Path(self.file_location)

        if not isinstance(path, Path):
            raise TypeError("Path must be a Path object or a string representing a path.")

        if not path.exists():
            return None

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.on_loaded(data)
                return data
        except (IOError, OSError, json.JSONDecodeError) as e:
            raise IOError(f"Failed to load JSON from {path}: {e}")
