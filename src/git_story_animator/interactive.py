"""Interactive mode — keyboard input capture, pause/navigate/expand.

Handles raw terminal input parsing and the interactive state machine
for controlling animation playback.
"""

from __future__ import annotations

import sys
import termios
import tty
import select
from dataclasses import dataclass
from enum import Enum, auto


class KeyEvent(Enum):
    """Normalized keyboard events for interactive control."""
    SPACE = auto()
    ARROW_UP = auto()
    ARROW_DOWN = auto()
    ARROW_LEFT = auto()
    ARROW_RIGHT = auto()
    ENTER = auto()
    ESCAPE = auto()
    Q = auto()
    UNKNOWN = auto()


class InteractiveState(Enum):
    """States of the interactive mode state machine."""
    PLAYING = "playing"
    PAUSED = "paused"
    EXPANDED = "expanded"


@dataclass
class InteractiveContext:
    """Current state of the interactive controller."""
    state: InteractiveState = InteractiveState.PLAYING
    cursor_index: int = 0
    total_commits: int = 0
    want_quit: bool = False


class KeyParser:
    """Reads raw terminal input and parses key events.

    Sets terminal to raw mode for unbuffered character reading,
    mapping escape sequences to normalized KeyEvent values.

    Usage:
        parser = KeyParser()
        event = parser.read_key()  # blocking read
        event = parser.read_key_nonblocking()  # non-blocking read
    """

    _ESCAPE_SEQUENCES: dict[str, KeyEvent] = {
        "[A": KeyEvent.ARROW_UP,
        "[B": KeyEvent.ARROW_DOWN,
        "[C": KeyEvent.ARROW_RIGHT,
        "[D": KeyEvent.ARROW_LEFT,
    }

    def __init__(self):
        self._original_settings: list | None = None
        self._raw_mode = False

    def enable_raw_mode(self) -> None:
        """Set terminal to raw mode for unbuffered input."""
        if self._raw_mode:
            return
        fd = sys.stdin.fileno()
        self._original_settings = termios.tcgetattr(fd)
        tty.setraw(fd)
        self._raw_mode = True

    def disable_raw_mode(self) -> None:
        """Restore original terminal settings."""
        if not self._raw_mode or self._original_settings is None:
            return
        fd = sys.stdin.fileno()
        termios.tcsetattr(fd, termios.TCSADRAIN, self._original_settings)
        self._raw_mode = False
        self._original_settings = None

    def read_key(self) -> KeyEvent:
        """Read a single key press (blocking).

        Returns:
            Parsed KeyEvent.
        """
        fd = sys.stdin.fileno()
        char = sys.stdin.read(1)

        if char == " ":
            return KeyEvent.SPACE
        if char == "\r" or char == "\n":
            return KeyEvent.ENTER
        if char == "q" or char == "Q":
            return KeyEvent.Q
        if char == "\x1b":
            # Escape sequence — check if more chars available
            rlist, _, _ = select.select([fd], [], [], 0)
            if rlist:
                seq = sys.stdin.read(2)
                return self._ESCAPE_SEQUENCES.get(seq, KeyEvent.ESCAPE)
            return KeyEvent.ESCAPE

        return KeyEvent.UNKNOWN

    def read_key_nonblocking(self) -> KeyEvent | None:
        """Read a key press if available (non-blocking).

        Returns:
            KeyEvent if a key was pressed, None otherwise.
        """
        fd = sys.stdin.fileno()
        rlist, _, _ = select.select([fd], [], [], 0)
        if not rlist:
            return None
        return self.read_key()

    def __enter__(self):
        self.enable_raw_mode()
        return self

    def __exit__(self, *args):
        self.disable_raw_mode()


class InteractiveController:
    """Manages the interactive animation state machine.

    Dispatches state transitions based on keyboard input:

        PLAYING ──Space──> PAUSED
        PAUSED  ──Space──> PLAYING
        PAUSED  ──Enter──> EXPANDED
        EXPANDED──Escape─> PAUSED
        Any     ──Q──────> quit
    """

    def __init__(self, total_commits: int):
        """Initialize the controller.

        Args:
            total_commits: Total number of commits in the animation.
        """
        self.ctx = InteractiveContext(total_commits=total_commits)
        self._key_parser = KeyParser()

    @property
    def state(self) -> InteractiveState:
        return self.ctx.state

    @property
    def cursor_index(self) -> int:
        return self.ctx.cursor_index

    @property
    def want_quit(self) -> bool:
        return self.ctx.want_quit

    def enable(self) -> None:
        """Enable raw terminal mode for keyboard input."""
        self._key_parser.enable_raw_mode()

    def disable(self) -> None:
        """Restore terminal to normal mode."""
        self._key_parser.disable_raw_mode()

    def check_input(self) -> bool:
        """Check for available keyboard input and dispatch events.

        Returns:
            True if the state changed, False otherwise.
        """
        event = self._key_parser.read_key_nonblocking()
        if event is None:
            return False

        return self._handle_event(event)

    def _handle_event(self, event: KeyEvent) -> bool:
        """Process a key event and update state machine.

        Returns:
            True if state changed.
        """
        if event == KeyEvent.Q:
            self.ctx.want_quit = True
            return True

        if self.ctx.state == InteractiveState.PLAYING:
            if event == KeyEvent.SPACE:
                self.ctx.state = InteractiveState.PAUSED
                return True

        elif self.ctx.state == InteractiveState.PAUSED:
            if event == KeyEvent.SPACE:
                self.ctx.state = InteractiveState.PLAYING
                return True
            elif event == KeyEvent.ENTER:
                self.ctx.state = InteractiveState.EXPANDED
                return True
            elif event == KeyEvent.ARROW_DOWN:
                if self.ctx.cursor_index < self.ctx.total_commits - 1:
                    self.ctx.cursor_index += 1
                    return True
            elif event == KeyEvent.ARROW_UP:
                if self.ctx.cursor_index > 0:
                    self.ctx.cursor_index -= 1
                    return True

        elif self.ctx.state == InteractiveState.EXPANDED:
            if event == KeyEvent.ESCAPE:
                self.ctx.state = InteractiveState.PAUSED
                return True

        return False

    def __enter__(self):
        self.enable()
        return self

    def __exit__(self, *args):
        self.disable()
