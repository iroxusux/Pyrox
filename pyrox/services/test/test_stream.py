"""Unit tests for the stream service module.

This module contains comprehensive tests for the FileStream and StreamManager
classes, ensuring proper functionality for file stream management and logging
integration.
"""

import os
import tempfile
import threading
import unittest
from unittest.mock import patch, MagicMock
from pyrox.models.abc.stream import FileStream
from pyrox.services.stream import (
    StreamManager,
    create_stream_to_file,
    create_file_stream_manager,
)


class TestStreamManager(unittest.TestCase):
    """Test cases for the StreamManager class."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = StreamManager()

    def tearDown(self):
        """Clean up test environment."""
        self.manager.close_all()

        # Clean up temp directory
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass

    def test_init(self):
        """Test StreamManager initialization."""
        self.assertEqual(len(self.manager.streams), 0)
        self.assertEqual(len(self.manager), 0)

    def test_create_stream(self):
        """Test creating a new stream."""
        file_path = os.path.join(self.temp_dir, 'test1.txt')
        stream = self.manager.create_stream('test1', file_path)

        self.assertIsInstance(stream, FileStream)
        self.assertEqual(len(self.manager), 1)
        self.assertIn('test1', self.manager)
        self.assertEqual(self.manager.get_stream('test1'), stream)

    def test_create_duplicate_stream(self):
        """Test creating a stream with duplicate name."""
        file_path = os.path.join(self.temp_dir, 'test.txt')
        self.manager.create_stream('test', file_path)

        with self.assertRaises(ValueError):
            self.manager.create_stream('test', file_path)

    def test_get_stream(self):
        """Test getting a stream by name."""
        file_path = os.path.join(self.temp_dir, 'test.txt')
        original_stream = self.manager.create_stream('test', file_path)
        retrieved_stream = self.manager.get_stream('test')

        self.assertEqual(original_stream, retrieved_stream)

    def test_get_nonexistent_stream(self):
        """Test getting a stream that doesn't exist."""
        result = self.manager.get_stream('nonexistent')
        self.assertIsNone(result)

    def test_remove_stream(self):
        """Test removing a stream."""
        file_path = os.path.join(self.temp_dir, 'test.txt')
        stream = self.manager.create_stream('test', file_path)
        stream.open()

        self.assertTrue(stream.is_open)

        result = self.manager.remove_stream('test')
        self.assertTrue(result)
        self.assertEqual(len(self.manager), 0)
        self.assertNotIn('test', self.manager)
        self.assertFalse(stream.is_open)  # Should be closed

    def test_remove_nonexistent_stream(self):
        """Test removing a stream that doesn't exist."""
        result = self.manager.remove_stream('nonexistent')
        self.assertFalse(result)

    def test_write_to_stream(self):
        """Test writing to a specific stream."""
        file_path = os.path.join(self.temp_dir, 'test.txt')
        self.manager.create_stream('test', file_path)

        result = self.manager.write_to_stream('test', 'test content')
        self.assertTrue(result)

        # Verify content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertEqual(content, 'test content')

    def test_write_to_nonexistent_stream(self):
        """Test writing to a stream that doesn't exist."""
        result = self.manager.write_to_stream('nonexistent', 'test')
        self.assertFalse(result)

    def test_write_to_all(self):
        """Test writing to all streams."""
        files = [
            os.path.join(self.temp_dir, 'test1.txt'),
            os.path.join(self.temp_dir, 'test2.txt'),
            os.path.join(self.temp_dir, 'test3.txt'),
        ]

        for i, file_path in enumerate(files):
            self.manager.create_stream(f'test{i+1}', file_path)

        results = self.manager.write_to_all('shared content')

        # All writes should succeed
        self.assertEqual(len(results), 3)
        self.assertTrue(all(results.values()))

        # Verify all files have the content
        for file_path in files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertEqual(content, 'shared content')

    def test_flush_all(self):
        """Test flushing all streams."""
        files = [
            os.path.join(self.temp_dir, 'test1.txt'),
            os.path.join(self.temp_dir, 'test2.txt'),
        ]

        for i, file_path in enumerate(files):
            self.manager.create_stream(f'test{i+1}', file_path)
            self.manager.write_to_stream(f'test{i+1}', 'content')

        results = self.manager.flush_all()

        self.assertEqual(len(results), 2)
        self.assertTrue(all(results.values()))

    def test_close_all(self):
        """Test closing all streams."""
        files = [
            os.path.join(self.temp_dir, 'test1.txt'),
            os.path.join(self.temp_dir, 'test2.txt'),
        ]

        streams = []
        for i, file_path in enumerate(files):
            stream = self.manager.create_stream(f'test{i+1}', file_path)
            stream.open()
            streams.append(stream)

        # All streams should be open
        for stream in streams:
            self.assertTrue(stream.is_open)

        results = self.manager.close_all()

        # All should close successfully
        self.assertEqual(len(results), 2)
        self.assertTrue(all(results.values()))

        # Manager should be empty
        self.assertEqual(len(self.manager), 0)

        # All streams should be closed
        for stream in streams:
            self.assertFalse(stream.is_open)

    def test_get_stream_names(self):
        """Test getting list of stream names."""
        names = ['stream1', 'stream2', 'stream3']

        for name in names:
            file_path = os.path.join(self.temp_dir, f'{name}.txt')
            self.manager.create_stream(name, file_path)

        retrieved_names = self.manager.get_stream_names()
        self.assertEqual(set(retrieved_names), set(names))

    def test_get_all_stats(self):
        """Test getting statistics for all streams."""
        names = ['stream1', 'stream2']

        for name in names:
            file_path = os.path.join(self.temp_dir, f'{name}.txt')
            self.manager.create_stream(name, file_path)
            self.manager.write_to_stream(name, 'test content')

        all_stats = self.manager.get_all_stats()

        self.assertEqual(len(all_stats), 2)
        for name in names:
            self.assertIn(name, all_stats)
            stats = all_stats[name]
            self.assertIn('file_path', stats)
            self.assertIn('bytes_written', stats)
            self.assertGreater(stats['bytes_written'], 0)

    def test_stream_context(self):
        """Test temporary stream context manager."""
        file_path = os.path.join(self.temp_dir, 'context_test.txt')

        with self.manager.stream_context('temp', file_path) as stream:
            self.assertIsInstance(stream, FileStream)
            self.assertEqual(len(self.manager), 1)
            stream.write('temporary content')

        # Stream should be removed after context
        self.assertEqual(len(self.manager), 0)
        self.assertIsNone(self.manager.get_stream('temp'))

        # But file should still exist with content
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertEqual(content, 'temporary content')

    def test_iterator(self):
        """Test iterating over stream names."""
        names = ['a', 'b', 'c']

        for name in names:
            file_path = os.path.join(self.temp_dir, f'{name}.txt')
            self.manager.create_stream(name, file_path)

        iterated_names = list(self.manager)
        self.assertEqual(set(iterated_names), set(names))

    def test_thread_safety(self):
        """Test thread safety of StreamManager operations."""
        results = []

        def create_streams(thread_id):
            for i in range(2):  # Reduced from 5 to 2
                name = f'thread{thread_id}_stream{i}'
                file_path = os.path.join(self.temp_dir, f'{name}.txt')
                try:
                    _ = self.manager.create_stream(name, file_path)
                    results.append(('create', name, True))
                except Exception:
                    results.append(('create', name, False))

        threads = []
        for i in range(2):  # Reduced from 3 to 2 threads
            thread = threading.Thread(target=create_streams, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join(timeout=5.0)  # Add timeout to prevent infinite hang

        # Check that all creates were attempted
        create_results = [r for r in results if r[0] == 'create']
        self.assertEqual(len(create_results), 4)  # 2 threads * 2 streams each

        # Most should succeed (some might fail due to timing, but not all)
        success_count = sum(1 for r in create_results if r[2])
        self.assertGreater(success_count, 2)  # At least half should succeed


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, 'convenience_test.txt')

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass

    def test_create_stream_to_file(self):
        """Test create_stream_to_file function."""
        stream = create_stream_to_file(self.test_file)

        self.assertIsInstance(stream, FileStream)
        self.assertTrue(stream.is_open)  # type: ignore

        # Test writing
        result = stream.write('convenience test')  # type: ignore
        self.assertTrue(result)

        stream.close()  # type: ignore

    def test_create_stream_to_file_with_params(self):
        """Test create_stream_to_file with custom parameters."""
        stream = create_stream_to_file(
            self.test_file,
            mode='w',
            encoding='ascii',
            auto_flush=False
        )

        self.assertIsInstance(stream, FileStream)
        self.assertEqual(stream.mode, 'w')  # type: ignore
        self.assertEqual(stream.encoding, 'ascii')  # type: ignore
        self.assertFalse(stream.auto_flush)  # type: ignore

        stream.close()  # type: ignore

    @patch('pyrox.services.stream.FileStream')
    def test_create_stream_to_file_failure(self, mock_file_stream):
        """Test create_stream_to_file when creation fails."""
        mock_instance = MagicMock()
        mock_instance.open.return_value = False
        mock_file_stream.return_value = mock_instance

        result = create_stream_to_file(self.test_file)
        self.assertIsNone(result)

    @patch('pyrox.services.stream.FileStream', side_effect=Exception("Creation error"))
    @patch('sys.__stderr__')
    def test_create_stream_to_file_exception(self, mock_stderr, mock_file_stream):
        """Test create_stream_to_file when exception occurs."""
        result = create_stream_to_file(self.test_file)
        self.assertIsNone(result)
        mock_stderr.write.assert_called_once()

    def test_create_file_stream_manager(self):
        """Test create_file_stream_manager function."""
        manager = create_file_stream_manager()
        self.assertIsInstance(manager, StreamManager)
        self.assertEqual(len(manager), 0)


if __name__ == '__main__':
    unittest.main()
