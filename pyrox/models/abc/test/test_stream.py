"""Unit tests for stream.py module."""

import io
import sys
import unittest
from unittest.mock import MagicMock, patch, call

from pyrox.models.abc.stream import SimpleStream, MultiStream


class TestSimpleStream(unittest.TestCase):
    """Test cases for SimpleStream class."""

    def test_init_with_valid_callback(self):
        """Test initialization with valid callback function."""
        callback = MagicMock()
        stream = SimpleStream(callback)

        self.assertEqual(stream.callback, callback)
        self.assertFalse(stream.closed)

    def test_init_with_lambda_callback(self):
        """Test initialization with lambda callback."""
        def callback(x): return x.upper()
        stream = SimpleStream(callback)

        self.assertEqual(stream.callback, callback)
        self.assertTrue(callable(stream.callback))

    def test_init_with_method_callback(self):
        """Test initialization with method as callback."""
        class TestClass:
            def __init__(self):
                self.messages = []

            def handle_message(self, text):
                self.messages.append(text)

        test_obj = TestClass()
        stream = SimpleStream(test_obj.handle_message)

        stream.write("test message")
        self.assertEqual(test_obj.messages, ["test message"])

    def test_init_with_invalid_callback_none(self):
        """Test initialization with None callback raises TypeError."""
        with self.assertRaises(TypeError) as context:
            SimpleStream(None)  # type: ignore

        self.assertEqual(str(context.exception), "Callback must be a callable function.")

    def test_init_with_invalid_callback_string(self):
        """Test initialization with string callback raises TypeError."""
        with self.assertRaises(TypeError) as context:
            SimpleStream("not a function")  # type: ignore

        self.assertEqual(str(context.exception), "Callback must be a callable function.")

    def test_init_with_invalid_callback_number(self):
        """Test initialization with number callback raises TypeError."""
        with self.assertRaises(TypeError) as context:
            SimpleStream(123)  # type: ignore

        self.assertEqual(str(context.exception), "Callback must be a callable function.")

    def test_init_with_invalid_callback_dict(self):
        """Test initialization with dict callback raises TypeError."""
        with self.assertRaises(TypeError) as context:
            SimpleStream({'key': 'value'})  # type: ignore

        self.assertEqual(str(context.exception), "Callback must be a callable function.")

    def test_write_calls_callback(self):
        """Test that write calls the callback with correct text."""
        callback = MagicMock()
        stream = SimpleStream(callback)

        stream.write("test message")

        callback.assert_called_once_with("test message")

    def test_write_multiple_calls(self):
        """Test multiple write calls."""
        callback = MagicMock()
        stream = SimpleStream(callback)

        stream.write("first message")
        stream.write("second message")
        stream.write("third message")

        expected_calls = [
            call("first message"),
            call("second message"),
            call("third message")
        ]
        callback.assert_has_calls(expected_calls)

    def test_write_empty_string(self):
        """Test writing empty string."""
        callback = MagicMock()
        stream = SimpleStream(callback)

        stream.write("")

        callback.assert_called_once_with("")

    def test_write_multiline_string(self):
        """Test writing multiline string."""
        callback = MagicMock()
        stream = SimpleStream(callback)
        multiline_text = "line 1\nline 2\nline 3"

        stream.write(multiline_text)

        callback.assert_called_once_with(multiline_text)

    def test_write_unicode_text(self):
        """Test writing Unicode text."""
        callback = MagicMock()
        stream = SimpleStream(callback)
        unicode_text = "Unicode: àáâãäå æç èéêë 🌍"

        stream.write(unicode_text)

        callback.assert_called_once_with(unicode_text)

    def test_write_when_closed(self):
        """Test that write does nothing when stream is closed."""
        callback = MagicMock()
        stream = SimpleStream(callback)
        stream.close()

        stream.write("test message")

        callback.assert_not_called()

    def test_write_callback_exception_handling(self):
        """Test that callback exceptions are handled gracefully."""
        def error_callback(text):
            raise ValueError("Callback error")

        stream = SimpleStream(error_callback)

        with patch('sys.__stderr__.write') as mock_stderr:
            stream.write("test message")

            mock_stderr.assert_called_once()
            error_message = mock_stderr.call_args[0][0]
            self.assertIn("SimpleStream error", error_message)
            self.assertIn("Callback error", error_message)

    def test_write_callback_different_exceptions(self):
        """Test different types of callback exceptions."""
        exceptions_to_test = [
            RuntimeError("Runtime error"),
            TypeError("Type error"),
            ValueError("Value error"),
            Exception("Generic exception")
        ]

        for exception in exceptions_to_test:
            with self.subTest(exception=type(exception).__name__):
                def error_callback(text):
                    raise exception

                stream = SimpleStream(error_callback)

                with patch('sys.__stderr__.write') as mock_stderr:
                    stream.write("test message")

                    mock_stderr.assert_called_once()
                    error_message = mock_stderr.call_args[0][0]
                    self.assertIn("SimpleStream error", error_message)

    def test_flush_method(self):
        """Test flush method (should be no-op)."""
        callback = MagicMock()
        stream = SimpleStream(callback)

        # Should not raise any errors
        stream.flush()

        # Callback should not be called by flush
        callback.assert_not_called()

    def test_flush_when_closed(self):
        """Test flush method when stream is closed."""
        callback = MagicMock()
        stream = SimpleStream(callback)
        stream.close()

        # Should not raise any errors
        stream.flush()

    def test_close_method(self):
        """Test close method sets closed flag."""
        callback = MagicMock()
        stream = SimpleStream(callback)

        self.assertFalse(stream.closed)

        stream.close()

        self.assertTrue(stream.closed)

    def test_close_multiple_times(self):
        """Test that calling close multiple times is safe."""
        callback = MagicMock()
        stream = SimpleStream(callback)

        stream.close()
        stream.close()
        stream.close()

        self.assertTrue(stream.closed)

    def test_close_then_write(self):
        """Test that write after close does nothing."""
        callback = MagicMock()
        stream = SimpleStream(callback)

        stream.close()
        stream.write("should not be called")

        callback.assert_not_called()

    def test_callback_with_side_effects(self):
        """Test callback that has side effects."""
        messages = []

        def collecting_callback(text):
            messages.append(text.upper())

        stream = SimpleStream(collecting_callback)

        stream.write("hello")
        stream.write("world")

        self.assertEqual(messages, ["HELLO", "WORLD"])

    def test_stream_lifecycle(self):
        """Test complete stream lifecycle."""
        callback = MagicMock()
        stream = SimpleStream(callback)

        # Initial state
        self.assertFalse(stream.closed)

        # Write some data
        stream.write("message 1")
        stream.write("message 2")

        # Flush (no-op)
        stream.flush()

        # Close stream
        stream.close()
        self.assertTrue(stream.closed)

        # Try to write after close
        stream.write("message 3")

        # Verify only the first two messages were written
        expected_calls = [call("message 1"), call("message 2")]
        callback.assert_has_calls(expected_calls)
        self.assertEqual(callback.call_count, 2)


class TestMultiStream(unittest.TestCase):
    """Test cases for MultiStream class."""

    def test_init_with_no_streams(self):
        """Test initialization with no streams."""
        multi_stream = MultiStream()

        self.assertEqual(multi_stream.streams, [])
        self.assertFalse(multi_stream.closed)

    def test_init_with_single_stream(self):
        """Test initialization with single stream."""
        mock_stream = MagicMock()
        multi_stream = MultiStream(mock_stream)

        self.assertEqual(multi_stream.streams, [mock_stream])
        self.assertFalse(multi_stream.closed)

    def test_init_with_multiple_streams(self):
        """Test initialization with multiple streams."""
        stream1 = MagicMock()
        stream2 = MagicMock()
        stream3 = MagicMock()
        multi_stream = MultiStream(stream1, stream2, stream3)

        self.assertEqual(multi_stream.streams, [stream1, stream2, stream3])
        self.assertFalse(multi_stream.closed)

    def test_init_with_real_io_streams(self):
        """Test initialization with real IO streams."""
        stream1 = io.StringIO()
        stream2 = io.StringIO()
        multi_stream = MultiStream(stream1, stream2)

        self.assertEqual(len(multi_stream.streams), 2)
        self.assertIn(stream1, multi_stream.streams)
        self.assertIn(stream2, multi_stream.streams)

    def test_write_to_single_stream(self):
        """Test writing to single stream."""
        mock_stream = MagicMock()
        multi_stream = MultiStream(mock_stream)

        multi_stream.write("test message")

        mock_stream.write.assert_called_once_with("test message")

    def test_write_to_multiple_streams(self):
        """Test writing to multiple streams."""
        stream1 = MagicMock()
        stream2 = MagicMock()
        stream3 = MagicMock()
        multi_stream = MultiStream(stream1, stream2, stream3)

        multi_stream.write("test message")

        stream1.write.assert_called_once_with("test message")
        stream2.write.assert_called_once_with("test message")
        stream3.write.assert_called_once_with("test message")

    def test_write_to_real_io_streams(self):
        """Test writing to real IO streams."""
        stream1 = io.StringIO()
        stream2 = io.StringIO()
        multi_stream = MultiStream(stream1, stream2)

        multi_stream.write("hello world")

        self.assertEqual(stream1.getvalue(), "hello world")
        self.assertEqual(stream2.getvalue(), "hello world")

    def test_write_when_closed(self):
        """Test that write does nothing when multistream is closed."""
        mock_stream = MagicMock()
        multi_stream = MultiStream(mock_stream)
        multi_stream.close()

        multi_stream.write("test message")

        mock_stream.write.assert_not_called()

    def test_write_stream_without_write_method(self):
        """Test writing to object without write method."""
        fake_stream = object()  # Has no write method
        real_stream = MagicMock()
        multi_stream = MultiStream(fake_stream, real_stream)

        multi_stream.write("test message")

        # Real stream should still be called
        real_stream.write.assert_called_once_with("test message")

    def test_write_with_stream_exception(self):
        """Test handling exceptions during write to individual streams."""
        error_stream = MagicMock()
        error_stream.write.side_effect = Exception("Write failed")
        good_stream = MagicMock()

        multi_stream = MultiStream(error_stream, good_stream)

        with patch.object(multi_stream, '_fallback_write') as mock_fallback:
            multi_stream.write("test message")

            # Fallback should be called for the error
            mock_fallback.assert_called_once()

            # Good stream should still be called
            good_stream.write.assert_called_once_with("test message")

    def test_write_multiple_stream_exceptions(self):
        """Test handling exceptions from multiple streams."""
        stream1 = MagicMock()
        stream1.write.side_effect = ValueError("Error 1")
        stream2 = MagicMock()
        stream2.write.side_effect = RuntimeError("Error 2")
        stream3 = MagicMock()  # Good stream

        multi_stream = MultiStream(stream1, stream2, stream3)

        with patch.object(multi_stream, '_fallback_write') as mock_fallback:
            multi_stream.write("test message")

            # Fallback should be called twice (for each error)
            self.assertEqual(mock_fallback.call_count, 2)

            # Good stream should still be called
            stream3.write.assert_called_once_with("test message")

    def test_flush_single_stream(self):
        """Test flushing single stream."""
        mock_stream = MagicMock()
        multi_stream = MultiStream(mock_stream)

        multi_stream.flush()

        mock_stream.flush.assert_called_once()

    def test_flush_multiple_streams(self):
        """Test flushing multiple streams."""
        stream1 = MagicMock()
        stream2 = MagicMock()
        stream3 = MagicMock()
        multi_stream = MultiStream(stream1, stream2, stream3)

        multi_stream.flush()

        stream1.flush.assert_called_once()
        stream2.flush.assert_called_once()
        stream3.flush.assert_called_once()

    def test_flush_stream_without_flush_method(self):
        """Test flushing object without flush method."""
        fake_stream = object()  # Has no flush method
        real_stream = MagicMock()
        multi_stream = MultiStream(fake_stream, real_stream)

        multi_stream.flush()

        # Real stream should still be flushed
        real_stream.flush.assert_called_once()

    def test_flush_with_stream_exception(self):
        """Test handling exceptions during flush."""
        error_stream = MagicMock()
        error_stream.flush.side_effect = Exception("Flush failed")
        good_stream = MagicMock()

        multi_stream = MultiStream(error_stream, good_stream)

        with patch.object(multi_stream, '_fallback_write') as mock_fallback:
            multi_stream.flush()

            # Fallback should be called for the error
            mock_fallback.assert_called_once()

            # Good stream should still be flushed
            good_stream.flush.assert_called_once()

    def test_close_single_stream(self):
        """Test closing single stream."""
        mock_stream = MagicMock()
        multi_stream = MultiStream(mock_stream)

        multi_stream.close()

        self.assertTrue(multi_stream.closed)
        mock_stream.close.assert_called_once()

    def test_close_multiple_streams(self):
        """Test closing multiple streams."""
        stream1 = MagicMock()
        stream2 = MagicMock()
        stream3 = MagicMock()
        multi_stream = MultiStream(stream1, stream2, stream3)

        multi_stream.close()

        self.assertTrue(multi_stream.closed)
        stream1.close.assert_called_once()
        stream2.close.assert_called_once()
        stream3.close.assert_called_once()

    def test_close_system_streams_not_closed(self):
        """Test that system streams (stdout, stderr) are not closed."""
        custom_stream = MagicMock()
        multi_stream = MultiStream(sys.__stdout__, sys.__stderr__, custom_stream)

        multi_stream.close()

        self.assertTrue(multi_stream.closed)
        # Custom stream should be closed
        custom_stream.close.assert_called_once()

    def test_close_stream_without_close_method(self):
        """Test closing object without close method."""
        fake_stream = object()  # Has no close method
        real_stream = MagicMock()
        multi_stream = MultiStream(fake_stream, real_stream)

        multi_stream.close()

        self.assertTrue(multi_stream.closed)
        # Real stream should still be closed
        real_stream.close.assert_called_once()

    def test_close_with_stream_exception(self):
        """Test handling exceptions during close."""
        error_stream = MagicMock()
        error_stream.close.side_effect = Exception("Close failed")
        good_stream = MagicMock()

        multi_stream = MultiStream(error_stream, good_stream)

        with patch.object(multi_stream, '_fallback_write') as mock_fallback:
            multi_stream.close()

            self.assertTrue(multi_stream.closed)
            # Fallback should be called for the error
            mock_fallback.assert_called_once()

            # Good stream should still be closed
            good_stream.close.assert_called_once()

    def test_add_stream(self):
        """Test adding a new stream."""
        stream1 = MagicMock()
        stream2 = MagicMock()
        multi_stream = MultiStream(stream1)

        self.assertEqual(len(multi_stream.streams), 1)

        multi_stream.add_stream(stream2)

        self.assertEqual(len(multi_stream.streams), 2)
        self.assertIn(stream2, multi_stream.streams)

    def test_add_duplicate_stream(self):
        """Test that adding duplicate stream is ignored."""
        stream1 = MagicMock()
        multi_stream = MultiStream(stream1)

        initial_length = len(multi_stream.streams)

        multi_stream.add_stream(stream1)  # Add same stream again

        self.assertEqual(len(multi_stream.streams), initial_length)

    def test_add_stream_then_write(self):
        """Test adding stream and then writing to all streams."""
        stream1 = MagicMock()
        stream2 = MagicMock()
        multi_stream = MultiStream(stream1)

        multi_stream.add_stream(stream2)
        multi_stream.write("test message")

        stream1.write.assert_called_once_with("test message")
        stream2.write.assert_called_once_with("test message")

    def test_remove_stream(self):
        """Test removing a stream."""
        stream1 = MagicMock()
        stream2 = MagicMock()
        multi_stream = MultiStream(stream1, stream2)

        self.assertEqual(len(multi_stream.streams), 2)

        multi_stream.remove_stream(stream1)

        self.assertEqual(len(multi_stream.streams), 1)
        self.assertNotIn(stream1, multi_stream.streams)
        self.assertIn(stream2, multi_stream.streams)

    def test_remove_nonexistent_stream(self):
        """Test removing a stream that doesn't exist."""
        stream1 = MagicMock()
        stream2 = MagicMock()
        multi_stream = MultiStream(stream1)

        initial_length = len(multi_stream.streams)

        # Try to remove stream that's not in the list
        multi_stream.remove_stream(stream2)

        self.assertEqual(len(multi_stream.streams), initial_length)
        self.assertIn(stream1, multi_stream.streams)

    def test_remove_stream_then_write(self):
        """Test removing stream and then writing."""
        stream1 = MagicMock()
        stream2 = MagicMock()
        multi_stream = MultiStream(stream1, stream2)

        multi_stream.remove_stream(stream1)
        multi_stream.write("test message")

        stream1.write.assert_not_called()
        stream2.write.assert_called_once_with("test message")

    def test_fallback_write_method(self):
        """Test _fallback_write method."""
        multi_stream = MultiStream()

        with patch('sys.__stderr__.write') as mock_stderr:
            multi_stream._fallback_write("error message")

            mock_stderr.assert_called_once()
            error_text = mock_stderr.call_args[0][0]
            self.assertIn("MultiStream error", error_text)
            self.assertIn("error message", error_text)

    def test_empty_multistream_operations(self):
        """Test operations on empty MultiStream."""
        multi_stream = MultiStream()

        # Should not raise errors
        multi_stream.write("test")
        multi_stream.flush()
        multi_stream.close()

        self.assertTrue(multi_stream.closed)


class TestStreamIntegration(unittest.TestCase):
    """Integration tests for stream classes working together."""

    def test_simple_stream_in_multistream(self):
        """Test using SimpleStream as part of MultiStream."""
        messages = []

        def collector(text):
            messages.append(f"collected: {text}")

        simple_stream = SimpleStream(collector)
        string_io = io.StringIO()
        multi_stream = MultiStream(simple_stream, string_io)

        multi_stream.write("integration test")

        self.assertEqual(messages, ["collected: integration test"])
        self.assertEqual(string_io.getvalue(), "integration test")

    def test_nested_multistreams(self):
        """Test MultiStream containing other MultiStreams."""
        stream1 = io.StringIO()
        stream2 = io.StringIO()
        stream3 = io.StringIO()

        inner_multi = MultiStream(stream1, stream2)
        outer_multi = MultiStream(inner_multi, stream3)

        outer_multi.write("nested test")

        # All streams should receive the message
        self.assertEqual(stream1.getvalue(), "nested test")
        self.assertEqual(stream2.getvalue(), "nested test")
        self.assertEqual(stream3.getvalue(), "nested test")

    def test_real_world_logging_scenario(self):
        """Test realistic logging scenario with file and console output."""
        # Simulate file stream
        file_stream = io.StringIO()

        # Simulate console callback
        console_messages = []

        def console_logger(text):
            console_messages.append(f"[CONSOLE] {text}")

        console_stream = SimpleStream(console_logger)

        # Create multi-stream logger
        logger_stream = MultiStream(file_stream, console_stream)

        # Log some messages
        logger_stream.write("Application started")
        logger_stream.write("Processing data...")
        logger_stream.write("Application finished")

        # Verify both outputs
        file_content = file_stream.getvalue()
        self.assertIn("Application started", file_content)
        self.assertIn("Processing data...", file_content)
        self.assertIn("Application finished", file_content)

        self.assertEqual(len(console_messages), 3)
        self.assertEqual(console_messages[0], "[CONSOLE] Application started")
        self.assertEqual(console_messages[1], "[CONSOLE] Processing data...")
        self.assertEqual(console_messages[2], "[CONSOLE] Application finished")

    def test_error_resilient_logging(self):
        """Test that logging continues even if some streams fail."""
        # Create streams: one that fails, one that works
        failing_stream = MagicMock()
        failing_stream.write.side_effect = Exception("Write failed")

        working_stream = io.StringIO()

        multi_stream = MultiStream(failing_stream, working_stream)

        with patch('sys.__stderr__.write'):  # Suppress error output
            multi_stream.write("resilient message")

        # Working stream should still receive the message
        self.assertEqual(working_stream.getvalue(), "resilient message")

    def test_dynamic_stream_management(self):
        """Test adding and removing streams dynamically."""
        stream1 = io.StringIO()
        stream2 = io.StringIO()
        stream3 = io.StringIO()

        multi_stream = MultiStream(stream1)

        # Initial write
        multi_stream.write("message 1")

        # Add second stream
        multi_stream.add_stream(stream2)
        multi_stream.write("message 2")

        # Add third stream
        multi_stream.add_stream(stream3)
        multi_stream.write("message 3")

        # Remove first stream
        multi_stream.remove_stream(stream1)
        multi_stream.write("message 4")

        # Verify message distribution
        self.assertEqual(stream1.getvalue(), "message 1message 2message 3")
        self.assertEqual(stream2.getvalue(), "message 2message 3message 4")
        self.assertEqual(stream3.getvalue(), "message 3message 4")

    def test_stream_lifecycle_management(self):
        """Test complete lifecycle of stream objects."""
        callback = MagicMock()
        simple_stream = SimpleStream(callback)
        string_io = io.StringIO()

        multi_stream = MultiStream(simple_stream, string_io)

        # Write phase
        multi_stream.write("lifecycle test")

        callback.assert_called_once_with("lifecycle test")
        self.assertEqual(string_io.getvalue(), "lifecycle test")

        # Flush phase
        multi_stream.flush()

        # Close phase
        multi_stream.close()

        # Verify everything worked

        self.assertTrue(multi_stream.closed)
        self.assertTrue(simple_stream.closed)

    def test_unicode_and_special_characters(self):
        """Test handling of Unicode and special characters across streams."""
        special_text = "Special: àáâãäå æç 🌍 \n\t\r"

        collector = []
        simple_stream = SimpleStream(lambda x: collector.append(x))
        string_io = io.StringIO()

        multi_stream = MultiStream(simple_stream, string_io)
        multi_stream.write(special_text)

        self.assertEqual(collector[0], special_text)
        self.assertEqual(string_io.getvalue(), special_text)

    def test_performance_with_many_streams(self):
        """Test performance characteristics with many streams."""
        num_streams = 50
        streams = [io.StringIO() for _ in range(num_streams)]
        multi_stream = MultiStream(*streams)

        test_message = "performance test message"
        multi_stream.write(test_message)

        # Verify all streams received the message
        for stream in streams:
            self.assertEqual(stream.getvalue(), test_message)

    def test_exception_isolation(self):
        """Test that exceptions in one stream don't affect others."""
        class ExceptionStream:
            def __init__(self, should_fail_on):
                self.should_fail_on = should_fail_on
                self.call_count = 0

            def write(self, text):
                self.call_count += 1
                if self.call_count == self.should_fail_on:
                    raise RuntimeError(f"Intentional failure on call {self.call_count}")

            def flush(self):
                pass

            def close(self):
                pass

        stream1 = ExceptionStream(should_fail_on=2)  # Fails on second write
        stream2 = io.StringIO()  # Always works
        stream3 = ExceptionStream(should_fail_on=3)  # Fails on third write

        multi_stream = MultiStream(stream1, stream2, stream3)

        with patch('sys.__stderr__.write'):  # Suppress error output
            multi_stream.write("message 1")  # All work
            multi_stream.write("message 2")  # stream1 fails
            multi_stream.write("message 3")  # stream3 fails

        # stream2 should have received all messages
        self.assertEqual(stream2.getvalue(), "message 1message 2message 3")


if __name__ == '__main__':
    unittest.main(verbosity=2)
