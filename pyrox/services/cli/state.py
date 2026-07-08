from pyrox.interfaces.cli.state import AppState
from pyrox.services.cli.core import ANSIFormatter
from pyrox.services.cli.print import _make_pretty
from pyrox.services.cli.menu import MenuItem
from pyrox.services.cli.alt.line import TrackedLine
from pyrox.services.cli.alt.print import update_target_line


class _BaseState(AppState):
    def enter(self):
        self.is_alive = True
        self.render()

    def exit(self) -> None:
        self.is_alive = False


class MainMenuState(_BaseState):
    def handle_input(self, key):
        if key == "e":
            # Transition to the editor (which uses Alt Mode)
            self.app.change_state(AltEditorState(self.app))
        elif key == "q":
            self.app.stop()

    def render(self):
        print("\n=== MAIN MENU ===")
        print("[e] Open Advanced Editor (Alt Mode)")
        print("[q] Quit Application")


class AltEditorState(_BaseState):
    def enter(self):
        # Enable Alternate Screen Buffer using ANSI escape codes
        print("\033[?1049h\033[H", end="", flush=True)
        self.render()

    def handle_input(self, key):
        if key == "b":
            # Go back to main menu
            self.app.change_state(MainMenuState(self.app))

    def render(self):
        # Clear screen and draw editor UI
        print("\033[2J\033[H", end="")
        print("--- ADVANCED ALT-MODE EDITOR ---")
        print("Type text here... (Simulated)")
        print("\nPress [b] to return to Main Menu.")

    def exit(self):
        # Disable Alternate Screen Buffer safely when leaving
        print("\033[?1049l", end="", flush=True)


class InteractiveMenuState(_BaseState):

    def __init__(
        self,
        app_context,
        title: str,
        items: list[MenuItem],
        footer: str = '',
        pointer_char: str = '<',
        as_root: bool = False
    ):
        super().__init__(app_context)
        self.title = title
        self.items = items
        self.length = len(items)
        self.pointer = 0
        line_items = []
        for x in range(self.length):
            text = _make_pretty(self.items[x].display_value, '#', ' ')
            line_items.append(TrackedLine(2+x, text))

        self.lines = {
            'header': TrackedLine(1, _make_pretty(title, '#', '-')),
            'list': line_items,
            'status': TrackedLine(3 + self.length, ''),
            'footer': TrackedLine(4 + self.length, footer),
        }
        self._can_exit = not as_root
        if self._can_exit:
            self.lines['end'] = TrackedLine(5 + self.length, 'Press "e" to exit...')

        if len(pointer_char) != 1:
            raise ValueError('Pointer character must be a single character string!')
        self.pointer_char = pointer_char

    @property
    def status(self) -> TrackedLine:
        return self.lines['status']

    def all_lines(self) -> list[TrackedLine]:
        lines = []
        for value in self.lines.values():
            if isinstance(value, list):
                lines.extend(value)
            elif isinstance(value, TrackedLine):
                lines.append(value)
            else:
                raise ValueError(f'Unexpected type found! {type(value)}')
        return lines

    # --- Pointer Manipulation ----------
    def _strip_pointer(self, line: TrackedLine) -> None:
        """Remove the pointer character from a given line. """
        if not line.value.strip().endswith(self.pointer_char):
            return
        line.value = line.value.removesuffix(self.pointer_char)

    def _append_pointer(self, line: TrackedLine) -> None:
        """Append pointer character to a given line."""
        if line.value.strip().endswith(self.pointer_char):
            return
        line.value = line.value + f'{self.pointer_char}'

    def _change_line_position(self, offset: int) -> None:
        self._strip_pointer(self.lines['list'][self.pointer])
        self.pointer += offset
        if self.pointer >= self.length:
            self.pointer = 0
        if self.pointer < 0:
            self.pointer = self.length - 1
        self._append_pointer(self.lines['list'][self.pointer])

    def _increment_pointer(self):
        self._change_line_position(1)

    def _decrement_pointer(self):
        self._change_line_position(-1)

    def _set_pointer(self, pos: int) -> None:
        """Set pointer to a specified value."""
        self._change_line_position(-(self.pointer - pos))

    # --- Execute ----------
    def execute_line_item(self):
        ret_value = self.items[self.pointer].callback()
        if ret_value is not None:
            self.status.value = f'Got value from callback: {ret_value}'

    # --- Abstract Fullfillment ----------
    def enter(self):
        super().enter()
        # Enable Alternate Screen Buffer using ANSI escape codes
        ANSIFormatter.enter_alt_mode()
        ANSIFormatter.clear_screen()
        ANSIFormatter.move_home(end="", flush=True)
        ANSIFormatter.hide_cursor()
        self._set_pointer(0)
        self.render(redraw=True)

    def handle_input(self, key):
        if key == 'e':
            if not self._can_exit:
                return
            self.app.restore_state()
        if key == 'j':
            self._increment_pointer()
        if key == 'k':
            self._decrement_pointer()
        if key in ANSIFormatter.ENTER_CHARS:
            self.execute_line_item()
        self.render()

    def render(self, redraw: bool = False):
        # Don't process if our app killed us.
        if not self.is_alive:
            return
        # Clear screen and draw editor UI
        for line in self.all_lines():
            if redraw:
                line.mark_dirty()
            update_target_line(line)

    def exit(self):
        # Disable Alternate Screen Buffer safely when leaving
        ANSIFormatter.enter_regular_mode(end="", flush=True)
        ANSIFormatter.clear_screen()
        ANSIFormatter.move_home(end="", flush=True)
        ANSIFormatter.show_cursor()
        super().exit()

    def mark_dirty(self) -> None:
        for line in self.all_lines():
            line.mark_dirty()
