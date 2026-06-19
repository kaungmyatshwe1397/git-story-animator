"""Shared test fixtures for git-story-animator tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def git_repo(tmp_path):
    """Create a small git repo with a few commits for testing.

    Used by contract tests and integration tests.
    """
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    def _run(cmd, **kwargs):
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(repo_path),
            **kwargs,
        )

    _run(["git", "init"])
    _run(["git", "config", "user.name", "Test User"])
    _run(["git", "config", "user.email", "test@example.com"])

    for i in range(3):
        file_path = repo_path / f"file{i}.txt"
        file_path.write_text(f"content {i}")
        _run(["git", "add", "."])
        _run(["git", "commit", "-m", f"commit {i}"])

    return str(repo_path)
