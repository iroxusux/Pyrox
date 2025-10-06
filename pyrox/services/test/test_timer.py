"""Unit tests for timer.py module."""

import threading
import time
import unittest
from unittest.mock import Mock

from pyrox.services.timer import TimerService


class TestTimerService(unittest.TestCase):
    """Test cases for TimerService class."""

    def setUp(self):
        """Set up test fixtures."""
        self.timer_service = TimerService()
        self.callback_results = []

    def tearDown(self):
        """Clean up after tests."""
        self.timer_service.shutdown()
        self.callback_results.clear()

    def test_init(self):
        """Test TimerService initialization."""
        timer = TimerService()

        self.assertEqual(timer.get_task_count(), 0)
        self.assertEqual(timer.list_scheduled_tasks(), [])
        self.assertIsInstance(timer._tasks, dict)
        self.assertIsInstance(timer._lock, threading.Lock)

    def test_schedule_task_with_auto_id(self):
        """Test scheduling a task with auto-generated ID."""
        callback = Mock()

        task_id = self.timer_service.schedule_task(callback, 0.1)

        self.assertIsInstance(task_id, str)
        self.assertEqual(self.timer_service.get_task_count(), 1)
        self.assertIn(task_id, self.timer_service.list_scheduled_tasks())

        # Wait for task to execute
        time.sleep(0.2)
        callback.assert_called_once()

        # Task should be removed after execution
        self.assertEqual(self.timer_service.get_task_count(), 0)

    def test_schedule_task_with_custom_id(self):
        """Test scheduling a task with custom ID."""
        callback = Mock()
        custom_id = "my_custom_task"

        task_id = self.timer_service.schedule_task(callback, 0.1, custom_id)

        self.assertEqual(task_id, custom_id)
        self.assertTrue(self.timer_service.is_task_scheduled(custom_id))

        # Wait for task to execute
        time.sleep(0.2)
        callback.assert_called_once()

    def test_schedule_task_invalid_callback(self):
        """Test scheduling with invalid callback raises ValueError."""
        with self.assertRaises(ValueError) as context:
            self.timer_service.schedule_task("not_callable", 1.0)  # type: ignore

        self.assertIn("Callback must be callable", str(context.exception))

    def test_schedule_task_negative_delay(self):
        """Test scheduling with negative delay raises ValueError."""
        callback = Mock()

        with self.assertRaises(ValueError) as context:
            self.timer_service.schedule_task(callback, -1.0)

        self.assertIn("Delay must be non-negative", str(context.exception))

    def test_schedule_task_zero_delay(self):
        """Test scheduling with zero delay is allowed."""
        callback = Mock()

        task_id = self.timer_service.schedule_task(callback, 0.0)

        self.assertIsInstance(task_id, str)
        # Wait a moment for zero-delay task to execute
        time.sleep(0.05)
        callback.assert_called_once()

    def test_cancel_task_existing(self):
        """Test canceling an existing task."""
        callback = Mock()

        task_id = self.timer_service.schedule_task(callback, 1.0)  # Long delay
        self.assertTrue(self.timer_service.is_task_scheduled(task_id))

        result = self.timer_service.cancel_task(task_id)

        self.assertTrue(result)
        self.assertFalse(self.timer_service.is_task_scheduled(task_id))
        self.assertEqual(self.timer_service.get_task_count(), 0)

        # Callback should not be called
        time.sleep(0.1)
        callback.assert_not_called()

    def test_cancel_task_nonexistent(self):
        """Test canceling a non-existent task."""
        result = self.timer_service.cancel_task("nonexistent_id")

        self.assertFalse(result)

    def test_schedule_task_duplicate_id_replaces(self):
        """Test scheduling with duplicate ID replaces existing task."""
        callback1 = Mock()
        callback2 = Mock()
        custom_id = "duplicate_id"

        # Schedule first task
        task_id1 = self.timer_service.schedule_task(callback1, 1.0, custom_id)
        self.assertEqual(self.timer_service.get_task_count(), 1)

        # Schedule second task with same ID
        task_id2 = self.timer_service.schedule_task(callback2, 0.1, custom_id)

        self.assertEqual(task_id1, task_id2)
        self.assertEqual(self.timer_service.get_task_count(), 1)

        # Wait for second task to execute
        time.sleep(0.2)

        # Only second callback should be called
        callback1.assert_not_called()
        callback2.assert_called_once()

    def test_list_scheduled_tasks(self):
        """Test listing scheduled tasks."""
        callback = Mock()

        # No tasks initially
        self.assertEqual(self.timer_service.list_scheduled_tasks(), [])

        # Schedule multiple tasks
        task_id1 = self.timer_service.schedule_task(callback, 1.0, "task1")
        task_id2 = self.timer_service.schedule_task(callback, 1.0, "task2")

        scheduled_tasks = self.timer_service.list_scheduled_tasks()
        self.assertEqual(len(scheduled_tasks), 2)
        self.assertIn(task_id1, scheduled_tasks)
        self.assertIn(task_id2, scheduled_tasks)

    def test_clear_all_tasks(self):
        """Test clearing all scheduled tasks."""
        callback = Mock()

        # Schedule multiple tasks
        self.timer_service.schedule_task(callback, 1.0, "task1")
        self.timer_service.schedule_task(callback, 1.0, "task2")
        self.timer_service.schedule_task(callback, 1.0, "task3")

        self.assertEqual(self.timer_service.get_task_count(), 3)

        count = self.timer_service.clear_all_tasks()

        self.assertEqual(count, 3)
        self.assertEqual(self.timer_service.get_task_count(), 0)
        self.assertEqual(self.timer_service.list_scheduled_tasks(), [])

        # Wait to ensure no callbacks are executed
        time.sleep(0.1)
        callback.assert_not_called()

    def test_get_task_count(self):
        """Test getting task count."""
        callback = Mock()

        self.assertEqual(self.timer_service.get_task_count(), 0)

        self.timer_service.schedule_task(callback, 1.0)
        self.assertEqual(self.timer_service.get_task_count(), 1)

        self.timer_service.schedule_task(callback, 1.0)
        self.assertEqual(self.timer_service.get_task_count(), 2)

    def test_is_task_scheduled(self):
        """Test checking if task is scheduled."""
        callback = Mock()

        # Non-existent task
        self.assertFalse(self.timer_service.is_task_scheduled("nonexistent"))

        # Scheduled task
        task_id = self.timer_service.schedule_task(callback, 1.0)
        self.assertTrue(self.timer_service.is_task_scheduled(task_id))

        # Canceled task
        self.timer_service.cancel_task(task_id)
        self.assertFalse(self.timer_service.is_task_scheduled(task_id))

    def test_schedule_repeating_task(self):
        """Test scheduling a repeating task."""
        callback = Mock()

        task_id = self.timer_service.schedule_repeating_task(callback, 0.1)

        self.assertIsInstance(task_id, str)
        self.assertTrue(self.timer_service.is_task_scheduled(task_id))

        # Wait for multiple executions
        time.sleep(0.35)

        # Should have been called multiple times
        self.assertGreaterEqual(callback.call_count, 3)

    def test_schedule_repeating_task_with_custom_id(self):
        """Test scheduling repeating task with custom ID."""
        callback = Mock()
        custom_id = "repeating_task"

        task_id = self.timer_service.schedule_repeating_task(callback, 0.1, custom_id)

        self.assertEqual(task_id, custom_id)
        self.assertTrue(self.timer_service.is_task_scheduled(custom_id))

    def test_schedule_repeating_task_invalid_callback(self):
        """Test scheduling repeating task with invalid callback."""
        with self.assertRaises(ValueError) as context:
            self.timer_service.schedule_repeating_task("not_callable", 1.0)  # type: ignore

        self.assertIn("Callback must be callable", str(context.exception))

    def test_schedule_repeating_task_invalid_interval(self):
        """Test scheduling repeating task with invalid interval."""
        callback = Mock()

        with self.assertRaises(ValueError) as context:
            self.timer_service.schedule_repeating_task(callback, 0.0)

        self.assertIn("Interval must be positive", str(context.exception))

        with self.assertRaises(ValueError) as context:
            self.timer_service.schedule_repeating_task(callback, -1.0)

        self.assertIn("Interval must be positive", str(context.exception))

    def test_cancel_repeating_task(self):
        """Test canceling a repeating task."""
        callback = Mock()

        task_id = self.timer_service.schedule_repeating_task(callback, 0.1)

        # Let it run a few times
        time.sleep(0.25)
        initial_count = callback.call_count

        # Cancel the task
        result = self.timer_service.cancel_task(task_id)

        self.assertTrue(result)
        self.assertFalse(self.timer_service.is_task_scheduled(task_id))

        # Wait and verify no more calls
        time.sleep(0.2)
        final_count = callback.call_count

        self.assertEqual(initial_count, final_count)

    def test_repeating_task_continues_on_exception(self):
        """Test that repeating task continues even if callback raises exception."""
        call_count = [0]

        def failing_callback():
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("Test exception")

        task_id = self.timer_service.schedule_repeating_task(failing_callback, 0.1)

        # Wait for multiple executions including the failure
        time.sleep(0.35)

        # Should have been called multiple times despite the exception
        self.assertGreaterEqual(call_count[0], 3)
        self.assertTrue(self.timer_service.is_task_scheduled(task_id))

    def test_task_cleanup_after_execution(self):
        """Test that tasks are properly cleaned up after execution."""
        callback = Mock()

        task_id = self.timer_service.schedule_task(callback, 0.05)

        # Task should be scheduled initially
        self.assertTrue(self.timer_service.is_task_scheduled(task_id))

        # Wait for execution and cleanup
        time.sleep(0.1)

        # Task should be cleaned up automatically
        self.assertFalse(self.timer_service.is_task_scheduled(task_id))
        self.assertEqual(self.timer_service.get_task_count(), 0)

    def test_shutdown(self):
        """Test shutdown method."""
        callback = Mock()

        # Schedule multiple tasks
        self.timer_service.schedule_task(callback, 1.0)
        self.timer_service.schedule_repeating_task(callback, 0.1)

        self.assertEqual(self.timer_service.get_task_count(), 2)

        # Shutdown
        self.timer_service.shutdown()

        self.assertEqual(self.timer_service.get_task_count(), 0)
        self.assertEqual(self.timer_service.list_scheduled_tasks(), [])

    def test_thread_safety_concurrent_operations(self):
        """Test thread safety with concurrent operations."""
        callback = Mock()
        results = []

        def schedule_tasks():
            for i in range(10):
                task_id = self.timer_service.schedule_task(callback, 0.2, f"task_{i}")
                results.append(task_id)

        def cancel_tasks():
            time.sleep(0.05)  # Let some tasks get scheduled first
            for i in range(5):
                self.timer_service.cancel_task(f"task_{i}")

        # Run operations concurrently
        thread1 = threading.Thread(target=schedule_tasks)
        thread2 = threading.Thread(target=cancel_tasks)

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        # Should have some tasks remaining (those not canceled)
        remaining_count = self.timer_service.get_task_count()
        self.assertGreater(remaining_count, 0)
        self.assertLess(remaining_count, 10)

    def test_callback_execution_with_parameters(self):
        """Test callback execution with captured variables."""
        results = []

        def callback_with_data(data):
            results.append(data)

        # Use lambda to capture the parameter
        self.timer_service.schedule_task(lambda: callback_with_data("test_data"), 0.05)

        time.sleep(0.1)

        self.assertEqual(results, ["test_data"])

    def test_multiple_services_independence(self):
        """Test that multiple TimerService instances are independent."""
        callback1 = Mock()
        callback2 = Mock()

        timer2 = TimerService()

        try:
            # Schedule tasks on different services
            task_id1 = self.timer_service.schedule_task(callback1, 0.1)
            _ = timer2.schedule_task(callback2, 0.1)

            self.assertEqual(self.timer_service.get_task_count(), 1)
            self.assertEqual(timer2.get_task_count(), 1)

            # Cancel task on first service
            self.timer_service.cancel_task(task_id1)

            self.assertEqual(self.timer_service.get_task_count(), 0)
            self.assertEqual(timer2.get_task_count(), 1)  # Should remain unchanged

            # Wait for second service task to execute
            time.sleep(0.15)

            callback1.assert_not_called()
            callback2.assert_called_once()

        finally:
            timer2.shutdown()

    def test_edge_case_very_short_delay(self):
        """Test scheduling with very short delays."""
        callback = Mock()

        task_id = self.timer_service.schedule_task(callback, 0.001)  # 1ms

        time.sleep(0.02)  # 20ms should be enough

        callback.assert_called_once()
        self.assertFalse(self.timer_service.is_task_scheduled(task_id))

    def test_large_number_of_tasks(self):
        """Test scheduling a large number of tasks."""
        callback = Mock()
        task_ids = []

        # Schedule many tasks
        for i in range(100):
            task_id = self.timer_service.schedule_task(callback, 0.5, f"task_{i}")
            task_ids.append(task_id)

        self.assertEqual(self.timer_service.get_task_count(), 100)

        # Cancel half of them
        for i in range(0, 50):
            self.timer_service.cancel_task(task_ids[i])

        self.assertEqual(self.timer_service.get_task_count(), 50)

        # Clear the rest
        cleared_count = self.timer_service.clear_all_tasks()
        self.assertEqual(cleared_count, 50)


if __name__ == '__main__':
    unittest.main()
