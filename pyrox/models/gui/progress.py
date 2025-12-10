"""
GUI Progress Integration for ControlRox.

This module provides integration between the ProgressService and GUI loading bars,
allowing automatic display of progress updates without coupling models to GUI.
"""
from __future__ import annotations

from typing import Optional, Union
import tkinter as tk

from pyrox.models.gui.loadingbar import PyroxLoadingBar, LoadingConfig, LoadingMode
from pyrox.services.progress import ProgressService, ProgressUpdate, ProgressStatus
from pyrox.services.logging import log


class ProgressBarController:
    """
    Controller that connects ProgressService to a PyroxLoadingBar.

    This class automatically updates a loading bar based on progress updates
    from the ProgressService, providing a clean separation between business
    logic and GUI display.
    """

    def __init__(
        self,
        loading_bar: PyroxLoadingBar,
        operation_filter: Optional[str] = None
    ):
        """
        Initialize the progress bar controller.

        Args:
            loading_bar: The PyroxLoadingBar to control
            operation_filter: If specified, only updates for this operation ID will be processed
        """
        self.loading_bar = loading_bar
        self.operation_filter = operation_filter
        self._progress_service = ProgressService.get_instance()
        self._current_operation_id: Optional[str] = None

        # Subscribe to progress updates
        self._progress_service.subscribe(self._on_progress_update)
        log(self).info(f"ProgressBarController created with filter: {operation_filter}")

    def _on_progress_update(self, update: ProgressUpdate) -> None:
        """Handle progress updates from the ProgressService."""
        # Filter by operation if specified
        if self.operation_filter and update.operation_id != self.operation_filter:
            return

        # Update current operation tracking
        if update.status == ProgressStatus.STARTING:
            self._current_operation_id = update.operation_id
        elif update.is_complete and update.operation_id == self._current_operation_id:
            self._current_operation_id = None

        # Update loading bar based on status
        self._update_loading_bar(update)

    def _update_loading_bar(self, update: ProgressUpdate) -> None:
        """Update the loading bar based on progress update."""
        try:
            # Map progress status to loading state
            if update.status == ProgressStatus.STARTING:
                self.loading_bar.start_loading(update.message)

            elif update.status == ProgressStatus.IN_PROGRESS:
                # Build status text
                status_text = self._build_status_text(update)

                # Update progress
                if self.loading_bar.config.mode == LoadingMode.DETERMINATE:
                    self.loading_bar.set_progress(update.progress, 100)
                else:
                    self.loading_bar.set_status_text(status_text)

            elif update.status == ProgressStatus.COMPLETED:
                self.loading_bar.set_completed(update.message or "Operation completed successfully")

            elif update.status == ProgressStatus.ERROR:
                self.loading_bar.set_error(update.message or "Operation failed")

            elif update.status == ProgressStatus.CANCELED:
                self.loading_bar.set_canceled()

        except Exception as e:
            log(self).error(f"Error updating loading bar: {e}")

    def _build_status_text(self, update: ProgressUpdate) -> str:
        """Build comprehensive status text from progress update."""
        parts = []

        # Main message
        if update.message:
            parts.append(update.message)

        # Step information
        if update.current_step:
            if update.step_text:
                parts.append(f"{update.step_text}: {update.current_step}")
            else:
                parts.append(update.current_step)

        # Time information if available
        if hasattr(self.loading_bar.config, 'show_time') and self.loading_bar.config.show_time:
            if update.estimated_remaining:
                time_text = f"~{update.estimated_remaining:.0f}s remaining"
                parts.append(time_text)

        return " | ".join(parts) if parts else "Processing..."

    def disconnect(self) -> None:
        """Disconnect from the ProgressService."""
        self._progress_service.unsubscribe(self._on_progress_update)
        log(self).info("ProgressBarController disconnected")


class LoadingBarManager:
    """
    High-level manager for loading bars with progress integration.

    This class provides convenient methods to create and manage loading bars
    that are automatically connected to the ProgressService.
    """

    @staticmethod
    def create_progress_window(
        title: str = "Loading...",
        operation_id: Optional[str] = None,
        config: Optional[LoadingConfig] = None,
        parent: Optional[Union[tk.Widget, tk.Tk, tk.Toplevel]] = None
    ) -> tuple[tk.Toplevel, ProgressBarController]:
        """
        Create a popup window with a loading bar connected to ProgressService.

        Args:
            title: Window title
            operation_id: Operation ID to filter for (None for all operations)
            config: LoadingConfig for the bar appearance
            parent: Parent widget

        Returns:
            Tuple of (window, controller)
        """
        # Create popup window
        window = tk.Toplevel(parent)
        window.title(title)
        window.geometry("400x120")
        window.resizable(False, False)

        # Center the window
        window.update_idletasks()
        x = (window.winfo_screenwidth() // 2) - (400 // 2)
        y = (window.winfo_screenheight() // 2) - (120 // 2)
        window.geometry(f"400x120+{x}+{y}")

        # Make window modal
        window.transient(parent)  # type: ignore
        window.grab_set()

        # Create loading bar
        if config is None:
            config = LoadingConfig(
                mode=LoadingMode.DETERMINATE,
                show_percentage=True,
                show_text=True,
                animate=True
            )

        loading_bar = PyroxLoadingBar(window, config=config)
        loading_bar.frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Create controller
        controller = ProgressBarController(loading_bar, operation_id)

        return window, controller

    @staticmethod
    def create_embedded_progress_bar(
        parent: tk.Widget,
        operation_id: Optional[str] = None,
        config: Optional[LoadingConfig] = None
    ) -> ProgressBarController:
        """
        Create an embedded loading bar connected to ProgressService.

        Args:
            parent: Parent widget to embed the bar in
            operation_id: Operation ID to filter for (None for all operations)
            config: LoadingConfig for the bar appearance

        Returns:
            ProgressBarController
        """
        # Create loading bar
        if config is None:
            config = LoadingConfig(
                mode=LoadingMode.DETERMINATE,
                show_percentage=True,
                show_text=True,
                height=20
            )

        loading_bar = PyroxLoadingBar(parent, config=config)

        # Create controller
        controller = ProgressBarController(loading_bar, operation_id)

        return controller


# Convenience functions for common use cases
def show_controller_loading_progress(
    parent: Optional[Union[tk.Widget, tk.Tk, tk.Toplevel]] = None
) -> tuple[tk.Toplevel, ProgressBarController]:
    """Show a loading window specifically for controller loading operations."""
    return LoadingBarManager.create_progress_window(
        title="Loading Controller...",
        operation_id="load_controller",
        config=LoadingConfig(
            mode=LoadingMode.DETERMINATE,
            show_percentage=True,
            show_text=True,
            show_time=True,
            animate=True,
            color_scheme='default'
        ),
        parent=parent
    )


def show_generic_loading_progress(
    title: str = "Processing...",
    parent: Optional[tk.Widget] = None
) -> tuple[tk.Toplevel, ProgressBarController]:
    """Show a generic loading window for any operation."""
    return LoadingBarManager.create_progress_window(
        title=title,
        config=LoadingConfig(
            mode=LoadingMode.INDETERMINATE,
            show_text=True,
            animate=True,
            color_scheme='info'
        ),
        parent=parent
    )
