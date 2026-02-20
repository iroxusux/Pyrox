"""Keyboard input source for scene bindings.

Provides a GUI-agnostic data object that tracks which keyboard keys are
currently held down.  It exposes each tracked key as a plain ``bool``
instance attribute, which means :meth:`SceneBoundLayer.enumerate_source_properties`
discovers them automatically and the GUI browser shows them without any
special-casing.

The source itself never imports a GUI toolkit.  Callers are responsible for
wiring ``press`` / ``release`` to whatever event system they use::

    # Tkinter example (in a SceneViewer or similar GUI class)
    kb = KeyboardSource()
    widget.bind("<KeyPress>",   lambda e: kb.press(e.keysym))
    widget.bind("<KeyRelease>", lambda e: kb.release(e.keysym))

    SceneBridgeService.register_source_factory("keyboard", lambda: kb)

The set of *pre-declared* keys determines what the GUI browses.  Any key
not in this set can still be queried dynamically via :meth:`is_pressed`; it
just will not appear in the introspection browser.

To add more keys, either subclass and extend ``__init__``, or register a
custom factory that adds extra attributes after construction.
"""
from __future__ import annotations
from pyrox.services.scene import SceneBridgeService
from pyrox.services.gui import TkGuiManager

from typing import FrozenSet


# Keys whose state is pre-declared as instance attributes (appear in browser)
_DECLARED_KEYS: FrozenSet[str] = frozenset({
    # WASD movement
    "w", "a", "s", "d",
    # Arrow keys  (tkinter keysym names)
    "Up", "Down", "Left", "Right",
    # Common actions
    "space", "Return", "BackSpace", "Escape", "Tab",
    # Modifiers
    "shift_l", "shift_r", "control_l", "control_r", "alt_l", "alt_r",
    # Number row
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    # Common extras
    "e", "q", "f", "r", "z", "x", "c", "v",
})


class KeyboardSource:
    """GUI-agnostic keyboard state for use as a :class:`SceneBoundLayer` source.

    Each declared key is a ``bool`` instance attribute (``True`` = held down).
    Call :meth:`press` and :meth:`release` from your GUI event handlers to
    update the state.

    Attributes are named using the keysym convention used by most GUI
    toolkits (tkinter, pygame, etc.).  Example keysym values: ``"w"``,
    ``"Up"``, ``"space"``, ``"shift_l"``.

    Example bridge binding::

        bridge.add_binding(
            binding_key="keyboard.w",
            object_id="player",
            property_path="move_forward",
            direction=BindingDirection.READ,
        )
    """

    def __init__(self) -> None:
        # Declare every tracked key as a False bool attribute so that
        # SceneBoundLayer._inspect_properties discovers them without needing
        # to iterate the _pressed set.
        for key in _DECLARED_KEYS:
            object.__setattr__(self, key, False)

        # Internal set for fast membership tests and dynamic key support.
        object.__setattr__(self, '_pressed', set())

        # Bind to GUI keyboard events when a root window is available.
        # This is a convenience only — if no GUI is active the KeyboardSource
        # still works; callers are responsible for driving press/release manually.
        try:
            root = TkGuiManager.get_root()
            root.bind("<KeyPress>", lambda e: self.press(e.keysym))
            root.bind("<KeyRelease>", lambda e: self.release(e.keysym))
            root.bind("<FocusOut>", lambda e: self.release_all())
        except RuntimeError:
            pass  # No GUI initialized; bindings must be wired by the caller.

    # ------------------------------------------------------------------
    # Input methods — call these from your GUI event handler
    # ------------------------------------------------------------------

    def press(self, keysym: str) -> None:
        """Mark *keysym* as held down.

        If *keysym* is a declared key its attribute is set to ``True``.
        Any keysym (declared or not) can be queried via :meth:`is_pressed`.

        Args:
            keysym: Key symbol string, e.g. ``"w"``, ``"Up"``, ``"space"``.
        """
        pressed: set = object.__getattribute__(self, '_pressed')
        pressed.add(keysym)
        if keysym in _DECLARED_KEYS:
            object.__setattr__(self, keysym, True)

    def release(self, keysym: str) -> None:
        """Mark *keysym* as released.

        Args:
            keysym: Key symbol string.
        """
        pressed: set = object.__getattribute__(self, '_pressed')
        pressed.discard(keysym)
        if keysym in _DECLARED_KEYS:
            object.__setattr__(self, keysym, False)

    def release_all(self) -> None:
        """Release all currently held keys.

        Useful when the window loses focus to prevent keys staying stuck.
        """
        pressed: set = object.__getattribute__(self, '_pressed')
        held = list(pressed)
        for keysym in held:
            self.release(keysym)

    # ------------------------------------------------------------------
    # Dynamic query
    # ------------------------------------------------------------------

    def is_pressed(self, keysym: str) -> bool:
        """Return ``True`` if *keysym* is currently held, regardless of whether
        it was pre-declared.

        Args:
            keysym: Key symbol string.
        """
        pressed: set = object.__getattribute__(self, '_pressed')
        return keysym in pressed

    def currently_pressed(self) -> frozenset[str]:
        """Return an immutable snapshot of all currently held keys."""
        pressed: set = object.__getattribute__(self, '_pressed')
        return frozenset(pressed)

    # ------------------------------------------------------------------
    # Declared key set (class-level, for external inspection)
    # ------------------------------------------------------------------

    @staticmethod
    def declared_keys() -> FrozenSet[str]:
        """Return the set of keys pre-declared as instance attributes."""
        return _DECLARED_KEYS

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        pressed: set = object.__getattribute__(self, '_pressed')
        held = sorted(pressed) if pressed else []
        return f"KeyboardSource(held={held})"


# Register this source with the SceneBridgeService so it's available for binding by default.
SceneBridgeService.register_source_factory("keyboard", lambda: KeyboardSource())
