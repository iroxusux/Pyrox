"""GUI state persistence service for Pyrox.

Stores and restores window geometry (size, position, maximized/fullscreen
state) between application runs using the platform-appropriate user data
directory rather than the .env file.

State is written to:
    <user_data_dir>/<app_name>_gui_state.json
"""
from __future__ import annotations

import json
import os
from typing import Any

from pyrox.services.file import PlatformDirectoryService


# ---------------------------------------------------------------------------
# Data shape
# ---------------------------------------------------------------------------

_DEFAULT_STATE: dict[str, Any] = {
    'width': None,
    'height': None,
    'x': None,
    'y': None,
    'window_state': 'normal',   # 'normal' | 'zoomed' | 'iconic'
    'fullscreen': False,
    'geometry': {},  # Optional additional geometry state (e.g. sidebar visibility)
}


# ---------------------------------------------------------------------------
# GuiStateService
# ---------------------------------------------------------------------------

class GuiStateService:
    """Static service for persisting and restoring GUI window state.

    State is stored as a JSON file inside the platform user-data directory
    so it is per-user, survives reinstalls, and is never committed to source
    control.

    Example usage::

        # On startup:
        GuiStateService.load()
        w, h = GuiStateService.get_size()         # (800, 600) or (None, None)
        x, y = GuiStateService.get_position()     # (100, 100) or (None, None)
        state = GuiStateService.get_window_state() # 'normal' | 'zoomed' | 'iconic'
        is_fs = GuiStateService.is_fullscreen()   # bool

        # After a resize / move:
        GuiStateService.set_size(1024, 768)
        GuiStateService.set_position(50, 50)
        GuiStateService.set_window_state('zoomed')
        GuiStateService.save()
    """

    _state: dict[str, Any] = dict(_DEFAULT_STATE)
    _loaded: bool = False

    def __init__(self) -> None:
        raise TypeError("GuiStateService is a static class and cannot be instantiated")

    # ------------------------------------------------------------------
    # File path
    # ------------------------------------------------------------------

    @classmethod
    def get_state_file_path(cls) -> str:
        """Absolute path to the JSON state file in the user data directory."""
        app_name = PlatformDirectoryService.get_app_name()
        return os.path.join(
            PlatformDirectoryService.get_user_data(),
            f'{app_name}_gui_state.json',
        )

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    @classmethod
    def load(cls) -> None:
        """Load state from disk.  Missing or corrupt files are silently ignored."""
        path = cls.get_state_file_path()
        cls._state = dict(_DEFAULT_STATE)
        if os.path.isfile(path):
            try:
                with open(path, encoding='utf-8') as fh:
                    data = json.load(fh)
                if isinstance(data, dict):
                    # Only accept known keys to avoid stale/foreign data pollution
                    for key in _DEFAULT_STATE:
                        if key in data:
                            cls._state[key] = data[key]
            except (OSError, json.JSONDecodeError):
                pass  # Start fresh if the file is unreadable
        cls._loaded = True

    @classmethod
    def save(cls) -> None:
        """Persist the current state to disk."""
        path = cls.get_state_file_path()
        try:
            with open(path, 'w', encoding='utf-8') as fh:
                json.dump(cls._state, fh, indent=2)
        except OSError:
            pass  # Non-fatal — state simply won't survive this session

    # ------------------------------------------------------------------
    # Getters
    # ------------------------------------------------------------------

    @classmethod
    def get_size(cls) -> tuple[int, int] | tuple[None, None]:
        """Return ``(width, height)`` or ``(None, None)`` if not persisted."""
        w = cls._state.get('width')
        h = cls._state.get('height')
        if w is not None and h is not None:
            return int(w), int(h)
        return None, None

    @classmethod
    def get_position(cls) -> tuple[int, int] | tuple[None, None]:
        """Return ``(x, y)`` or ``(None, None)`` if not persisted."""
        x = cls._state.get('x')
        y = cls._state.get('y')
        if x is not None and y is not None:
            return int(x), int(y)
        return None, None

    @classmethod
    def get_window_state(cls) -> str:
        """Return the window state string: ``'normal'``, ``'zoomed'``, or ``'iconic'``."""
        return str(cls._state.get('window_state', 'normal'))

    @classmethod
    def is_fullscreen(cls) -> bool:
        """Return ``True`` if the window was in fullscreen mode."""
        return bool(cls._state.get('fullscreen', False))

    # ------------------------------------------------------------------
    # Setters
    # ------------------------------------------------------------------

    @classmethod
    def set_size(cls, width: int, height: int) -> None:
        """Record the current window size."""
        cls._state['width'] = int(width)
        cls._state['height'] = int(height)

    @classmethod
    def set_position(cls, x: int, y: int) -> None:
        """Record the current window position."""
        cls._state['x'] = int(x)
        cls._state['y'] = int(y)

    @classmethod
    def set_window_state(cls, state: str) -> None:
        """Record the window state (``'normal'``, ``'zoomed'``, or ``'iconic'``)."""
        if state not in ('normal', 'zoomed', 'iconic'):
            raise ValueError(f"Invalid window state: {state!r}")
        cls._state['window_state'] = state

    @classmethod
    def set_fullscreen(cls, fullscreen: bool) -> None:
        """Record whether the window is in fullscreen mode."""
        cls._state['fullscreen'] = bool(fullscreen)

    # ------------------------------------------------------------------
    # Convenience: capture from a QMainWindow
    # ------------------------------------------------------------------

    @classmethod
    def capture_from_window(cls, window: object) -> None:
        """Snapshot all geometry from a ``QMainWindow`` instance.

        Size and position are only updated when the window is **not** in
        fullscreen mode so that the last non-fullscreen geometry is preserved
        and can be correctly restored when the user exits fullscreen.

        Args:
            window: A ``QMainWindow`` (or any object exposing ``width()``,
                ``height()``, ``x()``, ``y()``, ``isMaximized()``,
                ``isMinimized()``, ``isFullScreen()``).
        """
        is_fullscreen: bool = bool(window.isFullScreen())  # type: ignore[attr-defined]
        cls.set_fullscreen(is_fullscreen)

        # Don't overwrite size/position while fullscreen — the values reported
        # by Qt in that state are either screen dimensions or uninitialised
        # defaults, neither of which should be restored later as a window size.
        if not is_fullscreen:
            cls.set_size(window.width(), window.height())  # type: ignore[attr-defined]
            cls.set_position(window.x(), window.y())  # type: ignore[attr-defined]

        if window.isMaximized():  # type: ignore[attr-defined]
            cls.set_window_state('zoomed')
        elif window.isMinimized():  # type: ignore[attr-defined]
            cls.set_window_state('iconic')
        elif not is_fullscreen:
            cls.set_window_state('normal')

    @classmethod
    def apply_to_window(cls, window: object) -> None:
        """Apply persisted geometry to a ``QMainWindow`` instance.

        Fullscreen takes priority, then maximized/minimized state, then
        explicit size and position.

        Args:
            window: A ``QMainWindow`` (or compatible object).
        """
        if cls.is_fullscreen():
            window.showFullScreen()  # type: ignore[attr-defined]
            return

        w, h = cls.get_size()
        if w is not None and h is not None:
            window.resize(w, h)  # type: ignore[attr-defined]

        x, y = cls.get_position()
        if x is not None and y is not None:
            window.move(x, y)  # type: ignore[attr-defined]

        state = cls.get_window_state()
        if state == 'zoomed':
            window.showMaximized()  # type: ignore[attr-defined]
        elif state == 'iconic':
            window.showMinimized()  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Convenience: Capture additional GUI states as needed
    # ------------------------------------------------------------------

    @classmethod
    def capture_geometry_state(cls, geometry: dict[str, Any]) -> None:
        """Capture additional geometry-related state from a custom dictionary.

        This can be used to persist extra window states like sidebar visibility
        or dock widget arrangements without coupling the service to specific
        GUI components.

        Args:
            geometry: A dictionary of arbitrary key-value pairs representing
                additional geometry state.  This will be merged into the main
                state file under a "geometry" key.
        """
        cls._state['geometry'] = geometry

    @classmethod
    def get_geometry_state(cls) -> dict[str, Any]:
        """Return the additional geometry state dictionary, or an empty dict if not set."""
        return cls._state.get('geometry', {})


__all__ = ('GuiStateService',)
