import subprocess
import os
import sys
from pyrox.services import log


def execute_file_as_subprocess(
    file_path: str,
) -> None:
    """Execute a file as a subprocess.

    Args:
        file_path (str): The path to the file to be executed.
    """

    if not os.path.isfile(file_path):
        log(__name__).error(f"File not found: {file_path}")
        return

    try:
        if sys.platform.startswith('win'):
            # Windows — use cmd /c start so the child is detached from the
            # parent's Job Object and survives the parent process exiting.
            subprocess.Popen(
                ['cmd', '/c', 'start', '', file_path],
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                close_fds=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif sys.platform.startswith('darwin'):
            # macOS
            subprocess.Popen(['open', file_path], start_new_session=True)
        else:
            # Linux and other Unix-like systems
            subprocess.Popen(['xdg-open', file_path], start_new_session=True)
        log(__name__).info(f"Successfully executed file: {file_path}")
    except Exception as e:
        log(__name__).error(f"Failed to execute file {file_path}: {e}")
