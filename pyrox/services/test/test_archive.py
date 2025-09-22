"""Unit tests for archive services."""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock, mock_open
import shutil
import io

try:
    import py7zr
    PY7ZR_AVAILABLE = True
except ImportError:
    PY7ZR_AVAILABLE = False

from pyrox.services.archive import (
    decompress_7zip_to_dict,
    decompress_7zip_filtered,
    compress_dict_to_7zip,
    extract_7zip_files,
    list_7zip_contents,
    compress_directory_to_7zip,
    is_7zip_file,
    extract_7zip_file_to_memory,
    get_7zip_file_list
)


class TestDecompress7zipToDict(unittest.TestCase):
    """Test cases for decompress_7zip_to_dict function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_archive_path = os.path.join(self.test_dir, 'test.7z')

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @unittest.skipUnless(PY7ZR_AVAILABLE, "py7zr not available")
    @patch('tempfile.TemporaryDirectory')
    @patch('py7zr.SevenZipFile')
    @patch('os.walk')
    @patch('builtins.open', new_callable=mock_open)
    def test_decompress_basic_files(self, mock_file, mock_walk, mock_7zip_class, mock_temp_dir):
        """Test basic decompression of 7zip files."""
        # Setup mock temporary directory
        mock_temp_dir_obj = MagicMock()
        mock_temp_dir_obj.__enter__ = MagicMock(return_value='/tmp/test')
        mock_temp_dir_obj.__exit__ = MagicMock(return_value=None)
        mock_temp_dir.return_value = mock_temp_dir_obj

        # Setup mock archive
        mock_archive = MagicMock()
        mock_7zip_class.return_value = mock_archive
        mock_archive.__enter__ = MagicMock(return_value=mock_archive)
        mock_archive.__exit__ = MagicMock(return_value=None)

        # Mock os.walk to return test files
        mock_walk.return_value = [
            ('/tmp/test', [], ['file1.txt', 'file2.log'])
        ]

        # Mock file contents
        file_contents = {
            '/tmp/test/file1.txt': b'This is file 1 content',
            '/tmp/test/file2.log': b'This is file 2 content'
        }

        def mock_open_side_effect(filename, mode='r', **kwargs):
            mock_file_obj = mock_open(read_data=file_contents.get(filename, b''))()
            return mock_file_obj

        mock_file.side_effect = mock_open_side_effect

        # Mock os.path.relpath
        with patch('os.path.relpath') as mock_relpath:
            mock_relpath.side_effect = lambda path, start: {
                '/tmp/test/file1.txt': 'file1.txt',
                '/tmp/test/file2.log': 'file2.log'
            }.get(path, os.path.basename(path))

            result = decompress_7zip_to_dict(self.test_archive_path)

        # Verify results
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 2)
        self.assertIn('file1.txt', result)
        self.assertIn('file2.log', result)

        mock_7zip_class.assert_called_once_with(self.test_archive_path, mode='r')
        mock_archive.extractall.assert_called_once_with(path='/tmp/test')

    @unittest.skipUnless(PY7ZR_AVAILABLE, "py7zr not available")
    @patch('tempfile.TemporaryDirectory')
    @patch('py7zr.SevenZipFile')
    @patch('os.walk')
    def test_decompress_empty_archive(self, mock_walk, mock_7zip_class, mock_temp_dir):
        """Test decompression of empty 7zip archive."""
        # Setup mock temporary directory
        mock_temp_dir_obj = MagicMock()
        mock_temp_dir_obj.__enter__ = MagicMock(return_value='/tmp/test')
        mock_temp_dir_obj.__exit__ = MagicMock(return_value=None)
        mock_temp_dir.return_value = mock_temp_dir_obj

        mock_archive = MagicMock()
        mock_7zip_class.return_value = mock_archive
        mock_archive.__enter__ = MagicMock(return_value=mock_archive)
        mock_archive.__exit__ = MagicMock(return_value=None)

        # Mock empty directory
        mock_walk.return_value = [('/tmp/test', [], [])]

        result = decompress_7zip_to_dict(self.test_archive_path)

        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)

    @unittest.skipUnless(PY7ZR_AVAILABLE, "py7zr not available")
    @patch('py7zr.SevenZipFile')
    def test_decompress_file_not_found_error(self, mock_7zip_class):
        """Test handling of file not found error."""
        mock_7zip_class.side_effect = FileNotFoundError("Archive not found")

        with self.assertRaises(FileNotFoundError):
            decompress_7zip_to_dict(self.test_archive_path)

    @unittest.skipUnless(PY7ZR_AVAILABLE, "py7zr not available")
    @patch('py7zr.SevenZipFile')
    def test_decompress_corrupted_archive_error(self, mock_7zip_class):
        """Test handling of corrupted archive error."""
        if PY7ZR_AVAILABLE:
            mock_7zip_class.side_effect = py7zr.Bad7zFile("Corrupted archive")
            with self.assertRaises(py7zr.Bad7zFile):
                decompress_7zip_to_dict(self.test_archive_path)


class TestDecompress7zipFiltered(unittest.TestCase):
    """Test cases for decompress_7zip_filtered function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_archive_path = os.path.join(self.test_dir, 'test.7z')

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @unittest.skipUnless(PY7ZR_AVAILABLE, "py7zr not available")
    @patch('tempfile.TemporaryDirectory')
    @patch('py7zr.SevenZipFile')
    @patch('os.walk')
    @patch('builtins.open', new_callable=mock_open)
    def test_filtered_text_conversion(self, mock_file, mock_walk, mock_7zip_class, mock_temp_dir):
        """Test filtering and text conversion of files."""
        # Setup mock temporary directory
        mock_temp_dir_obj = MagicMock()
        mock_temp_dir_obj.__enter__ = MagicMock(return_value='/tmp/test')
        mock_temp_dir_obj.__exit__ = MagicMock(return_value=None)
        mock_temp_dir.return_value = mock_temp_dir_obj

        mock_archive = MagicMock()
        mock_7zip_class.return_value = mock_archive
        mock_archive.__enter__ = MagicMock(return_value=mock_archive)
        mock_archive.__exit__ = MagicMock(return_value=None)

        # Mock files
        mock_walk.return_value = [
            ('/tmp/test', [], ['text_file.txt', 'binary_file.exe'])
        ]

        # Mock file contents
        file_contents = {
            '/tmp/test/text_file.txt': b'This is plain text',
            '/tmp/test/binary_file.exe': b'\x4d\x5a\x90\x00'
        }

        def mock_open_side_effect(filename, mode='r', **kwargs):
            # replace backslashes with forward slashes for consistency
            filename = filename.replace('\\', '/')
            mock_file_obj = mock_open(read_data=file_contents.get(filename, b''))()
            return mock_file_obj

        mock_file.side_effect = mock_open_side_effect

        with patch('os.path.relpath') as mock_relpath:
            mock_relpath.side_effect = lambda path, start: {
                '/tmp/test/text_file.txt': 'text_file.txt',
                '/tmp/test/binary_file.exe': 'binary_file.exe'
            }.get(path, os.path.basename(path))

            result = decompress_7zip_filtered(self.test_archive_path)

        self.assertEqual(len(result), 2)

        # Check that text files were converted to strings
        self.assertIsInstance(result['text_file.txt'], str)
        self.assertEqual(result['text_file.txt'], "This is plain text")

        # Check that binary files remained as bytes
        self.assertIsInstance(result['binary_file.exe'], bytes)
        self.assertEqual(result['binary_file.exe'], b'\x4d\x5a\x90\x00')

    @unittest.skipUnless(PY7ZR_AVAILABLE, "py7zr not available")
    @patch('tempfile.TemporaryDirectory')
    @patch('py7zr.SevenZipFile')
    @patch('os.walk')
    @patch('builtins.open', new_callable=mock_open)
    def test_filtered_custom_extensions(self, mock_file, mock_walk, mock_7zip_class, mock_temp_dir):
        """Test filtering with custom file extensions."""
        mock_temp_dir_obj = MagicMock()
        mock_temp_dir_obj.__enter__ = MagicMock(return_value='/tmp/test')
        mock_temp_dir_obj.__exit__ = MagicMock(return_value=None)
        mock_temp_dir.return_value = mock_temp_dir_obj

        mock_archive = MagicMock()
        mock_7zip_class.return_value = mock_archive
        mock_archive.__enter__ = MagicMock(return_value=mock_archive)
        mock_archive.__exit__ = MagicMock(return_value=None)

        mock_walk.return_value = [
            ('/tmp/test', [], ['script.py', 'data.bin'])
        ]

        file_contents = {
            '/tmp/test/script.py': b"print('Hello, World!')",
            '/tmp/test/data.bin': b'\x00\x01\x02\x03'
        }

        def mock_open_side_effect(filename, mode='r', **kwargs):
            # replace backslashes with forward slashes for consistency
            filename = filename.replace('\\', '/')
            mock_file_obj = mock_open(read_data=file_contents.get(filename, b''))()
            return mock_file_obj

        mock_file.side_effect = mock_open_side_effect

        with patch('os.path.relpath') as mock_relpath:
            mock_relpath.side_effect = lambda path, start: {
                '/tmp/test/script.py': 'script.py',
                '/tmp/test/data.bin': 'data.bin'
            }.get(path, os.path.basename(path))

            custom_extensions = ['.py']
            result = decompress_7zip_filtered(self.test_archive_path, extensions=custom_extensions)

        # Check that .py files were converted to strings
        self.assertIsInstance(result['script.py'], str)
        self.assertEqual(result['script.py'], "print('Hello, World!')")

        # Binary file should remain as bytes
        self.assertIsInstance(result['data.bin'], bytes)
        self.assertEqual(result['data.bin'], b'\x00\x01\x02\x03')


class TestCompressDictTo7zip(unittest.TestCase):
    """Test cases for compress_dict_to_7zip function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_archive_path = os.path.join(self.test_dir, 'test_output.7z')

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @unittest.skipUnless(PY7ZR_AVAILABLE, "py7zr not available")
    @patch('tempfile.TemporaryDirectory')
    @patch('py7zr.SevenZipFile')
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_compress_dict_basic(self, mock_file, mock_exists, mock_makedirs, mock_7zip_class, mock_temp_dir):
        """Test basic dictionary compression."""
        mock_temp_dir_obj = MagicMock()
        mock_temp_dir_obj.__enter__ = MagicMock(return_value='/tmp/compress')
        mock_temp_dir_obj.__exit__ = MagicMock(return_value=None)
        mock_temp_dir.return_value = mock_temp_dir_obj

        mock_archive = MagicMock()
        mock_7zip_class.return_value = mock_archive
        mock_archive.__enter__ = MagicMock(return_value=mock_archive)
        mock_archive.__exit__ = MagicMock(return_value=None)

        mock_exists.return_value = True

        test_dict = {
            'file1.txt': 'Hello, World!',
            'file2.bin': b'\x00\x01\x02\x03'
        }

        compress_dict_to_7zip(test_dict, self.test_archive_path)

        # Verify archive was opened correctly
        mock_7zip_class.assert_called_once_with(self.test_archive_path, mode='w')

        # Verify write was called for each file
        self.assertEqual(mock_archive.write.call_count, 2)

    @unittest.skipUnless(PY7ZR_AVAILABLE, "py7zr not available")
    @patch('tempfile.TemporaryDirectory')
    @patch('py7zr.SevenZipFile')
    @patch('os.makedirs')
    def test_compress_empty_dict(self, mock_makedirs, mock_7zip_class, mock_temp_dir):
        """Test compressing empty dictionary."""
        mock_temp_dir_obj = MagicMock()
        mock_temp_dir_obj.__enter__ = MagicMock(return_value='/tmp/compress')
        mock_temp_dir_obj.__exit__ = MagicMock(return_value=None)
        mock_temp_dir.return_value = mock_temp_dir_obj

        mock_archive = MagicMock()
        mock_7zip_class.return_value = mock_archive
        mock_archive.__enter__ = MagicMock(return_value=mock_archive)
        mock_archive.__exit__ = MagicMock(return_value=None)

        compress_dict_to_7zip({}, self.test_archive_path)

        mock_archive.write.assert_not_called()


class TestExtract7zipFiles(unittest.TestCase):
    """Test cases for extract_7zip_files function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_archive_path = os.path.join(self.test_dir, 'test.7z')
        self.extract_dir = os.path.join(self.test_dir, 'extracted')

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @unittest.skipUnless(PY7ZR_AVAILABLE, "py7zr not available")
    @patch('py7zr.SevenZipFile')
    @patch('os.makedirs')
    @patch('os.walk')
    def test_extract_all_files(self, mock_walk, mock_makedirs, mock_7zip_class):
        """Test extracting all files from archive."""
        mock_archive = MagicMock()
        mock_7zip_class.return_value = mock_archive
        mock_archive.__enter__ = MagicMock(return_value=mock_archive)
        mock_archive.__exit__ = MagicMock(return_value=None)

        # Mock os.walk to return extracted files
        mock_walk.return_value = [
            (self.extract_dir, [], ['file1.txt', 'file2.log'])
        ]

        result = extract_7zip_files(self.test_archive_path, self.extract_dir)

        mock_archive.extractall.assert_called_once_with(path=self.extract_dir)
        self.assertEqual(len(result), 2)
        self.assertIn(os.path.join(self.extract_dir, 'file1.txt'), result)
        self.assertIn(os.path.join(self.extract_dir, 'file2.log'), result)

    @unittest.skipUnless(PY7ZR_AVAILABLE, "py7zr not available")
    @patch('tempfile.TemporaryDirectory')
    @patch('py7zr.SevenZipFile')
    @patch('os.makedirs')
    @patch('os.walk')
    @patch('fnmatch.fnmatch')
    @patch('builtins.open', new_callable=mock_open)
    def test_extract_filtered_files(self, mock_file, mock_fnmatch, mock_walk, mock_makedirs, mock_7zip_class, mock_temp_dir):
        """Test extracting files with patterns."""
        mock_temp_dir_obj = MagicMock()
        mock_temp_dir_obj.__enter__ = MagicMock(return_value='/tmp/extract')
        mock_temp_dir_obj.__exit__ = MagicMock(return_value=None)
        mock_temp_dir.return_value = mock_temp_dir_obj

        mock_archive = MagicMock()
        mock_7zip_class.return_value = mock_archive
        mock_archive.__enter__ = MagicMock(return_value=mock_archive)
        mock_archive.__exit__ = MagicMock(return_value=None)

        # Mock files in temp directory
        mock_walk.return_value = [
            ('/tmp/extract', [], ['file1.txt', 'file2.log'])
        ]

        # Mock fnmatch to only match .txt files
        def fnmatch_side_effect(filename, pattern):
            if pattern == '*.txt':
                return filename.endswith('.txt')
            return False

        mock_fnmatch.side_effect = fnmatch_side_effect

        with patch('os.path.relpath') as mock_relpath, \
                patch('os.path.exists') as mock_exists:

            mock_relpath.side_effect = lambda path, start: os.path.basename(path)
            mock_exists.return_value = False  # No target directory initially

            result = extract_7zip_files(self.test_archive_path, self.extract_dir, ['*.txt'])

        # Should extract 1 .txt file
        self.assertEqual(len(result), 1)
        self.assertIn(os.path.join(self.extract_dir, 'file1.txt'), result)


class TestList7zipContents(unittest.TestCase):
    """Test cases for list_7zip_contents function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_archive_path = os.path.join(self.test_dir, 'test.7z')

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @unittest.skipUnless(PY7ZR_AVAILABLE, "py7zr not available")
    @patch('py7zr.SevenZipFile')
    def test_list_contents(self, mock_7zip_class):
        """Test listing archive contents."""
        mock_archive = MagicMock()
        mock_7zip_class.return_value = mock_archive
        mock_archive.__enter__ = MagicMock(return_value=mock_archive)
        mock_archive.__exit__ = MagicMock(return_value=None)

        # Mock file info objects
        mock_info1 = MagicMock()
        mock_info1.filename = 'file1.txt'
        mock_info1.is_directory = False
        mock_info1.uncompressed = 1000
        mock_info1.compressed = 500
        mock_info1.crc32 = 0x12345678

        mock_info2 = MagicMock()
        mock_info2.filename = 'folder/'
        mock_info2.is_directory = True
        mock_info2.uncompressed = 0
        mock_info2.compressed = 0

        mock_archive.list.return_value = [mock_info1, mock_info2]

        result = list_7zip_contents(self.test_archive_path)

        self.assertEqual(len(result), 2)

        # Check file info
        file_info = result[0]
        self.assertEqual(file_info['filename'], 'file1.txt')
        self.assertFalse(file_info['is_directory'])
        self.assertEqual(file_info['file_size'], 1000)
        self.assertEqual(file_info['compressed_size'], 500)
        self.assertEqual(file_info['crc'], 0x12345678)

        # Check directory info
        dir_info = result[1]
        self.assertEqual(dir_info['filename'], 'folder/')
        self.assertTrue(dir_info['is_directory'])


class TestIs7zipFile(unittest.TestCase):
    """Test cases for is_7zip_file function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @unittest.skipUnless(PY7ZR_AVAILABLE, "py7zr not available")
    @patch('py7zr.SevenZipFile')
    def test_valid_7zip_file(self, mock_7zip_class):
        """Test valid 7zip file detection."""
        mock_archive = MagicMock()
        mock_7zip_class.return_value = mock_archive
        mock_archive.__enter__ = MagicMock(return_value=mock_archive)
        mock_archive.__exit__ = MagicMock(return_value=None)
        mock_archive.list.return_value = []

        test_file = os.path.join(self.test_dir, 'test.7z')

        result = is_7zip_file(test_file)

        self.assertTrue(result)

    @unittest.skipUnless(PY7ZR_AVAILABLE, "py7zr not available")
    @patch('py7zr.SevenZipFile')
    def test_invalid_7zip_file(self, mock_7zip_class):
        """Test invalid 7zip file detection."""
        mock_7zip_class.side_effect = py7zr.Bad7zFile("Invalid archive")

        test_file = os.path.join(self.test_dir, 'invalid.7z')

        result = is_7zip_file(test_file)

        self.assertFalse(result)


class TestExtract7zipFileToMemory(unittest.TestCase):
    """Test cases for extract_7zip_file_to_memory function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_archive_path = os.path.join(self.test_dir, 'test.7z')

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @unittest.skipUnless(PY7ZR_AVAILABLE, "py7zr not available")
    @patch('tempfile.TemporaryDirectory')
    @patch('py7zr.SevenZipFile')
    @patch('os.walk')
    @patch('builtins.open', new_callable=mock_open)
    def test_extract_existing_file(self, mock_file, mock_walk, mock_7zip_class, mock_temp_dir):
        """Test extracting existing file to memory."""
        mock_temp_dir_obj = MagicMock()
        mock_temp_dir_obj.__enter__ = MagicMock(return_value='/tmp/extract')
        mock_temp_dir_obj.__exit__ = MagicMock(return_value=None)
        mock_temp_dir.return_value = mock_temp_dir_obj

        mock_archive = MagicMock()
        mock_7zip_class.return_value = mock_archive
        mock_archive.__enter__ = MagicMock(return_value=mock_archive)
        mock_archive.__exit__ = MagicMock(return_value=None)

        target_content = b"Target file content"

        mock_walk.return_value = [
            ('/tmp/extract', [], ['target.txt', 'other.txt'])
        ]

        file_contents = {
            '/tmp/extract/target.txt': target_content,
            '/tmp/extract/other.txt': b"Other content"
        }

        def mock_open_side_effect(filename, mode='r', **kwargs):
            # replace backslashes with forward slashes for consistency
            filename = filename.replace('\\', '/')
            mock_file_obj = mock_open(read_data=file_contents.get(filename, b''))()
            return mock_file_obj

        mock_file.side_effect = mock_open_side_effect

        with patch('os.path.relpath') as mock_relpath:
            mock_relpath.side_effect = lambda path, start: {
                '/tmp/extract/target.txt': 'target.txt',
                '/tmp/extract/other.txt': 'other.txt'
            }.get(path, os.path.basename(path))

            result = extract_7zip_file_to_memory(self.test_archive_path, 'target.txt')

        self.assertEqual(result, target_content)

    @unittest.skipUnless(PY7ZR_AVAILABLE, "py7zr not available")
    @patch('tempfile.TemporaryDirectory')
    @patch('py7zr.SevenZipFile')
    @patch('os.walk')
    def test_extract_nonexistent_file(self, mock_walk, mock_7zip_class, mock_temp_dir):
        """Test extracting nonexistent file."""
        mock_temp_dir_obj = MagicMock()
        mock_temp_dir_obj.__enter__ = MagicMock(return_value='/tmp/extract')
        mock_temp_dir_obj.__exit__ = MagicMock(return_value=None)
        mock_temp_dir.return_value = mock_temp_dir_obj

        mock_archive = MagicMock()
        mock_7zip_class.return_value = mock_archive
        mock_archive.__enter__ = MagicMock(return_value=mock_archive)
        mock_archive.__exit__ = MagicMock(return_value=None)

        mock_walk.return_value = [('/tmp/extract', [], ['other.txt'])]

        with patch('os.path.relpath') as mock_relpath:
            mock_relpath.return_value = 'other.txt'
            result = extract_7zip_file_to_memory(self.test_archive_path, 'nonexistent.txt')

        self.assertIsNone(result)


class TestGet7zipFileList(unittest.TestCase):
    """Test cases for get_7zip_file_list function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_archive_path = os.path.join(self.test_dir, 'test.7z')

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @unittest.skipUnless(PY7ZR_AVAILABLE, "py7zr not available")
    @patch('py7zr.SevenZipFile')
    def test_get_file_list(self, mock_7zip_class):
        """Test getting list of files from archive."""
        mock_archive = MagicMock()
        mock_7zip_class.return_value = mock_archive
        mock_archive.__enter__ = MagicMock(return_value=mock_archive)
        mock_archive.__exit__ = MagicMock(return_value=None)

        # Mock file info objects
        mock_info1 = MagicMock()
        mock_info1.filename = 'file1.txt'
        mock_info1.is_directory = False

        mock_info2 = MagicMock()
        mock_info2.filename = 'folder/'
        mock_info2.is_directory = True

        mock_info3 = MagicMock()
        mock_info3.filename = 'folder/file2.log'
        mock_info3.is_directory = False

        mock_archive.list.return_value = [mock_info1, mock_info2, mock_info3]

        result = get_7zip_file_list(self.test_archive_path)

        # Should only include files, not directories
        self.assertEqual(len(result), 2)
        self.assertIn('file1.txt', result)
        self.assertIn('folder/file2.log', result)
        self.assertNotIn('folder/', result)


class TestArchiveRealIntegration(unittest.TestCase):
    """Real integration tests using actual py7zr (only if available)."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @unittest.skipUnless(PY7ZR_AVAILABLE, "py7zr not available")
    def test_create_and_extract_real_archive(self):
        """Test creating and extracting a real 7zip archive."""
        # Create test files
        test_files = {
            'test1.txt': "Hello, World!",
            'test2.xml': "<root><item>value</item></root>",
            'binary.dat': bytes(range(10)),
        }

        # Create temporary files
        temp_files = []
        for filename, content in test_files.items():
            file_path = os.path.join(self.test_dir, filename)
            mode = 'w' if isinstance(content, str) else 'wb'
            encoding = 'utf-8' if isinstance(content, str) else None

            with open(file_path, mode, encoding=encoding) as f:
                f.write(content)
            temp_files.append(file_path)

        # Create 7zip archive
        archive_path = os.path.join(self.test_dir, 'test.7z')
        with py7zr.SevenZipFile(archive_path, 'w') as archive:
            for file_path in temp_files:
                archive.write(file_path, arcname=os.path.basename(file_path))

        # Test basic extraction
        result_dict = decompress_7zip_to_dict(archive_path)

        self.assertEqual(len(result_dict), 3)
        self.assertIn('test1.txt', result_dict)
        self.assertIn('test2.xml', result_dict)
        self.assertIn('binary.dat', result_dict)

        # Test filtered extraction
        result_filtered = decompress_7zip_filtered(archive_path)

        self.assertEqual(len(result_filtered), 3)

        # Text files should be strings
        self.assertIsInstance(result_filtered['test1.txt'], str)
        self.assertEqual(result_filtered['test1.txt'], "Hello, World!")

        # Binary file should remain bytes
        self.assertIsInstance(result_filtered['binary.dat'], bytes)
        self.assertEqual(result_filtered['binary.dat'], bytes(range(10)))

        # Test other functions
        self.assertTrue(is_7zip_file(archive_path))

        contents = list_7zip_contents(archive_path)
        self.assertEqual(len(contents), 3)

        file_list = get_7zip_file_list(archive_path)
        self.assertEqual(len(file_list), 3)

        single_file = extract_7zip_file_to_memory(archive_path, 'test1.txt')
        self.assertEqual(single_file, b"Hello, World!")


class TestArchiveErrorHandling(unittest.TestCase):
    """Test error handling scenarios for archive services."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_archive_path = os.path.join(self.test_dir, 'test.7z')

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @unittest.skipUnless(PY7ZR_AVAILABLE, "py7zr not available")
    def test_nonexistent_archive_file(self):
        """Test handling of nonexistent archive file."""
        nonexistent_path = os.path.join(self.test_dir, 'nonexistent.7z')

        with self.assertRaises(FileNotFoundError):
            decompress_7zip_to_dict(nonexistent_path)

        with self.assertRaises(FileNotFoundError):
            decompress_7zip_filtered(nonexistent_path)

        with self.assertRaises(FileNotFoundError):
            list_7zip_contents(nonexistent_path)

        with self.assertRaises(FileNotFoundError):
            get_7zip_file_list(nonexistent_path)

    @unittest.skipUnless(PY7ZR_AVAILABLE, "py7zr not available")
    @patch('py7zr.SevenZipFile')
    def test_permission_error(self, mock_7zip_class):
        """Test handling of permission errors."""
        mock_7zip_class.side_effect = PermissionError("Access denied")

        with self.assertRaises(PermissionError):
            decompress_7zip_to_dict(self.test_archive_path)

        with self.assertRaises(PermissionError):
            decompress_7zip_filtered(self.test_archive_path)


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
