"""Animation engine — controls frame sequencing and timing for the timeline animation."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from .models import Commit, AnimationConfig, AnimationState, Speed

# Frame delay mapping (seconds)
_SPEED_DELAYS: dict[Speed, float] = {
    Speed.SLOW: 0.8,
    Speed.NORMAL: 0.3,
    Speed.FAST: 0.1,
}


@dataclass
class AnimationFrame:
    """A single step in the animation sequence."""

    commit: Commit
    state: AnimationState
    index: int
    total: int


class Animator:
    """Controls the animation playback sequence.

    Iterates over commits, yielding frames with progressive timing for
    the renderer to display.

    Usage:
        animator = Animator(config)
        for frame in animator.animate(commits):
            renderer.render_frame(frame)
    """

    def __init__(self, config: AnimationConfig):
        """Initialize the animator.

        Args:
            config: Animation configuration controlling speed and behavior.
        """
        self.config = config
        self._paused = False
        self._stop = False

    @property
    def frame_delay(self) -> float:
        """Get the delay between frames based on configured speed."""
        return _SPEED_DELAYS.get(self.config.speed, 0.3)

    def animate(self, commits: list[Commit]):
        """Generator yielding animation frames with timing.

        Args:
            commits: Ordered list of commits to animate.

        Yields:
            AnimationFrame objects with progressive timing.
        """
        total = len(commits)

        for i, commit in enumerate(commits):
            if self._stop:
                break

            if self._paused:
                # When paused, keep yielding the current frame
                while self._paused and not self._stop:
                    time.sleep(0.05)

            if self._stop:
                break

            # New commit entering
            frame = AnimationFrame(
                commit=commit,
                state=AnimationState.ENTERING,
                index=i,
                total=total,
            )
            yield frame

            # Delay between frames (skip delay for the last commit)
            if i < total - 1:
                self._sleep_with_check(self.frame_delay)

        # Final frame: all commits visible
        if not self._stop and commits:
            for i, commit in enumerate(commits):
                frame = AnimationFrame(
                    commit=commit,
                    state=AnimationState.VISIBLE,
                    index=i,
                    total=total,
                )
                yield frame

    def pause(self) -> None:
        """Pause the animation."""
        self._paused = True

    def resume(self) -> None:
        """Resume the animation from pause."""
        self._paused = False

    def stop(self) -> None:
        """Stop the animation entirely."""
        self._stop = True
        self._paused = False

    @property
    def is_paused(self) -> bool:
        return self._paused

    def _sleep_with_check(self, duration: float) -> None:
        """Sleep for duration, but check pause/stop state periodically."""
        check_interval = 0.05
        elapsed = 0.0
        while elapsed < duration:
            if self._stop:
                return
            if self._paused:
                while self._paused and not self._stop:
                    time.sleep(0.05)
                if self._stop:
                    return
            sleep_time = min(check_interval, duration - elapsed)
            time.sleep(sleep_time)
            elapsed += sleep_time
