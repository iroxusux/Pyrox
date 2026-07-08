"""Core components and methods for CLI / Terminal interaction
    """
import msvcrt
import os


class ANSIFormatter:
    """Provides parametrized ANSI escape sequences for CLI formatting."""
    REG_BUFFER_CMD = '\x1b[?1049l'
    ALT_BUFFER_CMD = '\x1b[?1049h'

    ESC = "\033["
    ENTER_CHARS = [' ', '\r']

    def __init__(self) -> None:
        raise TypeError("This class is static and cannot be created!")

    @classmethod
    def enter_regular_mode(cls, end: str = '\n', flush: bool = False) -> None:
        print(cls.REG_BUFFER_CMD, end=end, flush=flush)

    @classmethod
    def enter_alt_mode(cls) -> None:
        print(cls.ALT_BUFFER_CMD)

    @classmethod
    def move_home(cls, end: str = "\n", flush: bool = False) -> None:
        """Moves the cursor home."""
        print(f'{cls.ESC}H', end=end, flush=flush)

    @classmethod
    def move_absolute(cls, row: int, col: int, end: str = "\n", flush: bool = False) -> None:
        """Moves the cursor to a specific row and column."""
        print(f'{cls.ESC}{row};{col}H', end=end, flush=flush)

    @classmethod
    def move_to_column(cls, col: int) -> None:
        """Moves the cursor to a specific column."""
        print(f'{cls.ESC}{col}G')

    @classmethod
    def cursor_up(cls, n: int = 1) -> None:
        """Moves the cursor up by n lines."""
        print(f"{cls.ESC}{n}A")

    @classmethod
    def cursor_down(cls, n: int = 1) -> None:
        """Moves the cursor down by n lines."""
        print(f"{cls.ESC}{n}B")

    @classmethod
    def cursor_right(cls, n: int = 1) -> None:
        """Moves the cursor right by n columns."""
        print(f"{cls.ESC}{n}C")

    @classmethod
    def cursor_left(cls, n: int = 1) -> None:
        """Moves the cursor left by n columns."""
        print(f"{cls.ESC}{n}D")

    @classmethod
    def hide_cursor(cls) -> None:
        """Hide the cursor from the cuser."""
        print(f'{cls.ESC}?25l')

    @classmethod
    def show_cursor(cls) -> None:
        """Show the cursor to the user."""
        print(f'{cls.ESC}?25h')

    @classmethod
    def save_cursor_position(cls) -> None:
        """Save cursor position."""
        print(f'{cls.ESC}s')

    @classmethod
    def restor_last_cursor_position(cls) -> None:
        """Restore the last cursor position saved."""
        print(f'{cls.ESC}u')

    @classmethod
    def text_color_256(cls, n: int) -> None:
        """Sets foreground color using 256-color palette (0-255)."""
        print(f"{cls.ESC}38;5;{n}m")

    @classmethod
    def bg_color_256(cls, n: int) -> None:
        """Sets background color using 256-color palette (0-255)."""
        print(f"{cls.ESC}48;5;{n}m")

    @classmethod
    def clear_screen(cls) -> None:
        """Clear the screen, leaving cursor in place."""
        print(f'{cls.ESC}2J')

    @classmethod
    def clear_to_end_of_line(cls, end: str = '\n', flush: bool = False) -> None:
        """Clear from the cursor to the end of the current line."""
        print(f'{cls.ESC}K', end=end, flush=flush)

    @classmethod
    def clear_line(cls) -> None:
        """Clear the entire current line."""
        print(f'{cls.ESC}2K')


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')
    clear_input_buffer()


def clear_input_buffer():
    # Clear any pending characters sitting in the buffer
    while msvcrt.kbhit():
        msvcrt.getch()
