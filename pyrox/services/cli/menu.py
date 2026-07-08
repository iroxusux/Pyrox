from typing import Callable
from pyrox.core.validators import unsafe_assert_is_type
from pyrox.services.cli.core import clear
from pyrox.services.cli.print import (
    print_header,
    print_user_input_prompt,
)


class MenuItem:
    def __init__(
        self,
        display_value: str,
        callback: Callable
    ) -> None:
        self.display_value = display_value
        self.callback = callback


def interactive_menu(items: list[tuple[str, Callable]]) -> None:
    """Handle list of callables by displaying them to a user and calling the option they select.

    Args:
        items (list[tuple[str, Callable]]): List of string (display) and call-back (function).

    Raises:
        ValueError: If tuple index 0 is not a string or tuple index 1 is not a callable function.
    """
    clear()

    if not items:
        return

    print_header('Select an item below...')

    for index, item in enumerate(items):
        unsafe_assert_is_type(item[0], str)
        if not callable(item[1]):
            raise ValueError('Second item in tuple MUST be callable!')
        print(f"[{index}] {item[0]}")

    user_selection = print_user_input_prompt()
    if not user_selection:
        interactive_menu(items)
    try:
        index = int(user_selection)
        items[index][1]()
        return
    except IndexError:
        input(f'Invalid selection: {user_selection}')
        interactive_menu(items)
    except ValueError:
        input(f'Selection must be a valid number between 0 -> {len(items)}... Got {user_selection}...')
        interactive_menu(items)
