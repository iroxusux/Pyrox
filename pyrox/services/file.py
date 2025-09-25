"""File services module
    """
import os
import shutil
import tkinter as tk
from tkinter import filedialog
from typing import Optional


def get_all_files_in_directory(
    directory: str
) -> list[str]:
    """get all files in a directory

    Args:
        directory (str): directory to search

    Returns:
        list[str]: list of file paths

    Raises:
        FileNotFoundError: if the directory does not exist
    """
    if not os.path.isdir(directory):
        raise FileNotFoundError(f'Directory not found: {directory}')
    file_list = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_list.append(os.path.join(root, file))
    return file_list


def get_open_file(
        filetypes: list[tuple],
        title: Optional[str] = None
) -> str:
    """get a file using tkinter as ui

    Args:
        filetypes (list[tuple]): file type arguments e.g. ('.L5x', 'L5X Files')
        title (Optional[str]): title of the dialog

    Returns:
        str: file location
    """
    root = tk.Tk()
    root.withdraw()
    filename = filedialog.askopenfilename(
        filetypes=filetypes,
        title=title,
    )
    root.update()
    return filename


def get_save_file(filetypes: list[tuple]) -> str:
    """get a location to save a file to

    Args:
        filetypes (list[tuple]): file type arguments e.g. ('.L5x', 'L5X Files')

    Returns:
        str: file location
    """
    root = tk.Tk()
    root.withdraw()
    filename = filedialog.asksaveasfilename(confirmoverwrite=True,
                                            filetypes=filetypes)
    root.update()
    return filename


def get_save_location() -> str:
    """get directory to save files to

    Returns:
        str: directory
    """
    root = tk.Tk()
    root.withdraw()
    directory = filedialog.askdirectory()
    root.update()
    return directory


def is_file_readable(
    file_path: str
) -> bool:
    """Check if file exists and is readable.

    Args:
        file_path: Path to the file to check

    Returns:
        True if file exists and is readable, False otherwise
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return False

        # Check if it's actually a file (not a directory)
        if not os.path.isfile(file_path):
            return False

        # Check read permissions using os.access
        if not os.access(file_path, os.R_OK):
            return False

        # Try to actually open and read a small portion to verify readability
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1)  # Try to read just one character
            return True
        except (IOError, OSError, PermissionError, UnicodeDecodeError) as e:
            print(e)
            return False

    except Exception as e:
        print(e)
        return False


def remove_all_files(directory: str):
    """Removes all files within a specified directory, including files in subdirectories.
    """
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)


def save_file(
    file_path: str,
    file_extension: str,
    save_mode: str,
    file_data: str | bytes,
    encoding: Optional[str] = None
) -> bool:
    """save file to location

    Args:
        file_path (str): file path to save to
        file_extension (str): file extension to save as
        save_mode (str): save mode 'w' or 'a'
        file_data (str | bytes): data to save
        encoding (str, optional): encoding to use when saving a string. Defaults to None.

    Returns:
        bool: bool of success
    """
    if 'w' not in save_mode and 'a' not in save_mode:
        print('no save mode!')
        return False

    if not file_extension.startswith('.'):
        file_extension = f'.{file_extension}'

    if not file_path.endswith(file_extension):
        file_path = f'{file_path}{file_extension}'

    try:
        # This protects against encoding errors when writing bytes to a file
        if encoding is None and 'b' not in save_mode:
            encoding = 'utf-8'
        elif encoding is not None and 'b' in save_mode:
            encoding = None

        with open(file_path, save_mode, encoding=encoding) as f:
            f.write(file_data)
            f.close()
    except FileNotFoundError:
        print('file not found error thrown!')
        return False
    return True


def _default_transform_function(
    file_path: str
) -> dict:
    """default transform function that reads a file and returns its contents as a dictionary

    Args:
        file_path (str): file path to read

    Returns:
        dict: dictionary with file contents
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.readlines()
    return {
        'file_path': file_path,
        'line_count': len(content),
        'content_preview': content[:5],  # Preview first 5 lines
        'content': content
    }


def transform_file_to_dict(
    file_path: Optional[str],
    transform_function=_default_transform_function
) -> dict:
    """transform a file to a dictionary using a provided function

    Args:
        file_path (str): file path to transform
        transform_function (Callable): function to transform the file

    Returns:
        dict: transformed dictionary
    """
    if not isinstance(file_path, str) or not file_path:
        raise TypeError('file_path must be a non-empty string')
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f'File not found: {file_path}')
    return transform_function(file_path)
