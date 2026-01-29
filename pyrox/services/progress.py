"""
Progress Service for ControlRox applications.

This service provides a clean way to report loading progress from model operations
to GUI components without coupling model logic to GUI implementations.
"""
from __future__ import annotations

from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import threading
import time

from pyrox.models.list import Subscribable
from pyrox.services import log


class ProgressStatus(Enum):
    """Progress status states."""
    IDLE = "idle"
    STARTING = "starting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELED = "canceled"


@dataclass
class ProgressUpdate:
    """Progress update event data."""
    operation_id: str
    status: ProgressStatus
    progress: float = 0.0  # 0.0 to 100.0
    message: str = ""
    current_step: Optional[str] = None
    total_steps: Optional[int] = None
    current_step_index: Optional[int] = None
    elapsed_time: float = 0.0
    estimated_remaining: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

    @property
    def is_complete(self) -> bool:
        """Check if this operation is complete."""
        return self.status in (ProgressStatus.COMPLETED, ProgressStatus.ERROR, ProgressStatus.CANCELED)

    @property
    def percentage_text(self) -> str:
        """Get formatted percentage text."""
        return f"{self.progress:.1f}%"

    @property
    def step_text(self) -> str:
        """Get formatted step text."""
        if self.current_step_index is not None and self.total_steps is not None:
            return f"Step {self.current_step_index + 1} of {self.total_steps}"
        return ""


class ProgressOperation:
    """Tracks progress for a single operation."""

    def __init__(self, operation_id: str, service: 'ProgressService'):
        self.operation_id = operation_id
        self.service = service
        self._start_time = time.time()
        self._status = ProgressStatus.STARTING
        self._progress = 0.0
        self._message = ""
        self._current_step = None
        self._total_steps = None
        self._current_step_index = None
        self._metadata = {}

    def update(
        self,
        progress: Optional[float] = None,
        message: Optional[str] = None,
        current_step: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update progress for this operation."""
        if progress is not None:
            self._progress = max(0.0, min(100.0, progress))
            if self._progress > 0 and self._status == ProgressStatus.STARTING:
                self._status = ProgressStatus.IN_PROGRESS

        if message is not None:
            self._message = message

        if current_step is not None:
            self._current_step = current_step

        if metadata is not None:
            self._metadata.update(metadata)

        self.service._emit_progress_update(self._build_update())

    def set_steps(self, total_steps: int, current_index: int = 0) -> None:
        """Set the total number of steps and current step index."""
        self._total_steps = total_steps
        self._current_step_index = current_index
        # Auto-calculate progress based on steps
        if total_steps > 0:
            self._progress = (current_index / total_steps) * 100.0
        self.service._emit_progress_update(self._build_update())

    def next_step(self, step_name: Optional[str] = None) -> None:
        """Advance to the next step."""
        if self._current_step_index is not None and self._total_steps is not None:
            self._current_step_index += 1
            if step_name:
                self._current_step = step_name
            self._status = ProgressStatus.IN_PROGRESS
            self._progress = (self._current_step_index / self._total_steps) * 100.0
            self.service._emit_progress_update(self._build_update())

    def complete(self, message: Optional[str] = None) -> None:
        """Mark the operation as completed."""
        self._status = ProgressStatus.COMPLETED
        self._progress = 100.0
        if message is not None:
            self._message = message
        self.service._emit_progress_update(self._build_update())
        self.service._cleanup_operation(self.operation_id)

    def error(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Mark the operation as failed."""
        self._status = ProgressStatus.ERROR
        self._message = message
        if metadata is not None:
            self._metadata.update(metadata)
        self.service._emit_progress_update(self._build_update())
        self.service._cleanup_operation(self.operation_id)

    def cancel(self, message: Optional[str] = None) -> None:
        """Cancel the operation."""
        self._status = ProgressStatus.CANCELED
        if message is not None:
            self._message = message
        self.service._emit_progress_update(self._build_update())
        self.service._cleanup_operation(self.operation_id)

    def _build_update(self) -> ProgressUpdate:
        """Build a progress update from current state."""
        elapsed = time.time() - self._start_time

        # Estimate remaining time based on progress
        estimated_remaining = None
        if self._progress > 0 and self._status == ProgressStatus.IN_PROGRESS:
            estimated_total = elapsed * (100.0 / self._progress)
            estimated_remaining = max(0, estimated_total - elapsed)

        return ProgressUpdate(
            operation_id=self.operation_id,
            status=self._status,
            progress=self._progress,
            message=self._message,
            current_step=self._current_step,
            total_steps=self._total_steps,
            current_step_index=self._current_step_index,
            elapsed_time=elapsed,
            estimated_remaining=estimated_remaining,
            metadata=self._metadata.copy() if self._metadata else None
        )


class ProgressService(Subscribable):
    """
    Service for tracking and reporting progress of long-running operations.

    This service allows model operations to report progress without knowing about
    GUI implementations. GUI components can subscribe to progress updates and
    display them appropriately.

    Usage in models:
        # Start tracking progress
        progress = ProgressService.get_instance().start_operation("load_controller", "Loading Controller...")

        # Update progress
        progress.update(25.0, "Parsing XML...")
        progress.update(50.0, "Building object model...")

        # Complete
        progress.complete("Controller loaded successfully")

    Usage in GUI:
        # Subscribe to progress updates
        ProgressService.get_instance().subscribe(self._on_progress_update)

        def _on_progress_update(self, update: ProgressUpdate):
            self.loading_bar.set_progress(update.progress, update.message)
    """

    _instance: Optional['ProgressService'] = None
    _lock = threading.Lock()

    def __init__(self):
        super().__init__()
        self._operations: Dict[str, ProgressOperation] = {}
        self._operation_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> 'ProgressService':
        """Get the singleton instance of ProgressService."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    log(cls).info("ProgressService instance created")
        return cls._instance

    def start_operation(
        self,
        operation_id: str,
        initial_message: str = "",
        total_steps: Optional[int] = None
    ) -> ProgressOperation:
        """
        Start tracking a new operation.

        Args:
            operation_id: Unique identifier for this operation
            initial_message: Initial status message
            total_steps: Total number of steps (optional)

        Returns:
            ProgressOperation: Operation tracker
        """
        with self._operation_lock:
            if operation_id in self._operations:
                log(self).warning(f"Operation {operation_id} already exists, replacing...")

            operation = ProgressOperation(operation_id, self)
            if total_steps is not None:
                operation.set_steps(total_steps, 0)
            if initial_message:
                operation.update(message=initial_message)

            self._operations[operation_id] = operation
            log(self).info(f"Started operation: {operation_id}")

        return operation

    def get_operation(self, operation_id: str) -> Optional[ProgressOperation]:
        """Get an existing operation by ID."""
        with self._operation_lock:
            return self._operations.get(operation_id)

    def cancel_operation(self, operation_id: str, message: Optional[str] = None) -> bool:
        """Cancel an operation by ID."""
        with self._operation_lock:
            operation = self._operations.get(operation_id)
            if operation:
                operation.cancel(message)
                return True
            return False

    def cancel_all_operations(self) -> None:
        """Cancel all active operations."""
        with self._operation_lock:
            for operation in list(self._operations.values()):
                operation.cancel("Cancelled by service")

    def get_active_operations(self) -> Dict[str, ProgressOperation]:
        """Get all active operations."""
        with self._operation_lock:
            return self._operations.copy()

    def _emit_progress_update(self, update: ProgressUpdate) -> None:
        """Emit a progress update to all subscribers."""
        log(self).debug(f"Progress update for {update.operation_id}: {update.progress:.1f}% - {update.message}")
        self.safe_emit(update)

    def _cleanup_operation(self, operation_id: str) -> None:
        """Remove completed operation from tracking."""
        with self._operation_lock:
            if operation_id in self._operations:
                del self._operations[operation_id]
                log(self).debug(f"Cleaned up operation: {operation_id}")
