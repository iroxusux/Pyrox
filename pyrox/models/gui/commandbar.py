"""Command Bar Widget for Pyrox applications.

This module provides a PyQt6-based command bar widget that allows easy
programmatic adding and removal of command buttons and dropdowns.  It
follows the Pyrox dark-theme GUI conventions and is self-contained — mount
it anywhere a ``QWidget`` is accepted.

Example Usage:
    ```python
    bar = CommandBar(parent=main_window)

    bar.add_button(CommandButton(
        id='open',
        text='Open',
        command=lambda: print('open'),
        tooltip='Open a file',
        icon='📂',
    ))

    bar.add_dropdown(CommandDropdown(
        id='mode',
        label='Mode',
        options=['Auto', 'Manual', 'Semi-Auto'],
        command=lambda val: print(f'Mode: {val}'),
        default='Auto',
    ))

    bar.add_separator()

    bar.add_button(CommandButton(id='stop', text='Stop', command=stop_fn,
                                 selectable=True))

    # Later — programmatic state changes
    bar.set_button_enabled('open', False)
    bar.set_button_selected('stop', True)
    bar.remove_item('mode')
    ```
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Union

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from pyrox.models.gui.theme import DefaultTheme

__all__ = ('CommandBar', 'CommandButton', 'CommandDropdown')

# ---------------------------------------------------------------------------
# Stylesheet
# ---------------------------------------------------------------------------

_BAR_STYLE = f"""
    QWidget#commandbar {{
        background-color: {DefaultTheme.background};
        border-bottom: {DefaultTheme.borderwidth}px solid {DefaultTheme.bordercolor};
    }}
    QPushButton {{
        background-color: {DefaultTheme.button_color};
        color: {DefaultTheme.foreground};
        border: {DefaultTheme.borderwidth}px solid {DefaultTheme.bordercolor};
        padding: 3px 10px;
        font-family: '{DefaultTheme.font_family}';
        font-size: {DefaultTheme.font_size}pt;
    }}
    QPushButton:hover {{
        background-color: {DefaultTheme.button_hover};
        color: {DefaultTheme.foreground_hover};
    }}
    QPushButton:pressed {{
        background-color: {DefaultTheme.button_active};
    }}
    QPushButton:disabled {{
        color: #555555;
        border-color: #444444;
    }}
    QPushButton[selected="true"] {{
        background-color: {DefaultTheme.background_selected};
        color: {DefaultTheme.foreground_selected};
        border-color: {DefaultTheme.foreground_selected};
    }}
    QComboBox {{
        background-color: {DefaultTheme.widget_background};
        color: {DefaultTheme.foreground};
        border: {DefaultTheme.borderwidth}px solid {DefaultTheme.bordercolor};
        padding: 2px 6px;
        font-family: '{DefaultTheme.font_family}';
        font-size: {DefaultTheme.font_size}pt;
    }}
    QComboBox::drop-down {{
        border: none;
        width: 18px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {DefaultTheme.widget_background};
        color: {DefaultTheme.foreground};
        selection-background-color: {DefaultTheme.background_selected};
        selection-color: {DefaultTheme.foreground_selected};
        border: {DefaultTheme.borderwidth}px solid {DefaultTheme.bordercolor};
    }}
    QLabel {{
        background-color: transparent;
        color: {DefaultTheme.foreground};
        font-family: '{DefaultTheme.font_family}';
        font-size: {DefaultTheme.font_size}pt;
    }}
    QFrame[frameShape="5"] {{
        color: {DefaultTheme.bordercolor};
    }}
"""

# ---------------------------------------------------------------------------
# Configuration dataclasses
# ---------------------------------------------------------------------------


@dataclass
class CommandButton:
    """Configuration for a command bar button.

    Attributes:
        id:         Unique identifier used for programmatic access.
        text:       Label displayed on the button face.
        command:    Callable invoked when the button is clicked.
        tooltip:    Optional tooltip shown on hover.
        icon:       Optional Unicode character or short string prepended to *text*.
        enabled:    Initial enabled state.
        visible:    Initial visibility.
        selectable: When ``True`` the button acts as a toggle (pressed / unpressed).
        width:      Fixed pixel width.  ``None`` lets the button size naturally.
    """
    id: str
    text: str
    command: Callable[[], None]
    tooltip: Optional[str] = None
    icon: Optional[str] = None
    enabled: bool = True
    visible: bool = True
    selectable: bool = False
    width: Optional[int] = None


@dataclass
class CommandDropdown:
    """Configuration for a command bar dropdown (QComboBox).

    Attributes:
        id:      Unique identifier used for programmatic access.
        options: Ordered list of selectable string values.
        command: Optional callback ``(selected_value: str) -> None`` fired on change.
        label:   Optional text label rendered immediately to the left of the combobox.
        default: Initially selected value.  Defaults to the first option.
        tooltip: Optional tooltip shown on hover.
        enabled: Initial enabled state.
        visible: Initial visibility.
        width:   Fixed pixel width for the combobox.  ``None`` sizes naturally.
    """
    id: str
    options: List[str]
    command: Optional[Callable[[str], None]] = None
    label: Optional[str] = None
    default: Optional[str] = None
    tooltip: Optional[str] = None
    enabled: bool = True
    visible: bool = True
    width: Optional[int] = None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _refresh_style(widget: QPushButton) -> None:
    """Force Qt to re-evaluate the stylesheet for *widget* after a property change."""
    style = widget.style()
    if style is not None:
        style.unpolish(widget)
        style.polish(widget)


# ---------------------------------------------------------------------------
# Internal slot tracking
# ---------------------------------------------------------------------------

@dataclass
class _ButtonSlot:
    config: CommandButton
    button: QPushButton
    selected: bool = False


@dataclass
class _DropdownSlot:
    config: CommandDropdown
    combo: QComboBox
    label_widget: Optional[QLabel]


# ---------------------------------------------------------------------------
# CommandBar widget
# ---------------------------------------------------------------------------


class CommandBar(QWidget):
    """A horizontal strip of buttons and dropdowns styled with the Pyrox theme.

    Items are laid out left-to-right in insertion order.  A stretch is always
    kept at the right end so items remain left-aligned.  Separators are thin
    vertical lines rendered between groups of controls.

    Items are identified by their ``id`` string for all programmatic mutations
    (enable/disable, show/hide, remove, check selected state).

    Attributes:
        orientation: ``Qt.Orientation.Horizontal`` (default) or ``Vertical``.
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        orientation: Qt.Orientation = Qt.Orientation.Horizontal,
        height: int = 34,
    ) -> None:
        """Initialise the CommandBar.

        Args:
            parent:      Parent widget.
            orientation: Bar direction.  Horizontal (default) or Vertical.
            height:      Fixed bar height (only applies to Horizontal bars).
        """
        super().__init__(parent)
        self.setObjectName('commandbar')
        self.setStyleSheet(_BAR_STYLE)

        self._orientation = orientation
        self._slots: Dict[str, Union[_ButtonSlot, _DropdownSlot]] = {}
        # Keep insertion-order list to enable ordered layout rebuilds
        self._order: List[str] = []
        # Separators are plain widgets — track them separately
        self._separators: List[QWidget] = []

        if orientation == Qt.Orientation.Horizontal:
            self.setFixedHeight(height)
            self._layout = QHBoxLayout(self)
        else:
            self._layout = QVBoxLayout(self)

        self._layout.setContentsMargins(4, 2, 4, 2)
        self._layout.setSpacing(4)
        self._layout.addStretch()

    # ------------------------------------------------------------------
    # Public mutators
    # ------------------------------------------------------------------

    def add_button(self, config: CommandButton) -> QPushButton:
        """Add a button to the bar from a :class:`CommandButton` config.

        The button is inserted before the trailing stretch.

        Args:
            config: Button configuration dataclass.

        Returns:
            The constructed :class:`QPushButton`.

        Raises:
            ValueError: If *config.id* is already registered.
        """
        if config.id in self._slots:
            raise ValueError(f"CommandBar: id '{config.id}' is already registered.")

        label = f'{config.icon} {config.text}' if config.icon else config.text
        btn = QPushButton(label, self)

        if config.tooltip:
            btn.setToolTip(config.tooltip)
        if config.width is not None:
            btn.setFixedWidth(config.width)

        btn.setEnabled(config.enabled)
        btn.setVisible(config.visible)

        slot = _ButtonSlot(config=config, button=btn)
        self._slots[config.id] = slot
        self._order.append(config.id)

        if config.selectable:
            btn.clicked.connect(lambda: self._toggle_selected(config.id))
        else:
            btn.clicked.connect(config.command)

        # Insert before the trailing stretch (last layout item)
        stretch_idx = self._layout.count() - 1
        self._layout.insertWidget(stretch_idx, btn)
        return btn

    def add_dropdown(self, config: CommandDropdown) -> QComboBox:
        """Add a dropdown (QComboBox) to the bar from a :class:`CommandDropdown` config.

        An optional label is placed immediately to the left of the combobox.

        Args:
            config: Dropdown configuration dataclass.

        Returns:
            The constructed :class:`QComboBox`.

        Raises:
            ValueError: If *config.id* is already registered.
        """
        if config.id in self._slots:
            raise ValueError(f"CommandBar: id '{config.id}' is already registered.")

        label_widget: Optional[QLabel] = None
        stretch_idx = self._layout.count() - 1

        if config.label:
            label_widget = QLabel(config.label, self)
            label_widget.setVisible(config.visible)
            self._layout.insertWidget(stretch_idx, label_widget)
            stretch_idx += 1

        combo = QComboBox(self)
        combo.addItems(config.options)

        if config.default and config.default in config.options:
            combo.setCurrentText(config.default)
        elif config.options:
            combo.setCurrentIndex(0)

        if config.tooltip:
            combo.setToolTip(config.tooltip)
        if config.width is not None:
            combo.setFixedWidth(config.width)

        combo.setEnabled(config.enabled)
        combo.setVisible(config.visible)

        if config.command:
            combo.currentTextChanged.connect(config.command)

        slot = _DropdownSlot(config=config, combo=combo, label_widget=label_widget)
        self._slots[config.id] = slot
        self._order.append(config.id)

        self._layout.insertWidget(stretch_idx, combo)
        return combo

    def add_separator(self) -> None:
        """Insert a thin vertical (or horizontal) separator line at the current end."""
        sep = QFrame(self)
        if self._orientation == Qt.Orientation.Horizontal:
            sep.setFrameShape(QFrame.Shape.VLine)
            sep.setFixedWidth(6)
        else:
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setFixedHeight(6)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        self._separators.append(sep)
        stretch_idx = self._layout.count() - 1
        self._layout.insertWidget(stretch_idx, sep)

    def remove_item(self, item_id: str) -> None:
        """Remove a button or dropdown from the bar by its *item_id*.

        Args:
            item_id: The ``id`` assigned when the item was added.

        Raises:
            KeyError: If *item_id* is not registered.
        """
        slot = self._slots.pop(item_id)
        self._order.remove(item_id)

        if isinstance(slot, _ButtonSlot):
            slot.button.deleteLater()
        else:
            if slot.label_widget is not None:
                slot.label_widget.deleteLater()
            slot.combo.deleteLater()

    # ------------------------------------------------------------------
    # State queries
    # ------------------------------------------------------------------

    def get_button(self, item_id: str) -> QPushButton:
        """Return the :class:`QPushButton` for *item_id*.

        Raises:
            KeyError: If not found.
            TypeError: If the item is not a button.
        """
        slot = self._slots[item_id]
        if not isinstance(slot, _ButtonSlot):
            raise TypeError(f"'{item_id}' is a dropdown, not a button.")
        return slot.button

    def get_dropdown(self, item_id: str) -> QComboBox:
        """Return the :class:`QComboBox` for *item_id*.

        Raises:
            KeyError: If not found.
            TypeError: If the item is not a dropdown.
        """
        slot = self._slots[item_id]
        if not isinstance(slot, _DropdownSlot):
            raise TypeError(f"'{item_id}' is a button, not a dropdown.")
        return slot.combo

    def is_selected(self, item_id: str) -> bool:
        """Return the current selected/toggled state of a selectable button."""
        slot = self._slots[item_id]
        if not isinstance(slot, _ButtonSlot):
            raise TypeError(f"'{item_id}' is not a button.")
        return slot.selected

    # ------------------------------------------------------------------
    # Programmatic state changes
    # ------------------------------------------------------------------

    def set_button_enabled(self, item_id: str, enabled: bool) -> None:
        """Enable or disable a button or dropdown.

        Args:
            item_id: Target item id.
            enabled: New enabled state.
        """
        slot = self._slots[item_id]
        if isinstance(slot, _ButtonSlot):
            slot.button.setEnabled(enabled)
        else:
            slot.combo.setEnabled(enabled)
            if slot.label_widget:
                slot.label_widget.setEnabled(enabled)

    def set_button_visible(self, item_id: str, visible: bool) -> None:
        """Show or hide a button or dropdown (and its label if present).

        Args:
            item_id: Target item id.
            visible: New visibility.
        """
        slot = self._slots[item_id]
        if isinstance(slot, _ButtonSlot):
            slot.button.setVisible(visible)
        else:
            slot.combo.setVisible(visible)
            if slot.label_widget:
                slot.label_widget.setVisible(visible)

    def set_button_selected(self, item_id: str, selected: bool) -> None:
        """Set the selected/toggled visual state of a selectable button.

        Non-selectable buttons can still have their state set, but the visual
        change only applies when ``config.selectable`` is ``True``.

        Args:
            item_id:  Target button id.
            selected: New selected state.
        """
        slot = self._slots[item_id]
        if not isinstance(slot, _ButtonSlot):
            raise TypeError(f"'{item_id}' is not a button.")
        slot.selected = selected
        slot.button.setProperty('selected', 'true' if selected else 'false')
        # Force Qt to re-evaluate the stylesheet for this widget
        _refresh_style(slot.button)
        if selected and slot.config.selectable:
            slot.config.command()

    def set_dropdown_value(self, item_id: str, value: str) -> None:
        """Programmatically change the selected value of a dropdown.

        Does *not* fire the ``command`` callback.

        Args:
            item_id: Target dropdown id.
            value:   Value to select (must be present in the dropdown's options).
        """
        slot = self._slots[item_id]
        if not isinstance(slot, _DropdownSlot):
            raise TypeError(f"'{item_id}' is not a dropdown.")
        combo = slot.combo
        combo.blockSignals(True)
        combo.setCurrentText(value)
        combo.blockSignals(False)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _toggle_selected(self, item_id: str) -> None:
        """Toggle the selected state of a selectable button and invoke its command."""
        slot = self._slots.get(item_id)
        if slot is None or not isinstance(slot, _ButtonSlot):
            return
        new_state = not slot.selected
        slot.selected = new_state
        slot.button.setProperty('selected', 'true' if new_state else 'false')
        _refresh_style(slot.button)
        slot.config.command()


# ---------------------------------------------------------------------------
# Standalone demo
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle('CommandBar — Demo')
    window.resize(700, 120)
    window.setStyleSheet(f'background-color: {DefaultTheme.background};')

    layout = QVBoxLayout(window)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    status_lbl = QLabel('Ready.', window)
    status_lbl.setContentsMargins(8, 4, 8, 4)
    status_lbl.setStyleSheet(
        f'color: {DefaultTheme.foreground};'
        f'background-color: {DefaultTheme.background};'
        f"font-family: '{DefaultTheme.font_family}';"
        f'font-size: {DefaultTheme.font_size}pt;'
    )

    def _log(msg: str) -> None:
        status_lbl.setText(msg)

    bar = CommandBar(parent=window)

    bar.add_button(CommandButton(
        id='new',
        text='New',
        icon='📄',
        command=lambda: _log('New clicked'),
        tooltip='Create a new file',
    ))
    bar.add_button(CommandButton(
        id='open',
        text='Open',
        icon='📂',
        command=lambda: _log('Open clicked'),
        tooltip='Open a file',
    ))
    bar.add_button(CommandButton(
        id='save',
        text='Save',
        icon='💾',
        command=lambda: _log('Save clicked'),
        tooltip='Save the current file',
    ))

    bar.add_separator()

    bar.add_button(CommandButton(
        id='run',
        text='Run',
        icon='▶',
        command=lambda: _log('Run clicked'),
        selectable=True,
        tooltip='Toggle run mode',
    ))
    bar.add_button(CommandButton(
        id='pause',
        text='Pause',
        icon='⏸',
        command=lambda: _log('Pause clicked'),
        enabled=False,
    ))

    bar.add_separator()

    bar.add_dropdown(CommandDropdown(
        id='mode',
        label='Mode:',
        options=['Auto', 'Manual', 'Semi-Auto'],
        command=lambda v: _log(f'Mode changed → {v}'),
        default='Auto',
        width=110,
    ))

    layout.addWidget(bar)

    sep = QFrame(window)
    sep.setFrameShape(QFrame.Shape.HLine)
    sep.setStyleSheet(f'color: {DefaultTheme.bordercolor};')
    layout.addWidget(sep)

    layout.addWidget(status_lbl)
    layout.addStretch()

    window.show()
    sys.exit(app.exec())
