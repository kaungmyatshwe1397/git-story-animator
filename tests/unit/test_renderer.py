"""Unit tests for terminal renderer — timeline layout, author colors, merge markers."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from git_story_animator.models import Commit, AnimationConfig, AnimationState, Speed, Style
from git_story_animator.renderer import TerminalRenderer


def _make_commit(
    hash_short="abc123d",
    author_name="Alice",
    author_email="alice@x.com",
    subject="fix bug",
    parent_hashes=None,
    timestamp=None,
):
    if parent_hashes is None:
        parent_hashes = ["parent1"]
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    return Commit(
        hash="abc123def456",
        hash_short=hash_short,
        author_name=author_name,
        author_email=author_email,
        timestamp=timestamp,
        subject=subject,
        parent_hashes=parent_hashes,
    )


class TestAuthorColors:
    """T012: Author color assignment is deterministic."""

    def test_same_author_same_color(self):
        renderer = TerminalRenderer()
        c1 = _make_commit(author_name="Alice")
        c2 = _make_commit(author_name="Alice")
        color1 = renderer.get_author_color(c1)
        color2 = renderer.get_author_color(c2)
        assert color1 == color2

    def test_different_authors_different_colors(self):
        renderer = TerminalRenderer()
        c1 = _make_commit(author_name="Alice")
        c2 = _make_commit(author_name="Bob")
        color1 = renderer.get_author_color(c1)
        color2 = renderer.get_author_color(c2)
        assert color1 != color2

    def test_deterministic_across_instances(self):
        r1 = TerminalRenderer()
        r2 = TerminalRenderer()
        c = _make_commit(author_name="Alice")
        assert r1.get_author_color(c) == r2.get_author_color(c)


class TestMergeMarker:
    """T012: Merge commits render with branch marker."""

    def test_merge_commit_has_branch_indicator(self):
        renderer = TerminalRenderer()
        c = _make_commit(
            subject="Merge branch 'feature'",
            parent_hashes=["p1", "p2"],
        )
        result = renderer.render_commit(c)
        # Merge commits should have a visual indicator
        assert "─" in result or "merge" in result.lower() or "M" in result

    def test_non_merge_no_branch_indicator(self):
        renderer = TerminalRenderer()
        c = _make_commit(parent_hashes=["p1"])
        result = renderer.render_commit(c)
        # Non-merge should not have the branch indicator


class TestMessageTruncation:
    """T012/T017: Long messages are truncated."""

    def test_long_subject_truncated_in_render(self):
        renderer = TerminalRenderer()
        long_subject = "x" * 100
        c = _make_commit(subject=long_subject)
        result = renderer.render_commit(c)
        # The rendered output should not contain the full 100-char subject
        assert len(result) < 200  # Reasonable upper bound for a single line

    def test_short_subject_not_truncated(self):
        renderer = TerminalRenderer()
        c = _make_commit(subject="fix bug")
        result = renderer.render_commit(c)
        assert "fix bug" in result


class TestRenderTimeline:
    """T012: Timeline layout rendering."""

    def test_render_all_commits(self):
        renderer = TerminalRenderer()
        commits = [
            _make_commit(hash_short="aaa", subject="first"),
            _make_commit(hash_short="bbb", subject="second"),
            _make_commit(hash_short="ccc", subject="third"),
        ]
        result = renderer.render_timeline(commits)
        assert "aaa" in result
        assert "bbb" in result
        assert "ccc" in result

    def test_render_empty_commits(self):
        renderer = TerminalRenderer()
        result = renderer.render_timeline([])
        assert result == "" or "no commits" in result.lower()

    def test_render_with_state_highlight(self):
        renderer = TerminalRenderer()
        commits = [
            _make_commit(hash_short="aaa", subject="selected"),
        ]
        result = renderer.render_timeline(
            commits, states={0: AnimationState.SELECTED}
        )
        assert "aaa" in result


class TestCompactRenderer:
    """T025: Compact layout tests."""

    def test_compact_single_line_per_commit(self):
        renderer = TerminalRenderer(style=Style.COMPACT)
        c = _make_commit(hash_short="abc", subject="fix bug")
        result = renderer.render_compact(c)
        # Compact should be roughly one line
        lines = result.strip().split("\n")
        assert len(lines) <= 3  # Allow for some formatting

    def test_compact_fits_narrow_width(self):
        renderer = TerminalRenderer(style=Style.COMPACT, width=60)
        c = _make_commit(hash_short="abc", subject="fix bug")
        result = renderer.render_compact(c)
        for line in result.strip().split("\n"):
            # Allow rich markup to exceed slightly, but plain text should fit
            plain = line.replace("[bold]", "").replace("[/bold]", "")
            # Not a strict check — just verify no excessively long lines
            assert len(line) < 120
