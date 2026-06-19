"""Contract tests for CLI execution — verify exit codes and output contracts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _git_story(*args, cwd=None):
    """Run the git-story CLI and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, "-m", "git_story_animator.cli", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=15,
    )
    return result.returncode, result.stdout, result.stderr


class TestBasicCliExecution:
    """T010: Basic CLI contract tests."""

    def test_exit_code_zero_for_valid_repo(self, git_repo):
        """Running in a valid repo with commits should exit 0."""
        returncode, stdout, stderr = _git_story(cwd=git_repo)
        assert returncode == 0, f"stderr: {stderr}"
        assert stdout  # Should have some output

    def test_non_zero_for_non_repo(self, tmp_path):
        """Running outside a git repo should exit 1."""
        returncode, stdout, stderr = _git_story(cwd=str(tmp_path))
        assert returncode == 1, f"Expected exit code 1 for non-repo, got {returncode}"

    def test_stdout_contains_commit_fields(self, git_repo):
        """Stdout should contain expected commit data fields."""
        returncode, stdout, stderr = _git_story(cwd=git_repo)
        # In non-TTY mode (piped), we get plaintext with hash|author|date|subject
        assert returncode == 0
        # Should contain at least the pipe separator
        assert " | " in stdout


class TestExitCodes:
    """T035: Distinct exit codes."""

    def test_invalid_args_exit_code_3(self, git_repo):
        """Invalid arguments should exit with code 3."""
        returncode, stdout, stderr = _git_story("--count", "not-a-number", cwd=git_repo)
        assert returncode == 3, f"Expected exit code 3 for invalid args, got {returncode}"

    def test_help_exit_code_zero(self):
        """--help should exit with code 0."""
        returncode, stdout, stderr = _git_story("--help")
        assert returncode == 0

    def test_help_documents_exit_codes(self):
        """--help output should document exit codes."""
        returncode, stdout, stderr = _git_story("--help")
        assert returncode == 0
        assert "Exit codes" in stdout or "exit codes" in stdout.lower()


class TestJsonOutput:
    """T036: Contract test for JSON output."""

    def test_json_produces_valid_array(self, git_repo):
        """--json should produce valid JSON array with correct fields."""
        returncode, stdout, stderr = _git_story("--json", cwd=git_repo)
        assert returncode == 0

        data = json.loads(stdout)
        assert isinstance(data, list)
        assert len(data) > 0

        commit = data[0]
        assert "hash" in commit
        assert "author_name" in commit
        assert "timestamp" in commit
        assert "subject" in commit


class TestPipeDetection:
    """T037: Contract test for pipe detection."""

    def test_piped_output_is_plaintext(self, git_repo):
        """Redirected stdout should produce plaintext (no ANSI escape codes)."""
        returncode, stdout, stderr = _git_story(cwd=git_repo)
        # When piped through subprocess, stdout is not a TTY
        # Should not contain ANSI escape codes
        assert "\x1b[" not in stdout
