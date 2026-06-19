"""Data models for Git Story Animator.

Commit dataclass, enums for animation control, and AnimationConfig.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class Speed(Enum):
    """Animation playback speed."""
    SLOW = "slow"
    NORMAL = "normal"
    FAST = "fast"


class Style(Enum):
    """Timeline display style."""
    DEFAULT = "default"
    COMPACT = "compact"


class AnimationState(Enum):
    """State of a single commit in the animation sequence."""
    ENTERING = "entering"
    VISIBLE = "visible"
    SELECTED = "selected"


@dataclass
class Commit:
    """A single commit from the git history.

    Fields parsed from `git log` output with a custom delimiter-based format.
    """

    hash: str
    hash_short: str
    author_name: str
    author_email: str
    timestamp: datetime
    subject: str
    body: str = ""
    parent_hashes: list[str] = field(default_factory=list)
    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0

    # --- Computed properties ---

    @property
    def is_merge(self) -> bool:
        """A merge commit has more than one parent."""
        return len(self.parent_hashes) > 1

    @property
    def is_initial(self) -> bool:
        """The initial/root commit has no parents."""
        return len(self.parent_hashes) == 0

    @property
    def relative_date(self) -> str:
        """Human-friendly relative date string (e.g. '2 hours ago')."""
        now = datetime.now(timezone.utc)
        delta = now - self.timestamp

        seconds = int(delta.total_seconds())
        if seconds < 0:
            return "just now"

        minutes = seconds // 60
        if minutes < 1:
            return f"{seconds}s ago"
        if minutes < 60:
            return f"{minutes}m ago"

        hours = minutes // 60
        if hours < 24:
            return f"{hours}h ago"

        days = hours // 24
        if days < 7:
            return f"{days}d ago"

        weeks = days // 7
        if weeks < 52:
            return f"{weeks}w ago"

        years = days // 365
        return f"{years}y ago"

    @property
    def author_display(self) -> str:
        """Best available author name for display.

        Fallback chain: author_name → email local-part → 'Unknown'.
        """
        if self.author_name and self.author_name.strip():
            return self.author_name.strip()
        if self.author_email:
            local = self.author_email.split("@")[0]
            if local.strip():
                return local.strip()
        return "Unknown"

    @property
    def author_color_key(self) -> str:
        """A stable, deterministic key derived from the author for color assignment."""
        raw = self.author_display
        return hashlib.sha256(raw.encode()).hexdigest()[:8]

    def subject_truncated(self, max_len: int = 80) -> str:
        """Truncate subject line with ellipsis if too long."""
        if len(self.subject) <= max_len:
            return self.subject
        return self.subject[: max_len - 1] + "…"


@dataclass
class AnimationConfig:
    """Configuration for animation playback.

    All fields use defaults matching the spec (FR-005 through FR-009).
    """

    count: int = 10
    speed: Speed = Speed.NORMAL
    style: Style = Style.DEFAULT
    reverse: bool = False
    json_mode: bool = False
    interactive: bool = True
