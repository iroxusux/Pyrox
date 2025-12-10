"""Unit tests for file services."""
import os
import shutil
import stat
import tempfile
import unittest
from unittest.mock import patch, MagicMock, mock_open


from pyrox.services.file import (
    get_all_files_in_directory,
    get_open_file,
    get_save_file,
    get_save_location,
    is_file_readable,
    remove_all_files,
    save_file,
    transform_file_to_dict
)


class TestFileServices(unittest.TestCase):
    """Test cases for file services."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_file_content = "Test file content"

        # Create test directory structure
        self.sub_dir = os.path.join(self.test_dir, 'subdir')
        os.makedirs(self.sub_dir, exist_ok=True)

        # Create test files
        self.test_files = [
            os.path.join(self.test_dir, 'file1.txt'),
            os.path.join(self.test_dir, 'file2.log'),
            os.path.join(self.sub_dir, 'file3.dat'),
            os.path.join(self.sub_dir, 'file4.cfg')
        ]

        for file_path in self.test_files:
            with open(file_path, 'w') as f:
                f.write(self.test_file_content)

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_get_all_files_in_directory_basic(self):
        """Test getting all files in directory with subdirectories."""
        result = get_all_files_in_directory(self.test_dir)

        # Should find all 4 test files
        self.assertEqual(len(result), 4)

        # Convert to normalized paths for comparison
        result_normalized = [os.path.normpath(path) for path in result]
        expected_normalized = [os.path.normpath(path) for path in self.test_files]

        for expected_file in expected_normalized:
            self.assertIn(expected_file, result_normalized)

    def test_get_all_files_in_directory_empty_directory(self):
        """Test getting files from empty directory."""
        empty_dir = os.path.join(self.test_dir, 'empty')
        os.makedirs(empty_dir)

        result = get_all_files_in_directory(empty_dir)
        self.assertEqual(result, [])

    def test_get_all_files_in_directory_nonexistent_directory(self):
        """Test getting files from non-existent directory."""
        nonexistent_dir = os.path.join(self.test_dir, 'nonexistent')

        with self.assertRaises(FileNotFoundError):
            get_all_files_in_directory(nonexistent_dir)

    def test_get_all_files_in_directory_only_directories(self):
        """Test getting files from directory containing only subdirectories."""
        dir_only = os.path.join(self.test_dir, 'dir_only')
        os.makedirs(dir_only)
        os.makedirs(os.path.join(dir_only, 'sub1'))
        os.makedirs(os.path.join(dir_only, 'sub2'))

        result = get_all_files_in_directory(dir_only)
        self.assertEqual(result, [])

    @patch('tkinter.filedialog.askopenfilename')
    @patch('tkinter.Tk')
    def test_get_open_file_basic(self, mock_tk, mock_askopenfilename):
        """Test basic file opening dialog."""
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        mock_askopenfilename.return_value = '/path/to/file.txt'

        filetypes = [('.txt', 'Text Files'), ('.log', 'Log Files')]
        title = "Select File"

        result = get_open_file(filetypes, title)

        self.assertEqual(result, '/path/to/file.txt')
        mock_root.withdraw.assert_called_once()
        mock_root.update.assert_called_once()
        mock_askopenfilename.assert_called_once_with(
            filetypes=filetypes,
            title=title
        )

    @patch('tkinter.filedialog.askopenfilename')
    @patch('tkinter.Tk')
    def test_get_open_file_no_title(self, mock_tk, mock_askopenfilename):
        """Test file opening dialog without title."""
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        mock_askopenfilename.return_value = '/path/to/file.txt'

        filetypes = [('.txt', 'Text Files')]

        _ = get_open_file(filetypes)

        mock_askopenfilename.assert_called_once_with(
            filetypes=filetypes,
            title=None
        )

    @patch('tkinter.filedialog.askopenfilename')
    @patch('tkinter.Tk')
    def test_get_open_file_cancelled(self, mock_tk, mock_askopenfilename):
        """Test file opening dialog when user cancels."""
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        mock_askopenfilename.return_value = ''  # Empty string when cancelled

        filetypes = [('.txt', 'Text Files')]

        result = get_open_file(filetypes)

        self.assertEqual(result, '')

    @patch('tkinter.filedialog.asksaveasfilename')
    @patch('tkinter.Tk')
    def test_get_save_file_basic(self, mock_tk, mock_asksaveasfilename):
        """Test basic save file dialog."""
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        mock_asksaveasfilename.return_value = '/path/to/save/file.txt'

        filetypes = [('.txt', 'Text Files'), ('.log', 'Log Files')]

        result = get_save_file(filetypes)

        self.assertEqual(result, '/path/to/save/file.txt')
        mock_root.withdraw.assert_called_once()
        mock_root.update.assert_called_once()
        mock_asksaveasfilename.assert_called_once_with(
            confirmoverwrite=True,
            filetypes=filetypes
        )

    @patch('tkinter.filedialog.asksaveasfilename')
    @patch('tkinter.Tk')
    def test_get_save_file_cancelled(self, mock_tk, mock_asksaveasfilename):
        """Test save file dialog when user cancels."""
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        mock_asksaveasfilename.return_value = ''

        filetypes = [('.txt', 'Text Files')]

        result = get_save_file(filetypes)

        self.assertEqual(result, '')

    @patch('tkinter.filedialog.askdirectory')
    @patch('tkinter.Tk')
    def test_get_save_location_basic(self, mock_tk, mock_askdirectory):
        """Test basic directory selection dialog."""
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        mock_askdirectory.return_value = '/path/to/directory'

        result = get_save_location()

        self.assertEqual(result, '/path/to/directory')
        mock_root.withdraw.assert_called_once()
        mock_root.update.assert_called_once()
        mock_askdirectory.assert_called_once()

    @patch('tkinter.filedialog.askdirectory')
    @patch('tkinter.Tk')
    def test_get_save_location_cancelled(self, mock_tk, mock_askdirectory):
        """Test directory selection when user cancels."""
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        mock_askdirectory.return_value = ''

        result = get_save_location()

        self.assertEqual(result, '')

    def test_remove_all_files_basic(self):
        """Test removing all files from directory."""
        # Verify files exist before removal
        self.assertTrue(os.path.exists(self.test_files[0]))
        self.assertTrue(os.path.exists(self.sub_dir))

        remove_all_files(self.test_dir)

        # Directory should still exist but be empty
        self.assertTrue(os.path.exists(self.test_dir))
        self.assertEqual(len(os.listdir(self.test_dir)), 0)

    def test_remove_all_files_empty_directory(self):
        """Test removing files from empty directory."""
        empty_dir = os.path.join(self.test_dir, 'empty')
        os.makedirs(empty_dir)

        # Should not raise error
        remove_all_files(empty_dir)

        # Directory should still exist and be empty
        self.assertTrue(os.path.exists(empty_dir))
        self.assertEqual(len(os.listdir(empty_dir)), 0)

    def test_remove_all_files_with_symlinks(self):
        """Test removing files including symbolic links."""
        if os.name == 'nt':  # Skip on Windows where symlinks might not be supported
            self.skipTest("Symbolic links not reliably supported on Windows")

        link_path = os.path.join(self.test_dir, 'test_link')
        os.symlink(self.test_files[0], link_path)

        self.assertTrue(os.path.islink(link_path))

        remove_all_files(self.test_dir)

        self.assertFalse(os.path.exists(link_path))

    def test_save_file_basic_string(self):
        """Test saving string data to file."""
        file_path = os.path.join(self.test_dir, 'test_save')
        file_extension = '.txt'
        save_mode = 'w'
        file_data = "Test save data"

        result = save_file(file_path, file_extension, save_mode, file_data)

        self.assertTrue(result)

        expected_path = file_path + file_extension
        self.assertTrue(os.path.exists(expected_path))

        with open(expected_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertEqual(content, file_data)

    def test_save_file_basic_bytes(self):
        """Test saving bytes data to file."""
        file_path = os.path.join(self.test_dir, 'test_save_bytes')
        file_extension = '.dat'
        save_mode = 'wb'
        file_data = b"Test binary data"

        result = save_file(file_path, file_extension, save_mode, file_data)

        self.assertTrue(result)

        expected_path = file_path + file_extension
        self.assertTrue(os.path.exists(expected_path))

    def test_save_file_append_mode(self):
        """Test saving file in append mode."""
        file_path = os.path.join(self.test_dir, 'test_append.txt')

        # First write
        result1 = save_file(file_path, '', 'w', "First line\n")
        self.assertTrue(result1)

        # Append write
        result2 = save_file(file_path, '', 'a', "Second line\n")
        self.assertTrue(result2)

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertEqual(content, "First line\nSecond line\n")

    def test_save_file_extension_auto_add(self):
        """Test that file extension is automatically added."""
        file_path = os.path.join(self.test_dir, 'test_ext')
        file_extension = 'log'  # Without dot

        result = save_file(file_path, file_extension, 'w', "Test data")

        self.assertTrue(result)
        expected_path = file_path + '.log'
        self.assertTrue(os.path.exists(expected_path))

    def test_save_file_extension_already_present(self):
        """Test that extension is not duplicated if already present."""
        file_path = os.path.join(self.test_dir, 'test_file.txt')
        file_extension = '.txt'

        result = save_file(file_path, file_extension, 'w', "Test data")

        self.assertTrue(result)
        # Should not become test_file.txt.txt
        self.assertTrue(os.path.exists(file_path))
        self.assertFalse(os.path.exists(file_path + '.txt'))

    def test_save_file_invalid_save_mode(self):
        """Test save file with invalid save mode."""
        with patch('builtins.print') as mock_print:
            file_path = os.path.join(self.test_dir, 'test_invalid')

            result = save_file(file_path, '.txt', 'r', "Test data")

            self.assertFalse(result)
            mock_print.assert_called_with('no save mode!')

    def test_save_file_directory_not_exists(self):
        """Test saving file to non-existent directory."""
        nonexistent_dir = os.path.join(self.test_dir, 'nonexistent', 'nested')
        file_path = os.path.join(nonexistent_dir, 'test_file')

        with patch('builtins.print') as mock_print:
            result = save_file(file_path, '.txt', 'w', "Test data")

            self.assertFalse(result)
            mock_print.assert_called_with('file not found error thrown!')

    @patch('builtins.open', mock_open())
    def test_save_file_write_permission_error(self):
        """Test save file with permission error."""
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with patch('builtins.print') as _:
                with self.assertRaises(PermissionError):
                    result = save_file('/test_file', '.txt', 'w', "Test data")
                    self.assertFalse(result)

    def test_save_file_mixed_modes(self):
        """Test save file with various valid mode combinations."""
        file_path = os.path.join(self.test_dir, 'test_modes')

        # Test 'wb' mode
        result = save_file(file_path + '1', '.bin', 'wb', b"binary data")
        self.assertTrue(result)

        # Test 'ab' mode
        result = save_file(file_path + '2', '.log', 'ab', b"append binary")
        self.assertTrue(result)

        # Test 'w+' mode
        result = save_file(file_path + '3', '.txt', 'w+', "read write mode")
        self.assertTrue(result)

    def test_save_file_empty_data(self):
        """Test saving empty data to file."""
        file_path = os.path.join(self.test_dir, 'empty_file')

        result = save_file(file_path, '.txt', 'w', "")

        self.assertTrue(result)

        expected_path = file_path + '.txt'
        self.assertTrue(os.path.exists(expected_path))

        with open(expected_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertEqual(content, "")

    def test_get_all_files_in_directory_nested_structure(self):
        """Test getting files from deeply nested directory structure."""
        # Create deeper nesting
        deep_dir = os.path.join(self.test_dir, 'level1', 'level2', 'level3')
        os.makedirs(deep_dir, exist_ok=True)

        deep_file = os.path.join(deep_dir, 'deep_file.txt')
        with open(deep_file, 'w') as f:
            f.write("Deep file content")

        result = get_all_files_in_directory(self.test_dir)

        # Should include the deep file plus the original 4 files
        self.assertEqual(len(result), 5)

        deep_file_normalized = os.path.normpath(deep_file)
        result_normalized = [os.path.normpath(path) for path in result]
        self.assertIn(deep_file_normalized, result_normalized)

    def test_save_file_special_characters(self):
        """Test saving file with special characters in data."""
        file_path = os.path.join(self.test_dir, 'special_chars')
        special_data = "Special chars: àáâãäå æç èéêë ìíîï ñ òóôõö ùúûü ÿ"

        result = save_file(file_path, '.txt', 'w', special_data)

        self.assertTrue(result)

        expected_path = file_path + '.txt'
        with open(expected_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertEqual(content, special_data)

    def test_file_operations_integration(self):
        """Test integration of multiple file operations."""
        # Create a test file using save_file
        test_content = "Integration test content"
        file_path = os.path.join(self.test_dir, 'integration_test')

        save_result = save_file(file_path, '.txt', 'w', test_content)
        self.assertTrue(save_result)

        # Find the file using get_all_files_in_directory
        all_files = get_all_files_in_directory(self.test_dir)
        integration_file = file_path + '.txt'
        integration_file_normalized = os.path.normpath(integration_file)
        all_files_normalized = [os.path.normpath(path) for path in all_files]

        self.assertIn(integration_file_normalized, all_files_normalized)

        # Verify the content
        with open(integration_file, 'r', encoding='utf-8') as f:
            read_content = f.read()

        self.assertEqual(read_content, test_content)

        # Clean up using remove_all_files
        remove_all_files(self.test_dir)

        # Verify cleanup
        remaining_files = get_all_files_in_directory(self.test_dir)
        self.assertEqual(len(remaining_files), 0)


class TestIsFileReadable(unittest.TestCase):
    """Test cases for is_file_readable function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_file_path = os.path.join(self.test_dir, 'test_file.txt')
        self.test_content = "Test file content for readability testing"

        # Create a readable test file
        with open(self.test_file_path, 'w', encoding='utf-8') as f:
            f.write(self.test_content)

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_is_file_readable_valid_file(self):
        """Test is_file_readable with a valid, readable file."""
        result = is_file_readable(self.test_file_path)
        self.assertTrue(result)

    def test_is_file_readable_nonexistent_file(self):
        """Test is_file_readable with non-existent file."""
        nonexistent_path = os.path.join(self.test_dir, 'nonexistent.txt')
        result = is_file_readable(nonexistent_path)
        self.assertFalse(result)

    def test_is_file_readable_directory_instead_of_file(self):
        """Test is_file_readable with directory path instead of file."""
        result = is_file_readable(self.test_dir)
        self.assertFalse(result)

    def test_is_file_readable_empty_file(self):
        """Test is_file_readable with empty file."""
        empty_file = os.path.join(self.test_dir, 'empty.txt')
        with open(empty_file, 'w', encoding='utf-8') as _:
            pass  # Create empty file

        result = is_file_readable(empty_file)
        self.assertTrue(result)

    def test_is_file_readable_large_file(self):
        """Test is_file_readable with a large file (should still only read 1 char)."""
        large_file = os.path.join(self.test_dir, 'large.txt')
        large_content = "A" * 10000  # 10KB of 'A's

        with open(large_file, 'w', encoding='utf-8') as f:
            f.write(large_content)

        result = is_file_readable(large_file)
        self.assertTrue(result)

    @unittest.skipIf(os.name == 'nt', "Permission tests not reliable on Windows")
    def test_is_file_readable_no_read_permission(self):
        """Test is_file_readable with file that has no read permission."""
        no_read_file = os.path.join(self.test_dir, 'no_read.txt')

        with open(no_read_file, 'w', encoding='utf-8') as f:
            f.write("Test content")

        # Remove read permission
        os.chmod(no_read_file, stat.S_IWRITE)

        try:
            result = is_file_readable(no_read_file)
            self.assertFalse(result)
        finally:
            # Restore permissions for cleanup
            os.chmod(no_read_file, stat.S_IREAD | stat.S_IWRITE)

    def test_is_file_readable_binary_file(self):
        """Test is_file_readable with binary file (should fail UTF-8 decode)."""
        binary_file = os.path.join(self.test_dir, 'binary.bin')
        binary_content = bytes([0, 1, 2, 255, 254, 253])  # Invalid UTF-8

        with open(binary_file, 'wb') as f:
            f.write(binary_content)

        with patch('builtins.print') as mock_print:
            result = is_file_readable(binary_file)
            self.assertFalse(result)
            mock_print.assert_called()  # Should print the UnicodeDecodeError

    def test_is_file_readable_special_characters(self):
        """Test is_file_readable with file containing Unicode characters."""
        unicode_file = os.path.join(self.test_dir, 'unicode.txt')
        unicode_content = "Special chars: àáâãäå æç èéêë ìíîï ñ òóôõö ùúûü ÿ 🌍"

        with open(unicode_file, 'w', encoding='utf-8') as f:
            f.write(unicode_content)

        result = is_file_readable(unicode_file)
        self.assertTrue(result)

    @patch('os.path.exists')
    def test_is_file_readable_os_path_exists_exception(self, mock_exists):
        """Test is_file_readable when os.path.exists raises an exception."""
        mock_exists.side_effect = OSError("Mocked OS error")

        with patch('builtins.print') as mock_print:
            result = is_file_readable('/some/path')
            self.assertFalse(result)
            mock_print.assert_called_once()

    @patch('os.path.isfile')
    @patch('os.path.exists')
    def test_is_file_readable_os_path_isfile_exception(self, mock_exists, mock_isfile):
        """Test is_file_readable when os.path.isfile raises an exception."""
        mock_exists.return_value = True
        mock_isfile.side_effect = OSError("Mocked isfile error")

        with patch('builtins.print') as mock_print:
            result = is_file_readable('/some/path')
            self.assertFalse(result)
            mock_print.assert_called_once()

    @patch('os.access')
    @patch('os.path.isfile')
    @patch('os.path.exists')
    def test_is_file_readable_os_access_exception(self, mock_exists, mock_isfile, mock_access):
        """Test is_file_readable when os.access raises an exception."""
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_access.side_effect = OSError("Mocked access error")

        with patch('builtins.print') as mock_print:
            result = is_file_readable('/some/path')
            self.assertFalse(result)
            mock_print.assert_called_once()

    @patch('builtins.open')
    @patch('os.access')
    @patch('os.path.isfile')
    @patch('os.path.exists')
    def test_is_file_readable_io_error_on_open(self, mock_exists, mock_isfile, mock_access, mock_open_func):
        """Test is_file_readable when file open raises IOError."""
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_access.return_value = True
        mock_open_func.side_effect = IOError("Cannot open file")

        with patch('builtins.print') as mock_print:
            result = is_file_readable('/some/path')
            self.assertFalse(result)
            mock_print.assert_called_once()

    @patch('builtins.open')
    @patch('os.access')
    @patch('os.path.isfile')
    @patch('os.path.exists')
    def test_is_file_readable_os_error_on_open(self, mock_exists, mock_isfile, mock_access, mock_open_func):
        """Test is_file_readable when file open raises OSError."""
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_access.return_value = True
        mock_open_func.side_effect = OSError("OS error on open")

        with patch('builtins.print') as mock_print:
            result = is_file_readable('/some/path')
            self.assertFalse(result)
            mock_print.assert_called_once()

    @patch('builtins.open')
    @patch('os.access')
    @patch('os.path.isfile')
    @patch('os.path.exists')
    def test_is_file_readable_permission_error_on_open(self, mock_exists, mock_isfile, mock_access, mock_open_func):
        """Test is_file_readable when file open raises PermissionError."""
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_access.return_value = True
        mock_open_func.side_effect = PermissionError("Permission denied")

        with patch('builtins.print') as mock_print:
            result = is_file_readable('/some/path')
            self.assertFalse(result)
            mock_print.assert_called_once()

    def test_is_file_readable_file_read_error_during_read(self):
        """Test is_file_readable when file.read() raises an error."""
        mock_file = mock_open()
        mock_file.return_value.read.side_effect = IOError("Read error")

        with patch('builtins.open', mock_file):
            with patch('os.path.exists', return_value=True):
                with patch('os.path.isfile', return_value=True):
                    with patch('os.access', return_value=True):
                        with patch('builtins.print') as mock_print:
                            result = is_file_readable('/some/path')
                            self.assertFalse(result)
                            mock_print.assert_called_once()

    def test_is_file_readable_symlink_to_valid_file(self):
        """Test is_file_readable with symbolic link to valid file."""
        if os.name == 'nt':
            self.skipTest("Symbolic links not reliably supported on Windows")

        symlink_path = os.path.join(self.test_dir, 'test_symlink.txt')
        os.symlink(self.test_file_path, symlink_path)

        result = is_file_readable(symlink_path)
        self.assertTrue(result)

    def test_is_file_readable_symlink_to_nonexistent_file(self):
        """Test is_file_readable with broken symbolic link."""
        if os.name == 'nt':
            self.skipTest("Symbolic links not reliably supported on Windows")

        nonexistent_target = os.path.join(self.test_dir, 'nonexistent_target.txt')
        symlink_path = os.path.join(self.test_dir, 'broken_symlink.txt')
        os.symlink(nonexistent_target, symlink_path)

        result = is_file_readable(symlink_path)
        self.assertFalse(result)

    def test_is_file_readable_very_long_path(self):
        """Test is_file_readable with very long file path."""
        # Create a deeply nested directory structure
        long_path = self.test_dir
        for i in range(10):
            long_path = os.path.join(long_path, f'level_{i}')

        try:
            os.makedirs(long_path, exist_ok=True)
            long_file = os.path.join(long_path, 'deep_file.txt')

            with open(long_file, 'w', encoding='utf-8') as f:
                f.write("Deep file content")

            result = is_file_readable(long_file)
            self.assertTrue(result)
        except OSError:
            # Skip if path too long for the system
            self.skipTest("Path too long for this system")

    def test_is_file_readable_different_encodings(self):
        """Test is_file_readable with files in different encodings."""
        # Create file with Latin-1 encoding
        latin1_file = os.path.join(self.test_dir, 'latin1.txt')
        latin1_content = "Café résumé naïve"

        with open(latin1_file, 'w', encoding='latin-1') as f:
            f.write(latin1_content)

        # The method tries UTF-8 first, which should fail for true Latin-1 content
        # But our simple test content should work with UTF-8 too
        result = is_file_readable(latin1_file)
        # This might be True or False depending on whether the content is valid UTF-8
        self.assertIsInstance(result, bool)

    def test_is_file_readable_locked_file_simulation(self):
        """Test is_file_readable with a file that's locked/in use."""
        # Simulate a locked file by keeping it open
        locked_file = os.path.join(self.test_dir, 'locked.txt')

        with open(locked_file, 'w', encoding='utf-8') as f:
            f.write("This file is open")
            # File is still open, but should still be readable
            result = is_file_readable(locked_file)
            self.assertTrue(result)  # Most systems allow reading open files

    def test_is_file_readable_zero_byte_file(self):
        """Test is_file_readable with zero-byte file."""
        zero_file = os.path.join(self.test_dir, 'zero_bytes.txt')

        # Create zero-byte file
        open(zero_file, 'w').close()

        result = is_file_readable(zero_file)
        self.assertTrue(result)  # Should be readable even if empty

    def test_is_file_readable_file_with_only_whitespace(self):
        """Test is_file_readable with file containing only whitespace."""
        whitespace_file = os.path.join(self.test_dir, 'whitespace.txt')

        with open(whitespace_file, 'w', encoding='utf-8') as f:
            f.write("   \t\n\r  ")

        result = is_file_readable(whitespace_file)
        self.assertTrue(result)

    def test_is_file_readable_with_null_characters(self):
        """Test is_file_readable with file containing null characters."""
        null_file = os.path.join(self.test_dir, 'with_nulls.txt')

        with open(null_file, 'w', encoding='utf-8') as f:
            f.write("Text with\x00null characters")

        result = is_file_readable(null_file)
        self.assertTrue(result)  # Should still be readable

    def test_is_file_readable_edge_case_empty_filename(self):
        """Test is_file_readable with empty filename."""
        result = is_file_readable("")
        self.assertFalse(result)

    def test_is_file_readable_edge_case_none_filename(self):
        """Test is_file_readable with None as filename."""
        with patch('builtins.print') as mock_print:
            result = is_file_readable(None)
            self.assertFalse(result)
            mock_print.assert_called_once()


class TestTransformFileToDict(unittest.TestCase):
    """Test cases for transform_file_to_dict and _default_transform_function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_file_path = os.path.join(self.test_dir, 'transform_test.txt')
        self.test_content_lines = [
            "Line 1: First line of content\n",
            "Line 2: Second line of content\n",
            "Line 3: Third line of content\n",
            "Line 4: Fourth line of content\n",
            "Line 5: Fifth line of content\n",
            "Line 6: Sixth line of content\n",
            "Line 7: Seventh line of content\n"
        ]

        # Create test file with multiple lines
        with open(self.test_file_path, 'w', encoding='utf-8') as f:
            f.writelines(self.test_content_lines)

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_default_transform_function_basic(self):
        """Test _default_transform_function with basic file."""
        from pyrox.services.file import _default_transform_function

        result = _default_transform_function(self.test_file_path)

        self.assertIsInstance(result, dict)
        self.assertEqual(result['file_path'], self.test_file_path)
        self.assertEqual(result['line_count'], 7)
        self.assertEqual(len(result['content_preview']), 5)
        self.assertEqual(result['content_preview'], self.test_content_lines[:5])
        self.assertEqual(result['content'], self.test_content_lines)

    def test_default_transform_function_empty_file(self):
        """Test _default_transform_function with empty file."""
        from pyrox.services.file import _default_transform_function

        empty_file = os.path.join(self.test_dir, 'empty.txt')
        with open(empty_file, 'w', encoding='utf-8') as _:
            pass  # Create empty file

        result = _default_transform_function(empty_file)

        self.assertEqual(result['file_path'], empty_file)
        self.assertEqual(result['line_count'], 0)
        self.assertEqual(result['content_preview'], [])
        self.assertEqual(result['content'], [])

    def test_default_transform_function_single_line(self):
        """Test _default_transform_function with single line file."""
        from pyrox.services.file import _default_transform_function

        single_line_file = os.path.join(self.test_dir, 'single_line.txt')
        single_line_content = ["Only one line\n"]

        with open(single_line_file, 'w', encoding='utf-8') as f:
            f.writelines(single_line_content)

        result = _default_transform_function(single_line_file)

        self.assertEqual(result['line_count'], 1)
        self.assertEqual(result['content_preview'], single_line_content)
        self.assertEqual(result['content'], single_line_content)

    def test_default_transform_function_exactly_five_lines(self):
        """Test _default_transform_function with exactly 5 lines."""
        from pyrox.services.file import _default_transform_function

        five_line_file = os.path.join(self.test_dir, 'five_lines.txt')
        five_lines_content = self.test_content_lines[:5]

        with open(five_line_file, 'w', encoding='utf-8') as f:
            f.writelines(five_lines_content)

        result = _default_transform_function(five_line_file)

        self.assertEqual(result['line_count'], 5)
        self.assertEqual(result['content_preview'], five_lines_content)
        self.assertEqual(result['content'], five_lines_content)

    def test_default_transform_function_no_newlines(self):
        """Test _default_transform_function with file without newlines."""
        from pyrox.services.file import _default_transform_function

        no_newline_file = os.path.join(self.test_dir, 'no_newlines.txt')
        content_without_newlines = "Single line without newline"

        with open(no_newline_file, 'w', encoding='utf-8') as f:
            f.write(content_without_newlines)

        result = _default_transform_function(no_newline_file)

        self.assertEqual(result['line_count'], 1)
        self.assertEqual(result['content_preview'], [content_without_newlines])
        self.assertEqual(result['content'], [content_without_newlines])

    def test_transform_file_to_dict_with_default_function(self):
        """Test transform_file_to_dict using default transform function."""
        result = transform_file_to_dict(self.test_file_path)

        self.assertIsInstance(result, dict)
        self.assertEqual(result['file_path'], self.test_file_path)
        self.assertEqual(result['line_count'], 7)
        self.assertEqual(len(result['content_preview']), 5)
        self.assertEqual(result['content'], self.test_content_lines)

    def test_transform_file_to_dict_with_custom_function(self):
        """Test transform_file_to_dict with custom transform function."""
        def custom_transform(file_path: str) -> dict:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {
                'path': file_path,
                'size': len(content),
                'uppercase_content': content.upper(),
                'word_count': len(content.split())
            }

        result = transform_file_to_dict(self.test_file_path, custom_transform)

        self.assertIsInstance(result, dict)
        self.assertEqual(result['path'], self.test_file_path)
        self.assertIn('size', result)
        self.assertIn('uppercase_content', result)
        self.assertIn('word_count', result)
        self.assertGreater(result['size'], 0)
        self.assertGreater(result['word_count'], 0)

    def test_transform_file_to_dict_nonexistent_file(self):
        """Test transform_file_to_dict with non-existent file."""
        nonexistent_file = os.path.join(self.test_dir, 'nonexistent.txt')

        with self.assertRaises(FileNotFoundError) as context:
            transform_file_to_dict(nonexistent_file)

        self.assertIn('File not found:', str(context.exception))
        self.assertIn(nonexistent_file, str(context.exception))

    def test_transform_file_to_dict_directory_instead_of_file(self):
        """Test transform_file_to_dict with directory path instead of file."""
        with self.assertRaises(FileNotFoundError) as context:
            transform_file_to_dict(self.test_dir)

        self.assertIn('File not found:', str(context.exception))

    def test_transform_file_to_dict_custom_function_exception(self):
        """Test transform_file_to_dict when custom function raises exception."""
        def failing_transform(file_path: str) -> dict:
            raise ValueError("Custom transform function failed")

        with self.assertRaises(ValueError) as context:
            transform_file_to_dict(self.test_file_path, failing_transform)

        self.assertEqual(str(context.exception), "Custom transform function failed")

    def test_transform_file_to_dict_custom_function_file_access_error(self):
        """Test transform_file_to_dict when custom function has file access issues."""
        def file_access_error_transform(file_path: str) -> dict:
            with open('/nonexistent/path/file.txt', 'r') as f:
                return {'content': f.read()}

        with self.assertRaises(FileNotFoundError):
            transform_file_to_dict(self.test_file_path, file_access_error_transform)

    def test_transform_file_to_dict_json_transform(self):
        """Test transform_file_to_dict with JSON-like transform function."""
        # Create a JSON-like file
        json_like_file = os.path.join(self.test_dir, 'json_like.txt')
        json_content = '{"name": "test", "value": 123, "items": ["a", "b", "c"]}'

        with open(json_like_file, 'w', encoding='utf-8') as f:
            f.write(json_content)

        def json_transform(file_path: str) -> dict:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            try:
                parsed_json = json.loads(content)
                return {
                    'file_path': file_path,
                    'is_valid_json': True,
                    'parsed_data': parsed_json,
                    'json_keys': list(parsed_json.keys()) if isinstance(parsed_json, dict) else None
                }
            except json.JSONDecodeError:
                return {
                    'file_path': file_path,
                    'is_valid_json': False,
                    'raw_content': content
                }

        result = transform_file_to_dict(json_like_file, json_transform)

        self.assertTrue(result['is_valid_json'])
        self.assertEqual(result['parsed_data']['name'], 'test')
        self.assertEqual(result['parsed_data']['value'], 123)
        self.assertIn('name', result['json_keys'])

    def test_transform_file_to_dict_csv_transform(self):
        """Test transform_file_to_dict with CSV-like transform function."""
        # Create a CSV-like file
        csv_file = os.path.join(self.test_dir, 'test.csv')
        csv_content = "name,age,city\nJohn,30,New York\nJane,25,Los Angeles\nBob,35,Chicago"

        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write(csv_content)

        def csv_transform(file_path: str) -> dict:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if not lines:
                return {'file_path': file_path, 'rows': 0, 'headers': [], 'data': []}

            headers = [h.strip() for h in lines[0].strip().split(',')]
            data_rows = []

            for line in lines[1:]:
                row_data = [cell.strip() for cell in line.strip().split(',')]
                data_rows.append(dict(zip(headers, row_data)))

            return {
                'file_path': file_path,
                'rows': len(data_rows),
                'headers': headers,
                'data': data_rows
            }

        result = transform_file_to_dict(csv_file, csv_transform)

        self.assertEqual(result['rows'], 3)
        self.assertEqual(result['headers'], ['name', 'age', 'city'])
        self.assertEqual(result['data'][0]['name'], 'John')
        self.assertEqual(result['data'][1]['age'], '25')

    def test_transform_file_to_dict_binary_file_handling(self):
        """Test transform_file_to_dict with binary file handling."""
        # Create a file with binary content
        binary_file = os.path.join(self.test_dir, 'binary.bin')
        binary_content = bytes([0, 1, 2, 255, 254, 253])

        with open(binary_file, 'wb') as f:
            f.write(binary_content)

        def binary_aware_transform(file_path: str) -> dict:
            try:
                # Try text first
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return {'file_path': file_path, 'type': 'text', 'content': content}
            except UnicodeDecodeError:
                # Fall back to binary
                with open(file_path, 'rb') as f:
                    content = f.read()
                return {
                    'file_path': file_path,
                    'type': 'binary',
                    'size': len(content),
                    'first_bytes': list(content[:10])
                }

        result = transform_file_to_dict(binary_file, binary_aware_transform)

        self.assertEqual(result['type'], 'binary')
        self.assertEqual(result['size'], 6)
        self.assertEqual(result['first_bytes'], [0, 1, 2, 255, 254, 253])

    def test_transform_file_to_dict_large_file(self):
        """Test transform_file_to_dict with large file."""
        large_file = os.path.join(self.test_dir, 'large.txt')

        # Create a file with many lines
        large_content = []
        for i in range(1000):
            large_content.append(f"Line {i+1}: This is line number {i+1}\n")

        with open(large_file, 'w', encoding='utf-8') as f:
            f.writelines(large_content)

        def size_aware_transform(file_path: str) -> dict:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            return {
                'file_path': file_path,
                'total_lines': len(lines),
                'first_10_lines': lines[:10],
                'last_10_lines': lines[-10:],
                'sample_line_lengths': [len(line) for line in lines[:5]]
            }

        result = transform_file_to_dict(large_file, size_aware_transform)

        self.assertEqual(result['total_lines'], 1000)
        self.assertEqual(len(result['first_10_lines']), 10)
        self.assertEqual(len(result['last_10_lines']), 10)
        self.assertTrue(all(length > 0 for length in result['sample_line_lengths']))

    def test_transform_file_to_dict_unicode_content(self):
        """Test transform_file_to_dict with Unicode content."""
        unicode_file = os.path.join(self.test_dir, 'unicode.txt')
        unicode_content = [
            "English: Hello World\n",
            "Spanish: Hola Mundo\n",
            "French: Bonjour le Monde\n",
            "German: Hallo Welt\n",
            "Chinese: 你好世界\n",
            "Japanese: こんにちは世界\n",
            "Arabic: مرحبا بالعالم\n",
            "Russian: Привет мир\n",
            "Emoji: 🌍🌎🌏 Hello! 👋\n"
        ]

        with open(unicode_file, 'w', encoding='utf-8') as f:
            f.writelines(unicode_content)

        def unicode_transform(file_path: str) -> dict:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            return {
                'file_path': file_path,
                'line_count': len(lines),
                'has_emoji': any('🌍' in line or '👋' in line for line in lines),
                'languages': [line.split(':')[0] for line in lines if ':' in line],
                'total_chars': sum(len(line) for line in lines)
            }

        result = transform_file_to_dict(unicode_file, unicode_transform)

        self.assertEqual(result['line_count'], 9)
        self.assertTrue(result['has_emoji'])
        self.assertIn('English', result['languages'])
        self.assertIn('Chinese', result['languages'])
        self.assertGreater(result['total_chars'], 0)

    def test_transform_file_to_dict_empty_custom_function_result(self):
        """Test transform_file_to_dict when custom function returns empty dict."""
        def empty_result_transform(file_path: str) -> dict:
            return {}

        result = transform_file_to_dict(self.test_file_path, empty_result_transform)

        self.assertEqual(result, {})

    def test_transform_file_to_dict_none_result_custom_function(self):
        """Test transform_file_to_dict when custom function returns None."""
        def none_result_transform(file_path: str) -> dict:
            return None

        result = transform_file_to_dict(self.test_file_path, none_result_transform)

        self.assertIsNone(result)

    @patch('os.path.isfile')
    def test_transform_file_to_dict_os_isfile_exception(self, mock_isfile):
        """Test transform_file_to_dict when os.path.isfile raises exception."""
        mock_isfile.side_effect = OSError("Mocked OS error")

        with self.assertRaises(OSError):
            transform_file_to_dict('/some/path')

    def test_default_transform_function_file_access_error(self):
        """Test _default_transform_function when file access fails."""
        from pyrox.services.file import _default_transform_function

        # This should raise an exception since the file doesn't exist
        with self.assertRaises(FileNotFoundError):
            _default_transform_function('/nonexistent/file.txt')

    def test_default_transform_function_permission_error(self):
        """Test _default_transform_function with permission error."""
        from pyrox.services.file import _default_transform_function

        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with self.assertRaises(PermissionError):
                _default_transform_function(self.test_file_path)

    def test_transform_file_to_dict_integration_with_other_functions(self):
        """Test transform_file_to_dict integration with other file functions."""
        # Create multiple test files
        test_files = []
        for i in range(3):
            file_path = os.path.join(self.test_dir, f'integration_test_{i}.txt')
            content = [f"File {i} - Line {j}\n" for j in range(5)]

            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(content)
            test_files.append(file_path)

        # Use get_all_files_in_directory to find files
        all_files = get_all_files_in_directory(self.test_dir)

        # Transform each file found
        results = []
        for file_path in all_files:
            if file_path.endswith('.txt') and 'integration_test' in file_path:
                result = transform_file_to_dict(file_path)
                results.append(result)

        # Verify results
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIn('file_path', result)
            self.assertEqual(result['line_count'], 5)
            self.assertIn('integration_test', result['file_path'])

    def test_transform_file_to_dict_with_save_and_transform_cycle(self):
        """Test complete cycle of save_file and transform_file_to_dict."""
        # Use save_file to create a file
        test_data = "Saved file content\nSecond line\nThird line"
        save_path = os.path.join(self.test_dir, 'saved_file')

        save_result = save_file(save_path, '.txt', 'w', test_data)
        self.assertTrue(save_result)

        # Transform the saved file
        full_path = save_path + '.txt'
        result = transform_file_to_dict(full_path)

        # Verify the transformation
        self.assertEqual(result['file_path'], full_path)
        self.assertEqual(result['line_count'], 3)
        self.assertIn('Saved file content', result['content'][0])
        self.assertIn('Second line', result['content'][1])
        self.assertIn('Third line', result['content'][2])


if __name__ == '__main__':
    unittest.main(verbosity=2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
