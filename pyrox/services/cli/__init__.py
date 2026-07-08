#        ┌────────────────────────┐
#        │   TerminalApplication  │ ◄───(Main Orchestrator)
#        └───────────┬────────────┘
#                    │
#          Tracks Current State
#                    │
#                    ▼
#        ┌────────────────────────┐
#        │      AppState (Base)   │
#        └─────┬────────────┬─────┘
#              │            │
#    Inherits  │            │  Inherits
#              ▼            ▼
#  ┌─────────────────┐    ┌──────────────────┐
#  │  MainMenuState  │    │  AltEditorState  │ ... (Other Screens)
#  └─────────────────┘    └──────────────────┘
import sys
import time


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


if __name__ == '__main__':
    try:
        while True:
            update_console_lines(
                line_count=10,
                line_content=[
                    'Here is line 1',
                    'Here is line 2',
                    'Here is line 3',
                    'Here is line 4',
                    'Here is line 5',
                    'Here is line 6',
                    'Here is line 7',
                    'Here is line 8',
                    'Here is line 9',
                    f'Current time is {time.time().hex}'
                ]
            )
    except KeyboardInterrupt:
        pass
