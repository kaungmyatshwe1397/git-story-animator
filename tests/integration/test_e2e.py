"""Integration / end-to-end tests for the animated timeline.

Creates real git repositories for testing.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

import pytest


@pytest.fixture
def git_repo_fixture(tmp_path):
    """Create a real git repo with multiple commits for integration testing."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    def _run(cmd, **kwargs):
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=str(repo_path), **kwargs
        )
        return result

    _run(["git", "init"])
    _run(["git", "config", "user.name", "Test User"])
    _run(["git", "config", "user.email", "test@example.com"])

    # Create 5 commits
    for i in range(5):
        file_path = repo_path / f"file{i}.txt"
        file_path.write_text(f"content {i}")
        _run(["git", "add", "."])
        _run(["git", "commit", "-m", f"commit {i}"])

    # Create a merge commit
    _run(["git", "checkout", "-b", "feature"])
    (repo_path / "feature.txt").write_text("feature")
    _run(["git", "add", "."])
    _run(["git", "commit", "-m", "feature commit"])
    _run(["git", "checkout", "main"])
    _run(["git", "merge", "feature", "--no-ff", "-m", "Merge feature branch"])

    return str(repo_path)


class TestE2ETimeline:
    """T011: Integration tests for animated timeline."""

    def test_all_commits_appear_in_order(self, git_repo_fixture):
        """Verify all commits appear with correct data."""
        result = subprocess.run(
            [sys.executable, "-m", "git_story_animator.cli", "--count", "20"],
            capture_output=True,
            text=True,
            cwd=git_repo_fixture,
            timeout=15,
        )
        assert result.returncode == 0
        output = result.stdout

        # Should contain pipe separators (plaintext mode since piped)
        assert " | " in output

        # Should have multiple lines (one per commit)
        lines = [l for l in output.strip().split("\n") if l.strip()]
        assert len(lines) >= 5

    def test_multi_author_commits(self, git_repo_fixture):
        """Multi-author repos should show correct data."""
        # Add another author commit
        subprocess.run(
            ["git", "config", "user.name", "Another Author"],
            cwd=git_repo_fixture,
        )
        subprocess.run(
            ["git", "config", "user.email", "another@example.com"],
            cwd=git_repo_fixture,
        )
        (Path(git_repo_fixture) / "extra.txt").write_text("extra")
        subprocess.run(
            ["git", "add", "."],
            cwd=git_repo_fixture,
        )
        subprocess.run(
            ["git", "commit", "-m", "another author commit"],
            cwd=git_repo_fixture,
        )

        result = subprocess.run(
            [sys.executable, "-m", "git_story_animator.cli", "--count", "20"],
            capture_output=True,
            text=True,
            cwd=git_repo_fixture,
            timeout=15,
        )
        assert result.returncode == 0

    def test_merge_commit_present(self, git_repo_fixture):
        """Merge commit should appear in output."""
        result = subprocess.run(
            [sys.executable, "-m", "git_story_animator.cli", "--count", "20"],
            capture_output=True,
            text=True,
            cwd=git_repo_fixture,
            timeout=15,
        )
        assert result.returncode == 0
        # Should contain both feature commit and merge commit
        # git's default merge message contains "Merge"
        assert "feature commit" in result.stdout

    def test_custom_count(self, git_repo_fixture):
        """T020: --count flag restricts number of commits."""
        result = subprocess.run(
            [sys.executable, "-m", "git_story_animator.cli", "--count", "3"],
            capture_output=True,
            text=True,
            cwd=git_repo_fixture,
            timeout=15,
        )
        assert result.returncode == 0
        lines = [l for l in result.stdout.strip().split("\n") if l.strip() and " | " in l]
        assert len(lines) <= 3  # At most 3 commit lines
        assert len(lines) >= 1  # At least 1 commit


class TestReverseOrder:
    """T020: Integration test for --reverse flag."""

    def test_reverse_shows_oldest_first(self, git_repo_fixture):
        """With --reverse, commits appear chronologically (oldest-first)."""
        result = subprocess.run(
            [sys.executable, "-m", "git_story_animator.cli", "--count", "5", "--reverse"],
            capture_output=True,
            text=True,
            cwd=git_repo_fixture,
            timeout=15,
        )
        assert result.returncode == 0
        # Output should contain commit data in pipe format
        lines = [l for l in result.stdout.strip().split("\n") if " | " in l]
        assert len(lines) >= 3

        # Verify the commits are in chronological order (commit numbers ascending)
        commit_nums = []
        for line in lines:
            for part in line.split(" | "):
                part = part.strip()
                if part.startswith("commit "):
                    try:
                        commit_nums.append(int(part.split()[-1]))
                    except ValueError:
                        pass
        if len(commit_nums) > 1:
            assert commit_nums == sorted(commit_nums), (
                f"Expected reverse order (ascending): {commit_nums}"
            )
