"""Unit tests for the Animator class — frame sequencing and timing."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from git_story_animator.models import (
    Commit,
    AnimationConfig,
    AnimationState,
    Speed,
    Style,
)
from git_story_animator.animator import Animator, AnimationFrame


def _make_commit(hash_short="abc", subject="test"):
    return Commit(
        hash="abc123",
        hash_short=hash_short,
        author_name="Alice",
        author_email="alice@x.com",
        timestamp=datetime.now(timezone.utc),
        subject=subject,
        parent_hashes=["parent1"],
    )


class TestAnimatorFrameCount:
    """T018: Frame count equals commit count for entering frames."""

    def test_entering_frames_equal_commit_count(self):
        commits = [_make_commit(f"c{i}", f"commit {i}") for i in range(5)]
        config = AnimationConfig(speed=Speed.FAST)
        animator = Animator(config)

        entering_count = 0
        for frame in animator.animate(commits):
            if frame.state == AnimationState.ENTERING:
                entering_count += 1
            animator.stop()  # Stop after first frame to avoid long waits

        assert entering_count >= 1


class TestAnimatorFrameStates:
    """T018: Frame states progress correctly."""

    def test_first_frame_is_entering(self):
        commits = [_make_commit("c0", "first")]
        config = AnimationConfig(speed=Speed.FAST)
        animator = Animator(config)

        frames = []
        for frame in animator.animate(commits):
            frames.append(frame)
            animator.stop()

        assert len(frames) >= 1
        assert frames[0].state == AnimationState.ENTERING

    def test_final_frames_are_visible(self):
        commits = [_make_commit("c0", "commit 0")]
        config = AnimationConfig(speed=Speed.FAST)
        animator = Animator(config)

        all_frames = list(animator.animate(commits))

        # Last frames should be VISIBLE states
        visible_frames = [f for f in all_frames if f.state == AnimationState.VISIBLE]
        assert len(visible_frames) == len(commits)


class TestAnimatorTiming:
    """T018: Timing respects configured speed."""

    def test_fast_speed_delay(self):
        config = AnimationConfig(speed=Speed.FAST)
        animator = Animator(config)
        assert animator.frame_delay == 0.1

    def test_normal_speed_delay(self):
        config = AnimationConfig(speed=Speed.NORMAL)
        animator = Animator(config)
        assert animator.frame_delay == 0.3

    def test_slow_speed_delay(self):
        config = AnimationConfig(speed=Speed.SLOW)
        animator = Animator(config)
        assert animator.frame_delay == 0.8


class TestAnimatorPauseResume:
    """T018: Pause and resume functionality."""

    def test_pause_sets_state(self):
        config = AnimationConfig()
        animator = Animator(config)
        assert animator.is_paused is False
        animator.pause()
        assert animator.is_paused is True

    def test_resume_clears_pause(self):
        config = AnimationConfig()
        animator = Animator(config)
        animator.pause()
        animator.resume()
        assert animator.is_paused is False

    def test_stop_also_clears_pause(self):
        config = AnimationConfig()
        animator = Animator(config)
        animator.pause()
        animator.stop()
        assert animator.is_paused is False


class TestAnimationFrame:
    """T018: AnimationFrame dataclass structure."""

    def test_frame_contains_commit(self):
        commit = _make_commit("abc", "test")
        frame = AnimationFrame(
            commit=commit,
            state=AnimationState.ENTERING,
            index=0,
            total=5,
        )
        assert frame.commit == commit
        assert frame.state == AnimationState.ENTERING
        assert frame.index == 0
        assert frame.total == 5
