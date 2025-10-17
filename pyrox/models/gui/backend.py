"""GUI backend abstract base class.
"""
from abc import ABC, abstractmethod
from typing import Any


class GuiBackend(ABC):
    """Abstract base class for GUI backends."""

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the GUI backend."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the backend is available on this system."""
        pass

    @abstractmethod
    def create_root_window(self, **kwargs) -> Any:
        """Create and return a root window."""
        pass

    @abstractmethod
    def get_root_window(self) -> Any:
        """Get the existing root window, if any."""
        pass

    @abstractmethod
    def run_main_loop(self, root_window: Any = None) -> None:
        """Start the GUI main loop."""
        pass

    @abstractmethod
    def quit_application(self) -> None:
        """Quit the GUI application."""
        pass

    @property
    @abstractmethod
    def framework_name(self) -> str:
        """Get the framework name."""
        pass
