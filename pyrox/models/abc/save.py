"""Save and load related abstract base classes.
These classes provide a structured way to implement saving and loading functionality in other classes.
"""
import json
from pathlib import Path
from typing import Any, Callable, Optional
from .meta import SupportsFileLocation

__all__ = (
    'SupportsLoading',
    'SupportsSaving',
    'SupportsJsonLoading',
    'SupportsJsonSaving',
)


class SupportsLoading(SupportsFileLocation):
    """A meta class for all classes to derive from to obtain loading capabilities.

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

    Attributes:
        save_path: Path to save the object to.
        save_data_callback: Callback to call when saving data.
    """
    __slots__ = ()

    @property
    def save_data_callback(self) -> Optional[Callable]:
        """Callback to call when saving data.

        Returns:
            Optional[Callable]: The callback function.

        Raises:
            NotImplementedError: This property should be implemented in subclasses.
        """
        raise NotImplementedError("This property should be implemented in subclasses.")

    def save(self, path: Optional[Path] = None, data: Optional[Any] = None) -> None:
        """Save the object to a file.

        Args:
            path: Path to save the object to. If not provided, uses the save_path attribute.
            data: Data to save. If not provided, uses the save_data_callback attribute.

        Raises:
            NotImplementedError: This method should be implemented in subclasses.
        """
        raise NotImplementedError("This method should be implemented in subclasses.")


class SupportsJsonSaving(SupportsSaving):
    """A meta class for all classes to derive from to obtain JSON saving capabilities.

    Attributes:
        save_path: Path to save the object to.
        save_data_callback: Callback to call when saving data.
    """
    __slots__ = ()

    def save_to_json(self, path: Optional[Path] = None, data: Optional[dict] = None) -> None:
        """Save the object to a JSON file.

        Args:
            path: Path to save the object to. If not provided, uses the save_path attribute.
            data: Data to save. If not provided, uses the save_data_callback attribute.

        Raises:
            ValueError: If no path is provided for saving JSON data.
            IOError: If the file cannot be written.
        """
        path = path or self.file_location
        data = data or self.save_data_callback()
        if not path:
            raise ValueError("No path provided for saving JSON data.")

        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except (IOError, OSError) as e:
            raise IOError(f"Failed to save JSON to {path}: {e}")


class SupportsJsonLoading(SupportsLoading):
    """A meta class for all classes to derive from to obtain JSON loading capabilities."""
    __slots__ = ()

    def load_from_json(self, path: Optional[Path] = None) -> Any:
        """Load the object from a JSON file.

        Args:
            path: Path to load the object from. If not provided, uses the load_path attribute.

        Returns:
            Any: Loaded data from the JSON file, or None if file doesn't exist.
        """
        path = Path(path) if path else Path(self.file_location)
        if not path or not path.exists():
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.on_loaded(data)
                return data
        except (IOError, OSError, json.JSONDecodeError) as e:
            raise IOError(f"Failed to load JSON from {path}: {e}")
