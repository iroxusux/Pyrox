"""Attribute Tree View for Pyrox GUI applications.

Provides a PyQt6-based panel that lazily introspects any Python object and
presents its public attributes in an expandable tree.  Private names (those
beginning with ``_``) and callable methods are hidden.  Native container
types (``list``, ``tuple``, ``dict``) are drilled into automatically so
their contents appear as child nodes.

``AttributeTreeView`` is a :class:`~pyrox.models.gui.frame.TaskFrame` and
therefore ships with the standard Pyrox title bar and close button.

Example Usage:
    ```python
    inspector = AttributeTreeView(parent=splitter, title="Inspector")
    inspector.set_object(my_controller)
    splitter.addWidget(inspector.root)

    # Refresh at any time
    inspector.refresh()

    # Clear the panel
    inspector.clear()
    ```
"""
from __future__ import annotations

import sys
from typing import Any, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pyrox.models.gui.frame import TaskFrame
from pyrox.models.gui.theme import DefaultTheme
from pyrox.services.logging import log

__all__ = ('AttributeTreeView',)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PRIMITIVE_TYPES = (int, float, str, bool, bytes, type(None))

# Types that are treated as "containers" and drilled into automatically
_CONTAINER_TYPES = (list, tuple, dict)

# Cap on how many list/tuple items are rendered before a "… N more" node
_MAX_SEQUENCE_ITEMS = 100

# Stylesheet applied to the entire panel root so all child widgets inherit
# the Pyrox dark theme without each widget needing its own style rule.
_PANEL_STYLE = f"""
    QWidget {{
        background-color: {DefaultTheme.background};
        color: {DefaultTheme.foreground};
        font-family: '{DefaultTheme.font_family}';
        font-size: {DefaultTheme.font_size}pt;
    }}
    QTreeWidget {{
        background-color: {DefaultTheme.widget_background};
        color: {DefaultTheme.foreground};
        border: {DefaultTheme.borderwidth}px solid {DefaultTheme.bordercolor};
        alternate-background-color: {DefaultTheme.background};
    }}
    QTreeWidget::item:selected {{
        background-color: {DefaultTheme.background_selected};
        color: {DefaultTheme.foreground_selected};
    }}
    QTreeWidget::item:hover {{
        background-color: {DefaultTheme.background_hover};
        color: {DefaultTheme.foreground_hover};
    }}
    QLineEdit {{
        background-color: {DefaultTheme.widget_background};
        color: {DefaultTheme.foreground};
        border: {DefaultTheme.borderwidth}px solid {DefaultTheme.bordercolor};
        padding: 2px 4px;
    }}
    QPushButton {{
        background-color: {DefaultTheme.button_color};
        color: {DefaultTheme.foreground};
        border: {DefaultTheme.borderwidth}px solid {DefaultTheme.bordercolor};
        padding: 2px 6px;
    }}
    QPushButton:hover {{
        background-color: {DefaultTheme.button_hover};
        color: {DefaultTheme.foreground_hover};
    }}
    QPushButton:pressed {{
        background-color: {DefaultTheme.button_active};
    }}
    QLabel {{
        background-color: transparent;
        color: {DefaultTheme.foreground};
    }}
    QFrame[frameShape="4"],
    QFrame[frameShape="5"] {{
        color: {DefaultTheme.bordercolor};
    }}
"""


def _is_public_attr(name: str, value: Any) -> bool:
    """Return True when *name* should be shown as an attribute node.

    Filters out:
    - Private / dunder names (start with ``_``).
    - Callable objects (methods, functions, lambdas).
    """
    if name.startswith('_'):
        return False
    if callable(value) and not isinstance(value, _CONTAINER_TYPES):
        return False
    return True


def _type_label(value: Any) -> str:
    """Return a short human-readable type hint string for *value*."""
    if value is None:
        return 'None'
    return type(value).__name__


def _preview(value: Any, max_len: int = 60) -> str:
    """Return a short preview string for *value* suitable for column 1."""
    if isinstance(value, dict):
        return f'{{…}} ({len(value)} keys)'
    if isinstance(value, (list, tuple)):
        bracket = '[]' if isinstance(value, list) else '()'
        return f'{bracket[0]}…{bracket[1]} ({len(value)} items)'
    raw = repr(value)
    return raw if len(raw) <= max_len else raw[:max_len - 1] + '…'


# ---------------------------------------------------------------------------
# Tree population
# ---------------------------------------------------------------------------

def _populate_item(parent_item: QTreeWidgetItem, value: Any, depth: int = 0) -> None:
    """Recursively populate *parent_item* with child nodes for *value*.

    For primitive types the parent item's columns are already set by the
    caller; this function only adds children for containers and objects.

    Args:
        parent_item: The QTreeWidgetItem to add children to.
        value:       The Python value to inspect.
        depth:       Current recursion depth (prevents infinite loops on
                     circular references).
    """
    if depth > 20:
        _add_leaf(parent_item, '…', 'max depth reached', 'str')
        return

    if isinstance(value, dict):
        for k, v in value.items():
            child = QTreeWidgetItem(parent_item)
            child.setText(0, str(k))
            child.setText(1, _type_label(v))
            child.setText(2, _preview(v))
            if not isinstance(v, _PRIMITIVE_TYPES):
                _populate_item(child, v, depth + 1)
                child.setChildIndicatorPolicy(
                    QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator
                )

    elif isinstance(value, (list, tuple)):
        items = list(value)
        render = items[:_MAX_SEQUENCE_ITEMS]
        for idx, v in enumerate(render):
            child = QTreeWidgetItem(parent_item)
            child.setText(0, f'[{idx}]')
            child.setText(1, _type_label(v))
            child.setText(2, _preview(v))
            if not isinstance(v, _PRIMITIVE_TYPES):
                _populate_item(child, v, depth + 1)
                child.setChildIndicatorPolicy(
                    QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator
                )
        if len(items) > _MAX_SEQUENCE_ITEMS:
            overflow = QTreeWidgetItem(parent_item)
            overflow.setText(0, f'… {len(items) - _MAX_SEQUENCE_ITEMS} more items')

    else:
        # Generic object — show public attributes
        _populate_object_attrs(parent_item, value, depth)


def _populate_object_attrs(
    parent_item: QTreeWidgetItem, obj: Any, depth: int
) -> None:
    """Add public attribute children of *obj* to *parent_item*."""
    try:
        attr_names = [
            name for name in dir(obj)
            if not name.startswith('_')
        ]
    except Exception:
        return

    for name in attr_names:
        try:
            value = getattr(obj, name)
        except Exception as exc:
            child = QTreeWidgetItem(parent_item)
            child.setText(0, name)
            child.setText(1, 'error')
            child.setText(2, str(exc))
            continue

        if not _is_public_attr(name, value):
            continue

        child = QTreeWidgetItem(parent_item)
        child.setText(0, name)
        child.setText(1, _type_label(value))
        child.setText(2, _preview(value))

        if not isinstance(value, _PRIMITIVE_TYPES):
            _populate_item(child, value, depth + 1)
            if child.childCount():
                child.setChildIndicatorPolicy(
                    QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator
                )


def _add_leaf(
    parent: QTreeWidgetItem, name: str, preview: str, type_str: str
) -> None:
    item = QTreeWidgetItem(parent)
    item.setText(0, name)
    item.setText(1, type_str)
    item.setText(2, preview)


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------


class AttributeTreeView(TaskFrame):
    """A lazy-loading attribute inspector presented as a tree view.

    Displays public, non-callable attributes of any Python object in a
    three-column tree: **Name**, **Type**, and **Value**.  Container types
    (``list``, ``tuple``, ``dict``) and nested objects are expanded into
    child nodes.  A live search bar filters visible rows by attribute name.

    The panel follows the Pyrox dark theme via :class:`DefaultTheme` and
    extends :class:`TaskFrame` for the standard title bar / close button.

    Attributes:
        target_object: The object currently being inspected, or ``None``.
    """

    _BOLD_FONT: Optional[QFont] = None

    def __init__(
        self,
        parent: QWidget,
        title: str = 'Attribute Inspector',
        width: int = 360,
    ) -> None:
        """Initialise the AttributeTreeView.

        Args:
            parent: Parent widget (e.g. a ``QSplitter``).
            title:  Title shown in the panel's title bar.
            width:  Minimum panel width in pixels.
        """
        super().__init__(name=title, parent=parent)
        self.root.setMinimumWidth(width)
        self.root.setStyleSheet(_PANEL_STYLE)

        self._target: Optional[Any] = None
        self._bold_font = QFont()
        self._bold_font.setBold(True)

        self._build_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def target_object(self) -> Optional[Any]:
        """The object currently being inspected."""
        return self._target

    def set_object(self, obj: Optional[Any]) -> None:
        """Bind a new object to inspect and refresh the tree.

        Args:
            obj: Any Python object, or ``None`` to clear the panel.
        """
        self._target = obj
        self.refresh()

    def refresh(self) -> None:
        """Rebuild the tree from scratch using the current target object.

        Safe to call at any time; clears existing content first.
        """
        self._tree.clear()
        self._status_label.setText('')

        if self._target is None:
            self._status_label.setText('No object set')
            return

        filter_text = self._search_edit.text().strip().lower()

        # Collect public, non-callable attributes
        try:
            all_names = [n for n in dir(self._target) if not n.startswith('_')]
        except Exception as exc:
            self._status_label.setText(f'Error: {exc}')
            log(self).warning(f'AttributeTreeView: could not inspect object: {exc}')
            return

        attr_count = 0
        for name in all_names:
            try:
                value = getattr(self._target, name)
            except Exception as exc:
                # Still show the slot but mark it as an error
                if filter_text and filter_text not in name.lower():
                    continue
                root_item = QTreeWidgetItem(self._tree)
                root_item.setText(0, name)
                root_item.setText(1, 'error')
                root_item.setText(2, str(exc))
                attr_count += 1
                continue

            if not _is_public_attr(name, value):
                continue

            if filter_text and filter_text not in name.lower():
                continue

            root_item = QTreeWidgetItem(self._tree)
            root_item.setText(0, name)
            root_item.setText(1, _type_label(value))
            root_item.setText(2, _preview(value))

            if not isinstance(value, _PRIMITIVE_TYPES):
                _populate_item(root_item, value, depth=1)
                if root_item.childCount():
                    root_item.setChildIndicatorPolicy(
                        QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator
                    )

            attr_count += 1

        noun = 'attribute' if attr_count == 1 else 'attributes'
        type_name = type(self._target).__name__
        self._status_label.setText(f'{type_name} — {attr_count} {noun}')
        log(self).debug(
            f'AttributeTreeView refreshed: {type_name} with {attr_count} {noun}'
        )

    def clear(self) -> None:
        """Clear the panel and remove the current target object."""
        self._target = None
        self._tree.clear()
        self._status_label.setText('No object set')

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Build the widget hierarchy inside ``content_frame``."""
        content_layout = self.content_frame.layout()
        content_layout.setContentsMargins(6, 6, 6, 4)  # type: ignore[union-attr]
        content_layout.setSpacing(4)  # type: ignore[union-attr]

        # -- Toolbar (search + refresh) ------------------------------------
        toolbar = QWidget(self.content_frame)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(2)

        search_icon = QLabel('🔍', toolbar)
        toolbar_layout.addWidget(search_icon)

        self._search_edit = QLineEdit(toolbar)
        self._search_edit.setPlaceholderText('Filter attributes…')
        self._search_edit.textChanged.connect(self._on_search_changed)
        toolbar_layout.addWidget(self._search_edit, 1)

        refresh_btn = QPushButton('↺', toolbar)
        refresh_btn.setFixedWidth(28)
        refresh_btn.setToolTip('Refresh attribute tree')
        refresh_btn.clicked.connect(self.refresh)
        toolbar_layout.addWidget(refresh_btn)

        content_layout.addWidget(toolbar)  # type: ignore[union-attr]

        # -- Tree ----------------------------------------------------------
        self._tree = QTreeWidget(self.content_frame)
        self._tree.setColumnCount(3)
        self._tree.setHeaderLabels(['Attribute', 'Type', 'Value'])
        self._tree.header().setDefaultSectionSize(120)  # type: ignore[union-attr]
        self._tree.setAlternatingRowColors(True)
        self._tree.setSortingEnabled(True)
        self._tree.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self._tree.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        content_layout.addWidget(self._tree, 1)  # type: ignore[union-attr]

        # -- Status bar ----------------------------------------------------
        separator = QFrame(self.content_frame)
        separator.setFrameShape(QFrame.Shape.HLine)
        content_layout.addWidget(separator)  # type: ignore[union-attr]

        self._status_label = QLabel('No object set', self.content_frame)
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        content_layout.addWidget(self._status_label)  # type: ignore[union-attr]

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_search_changed(self) -> None:
        """Re-filter the tree whenever the search text changes."""
        self.refresh()


# ---------------------------------------------------------------------------
# Standalone demo
# ---------------------------------------------------------------------------

if __name__ == '__main__':

    class _NestedExample:
        """Sample nested object used in the demo."""

        def __init__(self) -> None:
            self.motor_speed: float = 1450.0
            self.enabled: bool = True
            self.label: str = 'Drive M1'
            self._private_field: str = 'hidden'

        def start(self) -> None:  # method — should not appear
            pass

    class _DemoObject:
        """Rich sample object that exercises all tree features."""

        version: str = '1.2.3'
        max_connections: int = 8

        def __init__(self) -> None:
            self.name: str = 'Demo Controller'
            self.ip_address: str = '192.168.1.100'
            self.slot: int = 0
            self.connected: bool = False
            self.scan_rate_ms: float = 10.0
            self.tags: list[str] = [
                'Motor_Run', 'Motor_Fault', 'Conveyor_Speed',
                'PhotoEye_PE01', 'PhotoEye_PE02',
            ]
            self.module_map: dict[str, str] = {
                '1756-L85E': 'ControlLogix',
                '1756-EN2T': 'EtherNet/IP',
                '1756-IB16': 'Digital Input',
            }
            self.drive: _NestedExample = _NestedExample()
            self._internal: str = 'should be hidden'

        def connect(self) -> None:  # method — should not appear
            pass

    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle('AttributeTreeView — Demo')
    window.resize(800, 560)
    window.setStyleSheet(f'background-color: {DefaultTheme.background};')

    layout = QVBoxLayout(window)
    layout.setContentsMargins(8, 8, 8, 8)
    layout.setSpacing(6)

    # -- Top toolbar: object selector + status ---------------------------
    btn_bar = QWidget(window)
    btn_layout = QHBoxLayout(btn_bar)
    btn_layout.setContentsMargins(0, 0, 0, 0)
    btn_layout.setSpacing(6)

    status_lbl = QLabel('No object selected.', window)
    status_lbl.setStyleSheet(f'color: {DefaultTheme.foreground};')

    inspector = AttributeTreeView(parent=window, title='Attribute Inspector')

    demo_obj = _DemoObject()
    nested_obj = _NestedExample()

    def _load(obj: Any, label: str) -> None:
        inspector.set_object(obj)
        status_lbl.setText(f'Inspecting: {label}')

    for btn_text, obj, lbl in [
        ('Load DemoObject', demo_obj, '_DemoObject'),
        ('Load NestedExample', nested_obj, '_NestedExample'),
        ('Load plain list', ['alpha', 'beta', 'gamma', 42, True], 'list'),
        ('Load dict', {'key_a': 1, 'key_b': [1, 2, 3]}, 'dict'),
        ('Clear', None, '(none)'),
    ]:
        btn = QPushButton(btn_text, btn_bar)
        btn.setStyleSheet(
            f'background-color: {DefaultTheme.button_color};'
            f'color: {DefaultTheme.foreground};'
            f'border: 1px solid {DefaultTheme.bordercolor};'
            f'padding: 3px 8px;'
        )
        _obj, _lbl = obj, lbl
        btn.clicked.connect(lambda checked=False, o=_obj, lb=_lbl: _load(o, lb))
        btn_layout.addWidget(btn)

    btn_layout.addStretch()
    layout.addWidget(btn_bar)
    layout.addWidget(status_lbl)

    layout.addWidget(inspector.root, 1)

    # Pre-load with the demo object
    inspector.set_object(demo_obj)
    status_lbl.setText('Inspecting: _DemoObject')

    window.show()
    sys.exit(app.exec())
