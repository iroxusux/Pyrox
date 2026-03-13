"""PyQt6 frame implementations for the Pyrox GUI framework.

This module provides frame implementations for the Pyrox GUI framework,
including abstract base classes and concrete implementations for task frames
and other specialized frame types.
"""
from __future__ import annotations
from typing import Callable
from PyQt6.QtWidgets import (
    QWidget,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
)
from pyrox.services import log


class TaskFrame:
    """A PyQt6 frame for tasks in the application with title bar and close button.

    This frame provides a standardized interface for task windows with
    a title bar containing a close button and title label. It includes
    callback support for cleanup operations when the frame is destroyed.

    Attributes:
        _name (str): The name of the task frame.
        _shown (bool): Whether the frame is currently shown.
        _title_bar (QWidget): The title bar widget containing controls.
        _close_button (QPushButton): The close button in the title bar.
        _title_label (QLabel): The title label in the title bar.
        _content_frame (QWidget): The main content area of the frame.
        _on_destroy (list[Callable]): List of callbacks to execute on destroy.
    """

    def __init__(
        self,
        name: str,
        parent: QWidget,
    ):
        self._name = name or 'Task Frame'
        self._parent = parent

        self._root = QWidget(parent)
        self._root.setObjectName(name.lower())

        self._shown: bool = False

        outer_layout = QVBoxLayout(self._root)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Title bar
        self._title_bar = QWidget(self._root)
        self._title_bar.setFixedHeight(30)
        title_layout = QHBoxLayout(self._title_bar)
        title_layout.setContentsMargins(5, 2, 5, 2)

        self._title_label = QLabel(name or 'Task Frame', self._title_bar)
        title_layout.addWidget(self._title_label)
        title_layout.addStretch()

        self._close_button = QPushButton('X', self._title_bar)
        self._close_button.setFixedSize(24, 20)
        self._close_button.clicked.connect(self.destroy)
        title_layout.addWidget(self._close_button)

        outer_layout.addWidget(self._title_bar)

        # Content frame
        self._content_frame = QWidget(self._root)
        QVBoxLayout(self._content_frame).setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(self._content_frame, 1)

        self._on_destroy: list[Callable] = []

    @property
    def content_frame(self) -> QWidget:
        """Get the content frame for adding widgets.

        Returns:
            QWidget: The main content area where widgets should be added.
        """
        return self._content_frame

    @property
    def root(self) -> QWidget:
        """Get the root widget of the task frame.

        Returns:
            QWidget: The root widget containing the entire frame.
        """
        return self._root

    def build(self, **kwargs) -> None:
        """Build the task frame.

        This method can be overridden by subclasses to populate
        the content frame with widgets.
        """
        pass

    def set_shown(self, value: bool) -> None:
        """Set the shown state of the task frame.

        Args:
            value (bool): The new shown state.
        """
        self._shown = value
        self._root.setVisible(value)

    def destroy(self) -> None:
        """Destroy the task frame and execute all registered callbacks.

        Calls all functions in the on_destroy list before destroying the frame.
        Non-callable items in the list generate warning messages.
        """
        for callback in self.on_destroy():
            if callable(callback):
                try:
                    callback(self)
                except Exception as e:
                    log(self).warning(f'Error in destroy callback: {e}')
                    raise e
            else:
                log(self).warning(f'Callback {callback} is not callable.')

        self.on_destroy().clear()
        self._root.deleteLater()

    def on_destroy(self) -> list[Callable]:
        """Get the list of destroy callbacks.

        Returns:
            list[Callable]: List of functions to call when the frame is destroyed.
        """
        return self._on_destroy

    @property
    def name(self) -> str:
        """Get the name of the task frame."""
        return self._name

    def get_name(self) -> str:
        """Get the name of the task frame."""
        return self._name

    def set_name(self, name: str) -> None:
        """Set the name of the task frame."""
        self._name = name

    def get_shown(self) -> bool:
        """Get the shown state of the task frame."""
        return self._shown

    @property
    def shown(self) -> bool:
        """Get or set the shown state of the task frame."""
        return self._shown

    @shown.setter
    def shown(self, value: bool) -> None:
        """Set the shown state of the task frame."""
        self.set_shown(value)

    def get_root(self) -> QWidget:
        """Get the root widget of the task frame."""
        return self._root
