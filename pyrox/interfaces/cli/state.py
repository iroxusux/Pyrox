from abc import ABC, abstractmethod


class AppState(ABC):
    """Abstract base class representing a single terminal screen or mode."""

    def __init__(self, app_context):
        self.is_alive = False  # Alive context for rendering and processing
        self.app = app_context  # Reference to the main application orchestrator

    @abstractmethod
    def enter(self) -> None:
        """Called when entering this state (e.g., clear screen, set alt mode)."""

    @abstractmethod
    def handle_input(self, key: str) -> None:
        """Processes keyboard inputs specific to this screen state."""

    @abstractmethod
    def render(self) -> None:
        """Draws the UI components for this state onto the terminal."""

    @abstractmethod
    def exit(self) -> None:
        """Called before transitioning away to clean up local state."""

    @abstractmethod
    def mark_dirty(self) -> None:
        """Mark all lines for this state as 'dirty' (needs re-rendering.)"""
