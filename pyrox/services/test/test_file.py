"""Unit tests for file services."""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock, mock_open
import shutil

from pyrox.services.file import (
    get_all_files_in_directory,
    get_open_file,
    get_save_file,
    get_save_location,
    remove_all_files,
    save_file
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


if __name__ == '__main__':
    unittest.main(verbosity=2)
