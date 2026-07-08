from pyrox.services.cli.alt.line import TrackedLine
from pyrox.services.cli.core import ANSIFormatter


def update_target_line(line: TrackedLine) -> None:
    """Update a targeted line in the console / terminal.
    Designed for alternate mode use.

    Args:
        line (TrackedLine): :class:`TrackedLine` to update its' value.
    """
    if not line.dirty:
        return
    ANSIFormatter.move_absolute(line.line_no, 1, end='')
    ANSIFormatter.clear_to_end_of_line(end='')
    print(line.value, end='', flush=True)
    line.clean()
