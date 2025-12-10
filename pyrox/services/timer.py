"""Timer module for scheduling tasks.
"""

import threading
from typing import Callable, Optional, Dict, Any
import uuid


class TimerService:
    """Service for scheduling and managing timed tasks.

    This class provides functionality to schedule tasks to be executed after a
    certain delay. Each task is assigned a unique ID and runs in its own thread.

    Attributes:
        _tasks (Dict[str, threading.Timer]): Dictionary of active timers by ID
        _lock (threading.Lock): Thread lock for safe task management
    """

    def __init__(self):
        """Initialize the timer service."""
        self._tasks: Dict[str, threading.Timer] = {}
        self._lock = threading.Lock()

    def schedule_task(self, callback: Callable[[], Any], delay: float, task_id: Optional[str] = None) -> str:
        """Schedule a task to be executed after a delay.

        Args:
            callback: The callback function to be executed
            delay: Delay in seconds before executing the task
            task_id: Optional custom ID for the task. If None, a UUID will be generated

        Returns:
            str: The task ID that can be used to cancel the task

        Raises:
            ValueError: If delay is negative or callback is not callable
        """
        if not callable(callback):
            raise ValueError("Callback must be callable")
        if delay < 0:
            raise ValueError("Delay must be non-negative")

        if task_id is None:
            task_id = str(uuid.uuid4())

        def wrapped_callback():
            """Wrapper that removes the task from tracking after execution."""
            try:
                callback()
            finally:
                with self._lock:
                    self._tasks.pop(task_id, None)

        with self._lock:
            # Cancel existing task with same ID if it exists
            if task_id in self._tasks:
                self._tasks[task_id].cancel()

            # Create and start new timer
            timer = threading.Timer(delay, wrapped_callback)
            self._tasks[task_id] = timer
            timer.start()

        return task_id

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task.

        Args:
            task_id: The ID of the task to be canceled

        Returns:
            bool: True if task was found and canceled, False otherwise
        """
        with self._lock:
            timer = self._tasks.pop(task_id, None)
            if timer:
                timer.cancel()
                return True
            return False

    def list_scheduled_tasks(self) -> list[str]:
        """List all scheduled task IDs.

        Returns:
            List of active task IDs
        """
        with self._lock:
            return list(self._tasks.keys())

    def clear_all_tasks(self) -> int:
        """Clear all scheduled tasks.

        Returns:
            int: Number of tasks that were canceled
        """
        with self._lock:
            count = len(self._tasks)
            for timer in self._tasks.values():
                timer.cancel()
            self._tasks.clear()
            return count

    def get_task_count(self) -> int:
        """Get the number of currently scheduled tasks.

        Returns:
            int: Number of active tasks
        """
        with self._lock:
            return len(self._tasks)

    def is_task_scheduled(self, task_id: str) -> bool:
        """Check if a task is currently scheduled.

        Args:
            task_id: The ID of the task to check

        Returns:
            bool: True if task is scheduled, False otherwise
        """
        with self._lock:
            return task_id in self._tasks

    def schedule_repeating_task(self, callback: Callable[[], Any], interval: float, task_id: Optional[str] = None) -> str:
        """Schedule a task to be executed repeatedly at regular intervals.

        Args:
            callback: The callback function to be executed
            interval: Interval in seconds between executions
            task_id: Optional custom ID for the task. If None, a UUID will be generated

        Returns:
            str: The task ID that can be used to cancel the task

        Raises:
            ValueError: If interval is negative or callback is not callable
        """
        if not callable(callback):
            raise ValueError("Callback must be callable")
        if interval <= 0:
            raise ValueError("Interval must be positive")

        if task_id is None:
            task_id = str(uuid.uuid4())

        def repeating_callback():
            """Wrapper that reschedules itself after execution."""
            try:
                callback()
            except Exception:
                # Continue repeating even if callback fails
                pass

            # Reschedule if task hasn't been canceled
            with self._lock:
                if task_id in self._tasks:
                    timer = threading.Timer(interval, repeating_callback)
                    self._tasks[task_id] = timer
                    timer.start()

        with self._lock:
            # Cancel existing task with same ID if it exists
            if task_id in self._tasks:
                self._tasks[task_id].cancel()

            # Create and start new timer
            timer = threading.Timer(interval, repeating_callback)
            self._tasks[task_id] = timer
            timer.start()

        return task_id

    def shutdown(self):
        """Shutdown the timer service and cancel all tasks.

        This method should be called when the service is no longer needed
        to ensure all background threads are properly cleaned up.
        """
        self.clear_all_tasks()
