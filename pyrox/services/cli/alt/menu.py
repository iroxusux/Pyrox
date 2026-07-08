import msvcrt
from typing import Callable

from pyrox.core.validators import unsafe_assert_is_type
from pyrox.services.cli.core import clear, clear_input_buffer, ANSIFormatter
from pyrox.services.cli.print import (
    update_console_lines
)


def alternate_menu(items: list[tuple[str, Callable]]) -> None:
    clear()
    pointer = 0
    length = len(items)
    mut_lines = [''] * length

    while True:
        for x in range(length):
            unsafe_assert_is_type(items[x][0], str)
            if not callable(items[x][1]):
                raise ValueError('Second item in tuple MUST be callable!')
            mut_lines[x] = f"[{x}] {items[x][0]}"
            if pointer == x:
                mut_lines[x] += ' <'

        update_console_lines(length, mut_lines)
        char = msvcrt.getch().decode('utf-8', errors='ignore')
        if char.lower() == 'j':
            pointer += 1
        if char.lower() == 'k':
            pointer -= 1
        if pointer >= length:
            pointer = 0
        if pointer < 0:
            pointer = length - 1
        if char in ANSIFormatter.ENTER_CHARS:
            items[pointer][1]()
            return
        clear_input_buffer()


if __name__ == '__main__':
    alternate_menu([
        ('item1', lambda: print('item 1 selected')),
        ('item2', lambda: print('item 2 selected')),
        ('item3', lambda: print('item 3 selected')),
    ])
