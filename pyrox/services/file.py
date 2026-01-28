"""File services module
    """
import os
import platformdirs
import shutil
import tkinter as tk
from tkinter import filedialog
from typing import Optional
from io import TextIOWrapper

from .env import EnvManager
from pyrox.interfaces import EnvironmentKeys


class PlatformDirectoryService:
    """Platform Directory Service for managing platform-specific directories.

    Attributes:
        app_name: The name of the application.
        author_name: The name of the author.
        user_cache: The path to the user cache directory for the application.
        user_config: The path to the user config directory for the application.
        user_data: The path to the user data directory for the application.
        user_documents: The path to the user documents directory for the application.
        user_downloads: The path to the user downloads directory for the application.
        user_log: The path to the user log directory for the application.
        user_log_file: The path to the application's log file.
    """

    _log_file: Optional[TextIOWrapper] = None

    def __init__(
        self,
    ) -> None:
        raise TypeError("PlatformDirectoryService is a static class and cannot be instantiated")

    @classmethod
    def all_directories(cls) -> dict:
        """All directories for this service manager.

        Returns:
            dict: Dictionary of all directories for this service manager.
        """
        return {
            'user_cache': cls.get_user_cache(),
            'user_config': cls.get_user_config(),
            'user_data': cls.get_user_data(),
            'user_log': cls.get_user_log()
        }

    @classmethod
    def get_app_name(cls) -> str:
        """Application name from the application's .env file.

        Returns:
            str: The name of the application.
        """
        return EnvManager.get(
            EnvironmentKeys.core.APP_NAME,
            'Pyrox Application',
            str
        )

    @classmethod
    def get_app_runtime_info_file(cls) -> str:
        """Application runtime info file path.

        This is the file where the application will store runtime information.

        Returns:
            str: The path to the application's runtime info file.
        """
        return os.path.join(cls.get_user_data(), f'{cls.get_app_name()}_runtime_info.json')

    @classmethod
    def get_author_name(cls) -> str:
        """Author name supplied to this service class.

        Returns:
            str: The name of the author.
        """
        return EnvManager.get(
            EnvironmentKeys.core.APP_AUTHOR,
            'Pyrox Author',
            str
        )

    @classmethod
    def get_user_cache(cls) -> str:
        """User cache directory.

        Returns:
            str: The path to the user cache directory for the application.
        """
        return platformdirs.user_cache_dir(cls.get_app_name(), cls.get_author_name(), ensure_exists=True)

    @classmethod
    def get_user_config(cls) -> str:
        """User config directory.

        Returns:
            str: The path to the user config directory for the application.
        """
        return platformdirs.user_config_dir(cls.get_app_name(), cls.get_author_name(), ensure_exists=True)

    @classmethod
    def get_user_data(cls) -> str:
        """User data directory.

        Example: 'C:/Users/JohnSmith/AppData/Local/JSmithEnterprises/MyApplication'

        Returns:
            str: The path to the user data directory for the application.
        """
        return platformdirs.user_data_dir(cls.get_app_name(), cls.get_author_name(), ensure_exists=True)

    @classmethod
    def get_user_documents(cls) -> str:
        """User documents directory.

        Returns:
            str: The path to the user documents directory.
        """
        return platformdirs.user_documents_dir()

    @classmethod
    def get_user_downloads(cls) -> str:
        """User downloads directory.

        Returns:
            str: The path to the user downloads directory.
        """
        return platformdirs.user_downloads_dir()

    @classmethod
    def get_user_log(cls) -> str:
        """User log directory.

        Returns:
            str: The path to the user log directory for the application.
        """
        return platformdirs.user_log_dir(cls.get_app_name(), cls.get_author_name())

    @classmethod
    def get_user_log_file(cls) -> str:
        """User log file path.

        This is the file where the application will log messages.

        Returns:
            str: The path to the application's log file.
        """
        return os.path.join(cls.get_user_log(), f'{cls.get_app_name()}.log')

    @classmethod
    def build_directory(
        cls,
        as_refresh: bool = False
    ) -> None:
        """Build the directory for the parent application.

        Uses the supplied name for directory naming.

        Args:
            as_refresh: If True, the directories will be refreshed, removing all files in them.

        Raises:
            OSError: If the directory creation fails.
        """
        for dir_path in cls.all_directories().values():
            if not os.path.isdir(dir_path):
                try:
                    os.makedirs(dir_path, exist_ok=True)
                except OSError as e:
                    raise OSError(f'Failed to create directory {dir_path}: {e}') from e
            else:
                if as_refresh:
                    try:
                        remove_all_files(dir_path)
                    except OSError as e:
                        raise OSError(f'Failed to refresh directory {dir_path}: {e}') from e

    @classmethod
    def get_log_file_stream(cls) -> TextIOWrapper:
        """Get a SimpleStream for the user log file.

        Returns:
            TextIOWrapper: A stream object for the user log file.
        """
        if not cls._log_file:
            cls._log_file = open(cls.get_user_log_file(), 'a', encoding='utf-8')
        return cls._log_file


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


def save_dict_to_json_file(
    file_path: str,
    data: dict,
    encoding: Optional[str] = 'utf-8'
) -> bool:
    """save a dictionary to a json file

    Args:
        file_path (str): file path to save to
        data (dict): dictionary to save
        encoding (str, optional): encoding to use when saving. Defaults to 'utf-8'.

    Returns:
        bool: bool of success
    """
    import json
    try:
        with open(file_path, 'w', encoding=encoding) as f:
            json.dump(data, f, indent=4)
            f.close()
    except FileNotFoundError:
        print('file not found error thrown!')
        return False
    return True


def save_file(
    file_path: str,
    file_extension: str,
    save_mode: str = 'w',
    file_data: str | bytes = '',
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

    # Only add extension if non-empty
    if file_extension:
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
