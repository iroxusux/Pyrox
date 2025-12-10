"""Unit tests for progress.py module."""
import threading
import time
import unittest
from unittest.mock import Mock, patch


from pyrox.services.progress import (
    ProgressStatus,
    ProgressUpdate,
    ProgressOperation,
    ProgressService
)


class TestProgressStatus(unittest.TestCase):
    """Test cases for ProgressStatus enum."""

    def test_enum_values(self):
        """Test that all expected enum values exist."""
        expected_values = ["idle", "starting", "in_progress", "completed", "error", "canceled"]

        for value in expected_values:
            self.assertTrue(hasattr(ProgressStatus, value.upper()))
            self.assertEqual(getattr(ProgressStatus, value.upper()).value, value)

    def test_enum_count(self):
        """Test that enum has correct number of values."""
        self.assertEqual(len(ProgressStatus), 6)


class TestProgressUpdate(unittest.TestCase):
    """Test cases for ProgressUpdate dataclass."""

    def setUp(self):
        """Set up test fixtures."""
        self.update = ProgressUpdate(
            operation_id="test_op",
            status=ProgressStatus.IN_PROGRESS,
            progress=50.0,
            message="Test message",
            current_step="Test step",
            total_steps=5,
            current_step_index=2,
            elapsed_time=10.5,
            estimated_remaining=12.3,
            metadata={"key": "value"}
        )

    def test_init_with_defaults(self):
        """Test ProgressUpdate initialization with defaults."""
        update = ProgressUpdate(
            operation_id="test",
            status=ProgressStatus.STARTING
        )

        self.assertEqual(update.operation_id, "test")
        self.assertEqual(update.status, ProgressStatus.STARTING)
        self.assertEqual(update.progress, 0.0)
        self.assertEqual(update.message, "")
        self.assertIsNone(update.current_step)
        self.assertIsNone(update.total_steps)
        self.assertIsNone(update.current_step_index)
        self.assertEqual(update.elapsed_time, 0.0)
        self.assertIsNone(update.estimated_remaining)
        self.assertIsNone(update.metadata)

    def test_init_with_values(self):
        """Test ProgressUpdate initialization with provided values."""
        self.assertEqual(self.update.operation_id, "test_op")
        self.assertEqual(self.update.status, ProgressStatus.IN_PROGRESS)
        self.assertEqual(self.update.progress, 50.0)
        self.assertEqual(self.update.message, "Test message")
        self.assertEqual(self.update.current_step, "Test step")
        self.assertEqual(self.update.total_steps, 5)
        self.assertEqual(self.update.current_step_index, 2)
        self.assertEqual(self.update.elapsed_time, 10.5)
        self.assertEqual(self.update.estimated_remaining, 12.3)
        self.assertEqual(self.update.metadata, {"key": "value"})

    def test_is_complete_property_completed(self):
        """Test is_complete property for completed status."""
        update = ProgressUpdate("test", ProgressStatus.COMPLETED)
        self.assertTrue(update.is_complete)

    def test_is_complete_property_error(self):
        """Test is_complete property for error status."""
        update = ProgressUpdate("test", ProgressStatus.ERROR)
        self.assertTrue(update.is_complete)

    def test_is_complete_property_canceled(self):
        """Test is_complete property for canceled status."""
        update = ProgressUpdate("test", ProgressStatus.CANCELED)
        self.assertTrue(update.is_complete)

    def test_is_complete_property_in_progress(self):
        """Test is_complete property for in-progress status."""
        update = ProgressUpdate("test", ProgressStatus.IN_PROGRESS)
        self.assertFalse(update.is_complete)

    def test_is_complete_property_starting(self):
        """Test is_complete property for starting status."""
        update = ProgressUpdate("test", ProgressStatus.STARTING)
        self.assertFalse(update.is_complete)

    def test_percentage_text_property(self):
        """Test percentage_text property formatting."""
        test_cases = [
            (0.0, "0.0%"),
            (25.5, "25.5%"),
            (50.0, "50.0%"),
            (99.9, "99.9%"),
            (100.0, "100.0%")
        ]

        for progress, expected in test_cases:
            update = ProgressUpdate("test", ProgressStatus.IN_PROGRESS, progress=progress)
            self.assertEqual(update.percentage_text, expected)

    def test_step_text_property_with_steps(self):
        """Test step_text property with step information."""
        update = ProgressUpdate(
            "test",
            ProgressStatus.IN_PROGRESS,
            current_step_index=2,
            total_steps=5
        )
        self.assertEqual(update.step_text, "Step 3 of 5")

    def test_step_text_property_without_steps(self):
        """Test step_text property without step information."""
        test_cases = [
            (None, None),
            (None, 5),
            (2, None)
        ]

        for step_index, total_steps in test_cases:
            update = ProgressUpdate(
                "test",
                ProgressStatus.IN_PROGRESS,
                current_step_index=step_index,
                total_steps=total_steps
            )
            self.assertEqual(update.step_text, "")


class TestProgressOperation(unittest.TestCase):
    """Test cases for ProgressOperation class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_service = Mock(spec=ProgressService)
        self.operation = ProgressOperation("test_op", self.mock_service)

    def test_init(self):
        """Test ProgressOperation initialization."""
        self.assertEqual(self.operation.operation_id, "test_op")
        self.assertEqual(self.operation.service, self.mock_service)
        self.assertEqual(self.operation._status, ProgressStatus.STARTING)
        self.assertEqual(self.operation._progress, 0.0)
        self.assertEqual(self.operation._message, "")
        self.assertIsNone(self.operation._current_step)
        self.assertIsNone(self.operation._total_steps)
        self.assertIsNone(self.operation._current_step_index)
        self.assertEqual(self.operation._metadata, {})
        self.assertIsInstance(self.operation._start_time, float)

    def test_update_progress(self):
        """Test updating progress value."""
        self.operation.update(progress=50.0)

        self.assertEqual(self.operation._progress, 50.0)
        self.assertEqual(self.operation._status, ProgressStatus.IN_PROGRESS)
        self.mock_service._emit_progress_update.assert_called_once()

    def test_update_progress_bounds(self):
        """Test progress value bounds checking."""
        # Test lower bound
        self.operation.update(progress=-10.0)
        self.assertEqual(self.operation._progress, 0.0)

        # Test upper bound
        self.operation.update(progress=150.0)
        self.assertEqual(self.operation._progress, 100.0)

    def test_update_progress_status_change(self):
        """Test status change from STARTING to IN_PROGRESS."""
        self.assertEqual(self.operation._status, ProgressStatus.STARTING)

        self.operation.update(progress=25.0)
        self.assertEqual(self.operation._status, ProgressStatus.IN_PROGRESS)

    def test_update_message(self):
        """Test updating message."""
        self.operation.update(message="Test message")

        self.assertEqual(self.operation._message, "Test message")
        self.mock_service._emit_progress_update.assert_called_once()

    def test_update_current_step(self):
        """Test updating current step."""
        self.operation.update(current_step="Step 1")

        self.assertEqual(self.operation._current_step, "Step 1")
        self.mock_service._emit_progress_update.assert_called_once()

    def test_update_metadata(self):
        """Test updating metadata."""
        metadata = {"key1": "value1", "key2": "value2"}
        self.operation.update(metadata=metadata)

        self.assertEqual(self.operation._metadata, metadata)

        # Test metadata merging
        additional_metadata = {"key3": "value3"}
        self.operation.update(metadata=additional_metadata)

        expected_metadata = {"key1": "value1", "key2": "value2", "key3": "value3"}
        self.assertEqual(self.operation._metadata, expected_metadata)

    def test_set_steps(self):
        """Test setting total steps and current index."""
        self.operation.set_steps(5, 2)

        self.assertEqual(self.operation._total_steps, 5)
        self.assertEqual(self.operation._current_step_index, 2)
        self.assertEqual(self.operation._progress, 40.0)  # (2/5) * 100
        self.mock_service._emit_progress_update.assert_called_once()

    def test_set_steps_with_zero_total(self):
        """Test setting steps with zero total steps."""
        self.operation.set_steps(0, 0)

        self.assertEqual(self.operation._total_steps, 0)
        self.assertEqual(self.operation._current_step_index, 0)
        self.assertEqual(self.operation._progress, 0.0)

    def test_next_step_without_setup(self):
        """Test next_step when steps are not configured."""
        self.operation.next_step("Step 1")

        # Should not change anything if steps not set up
        self.assertIsNone(self.operation._current_step_index)
        self.assertIsNone(self.operation._total_steps)

    def test_next_step_with_setup(self):
        """Test next_step with proper step configuration."""
        self.operation.set_steps(3, 0)
        self.mock_service._emit_progress_update.reset_mock()

        self.operation.next_step("Step 2")

        self.assertEqual(self.operation._current_step_index, 1)
        self.assertEqual(self.operation._current_step, "Step 2")
        self.assertAlmostEqual(self.operation._progress, 33.33, places=1)
        self.mock_service._emit_progress_update.assert_called_once()

    def test_complete(self):
        """Test marking operation as completed."""
        self.operation.complete("Operation finished")

        self.assertEqual(self.operation._status, ProgressStatus.COMPLETED)
        self.assertEqual(self.operation._progress, 100.0)
        self.assertEqual(self.operation._message, "Operation finished")
        self.mock_service._emit_progress_update.assert_called_once()
        self.mock_service._cleanup_operation.assert_called_once_with("test_op")

    def test_complete_without_message(self):
        """Test completing without custom message."""
        original_message = "Original message"
        self.operation._message = original_message

        self.operation.complete()

        self.assertEqual(self.operation._status, ProgressStatus.COMPLETED)
        self.assertEqual(self.operation._progress, 100.0)
        self.assertEqual(self.operation._message, original_message)

    def test_error(self):
        """Test marking operation as failed."""
        error_metadata = {"error_code": "TEST_ERROR"}
        self.operation.error("Test error message", metadata=error_metadata)

        self.assertEqual(self.operation._status, ProgressStatus.ERROR)
        self.assertEqual(self.operation._message, "Test error message")
        self.assertEqual(self.operation._metadata, error_metadata)
        self.mock_service._emit_progress_update.assert_called_once()
        self.mock_service._cleanup_operation.assert_called_once_with("test_op")

    def test_error_without_metadata(self):
        """Test error without metadata."""
        self.operation.error("Test error")

        self.assertEqual(self.operation._status, ProgressStatus.ERROR)
        self.assertEqual(self.operation._message, "Test error")
        self.assertEqual(self.operation._metadata, {})

    def test_cancel(self):
        """Test canceling operation."""
        self.operation.cancel("Operation cancelled")

        self.assertEqual(self.operation._status, ProgressStatus.CANCELED)
        self.assertEqual(self.operation._message, "Operation cancelled")
        self.mock_service._emit_progress_update.assert_called_once()
        self.mock_service._cleanup_operation.assert_called_once_with("test_op")

    def test_cancel_without_message(self):
        """Test canceling without custom message."""
        original_message = "Original message"
        self.operation._message = original_message

        self.operation.cancel()

        self.assertEqual(self.operation._status, ProgressStatus.CANCELED)
        self.assertEqual(self.operation._message, original_message)

    @patch('time.time')
    def test_build_update_basic(self, mock_time):
        """Test building progress update with basic information."""
        mock_time.side_effect = [100.0, 110.5]  # start_time, build_time

        operation = ProgressOperation("test", self.mock_service)
        operation._progress = 25.0
        operation._message = "Test message"
        operation._status = ProgressStatus.IN_PROGRESS

        update = operation._build_update()

        self.assertEqual(update.operation_id, "test")
        self.assertEqual(update.status, ProgressStatus.IN_PROGRESS)
        self.assertEqual(update.progress, 25.0)
        self.assertEqual(update.message, "Test message")
        self.assertEqual(update.elapsed_time, 10.5)

    @patch('time.time')
    def test_build_update_with_time_estimation(self, mock_time):
        """Test building update with time estimation."""
        mock_time.side_effect = [100.0, 120.0]  # start_time, build_time

        operation = ProgressOperation("test", self.mock_service)
        operation._progress = 50.0
        operation._status = ProgressStatus.IN_PROGRESS

        update = operation._build_update()

        self.assertEqual(update.elapsed_time, 20.0)
        self.assertEqual(update.estimated_remaining, 20.0)  # 50% done, 50% remaining

    @patch('time.time')
    def test_build_update_no_time_estimation_zero_progress(self, mock_time):
        """Test building update with no time estimation for zero progress."""
        mock_time.side_effect = [100.0, 110.0]

        operation = ProgressOperation("test", self.mock_service)
        operation._progress = 0.0
        operation._status = ProgressStatus.IN_PROGRESS

        update = operation._build_update()

        self.assertIsNone(update.estimated_remaining)

    def test_build_update_with_metadata(self):
        """Test building update with metadata."""
        self.operation._metadata = {"key": "value"}

        update = self.operation._build_update()

        self.assertEqual(update.metadata, {"key": "value"})

        # Ensure it's a copy, not the original
        if update.metadata is not None:
            update.metadata["new_key"] = "new_value"
            self.assertNotEqual(self.operation._metadata, update.metadata)

    def test_build_update_step_information(self):
        """Test building update with step information."""
        self.operation._current_step = "Processing data"
        self.operation._total_steps = 5
        self.operation._current_step_index = 2

        update = self.operation._build_update()

        self.assertEqual(update.current_step, "Processing data")
        self.assertEqual(update.total_steps, 5)
        self.assertEqual(update.current_step_index, 2)


class TestProgressService(unittest.TestCase):
    """Test cases for ProgressService class."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear any existing instance for clean tests
        ProgressService._instance = None
        self.service = ProgressService()
        self.callback_results = []

    def tearDown(self):
        """Clean up after tests."""
        # Clear the singleton instance
        ProgressService._instance = None
        self.callback_results.clear()

    def test_init(self):
        """Test ProgressService initialization."""
        service = ProgressService()

        self.assertIsInstance(service._operations, dict)
        self.assertEqual(len(service._operations), 0)
        self.assertIsInstance(service._operation_lock, threading.Lock)
        self.assertIsInstance(service.subscribers, list)

    @patch('pyrox.services.progress.log')
    def test_singleton_get_instance(self, mock_log):
        """Test singleton pattern for get_instance."""
        service1 = ProgressService.get_instance()
        service2 = ProgressService.get_instance()

        self.assertIs(service1, service2)
        mock_log.assert_called()

    def test_singleton_thread_safety(self):
        """Test singleton thread safety."""
        instances = []

        def create_instance():
            instances.append(ProgressService.get_instance())

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=create_instance)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All instances should be the same
        for instance in instances:
            self.assertIs(instance, instances[0])

    @patch('pyrox.services.progress.log')
    def test_start_operation_basic(self, mock_log):
        """Test starting a basic operation."""
        operation = self.service.start_operation("test_op", "Starting test")

        self.assertIsInstance(operation, ProgressOperation)
        self.assertEqual(operation.operation_id, "test_op")
        self.assertIn("test_op", self.service._operations)
        mock_log.assert_called()

    @patch('pyrox.services.progress.log')
    def test_start_operation_with_steps(self, mock_log):
        """Test starting operation with total steps."""
        operation = self.service.start_operation("test_op", "Starting", total_steps=5)

        self.assertEqual(operation._total_steps, 5)
        self.assertEqual(operation._current_step_index, 0)

    @patch('pyrox.services.progress.log')
    def test_start_operation_replace_existing(self, mock_log):
        """Test starting operation that replaces existing one."""
        # Start first operation
        self.service.start_operation("test_op", "First operation")

        # Start second operation with same ID
        operation2 = self.service.start_operation("test_op", "Second operation")

        self.assertEqual(len(self.service._operations), 1)
        self.assertEqual(self.service._operations["test_op"], operation2)
        # Should log warning about replacement
        mock_log.return_value.warning.assert_called()

    def test_get_operation_existing(self):
        """Test getting an existing operation."""
        original_operation = self.service.start_operation("test_op", "Test")

        retrieved_operation = self.service.get_operation("test_op")

        self.assertIs(retrieved_operation, original_operation)

    def test_get_operation_nonexistent(self):
        """Test getting a non-existent operation."""
        operation = self.service.get_operation("nonexistent")

        self.assertIsNone(operation)

    def test_cancel_operation_existing(self):
        """Test canceling an existing operation."""
        operation = self.service.start_operation("test_op", "Test")

        with patch.object(operation, 'cancel') as mock_cancel:
            result = self.service.cancel_operation("test_op", "Cancelled by test")

            self.assertTrue(result)
            mock_cancel.assert_called_once_with("Cancelled by test")

    def test_cancel_operation_nonexistent(self):
        """Test canceling a non-existent operation."""
        result = self.service.cancel_operation("nonexistent")

        self.assertFalse(result)

    def test_cancel_all_operations(self):
        """Test canceling all operations."""
        # Create multiple operations
        operations = []
        for i in range(3):
            op = self.service.start_operation(f"op_{i}", f"Operation {i}")
            operations.append(op)

        # Mock the cancel method for each operation
        for op in operations:
            op.cancel = Mock()

        self.service.cancel_all_operations()

        # Verify all operations were cancelled
        for op in operations:
            op.cancel.assert_called_once_with("Cancelled by service")

    def test_get_active_operations(self):
        """Test getting active operations."""
        # Start some operations
        op1 = self.service.start_operation("op1", "Operation 1")
        op2 = self.service.start_operation("op2", "Operation 2")

        active_ops = self.service.get_active_operations()

        self.assertEqual(len(active_ops), 2)
        self.assertIn("op1", active_ops)
        self.assertIn("op2", active_ops)
        self.assertIs(active_ops["op1"], op1)
        self.assertIs(active_ops["op2"], op2)

        # Ensure it's a copy, not the original
        # We can't modify active_ops directly due to typing, so we test isolation differently
        original_count = len(self.service._operations)
        del active_ops["op1"]
        self.assertEqual(len(self.service._operations), original_count)

    @patch('pyrox.services.progress.log')
    def test_emit_progress_update(self, mock_log):
        """Test emitting progress updates."""
        # Subscribe to updates
        callback = Mock()
        self.service.subscribe(callback)

        update = ProgressUpdate("test", ProgressStatus.IN_PROGRESS, progress=50.0)

        self.service._emit_progress_update(update)

        callback.assert_called_once_with(update)
        mock_log.assert_called()

    @patch('pyrox.services.progress.log')
    def test_cleanup_operation(self, mock_log):
        """Test cleaning up completed operations."""
        # Start operation
        self.service.start_operation("test_op", "Test")
        self.assertIn("test_op", self.service._operations)

        # Cleanup operation
        self.service._cleanup_operation("test_op")

        self.assertNotIn("test_op", self.service._operations)
        mock_log.assert_called()

    def test_cleanup_operation_nonexistent(self):
        """Test cleaning up non-existent operation."""
        # Should not raise an error
        self.service._cleanup_operation("nonexistent")

        # Verify operations dict is still empty
        self.assertEqual(len(self.service._operations), 0)

    def test_thread_safety_operations(self):
        """Test thread safety of operations management."""
        results = []

        def start_and_complete_operation(op_id):
            try:
                operation = self.service.start_operation(f"op_{op_id}", f"Operation {op_id}")
                time.sleep(0.01)  # Simulate some work
                operation.complete("Finished")
                results.append(f"op_{op_id}")
            except Exception as e:
                results.append(f"ERROR: {e}")

        threads = []
        for i in range(10):
            thread = threading.Thread(target=start_and_complete_operation, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All operations should have completed successfully
        self.assertEqual(len(results), 10)
        for i in range(10):
            self.assertIn(f"op_{i}", results)

        # No operations should remain active
        self.assertEqual(len(self.service.get_active_operations()), 0)

    def test_integration_operation_lifecycle(self):
        """Test complete operation lifecycle integration."""
        updates_received = []

        def update_callback(update):
            updates_received.append((update.operation_id, update.status, update.progress))

        self.service.subscribe(update_callback)

        # Start operation (Calls 2 'emits': starting and first update)
        operation = self.service.start_operation("lifecycle_test", "Starting", total_steps=3)

        # Progress through steps
        operation.next_step("Step 1")
        operation.next_step("Step 2")
        operation.next_step("Step 3")

        # Complete operation
        operation.complete("All done")

        # Verify update sequence
        self.assertEqual(len(updates_received), 6)  # start(x2) + 3 steps + complete

        # Check final update
        final_update = updates_received[-1]
        self.assertEqual(final_update[0], "lifecycle_test")
        self.assertEqual(final_update[1], ProgressStatus.COMPLETED)
        self.assertEqual(final_update[2], 100.0)

        # Verify operation was cleaned up
        self.assertIsNone(self.service.get_operation("lifecycle_test"))

    def test_multiple_subscribers(self):
        """Test multiple subscribers receiving updates."""
        callbacks = [Mock() for _ in range(3)]

        for callback in callbacks:
            self.service.subscribe(callback)

        # Create and update operation
        operation = self.service.start_operation("multi_sub_test", "Testing")
        operation.update(progress=50.0, message="Half way")

        # Verify all callbacks were called
        for callback in callbacks:
            self.assertEqual(callback.call_count, 2)  # start + update

    def test_subscriber_error_handling(self):
        """Test that subscriber errors don't break the service."""
        def good_callback(update):
            self.callback_results.append("good")

        def bad_callback(update):
            raise Exception("Subscriber error")

        self.service.subscribe(good_callback)
        self.service.subscribe(bad_callback)

        # This should not raise an exception despite bad_callback failing
        self.service.start_operation("error_test", "Testing")

        # Good callback should still have been called
        self.assertEqual(len(self.callback_results), 1)
        self.assertEqual(self.callback_results[0], "good")


class TestProgressServiceIntegration(unittest.TestCase):
    """Integration tests for ProgressService with real operations."""

    def setUp(self):
        """Set up integration test fixtures."""
        ProgressService._instance = None
        self.service = ProgressService.get_instance()
        self.updates = []

    def tearDown(self):
        """Clean up integration tests."""
        ProgressService._instance = None

    def test_real_time_progress_tracking(self):
        """Test real-time progress tracking with actual delays."""
        def progress_callback(update):
            self.updates.append({
                'operation_id': update.operation_id,
                'status': update.status.value,
                'progress': update.progress,
                'message': update.message,
                'elapsed': update.elapsed_time
            })

        self.service.subscribe(progress_callback)

        # Start operation
        operation = self.service.start_operation(
            "real_time_test",
            "Starting real-time operation",
            total_steps=3
        )

        # Simulate work with real delays
        time.sleep(0.1)
        operation.next_step("Processing phase 1")

        time.sleep(0.1)
        operation.next_step("Processing phase 2")

        time.sleep(0.1)
        operation.next_step("Finalizing")

        time.sleep(0.1)
        operation.complete("Real-time operation completed")

        # Verify we received all updates
        self.assertGreaterEqual(len(self.updates), 4)

        # Verify elapsed time is realistic
        final_update = self.updates[-1]
        self.assertGreater(final_update['elapsed'], 0.3)  # At least 0.4 seconds

        # Verify status progression
        statuses = [update['status'] for update in self.updates]
        self.assertIn('starting', statuses)
        self.assertIn('in_progress', statuses)
        self.assertIn('completed', statuses)

    def test_concurrent_operations_independence(self):
        """Test that concurrent operations maintain independence."""
        operation1 = self.service.start_operation("concurrent_1", "Operation 1", total_steps=2)
        operation2 = self.service.start_operation("concurrent_2", "Operation 2", total_steps=3)

        # Progress operations independently
        operation1.next_step("Op1 Step 1")
        operation2.next_step("Op2 Step 1")
        operation1.next_step("Op1 Step 2")
        operation2.next_step("Op2 Step 2")

        # Check active operations
        active_ops = self.service.get_active_operations()
        self.assertEqual(len(active_ops), 2)

        # Complete operations
        operation1.complete("Op1 done")
        self.assertEqual(len(self.service.get_active_operations()), 1)

        operation2.next_step("Op2 Step 3")
        operation2.complete("Op2 done")
        self.assertEqual(len(self.service.get_active_operations()), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
