"""Unit tests for Commit model, AnimationConfig, and enums."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest

from git_story_animator.models import (
    Commit,
    AnimationConfig,
    Speed,
    Style,
    AnimationState,
)


# ── Commit model tests (T007) ────────────────────────────────────────────


class TestCommitIsMerge:
    """is_merge detection."""

    def test_single_parent_not_merge(self):
        c = Commit(
            hash="abc123",
            hash_short="abc",
            author_name="Alice",
            author_email="alice@example.com",
            timestamp=datetime.now(timezone.utc),
            subject="fix bug",
            parent_hashes=["def456"],
        )
        assert c.is_merge is False

    def test_two_parents_is_merge(self):
        c = Commit(
            hash="abc123",
            hash_short="abc",
            author_name="Alice",
            author_email="alice@example.com",
            timestamp=datetime.now(timezone.utc),
            subject="Merge branch",
            parent_hashes=["def456", "789ghi"],
        )
        assert c.is_merge is True

    def test_zero_parents_is_initial(self):
        c = Commit(
            hash="abc123",
            hash_short="abc",
            author_name="Alice",
            author_email="alice@example.com",
            timestamp=datetime.now(timezone.utc),
            subject="initial commit",
            parent_hashes=[],
        )
        assert c.is_initial is True
        assert c.is_merge is False


class TestCommitRelativeDate:
    """relative_date formatting."""

    def test_seconds_ago(self):
        ts = datetime.now(timezone.utc) - timedelta(seconds=30)
        c = _make_commit(timestamp=ts)
        assert "s ago" in c.relative_date

    def test_minutes_ago(self):
        ts = datetime.now(timezone.utc) - timedelta(minutes=10)
        c = _make_commit(timestamp=ts)
        assert "m ago" in c.relative_date

    def test_hours_ago(self):
        ts = datetime.now(timezone.utc) - timedelta(hours=3)
        c = _make_commit(timestamp=ts)
        assert "h ago" in c.relative_date

    def test_days_ago(self):
        ts = datetime.now(timezone.utc) - timedelta(days=5)
        c = _make_commit(timestamp=ts)
        assert "d ago" in c.relative_date

    def test_weeks_ago(self):
        ts = datetime.now(timezone.utc) - timedelta(days=14)
        c = _make_commit(timestamp=ts)
        assert "w ago" in c.relative_date

    def test_years_ago(self):
        ts = datetime.now(timezone.utc) - timedelta(days=400)
        c = _make_commit(timestamp=ts)
        assert "y ago" in c.relative_date

    def test_future_timestamp_returns_just_now(self):
        ts = datetime.now(timezone.utc) + timedelta(hours=1)
        c = _make_commit(timestamp=ts)
        assert c.relative_date == "just now"


class TestCommitAuthorDisplay:
    """author_display fallback chain."""

    def test_author_name_takes_priority(self):
        c = _make_commit(author_name="Alice", author_email="alice@example.com")
        assert c.author_display == "Alice"

    def test_falls_back_to_email_prefix(self):
        c = _make_commit(author_name="", author_email="bob@example.com")
        assert c.author_display == "bob"

    def test_falls_back_to_unknown(self):
        c = _make_commit(author_name="", author_email="")
        assert c.author_display == "Unknown"

    def test_whitespace_name_falls_back(self):
        c = _make_commit(author_name="   ", author_email="carol@example.com")
        assert c.author_display == "carol"


class TestCommitSubjectTruncation:
    """Subject line truncation."""

    def test_short_subject_not_truncated(self):
        c = _make_commit(subject="fix typo")
        assert c.subject_truncated() == "fix typo"

    def test_long_subject_truncated_with_ellipsis(self):
        long_subject = "A" * 100
        c = _make_commit(subject=long_subject)
        truncated = c.subject_truncated(max_len=80)
        assert len(truncated) == 80
        assert truncated.endswith("…")

    def test_custom_max_len(self):
        c = _make_commit(subject="Hello World")
        truncated = c.subject_truncated(max_len=6)
        assert truncated == "Hello…"


# ── AnimationConfig tests (T009) ─────────────────────────────────────────


class TestAnimationConfigDefaults:
    """Default values per spec."""

    def test_default_count_is_10(self):
        config = AnimationConfig()
        assert config.count == 10

    def test_default_speed_is_normal(self):
        config = AnimationConfig()
        assert config.speed == Speed.NORMAL

    def test_default_style_is_default(self):
        config = AnimationConfig()
        assert config.style == Style.DEFAULT

    def test_default_reverse_is_false(self):
        config = AnimationConfig()
        assert config.reverse is False

    def test_default_json_mode_is_false(self):
        config = AnimationConfig()
        assert config.json_mode is False

    def test_default_interactive_is_true(self):
        config = AnimationConfig()
        assert config.interactive is True


class TestSpeedEnum:
    def test_three_values(self):
        assert len(Speed) == 3
        assert Speed.SLOW.value == "slow"
        assert Speed.NORMAL.value == "normal"
        assert Speed.FAST.value == "fast"


class TestStyleEnum:
    def test_two_values(self):
        assert len(Style) == 2
        assert Style.DEFAULT.value == "default"
        assert Style.COMPACT.value == "compact"


class TestAnimationStateEnum:
    def test_three_states(self):
        assert len(AnimationState) == 3
        assert AnimationState.ENTERING.value == "entering"
        assert AnimationState.VISIBLE.value == "visible"
        assert AnimationState.SELECTED.value == "selected"


# ── Helpers ──────────────────────────────────────────────────────────────


def _make_commit(
    hash: str = "abc123",
    hash_short: str = "abc",
    author_name: str = "Alice",
    author_email: str = "alice@example.com",
    timestamp: datetime | None = None,
    subject: str = "test commit",
    body: str = "",
    parent_hashes: list[str] | None = None,
) -> Commit:
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    if parent_hashes is None:
        parent_hashes = ["def456"]
    return Commit(
        hash=hash,
        hash_short=hash_short,
        author_name=author_name,
        author_email=author_email,
        timestamp=timestamp,
        subject=subject,
        body=body,
        parent_hashes=parent_hashes,
    )
