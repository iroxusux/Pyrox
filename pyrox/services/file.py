"""File services module
    """
import os
import shutil
import tkinter as tk
from tkinter import filedialog


def get_open_file(filetypes: list[tuple]) -> str:
    """get a file using tkinter as ui

    Returns:
        str: file location
    """
    root = tk.Tk()
    root.withdraw()
    filename = filedialog.askopenfilename(filetypes=filetypes)
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


def remove_all_files(directory: str):
    """Removes all files within a specified directory, including files in subdirectories.
    """
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)


def save_file(file_path: str,
              file_extension: str,
              save_mode: str,
              file_data: str | bytes) -> bool:
    """save file to location

    Args:
        file_path (str): file path to save to
        file_extension (str): file extension to save as
        save_mode (str): save mode 'w' or 'a'
        file_data (str | bytes): data to save

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
        with open(file_path, save_mode, encoding='utf-8') as f:
            f.write(file_data)
            f.close()
    except FileNotFoundError:
        print('file not found error thrown!')
        return False
    return True
