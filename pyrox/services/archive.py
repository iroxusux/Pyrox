"""Archive services.
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Union, Optional, List
import py7zr
import os
import tempfile


def decompress_7zip_to_dict(archive_path: str) -> Dict[str, bytes]:
    """Decompress 7zip file into dictionary with filename -> content mapping.

    Args:
        archive_path: Path to the 7zip archive file

    Returns:
        Dictionary mapping filename to file content as bytes

    Raises:
        FileNotFoundError: If archive file doesn't exist
        py7zr.Bad7zFile: If archive is corrupted or invalid
    """
    archive_dict = {}

    # Create temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        with py7zr.SevenZipFile(archive_path, mode='r') as archive:
            # Extract all files to temporary directory
            archive.extractall(path=temp_dir)

        # Read all extracted files into memory
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Calculate relative path from temp_dir
                rel_path = os.path.relpath(file_path, temp_dir)
                # Convert Windows path separators to forward slashes
                archive_name = rel_path.replace(os.sep, '/')

                with open(file_path, 'rb') as f:
                    archive_dict[archive_name] = f.read()

    return archive_dict


def decompress_7zip_filtered(
    archive_path: str,
    extensions: Optional[List[str]] = None
) -> Dict[str, Union[str, bytes]]:
    """Decompress 7zip with filtering and text conversion.

    Args:
        archive_path: Path to the 7zip archive file
        extensions: List of file extensions to treat as text (e.g., ['.txt', '.xml'])
                   If None, uses default text extensions

    Returns:
        Dictionary mapping filename to content (str for text files, bytes for binary)

    Raises:
        FileNotFoundError: If archive file doesn't exist
        py7zr.Bad7zFile: If archive is corrupted or invalid
    """
    archive_dict = {}
    text_extensions = (
        {'.txt', '.xml', '.json', '.csv', '.log', '.md', '.ini', '.cfg', '.conf', '.yml', '.yaml'}
        if extensions is None
        else {ext.lower() for ext in extensions}
    )

    # Create temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        with py7zr.SevenZipFile(archive_path, mode='r') as archive:
            # Extract all files to temporary directory
            archive.extractall(path=temp_dir)

        # Read all extracted files into memory
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Calculate relative path from temp_dir
                rel_path = os.path.relpath(file_path, temp_dir)
                # Convert Windows path separators to forward slashes
                archive_name = rel_path.replace(os.sep, '/')

                # Read file content
                with open(file_path, 'rb') as f:
                    content = f.read()

                file_path_obj = Path(archive_name)

                # Convert text files to strings if extension matches
                if file_path_obj.suffix.lower() in text_extensions:
                    try:
                        # Try different encodings in order of preference
                        for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']:
                            try:
                                archive_dict[archive_name] = content.decode(encoding)
                                break
                            except UnicodeDecodeError:
                                continue
                        else:
                            # If all encodings fail, store as bytes
                            archive_dict[archive_name] = content
                    except Exception:
                        # Fallback to bytes if any other error occurs
                        archive_dict[archive_name] = content
                else:
                    # Store binary files as bytes
                    archive_dict[archive_name] = content

    return archive_dict


def compress_dict_to_7zip(
    data_dict: Dict[str, Union[str, bytes]],
    archive_path: str,
    compression_level: Optional[int] = None
) -> None:
    """Compress dictionary of files into 7zip archive.

    Args:
        data_dict: Dictionary mapping filename to content (str or bytes)
        archive_path: Output path for the 7zip archive
        compression_level: Compression level (0-9), None for default

    Raises:
        PermissionError: If unable to write to archive_path
        OSError: If file system error occurs
    """
    # Ensure output directory exists
    archive_dir = os.path.dirname(archive_path)
    if archive_dir:  # Only create if directory path is not empty
        os.makedirs(archive_dir, exist_ok=True)

    # Create temporary directory for files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Write all files to temporary directory
        for filename, content in data_dict.items():
            # Convert string content to bytes if necessary
            if isinstance(content, str):
                content_bytes = content.encode('utf-8')
            else:
                content_bytes = content

            # Create full file path
            file_path = os.path.join(temp_dir, filename)
            file_dir = os.path.dirname(file_path)

            # Create directories if needed
            if file_dir and not os.path.exists(file_dir):
                os.makedirs(file_dir, exist_ok=True)

            # Write file content
            with open(file_path, 'wb') as f:
                f.write(content_bytes)

        # Create 7zip archive from temporary directory
        with py7zr.SevenZipFile(archive_path, mode='w') as archive:
            for filename in data_dict.keys():
                file_path = os.path.join(temp_dir, filename)
                if os.path.exists(file_path):
                    archive.write(file_path, arcname=filename)


def extract_7zip_files(
    archive_path: str,
    extract_to: str,
    file_patterns: Optional[List[str]] = None
) -> List[str]:
    """Extract specific files from 7zip archive to directory.

    Args:
        archive_path: Path to the 7zip archive file
        extract_to: Directory to extract files to
        file_patterns: List of filename patterns to extract (None for all files)

    Returns:
        List of extracted file paths

    Raises:
        FileNotFoundError: If archive file doesn't exist
        py7zr.Bad7zFile: If archive is corrupted or invalid
    """
    extracted_files = []

    # Ensure extraction directory exists
    os.makedirs(extract_to, exist_ok=True)

    with py7zr.SevenZipFile(archive_path, mode='r') as archive:
        if file_patterns is None:
            # Extract all files
            archive.extractall(path=extract_to)

            # Get list of what was extracted by walking the directory
            for root, dirs, files in os.walk(extract_to):
                for file in files:
                    extracted_files.append(os.path.join(root, file))
        else:
            # For pattern matching, extract to temp directory first, then copy matching files
            import fnmatch

            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract all to temporary directory
                archive.extractall(path=temp_dir)

                # Find matching files and copy them
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        temp_file_path = os.path.join(root, file)
                        # Get relative path from temp directory
                        rel_path = os.path.relpath(temp_file_path, temp_dir)
                        archive_filename = rel_path.replace(os.sep, '/')

                        # Check if file matches any pattern
                        for pattern in file_patterns:
                            if fnmatch.fnmatch(archive_filename, pattern):
                                # Copy matching file to extraction directory
                                target_path = os.path.join(extract_to, rel_path)
                                target_dir = os.path.dirname(target_path)

                                if target_dir:
                                    os.makedirs(target_dir, exist_ok=True)

                                # Copy file
                                with open(temp_file_path, 'rb') as src, open(target_path, 'wb') as dst:
                                    dst.write(src.read())

                                extracted_files.append(target_path)
                                break

    return extracted_files


def list_7zip_contents(archive_path: str) -> List[Dict[str, Union[str, int, bool]]]:
    """List contents of 7zip archive.

    Args:
        archive_path: Path to the 7zip archive file

    Returns:
        List of dictionaries with file information (filename, size, is_dir, etc.)

    Raises:
        FileNotFoundError: If archive file doesn't exist
        py7zr.Bad7zFile: If archive is corrupted or invalid
    """
    contents = []

    with py7zr.SevenZipFile(archive_path, mode='r') as archive:
        for info in archive.list():
            file_info = {
                'filename': info.filename,
                'is_directory': info.is_directory,
                'file_size': getattr(info, 'uncompressed', 0),
                'compressed_size': getattr(info, 'compressed', 0),
                'crc': getattr(info, 'crc32', None),
                'creation_time': getattr(info, 'creationtime', None),
                'last_write_time': getattr(info, 'last_write_time', None),
            }
            contents.append(file_info)

    return contents


def compress_directory_to_7zip(
    directory_path: str,
    archive_path: str,
    compression_level: Optional[int] = None,
    exclude_patterns: Optional[List[str]] = None
) -> None:
    """Compress entire directory to 7zip archive.

    Args:
        directory_path: Path to directory to compress
        archive_path: Output path for the 7zip archive
        compression_level: Compression level (0-9), None for default
        exclude_patterns: List of filename patterns to exclude

    Raises:
        FileNotFoundError: If directory doesn't exist
        PermissionError: If unable to read files or write archive
    """
    import fnmatch

    if not os.path.isdir(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")

    # Ensure output directory exists
    archive_dir = os.path.dirname(archive_path)
    if archive_dir:
        os.makedirs(archive_dir, exist_ok=True)

    exclude_patterns = exclude_patterns or []

    with py7zr.SevenZipFile(archive_path, mode='w') as archive:
        for root, dirs, files in os.walk(directory_path):
            # Calculate relative path from base directory
            rel_root = os.path.relpath(root, directory_path)

            for file in files:
                file_path = os.path.join(root, file)

                # Calculate archive path (relative to base directory)
                if rel_root == '.':
                    archive_name = file
                else:
                    archive_name = os.path.join(rel_root, file).replace('\\', '/')

                # Check if file should be excluded
                should_exclude = False
                for pattern in exclude_patterns:
                    if fnmatch.fnmatch(file, pattern) or fnmatch.fnmatch(archive_name, pattern):
                        should_exclude = True
                        break

                if not should_exclude:
                    archive.write(file_path, arcname=archive_name)


def is_7zip_file(file_path: str) -> bool:
    """Check if file is a valid 7zip archive.

    Args:
        file_path: Path to file to check

    Returns:
        True if file is a valid 7zip archive, False otherwise
    """
    try:
        with py7zr.SevenZipFile(file_path, mode='r') as archive:
            # Try to list contents - if this succeeds, it's a valid archive
            list(archive.list())
            return True
    except (py7zr.Bad7zFile, FileNotFoundError, PermissionError):
        return False
    except Exception:
        # Catch any other unexpected errors
        return False


def extract_7zip_file_to_memory(archive_path: str, target_file: str) -> Optional[bytes]:
    """Extract a single specific file from 7zip archive to memory.

    Args:
        archive_path: Path to the 7zip archive file
        target_file: Filename to extract from the archive

    Returns:
        File content as bytes, or None if file not found

    Raises:
        FileNotFoundError: If archive file doesn't exist
        py7zr.Bad7zFile: If archive is corrupted or invalid
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        with py7zr.SevenZipFile(archive_path, mode='r') as archive:
            # Extract all files to temporary directory
            archive.extractall(path=temp_dir)

        # Look for the target file
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Calculate relative path from temp_dir
                rel_path = os.path.relpath(file_path, temp_dir)
                # Convert Windows path separators to forward slashes
                archive_name = rel_path.replace(os.sep, '/')

                if archive_name == target_file:
                    with open(file_path, 'rb') as f:
                        return f.read()

    return None


def get_7zip_file_list(archive_path: str) -> List[str]:
    """Get list of filenames in 7zip archive (excluding directories).

    Args:
        archive_path: Path to the 7zip archive file

    Returns:
        List of filenames in the archive

    Raises:
        FileNotFoundError: If archive file doesn't exist
        py7zr.Bad7zFile: If archive is corrupted or invalid
    """
    filenames = []

    with py7zr.SevenZipFile(archive_path, mode='r') as archive:
        for info in archive.list():
            if not info.is_directory:
                filenames.append(info.filename)

    return filenames
