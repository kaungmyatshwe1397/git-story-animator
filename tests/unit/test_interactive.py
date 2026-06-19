"""Unit tests for interactive module — KeyParser and InteractiveController."""

from __future__ import annotations

from unittest.mock import patch, MagicMock, call

import pytest

from git_story_animator.interactive import (
    KeyEvent,
    KeyParser,
    InteractiveState,
    InteractiveController,
    InteractiveContext,
)


# ── T026: KeyParser tests ───────────────────────────────────────────────


class TestKeyEventParsing:
    """T026: Verify correct key events parsed from raw terminal input."""

    def test_space_key(self):
        with patch("sys.stdin.read", return_value=" "), \
             patch("sys.stdin.fileno", return_value=0), \
             patch("termios.tcgetattr"), \
             patch("tty.setraw"):
            parser = KeyParser()
            parser.enable_raw_mode()
            event = parser.read_key()
            assert event == KeyEvent.SPACE

    def test_enter_key_cr(self):
        with patch("sys.stdin.read", return_value="\r"), \
             patch("sys.stdin.fileno", return_value=0), \
             patch("termios.tcgetattr"), \
             patch("tty.setraw"):
            parser = KeyParser()
            parser.enable_raw_mode()
            event = parser.read_key()
            assert event == KeyEvent.ENTER

    def test_enter_key_newline(self):
        with patch("sys.stdin.read", return_value="\n"), \
             patch("sys.stdin.fileno", return_value=0), \
             patch("termios.tcgetattr"), \
             patch("tty.setraw"):
            parser = KeyParser()
            parser.enable_raw_mode()
            event = parser.read_key()
            assert event == KeyEvent.ENTER

    def test_q_key_lowercase(self):
        with patch("sys.stdin.read", return_value="q"), \
             patch("sys.stdin.fileno", return_value=0), \
             patch("termios.tcgetattr"), \
             patch("tty.setraw"):
            parser = KeyParser()
            parser.enable_raw_mode()
            event = parser.read_key()
            assert event == KeyEvent.Q

    def test_q_key_uppercase(self):
        with patch("sys.stdin.read", return_value="Q"), \
             patch("sys.stdin.fileno", return_value=0), \
             patch("termios.tcgetattr"), \
             patch("tty.setraw"):
            parser = KeyParser()
            parser.enable_raw_mode()
            event = parser.read_key()
            assert event == KeyEvent.Q

    def test_escape_key(self):
        with patch("sys.stdin.read", side_effect=["\x1b"]), \
             patch("sys.stdin.fileno", return_value=0), \
             patch("select.select", return_value=([], [], [])), \
             patch("termios.tcgetattr"), \
             patch("tty.setraw"):
            parser = KeyParser()
            parser.enable_raw_mode()
            event = parser.read_key()
            assert event == KeyEvent.ESCAPE

    def test_arrow_up(self):
        with patch("sys.stdin.read", side_effect=["\x1b", "[A"]), \
             patch("sys.stdin.fileno", return_value=0), \
             patch("select.select", return_value=([0], [], [])), \
             patch("termios.tcgetattr"), \
             patch("tty.setraw"):
            parser = KeyParser()
            parser.enable_raw_mode()
            event = parser.read_key()
            assert event == KeyEvent.ARROW_UP

    def test_arrow_down(self):
        with patch("sys.stdin.read", side_effect=["\x1b", "[B"]), \
             patch("sys.stdin.fileno", return_value=0), \
             patch("select.select", return_value=([0], [], [])), \
             patch("termios.tcgetattr"), \
             patch("tty.setraw"):
            parser = KeyParser()
            parser.enable_raw_mode()
            event = parser.read_key()
            assert event == KeyEvent.ARROW_DOWN

    def test_unknown_key(self):
        with patch("sys.stdin.read", return_value="x"), \
             patch("sys.stdin.fileno", return_value=0), \
             patch("termios.tcgetattr"), \
             patch("tty.setraw"):
            parser = KeyParser()
            parser.enable_raw_mode()
            event = parser.read_key()
            assert event == KeyEvent.UNKNOWN


class TestKeyParserNonBlocking:
    """T026: Non-blocking read returns None when no input available."""

    def test_no_input_available(self):
        with patch("sys.stdin.fileno", return_value=0), \
             patch("select.select", return_value=([], [], [])), \
             patch("termios.tcgetattr"), \
             patch("tty.setraw"):
            parser = KeyParser()
            parser.enable_raw_mode()
            event = parser.read_key_nonblocking()
            assert event is None

    def test_input_available(self):
        with patch("sys.stdin.fileno", return_value=0), \
             patch("select.select", return_value=([0], [], [])), \
             patch("sys.stdin.read", return_value=" "), \
             patch("termios.tcgetattr"), \
             patch("tty.setraw"):
            parser = KeyParser()
            parser.enable_raw_mode()
            event = parser.read_key_nonblocking()
            assert event == KeyEvent.SPACE


# ── T027: InteractiveController state machine tests ─────────────────────


class TestStateTransitions:
    """T027: Verify correct state transitions."""

    def test_playing_to_paused_on_space(self):
        ctrl = InteractiveController(total_commits=5)
        assert ctrl.state == InteractiveState.PLAYING
        changed = ctrl._handle_event(KeyEvent.SPACE)
        assert changed is True
        assert ctrl.state == InteractiveState.PAUSED

    def test_paused_to_playing_on_space(self):
        ctrl = InteractiveController(total_commits=5)
        ctrl._handle_event(KeyEvent.SPACE)  # PLAYING → PAUSED
        changed = ctrl._handle_event(KeyEvent.SPACE)  # PAUSED → PLAYING
        assert changed is True
        assert ctrl.state == InteractiveState.PLAYING

    def test_paused_to_expanded_on_enter(self):
        ctrl = InteractiveController(total_commits=5)
        ctrl._handle_event(KeyEvent.SPACE)  # PLAYING → PAUSED
        changed = ctrl._handle_event(KeyEvent.ENTER)  # PAUSED → EXPANDED
        assert changed is True
        assert ctrl.state == InteractiveState.EXPANDED

    def test_expanded_to_paused_on_escape(self):
        ctrl = InteractiveController(total_commits=5)
        ctrl._handle_event(KeyEvent.SPACE)   # PLAYING → PAUSED
        ctrl._handle_event(KeyEvent.ENTER)   # PAUSED → EXPANDED
        changed = ctrl._handle_event(KeyEvent.ESCAPE)  # EXPANDED → PAUSED
        assert changed is True
        assert ctrl.state == InteractiveState.PAUSED

    def test_quit_from_any_state(self):
        ctrl = InteractiveController(total_commits=5)
        changed = ctrl._handle_event(KeyEvent.Q)
        assert changed is True
        assert ctrl.want_quit is True

    def test_paused_quit(self):
        ctrl = InteractiveController(total_commits=5)
        ctrl._handle_event(KeyEvent.SPACE)  # → PAUSED
        changed = ctrl._handle_event(KeyEvent.Q)
        assert changed is True
        assert ctrl.want_quit is True

    def test_expanded_quit(self):
        ctrl = InteractiveController(total_commits=5)
        ctrl._handle_event(KeyEvent.SPACE)   # → PAUSED
        ctrl._handle_event(KeyEvent.ENTER)   # → EXPANDED
        changed = ctrl._handle_event(KeyEvent.Q)
        assert changed is True
        assert ctrl.want_quit is True


class TestCursorNavigation:
    """T027: Cursor navigation bounds."""

    def test_cursor_starts_at_zero(self):
        ctrl = InteractiveController(total_commits=5)
        assert ctrl.cursor_index == 0

    def test_arrow_down_increments(self):
        ctrl = InteractiveController(total_commits=5)
        ctrl._handle_event(KeyEvent.SPACE)  # → PAUSED
        ctrl._handle_event(KeyEvent.ARROW_DOWN)
        assert ctrl.cursor_index == 1

    def test_arrow_up_decrements(self):
        ctrl = InteractiveController(total_commits=5)
        ctrl._handle_event(KeyEvent.SPACE)  # → PAUSED
        ctrl._handle_event(KeyEvent.ARROW_DOWN)
        ctrl._handle_event(KeyEvent.ARROW_DOWN)
        ctrl._handle_event(KeyEvent.ARROW_UP)
        assert ctrl.cursor_index == 1

    def test_arrow_down_lower_bound(self):
        ctrl = InteractiveController(total_commits=3)
        ctrl._handle_event(KeyEvent.SPACE)  # → PAUSED
        ctrl._handle_event(KeyEvent.ARROW_DOWN)
        ctrl._handle_event(KeyEvent.ARROW_DOWN)  # index 2
        ctrl._handle_event(KeyEvent.ARROW_DOWN)  # index 2 (clamped)
        assert ctrl.cursor_index == 2

    def test_arrow_up_upper_bound(self):
        ctrl = InteractiveController(total_commits=5)
        ctrl._handle_event(KeyEvent.SPACE)  # → PAUSED
        ctrl._handle_event(KeyEvent.ARROW_UP)  # stays at 0
        assert ctrl.cursor_index == 0

    def test_cursor_respects_total(self):
        ctrl = InteractiveController(total_commits=10)
        ctrl._handle_event(KeyEvent.SPACE)  # → PAUSED
        for _ in range(20):
            ctrl._handle_event(KeyEvent.ARROW_DOWN)
        assert ctrl.cursor_index == 9  # max is total - 1


class TestControllerNoStateChangeOnBadInput:
    """T027: Invalid keys in a state don't change state."""

    def test_enter_does_nothing_in_playing(self):
        ctrl = InteractiveController(total_commits=5)
        changed = ctrl._handle_event(KeyEvent.ENTER)
        assert changed is False
        assert ctrl.state == InteractiveState.PLAYING

    def test_escape_does_nothing_in_paused(self):
        ctrl = InteractiveController(total_commits=5)
        ctrl._handle_event(KeyEvent.SPACE)  # → PAUSED
        changed = ctrl._handle_event(KeyEvent.ESCAPE)
        # In PAUSED state, Escape doesn't transition (only to EXPANDED or back to PLAYING)
        assert ctrl.state == InteractiveState.PAUSED

    def test_space_does_nothing_in_expanded(self):
        ctrl = InteractiveController(total_commits=5)
        ctrl._handle_event(KeyEvent.SPACE)   # → PAUSED
        ctrl._handle_event(KeyEvent.ENTER)   # → EXPANDED
        changed = ctrl._handle_event(KeyEvent.SPACE)
        assert changed is False
        assert ctrl.state == InteractiveState.EXPANDED
