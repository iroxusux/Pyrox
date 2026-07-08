"""Print utilities for command line interface
"""
import sys


# --- Line generator methods ----------
def _make_pretty(message: str, header_char: str, fill_char: str) -> str:
    return f'{header_char} {fill_char * 3} {message} {fill_char * 10} '.ljust(25, fill_char)


def _continue_prompt_str() -> str:
    return 'Press "Enter" to continue...'


def _user_input_prompt_str() -> str:
    return '>>> '


# --- Print methods ----------
def print_user_input_prompt() -> str:
    """General helper method to prompt a user for input feedback.
    For consistency across the codebase.

    Returns:
        str: The user's response.
    """
    return input(_user_input_prompt_str())


def print_continue_prompt() -> str:
    """General helper method to prompt the user to press 'Enter' to continue.
    For consistency across the codebase.

    Returns:
        str: The user's response.
    """
    return input(_continue_prompt_str())


def prompt_user_confirm(confirm_message: str) -> bool:
    keys = ['y', 'yes']
    print(f'{confirm_message} -> [{keys}]')
    return print_user_input_prompt() in keys


def print_header(message: str, header_char: str = '#') -> None:
    """Print a header line.
    This method relies on :method:`print_pretty_line`, passing default characters to work.

    Args:
        message (str): Message to print to terminal.
        header_char (str, optional): Character to begin header with. Defaults to '#'.

    Example Output:
        >>>
        # --- This is an example header! ----------
    """
    print_pretty_line(message, header_char)


def print_pretty_line(message: str, header_char: str = '#', fill_char: str = ' ') -> None:
    """Print a pretty line to the console / terminal.

    Args:
        message (str): Message to print.
        header_char (str, optional): Header character to begin message with. Defaults to '#'.
        fill_char (str, optional): Fill character to wrap message with. Defaults to ' '.

    Raises:
        ValueError: If header_char is not a length of 1 (single character).
        ValueError: If fill_char is not a length of 1 (single character).

    Example Output:
        >>>
        print_pretty_line('This is an example message!, fill_char='-')
        # --- This is an example pretty message! ----------
    """
    if len(header_char) != 1:
        raise ValueError('Header character must be a single character!')
    if len(fill_char) != 1:
        raise ValueError('Fill character must be a single character!')
    print(_make_pretty(message, header_char, fill_char))


# --- Buffer methods ----------
def buffer_user_input_prompt(buffer: list[str]) -> None:
    buffer.append(_user_input_prompt_str())


def buffer_header(buffer: list[str], message: str) -> None:
    buffer_pretty_line(buffer, message, '-')


def buffer_line(buffer: list[str], message: str = '') -> None:
    buffer.append(message)


def buffer_pretty_line(buffer: list[str], message: str, header_char: str = '#', fill_char: str = ' ') -> None:
    if len(header_char) != 1:
        raise ValueError('Header character must be a single character!')
    if len(fill_char) != 1:
        raise ValueError('Fill character must be a single character!')
    buffer.append(_make_pretty(message, '#', fill_char))


# --- Update methods ----------
def update_console_lines(line_count: int, line_content: list[str]) -> None:
    """Update console lines by overwriting existing values and rewriting over the buffer.
    This method prevents flicker on the console for 'clear' events.

    Args:
        line_count (int): Number of lines to overwrite
        line_content (list[str]): List of lines to newly fill the console with
    """
    for _ in range(len(line_content)):
        sys.stdout.write(f'\033[{line_count}A')

        for line in line_content:
            sys.stdout.write(f"\033[K{line}\n")

        sys.stdout.flush()
