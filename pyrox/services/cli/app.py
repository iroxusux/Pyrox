import msvcrt
from pyrox.interfaces.cli.state import AppState


class TerminalApplication:
    """The central manager that orchestrates states and terminal lifecycles."""

    def __init__(
        self,
        initial_state: AppState | None = None
    ):
        self.state_tracking: list[AppState] = []
        self._fallback_state = initial_state
        if self._fallback_state:
            self._fallback_state.app = self
        self.current_state = None
        self.is_running = False

    def __enter__(self):
        """Context manager setup. Prepares terminal settings if needed."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Guarantees terminal restoration even if the app crashes."""
        # Force exit the current state to trigger its clean-up (like disabling alt mode)
        if self.current_state:
            self.current_state.exit()

        # ANSI fallback to ensure main screen and cursor are restored
        print("\033[?1049l\033[?25h", end="", flush=True)
        print("\nTerminal connection closed cleanly.")

    def change_state(self, new_state: AppState) -> None:
        """Safely transitions from one console state to another."""
        if self.current_state:
            self.current_state.exit()
        self.state_tracking.append(new_state)
        self.state_tracking[-1].app = self
        self.current_state = self.state_tracking[-1]
        self.current_state.enter()

    def restore_state(self) -> None:
        """Transion from current state to last known state.
        If no previous state found, safely transtion to MainMenuState
        """
        if self.current_state:
            self.current_state.exit()
            self.state_tracking.pop()

        try:
            prev_state = self.state_tracking[-1]
        except IndexError:
            prev_state = None

        if not prev_state:
            if self._fallback_state:
                prev_state = self._fallback_state
            else:
                raise ValueError('No initial state to fall back to!')
            self.state_tracking = [prev_state]

        self.current_state = self.state_tracking[-1]
        self.current_state.enter()

    def stop(self) -> None:
        self.is_running = False

    def run(self, state: AppState | None = None) -> None:
        """Launches the main execution loop."""
        self.is_running = True
        if state is None and self._fallback_state:
            state = self._fallback_state
        if state is not None and not self._fallback_state:
            self._fallback_state = state
        if not state:
            raise RuntimeError('Cannot run this application without a known, valid state!')
        self.change_state(state)

        if not self.current_state:
            raise RuntimeError('Error changing state!')

        # Basic placeholder execution loop
        while self.is_running:
            try:
                # In a real app, use a non-blocking key reader (like `readchar` or `curses`)
                char = msvcrt.getch().decode('utf-8', errors='ignore')
                self.current_state.handle_input(char)
            except (KeyboardInterrupt, SystemExit):
                self.stop()
