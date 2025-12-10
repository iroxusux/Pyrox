"""Unit tests for process.py module."""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock, call

from pyrox.services.process import execute_file_as_subprocess


class TestExecuteFileAsSubprocess(unittest.TestCase):
    """Test cases for execute_file_as_subprocess function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, 'test_file.txt')

        # Create a test file
        with open(self.test_file, 'w') as f:
            f.write("Test file content")

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    @patch('pyrox.services.process.log')
    def test_file_not_found(self, mock_log):
        """Test behavior when file does not exist."""
        nonexistent_file = os.path.join(self.test_dir, 'nonexistent.txt')

        execute_file_as_subprocess(nonexistent_file)

        mock_log.assert_called_once_with('pyrox.services.process')
        mock_log.return_value.error.assert_called_once_with(f"File not found: {nonexistent_file}")

    @patch('pyrox.services.process.log')
    @patch('os.path.isfile')
    def test_file_not_found_isfile_false(self, mock_isfile, mock_log):
        """Test behavior when os.path.isfile returns False."""
        mock_isfile.return_value = False

        execute_file_as_subprocess(self.test_file)

        mock_isfile.assert_called_once_with(self.test_file)
        mock_log.assert_called_once_with('pyrox.services.process')
        mock_log.return_value.error.assert_called_once_with(f"File not found: {self.test_file}")

    @patch('pyrox.services.process.log')
    @patch('sys.platform', 'win32')
    @patch('os.startfile')
    @patch('os.path.isfile')
    def test_windows_execution_success(self, mock_isfile, mock_startfile, mock_log):
        """Test successful file execution on Windows."""
        mock_isfile.return_value = True

        execute_file_as_subprocess(self.test_file)

        mock_isfile.assert_called_once_with(self.test_file)
        mock_startfile.assert_called_once_with(self.test_file)
        mock_log.assert_called_once_with('pyrox.services.process')
        mock_log.return_value.info.assert_called_once_with(f"Successfully executed file: {self.test_file}")

    @patch('pyrox.services.process.log')
    @patch('sys.platform', 'win32')
    @patch('os.startfile')
    @patch('os.path.isfile')
    def test_windows_execution_failure(self, mock_isfile, mock_startfile, mock_log):
        """Test failed file execution on Windows."""
        mock_isfile.return_value = True
        test_exception = OSError("Windows execution failed")
        mock_startfile.side_effect = test_exception

        execute_file_as_subprocess(self.test_file)

        mock_isfile.assert_called_once_with(self.test_file)
        mock_startfile.assert_called_once_with(self.test_file)
        mock_log.assert_called_once_with('pyrox.services.process')
        mock_log.return_value.error.assert_called_once_with(f"Failed to execute file {self.test_file}: {test_exception}")

    @patch('pyrox.services.process.log')
    @patch('sys.platform', 'darwin')
    @patch('subprocess.Popen')
    @patch('os.path.isfile')
    def test_macos_execution_success(self, mock_isfile, mock_popen, mock_log):
        """Test successful file execution on macOS."""
        mock_isfile.return_value = True
        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        execute_file_as_subprocess(self.test_file)

        mock_isfile.assert_called_once_with(self.test_file)
        mock_popen.assert_called_once_with(['open', self.test_file])
        mock_log.assert_called_once_with('pyrox.services.process')
        mock_log.return_value.info.assert_called_once_with(f"Successfully executed file: {self.test_file}")

    @patch('pyrox.services.process.log')
    @patch('sys.platform', 'darwin')
    @patch('subprocess.Popen')
    @patch('os.path.isfile')
    def test_macos_execution_failure(self, mock_isfile, mock_popen, mock_log):
        """Test failed file execution on macOS."""
        mock_isfile.return_value = True
        test_exception = OSError("macOS execution failed")
        mock_popen.side_effect = test_exception

        execute_file_as_subprocess(self.test_file)

        mock_isfile.assert_called_once_with(self.test_file)
        mock_popen.assert_called_once_with(['open', self.test_file])
        mock_log.assert_called_once_with('pyrox.services.process')
        mock_log.return_value.error.assert_called_once_with(f"Failed to execute file {self.test_file}: {test_exception}")

    @patch('pyrox.services.process.log')
    @patch('sys.platform', 'linux')
    @patch('subprocess.Popen')
    @patch('os.path.isfile')
    def test_linux_execution_success(self, mock_isfile, mock_popen, mock_log):
        """Test successful file execution on Linux."""
        mock_isfile.return_value = True
        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        execute_file_as_subprocess(self.test_file)

        mock_isfile.assert_called_once_with(self.test_file)
        mock_popen.assert_called_once_with(['xdg-open', self.test_file])
        mock_log.assert_called_once_with('pyrox.services.process')
        mock_log.return_value.info.assert_called_once_with(f"Successfully executed file: {self.test_file}")

    @patch('pyrox.services.process.log')
    @patch('sys.platform', 'linux')
    @patch('subprocess.Popen')
    @patch('os.path.isfile')
    def test_linux_execution_failure(self, mock_isfile, mock_popen, mock_log):
        """Test failed file execution on Linux."""
        mock_isfile.return_value = True
        test_exception = FileNotFoundError("Linux execution failed")
        mock_popen.side_effect = test_exception

        execute_file_as_subprocess(self.test_file)

        mock_isfile.assert_called_once_with(self.test_file)
        mock_popen.assert_called_once_with(['xdg-open', self.test_file])
        mock_log.assert_called_once_with('pyrox.services.process')
        mock_log.return_value.error.assert_called_once_with(f"Failed to execute file {self.test_file}: {test_exception}")

    @patch('pyrox.services.process.log')
    @patch('sys.platform', 'freebsd')
    @patch('subprocess.Popen')
    @patch('os.path.isfile')
    def test_unix_like_execution_success(self, mock_isfile, mock_popen, mock_log):
        """Test successful file execution on Unix-like systems (FreeBSD)."""
        mock_isfile.return_value = True
        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        execute_file_as_subprocess(self.test_file)

        mock_isfile.assert_called_once_with(self.test_file)
        mock_popen.assert_called_once_with(['xdg-open', self.test_file])
        mock_log.assert_called_once_with('pyrox.services.process')
        mock_log.return_value.info.assert_called_once_with(f"Successfully executed file: {self.test_file}")

    @patch('pyrox.services.process.log')
    @patch('sys.platform', 'freebsd')
    @patch('subprocess.Popen')
    @patch('os.path.isfile')
    def test_unix_like_execution_failure(self, mock_isfile, mock_popen, mock_log):
        """Test failed file execution on Unix-like systems (FreeBSD)."""
        mock_isfile.return_value = True
        test_exception = PermissionError("Unix execution failed")
        mock_popen.side_effect = test_exception

        execute_file_as_subprocess(self.test_file)

        mock_isfile.assert_called_once_with(self.test_file)
        mock_popen.assert_called_once_with(['xdg-open', self.test_file])
        mock_log.assert_called_once_with('pyrox.services.process')
        mock_log.return_value.error.assert_called_once_with(f"Failed to execute file {self.test_file}: {test_exception}")

    @patch('pyrox.services.process.log')
    @patch('sys.platform', 'win32')
    @patch('os.startfile')
    @patch('os.path.isfile')
    def test_empty_file_path(self, mock_isfile, mock_startfile, mock_log):
        """Test behavior with empty file path."""
        mock_isfile.return_value = False
        empty_path = ""

        execute_file_as_subprocess(empty_path)

        mock_isfile.assert_called_once_with(empty_path)
        mock_startfile.assert_not_called()
        mock_log.assert_called_once_with('pyrox.services.process')
        mock_log.return_value.error.assert_called_once_with(f"File not found: {empty_path}")

    @patch('pyrox.services.process.log')
    @patch('sys.platform', 'win32')
    @patch('os.startfile')
    @patch('os.path.isfile')
    def test_none_file_path(self, mock_isfile, mock_startfile, mock_log):
        """Test behavior with None file path."""
        mock_isfile.side_effect = TypeError("expected str, bytes or os.PathLike object, not NoneType")

        with self.assertRaises(TypeError):
            execute_file_as_subprocess(None)  # type: ignore

        mock_isfile.assert_called_once_with(None)
        mock_startfile.assert_not_called()

    @patch('pyrox.services.process.log')
    @patch('sys.platform', 'win32')
    @patch('os.startfile')
    @patch('os.path.isfile')
    def test_special_characters_in_path(self, mock_isfile, mock_startfile, mock_log):
        """Test behavior with special characters in file path."""
        mock_isfile.return_value = True
        special_path = os.path.join(self.test_dir, 'file with spaces & symbols!@#.txt')

        execute_file_as_subprocess(special_path)

        mock_isfile.assert_called_once_with(special_path)
        mock_startfile.assert_called_once_with(special_path)
        mock_log.assert_called_once_with('pyrox.services.process')
        mock_log.return_value.info.assert_called_once_with(f"Successfully executed file: {special_path}")

    @patch('pyrox.services.process.log')
    @patch('sys.platform', 'darwin')
    @patch('subprocess.Popen')
    @patch('os.path.isfile')
    def test_unicode_file_path(self, mock_isfile, mock_popen, mock_log):
        """Test behavior with Unicode characters in file path."""
        mock_isfile.return_value = True
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        unicode_path = os.path.join(self.test_dir, 'файл_тест.txt')

        execute_file_as_subprocess(unicode_path)

        mock_isfile.assert_called_once_with(unicode_path)
        mock_popen.assert_called_once_with(['open', unicode_path])
        mock_log.assert_called_once_with('pyrox.services.process')
        mock_log.return_value.info.assert_called_once_with(f"Successfully executed file: {unicode_path}")

    @patch('pyrox.services.process.log')
    @patch('sys.platform', 'linux')
    @patch('subprocess.Popen')
    @patch('os.path.isfile')
    def test_long_file_path(self, mock_isfile, mock_popen, mock_log):
        """Test behavior with very long file path."""
        mock_isfile.return_value = True
        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        # Create a long path (but still valid)
        long_filename = "a" * 200 + ".txt"
        long_path = os.path.join(self.test_dir, long_filename)

        execute_file_as_subprocess(long_path)

        mock_isfile.assert_called_once_with(long_path)
        mock_popen.assert_called_once_with(['xdg-open', long_path])
        mock_log.assert_called_once_with('pyrox.services.process')
        mock_log.return_value.info.assert_called_once_with(f"Successfully executed file: {long_path}")

    @patch('pyrox.services.process.log')
    @patch('sys.platform', 'win32')
    @patch('os.startfile')
    @patch('os.path.isfile')
    def test_multiple_calls_same_file(self, mock_isfile, mock_startfile, mock_log):
        """Test multiple calls with the same file."""
        mock_isfile.return_value = True

        # Execute the same file multiple times
        execute_file_as_subprocess(self.test_file)
        execute_file_as_subprocess(self.test_file)
        execute_file_as_subprocess(self.test_file)

        # Verify all calls were made
        self.assertEqual(mock_isfile.call_count, 3)
        self.assertEqual(mock_startfile.call_count, 3)
        self.assertEqual(mock_log.call_count, 3)

        expected_calls = [call(self.test_file)] * 3
        mock_isfile.assert_has_calls(expected_calls)
        mock_startfile.assert_has_calls(expected_calls)

    @patch('pyrox.services.process.log')
    @patch('sys.platform', 'darwin')
    @patch('subprocess.Popen')
    @patch('os.path.isfile')
    def test_platform_detection_edge_cases(self, mock_isfile, mock_popen, mock_log):
        """Test platform detection with edge cases."""
        mock_isfile.return_value = True
        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        execute_file_as_subprocess(self.test_file)

        # Should use macOS 'open' command for darwin platform
        mock_popen.assert_called_once_with(['open', self.test_file])

    @patch('pyrox.services.process.log')
    @patch('sys.platform', 'linux2')  # Old Python 2 Linux platform identifier
    @patch('subprocess.Popen')
    @patch('os.path.isfile')
    def test_old_linux_platform_identifier(self, mock_isfile, mock_popen, mock_log):
        """Test behavior with old Linux platform identifier."""
        mock_isfile.return_value = True
        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        execute_file_as_subprocess(self.test_file)

        # Should still use xdg-open for linux2 (falls through to else clause)
        mock_popen.assert_called_once_with(['xdg-open', self.test_file])

    @patch('pyrox.services.process.log')
    def test_integration_with_real_file(self, mock_log):
        """Integration test with a real file (no mocking of os operations)."""
        # This test uses a real file but mocks only the platform-specific execution
        with patch('sys.platform', 'linux'):
            with patch('subprocess.Popen') as mock_popen:
                mock_process = MagicMock()
                mock_popen.return_value = mock_process

                execute_file_as_subprocess(self.test_file)

                mock_popen.assert_called_once_with(['xdg-open', self.test_file])
                mock_log.return_value.info.assert_called_once_with(f"Successfully executed file: {self.test_file}")

    @patch('pyrox.services.process.log')
    @patch('sys.platform', 'win32')
    @patch('os.startfile')
    @patch('os.path.isfile')
    def test_different_exception_types(self, mock_isfile, mock_startfile, mock_log):
        """Test handling of different exception types."""
        mock_isfile.return_value = True

        # Test with different exception types
        exception_types = [
            OSError("OS Error"),
            FileNotFoundError("File not found"),
            PermissionError("Permission denied"),
            ValueError("Value error"),
            RuntimeError("Runtime error")
        ]

        for exception in exception_types:
            with self.subTest(exception=type(exception).__name__):
                mock_startfile.side_effect = exception
                mock_log.reset_mock()

                execute_file_as_subprocess(self.test_file)

                mock_log.return_value.error.assert_called_once_with(f"Failed to execute file {self.test_file}: {exception}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
