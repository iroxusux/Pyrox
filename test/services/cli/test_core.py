import pytest

from pyrox.services.cli.core import ANSIFormatter


class TestAnsiFormatter:

    def test_cannot_init(self):
        with pytest.raises(TypeError):
            ANSIFormatter()

    def test_move_home(self):
        assert ANSIFormatter.move_home()

    def test_esc_seq(self):
        assert ANSIFormatter.ESC == '\033['

    def test_enter_pressed_chars(self):
        assert ' ' in ANSIFormatter.ENTER_CHARS
        assert '\r' in ANSIFormatter.ENTER_CHARS

    def test_cursor_up(self):
        for x in range(256):
            assert ANSIFormatter.cursor_up(x) == f'\033[{x}A'

    def test_cursor_down(self):
        for x in range(256):
            assert ANSIFormatter.cursor_down(x) == f'\033[{x}B'

    def test_cursor_right(self):
        for x in range(256):
            assert ANSIFormatter.cursor_right(x) == f'\033[{x}C'

    def test_cursor_left(self):
        for x in range(256):
            assert ANSIFormatter.cursor_left(x) == f'\033[{x}D'

    def test_text_color(self):
        for x in range(256):
            assert ANSIFormatter.text_color_256(x) == f"\033[38;5;{x}m"

    def test_bg_color(self):
        for x in range(256):
            assert ANSIFormatter.bg_color_256(x) == f"\033[48;5;{x}m"
