from tkinter import messagebox


def notify_failure(title: str, message: str, err_info: str = '') -> None:
    """messagebox for failure

    Args:
        title (str): title
        message (str): message to dispaly
        err_info (str, optional): additional error info. Defaults to ''.
    """
    messagebox.showerror(title, f'{message}\nerror info: {err_info}')


def notify_success(title: str, message: str) -> None:
    """messagebox for success

    Args:
        title (str): title
        message (str): message
    """
    messagebox.showinfo(title, message)


def notify_warning(title: str, message: str) -> None:
    """messagebox for warning

    Args:
        title (str): title
        message (str): message
    """
    messagebox.showwarning(title, message)
