"""PyQt6 ToolBar widget for Pyrox applications.

A vertical or horizontal icon-button toolbar styled with the Pyrox dark theme.
Supports text buttons, icon-only buttons, separators, and toggle (checkable)
buttons.  Items are identified by a string ``id`` for programmatic access.

Example Usage::

    toolbar = ToolBar(parent=self.root_window)

    toolbar.add_button(ToolBarButton(
        id='open',
        text='Open',
        command=lambda: print('open'),
        tooltip='Open a file',
        icon='📂',
    ))

    toolbar.add_separator()

    toolbar.add_button(ToolBarButton(
        id='save',
        text='Save',
        command=lambda: print('save'),
        tooltip='Save file',
        icon='💾',
        checkable=True,
    ))

    toolbar.set_button_enabled('open', False)
    toolbar.set_button_checked('save', True)
    toolbar.remove_item('open')
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from pyrox.models.gui.theme import DefaultTheme

__all__ = ('ToolBar', 'ToolBarButton')

# ---------------------------------------------------------------------------
# Stylesheet
# ---------------------------------------------------------------------------

_TOOLBAR_STYLE = f"""
    QWidget#toolbar {{
        background-color: {DefaultTheme.widget_background};
        border: {DefaultTheme.borderwidth}px solid {DefaultTheme.bordercolor};
    }}
    QPushButton {{
        background-color: {DefaultTheme.button_color};
        color: {DefaultTheme.foreground};
        border: {DefaultTheme.borderwidth}px solid transparent;
        padding: 4px 6px;
        font-family: '{DefaultTheme.font_family}';
        font-size: {DefaultTheme.font_size}pt;
        text-align: center;
    }}
    QPushButton:hover {{
        background-color: {DefaultTheme.button_hover};
        color: {DefaultTheme.foreground_hover};
        border-color: {DefaultTheme.bordercolor};
    }}
    QPushButton:pressed {{
        background-color: {DefaultTheme.button_active};
    }}
    QPushButton:disabled {{
        color: #555555;
        border-color: transparent;
    }}
    QPushButton:checked {{
        background-color: {DefaultTheme.background_selected};
        color: {DefaultTheme.foreground_selected};
        border-color: {DefaultTheme.foreground_selected};
    }}
    QFrame[frameShape="4"],
    QFrame[frameShape="5"] {{
        color: {DefaultTheme.bordercolor};
    }}
    QLabel {{
        background-color: transparent;
        color: {DefaultTheme.foreground};
        font-family: '{DefaultTheme.font_family}';
        font-size: {DefaultTheme.font_size}pt;
    }}
"""

# ---------------------------------------------------------------------------
# Configuration dataclass
# ---------------------------------------------------------------------------


@dataclass
class ToolBarButton:
    """Configuration for a single toolbar button.

    Attributes:
        id:        Unique identifier for programmatic access.
        text:      Label text.  Hidden when *icon_only* is ``True``.
        command:   Callable invoked on click.
        tooltip:   Optional tooltip text shown on hover.
        icon:      Optional Unicode glyph or short string shown above / before text.
        enabled:   Initial enabled state.
        visible:   Initial visibility.
        checkable: When ``True`` the button acts as a toggle.
        checked:   Initial checked state (only meaningful when *checkable* is ``True``).
        icon_only: When ``True`` only the icon is shown and *text* is used as tooltip
                   fallback if *tooltip* is not provided.
        width:     Fixed pixel width.  ``None`` lets the button size naturally.
        height:    Fixed pixel height.  ``None`` lets the button size naturally.
    """
    id: str
    text: str
    command: Callable[[], None]
    tooltip: Optional[str] = None
    icon: Optional[str] = None
    enabled: bool = True
    visible: bool = True
    checkable: bool = False
    checked: bool = False
    icon_only: bool = False
    width: Optional[int] = None
    height: Optional[int] = None


# ---------------------------------------------------------------------------
# Internal slot
# ---------------------------------------------------------------------------


@dataclass
class _ButtonSlot:
    config: ToolBarButton
    button: QPushButton


# ---------------------------------------------------------------------------
# ToolBar widget
# ---------------------------------------------------------------------------


class ToolBar(QWidget):
    """A slim icon/button toolbar styled with the Pyrox dark theme.

    By default the toolbar is oriented **vertically** (a sidebar-style strip).
    Pass ``orientation=Qt.Orientation.Horizontal`` for a horizontal toolbar.

    Items are laid out in insertion order.  A stretch is always kept at the
    trailing end so buttons remain at the leading edge.  Separators are thin
    lines rendered between groups.

    Args:
        parent:      Parent widget.
        orientation: ``Qt.Orientation.Vertical`` (default) or ``Horizontal``.
        width:       Fixed width for vertical toolbars (ignored for horizontal).
        height:      Fixed height for horizontal toolbars (ignored for vertical).
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        orientation: Qt.Orientation = Qt.Orientation.Vertical,
        width: int = 42,
        height: int = 42,
    ) -> None:
        super().__init__(parent)
        self.setObjectName('toolbar')
        self.setStyleSheet(_TOOLBAR_STYLE)

        self._orientation = orientation
        self._slots: Dict[str, _ButtonSlot] = {}
        self._order: List[str] = []
        self._separators: List[QFrame] = []

        if orientation == Qt.Orientation.Vertical:
            self.setFixedWidth(width)
            self._layout: QVBoxLayout | QHBoxLayout = QVBoxLayout(self)
        else:
            self.setFixedHeight(height)
            self._layout = QHBoxLayout(self)

        self._layout.setContentsMargins(2, 2, 2, 2)
        self._layout.setSpacing(2)
        self._layout.addStretch()

    # ------------------------------------------------------------------
    # Public API — add items
    # ------------------------------------------------------------------

    def add_button(self, config: ToolBarButton) -> QPushButton:
        """Add a button to the toolbar.

        The button is inserted before the trailing stretch.

        Args:
            config: :class:`ToolBarButton` configuration.

        Returns:
            The constructed :class:`QPushButton`.

        Raises:
            ValueError: If ``config.id`` is already registered.
        """
        if config.id in self._slots:
            raise ValueError(f"ToolBar: id '{config.id}' is already registered.")

        if config.icon_only:
            label = config.icon or config.text
        else:
            label = f'{config.icon}\n{config.text}' if config.icon else config.text

        btn = QPushButton(label, self)
        btn.setCheckable(config.checkable)
        btn.setChecked(config.checked)
        btn.setEnabled(config.enabled)
        btn.setVisible(config.visible)

        tip = config.tooltip or (config.text if config.icon_only else None)
        if tip:
            btn.setToolTip(tip)

        if config.width is not None:
            btn.setFixedWidth(config.width)
        if config.height is not None:
            btn.setFixedHeight(config.height)

        btn.clicked.connect(config.command)

        slot = _ButtonSlot(config=config, button=btn)
        self._slots[config.id] = slot
        self._order.append(config.id)

        # Insert before the trailing stretch
        stretch_index = self._layout.count() - 1
        self._layout.insertWidget(stretch_index, btn)

        return btn

    def add_separator(self) -> None:
        """Insert a separator line before the trailing stretch."""
        sep = QFrame(self)
        if self._orientation == Qt.Orientation.Vertical:
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        else:
            sep.setFrameShape(QFrame.Shape.VLine)
            sep.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        self._separators.append(sep)
        stretch_index = self._layout.count() - 1
        self._layout.insertWidget(stretch_index, sep)

    # ------------------------------------------------------------------
    # Public API — mutate items
    # ------------------------------------------------------------------

    def set_button_enabled(self, id: str, enabled: bool) -> None:
        """Enable or disable a button by its ``id``.

        Args:
            id:      Registered button identifier.
            enabled: ``True`` to enable, ``False`` to disable.

        Raises:
            KeyError: If ``id`` is not registered.
        """
        self._get_slot(id).button.setEnabled(enabled)

    def set_button_visible(self, id: str, visible: bool) -> None:
        """Show or hide a button by its ``id``.

        Args:
            id:      Registered button identifier.
            visible: ``True`` to show, ``False`` to hide.

        Raises:
            KeyError: If ``id`` is not registered.
        """
        self._get_slot(id).button.setVisible(visible)

    def set_button_checked(self, id: str, checked: bool) -> None:
        """Set the checked state of a checkable button.

        Has no visual effect on non-checkable buttons.

        Args:
            id:      Registered button identifier.
            checked: ``True`` to check, ``False`` to uncheck.

        Raises:
            KeyError: If ``id`` is not registered.
        """
        self._get_slot(id).button.setChecked(checked)

    def set_button_command(self, id: str, command: Callable[[], None]) -> None:
        """Replace the click handler of a button.

        Args:
            id:      Registered button identifier.
            command: New callable to connect.

        Raises:
            KeyError: If ``id`` is not registered.
        """
        slot = self._get_slot(id)
        slot.button.clicked.disconnect()
        slot.button.clicked.connect(command)

    def is_checked(self, id: str) -> bool:
        """Return the checked state of a checkable button.

        Args:
            id: Registered button identifier.

        Returns:
            ``True`` if checked, ``False`` otherwise.

        Raises:
            KeyError: If ``id`` is not registered.
        """
        return self._get_slot(id).button.isChecked()

    def remove_item(self, id: str) -> None:
        """Remove a button from the toolbar and unregister its ``id``.

        Args:
            id: Registered button identifier.

        Raises:
            KeyError: If ``id`` is not registered.
        """
        slot = self._get_slot(id)
        self._layout.removeWidget(slot.button)
        slot.button.deleteLater()
        del self._slots[id]
        self._order.remove(id)

    def clear(self) -> None:
        """Remove all buttons and separators from the toolbar."""
        for id in list(self._order):
            self.remove_item(id)
        for sep in self._separators:
            self._layout.removeWidget(sep)
            sep.deleteLater()
        self._separators.clear()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_slot(self, id: str) -> _ButtonSlot:
        if id not in self._slots:
            raise KeyError(f"ToolBar: no item with id '{id}'.")
        return self._slots[id]
