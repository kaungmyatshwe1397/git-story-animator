"""Unit tests for GitReader — mock subprocess for parsing validation."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest

from git_story_animator.git_reader import (
    GitReader,
    GitNotFoundError,
    NotAGitRepoError,
    EmptyRepoError,
    GitReaderError,
    _parse_single_commit,
    _FIELD_DELIMITER,
)


# ── Helpers ──────────────────────────────────────────────────────────────


def _mock_run(returncode=0, stdout="", stderr=""):
    """Create a mock subprocess.CompletedProcess."""
    result = MagicMock(spec=subprocess.CompletedProcess)
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    return result


def _make_log_line(
    hash="abc123def456",
    hash_short="abc123d",
    author_name="Alice",
    author_email="alice@example.com",
    unix_ts="1700000000",
    subject="fix bug",
    body="",
    parent_hashes="def789",
) -> str:
    return _FIELD_DELIMITER.join([
        hash,
        hash_short,
        author_name,
        author_email,
        unix_ts,
        subject,
        body,
        parent_hashes,
        "",
        "",
        "",
    ])


# ── Tests for _parse_single_commit ───────────────────────────────────────


class TestParseSingleCommit:
    def test_parses_basic_commit(self):
        line = _make_log_line(
            hash="abc123",
            hash_short="abc",
            author_name="Alice",
            author_email="alice@x.com",
            unix_ts="1700000000",
            subject="fix bug",
            parent_hashes="parent1 parent2",
        )
        commit = _parse_single_commit(line)

        assert commit.hash == "abc123"
        assert commit.hash_short == "abc"
        assert commit.author_name == "Alice"
        assert commit.author_email == "alice@x.com"
        assert commit.subject == "fix bug"
        assert commit.parent_hashes == ["parent1", "parent2"]
        assert commit.is_merge is True

    def test_parses_empty_parents_as_initial(self):
        line = _make_log_line(
            parent_hashes="",
        )
        commit = _parse_single_commit(line)
        assert commit.parent_hashes == []
        assert commit.is_initial is True

    def test_parses_missing_author(self):
        line = _make_log_line(
            author_name="",
            author_email="",
        )
        commit = _parse_single_commit(line)
        assert commit.author_name == ""
        assert commit.author_email == ""
        assert commit.author_display == "Unknown"

    def test_handles_missing_fields(self):
        # Only 5 fields instead of 11
        parts = ["h1", "h2", "name", "email", "ts"]
        line = _FIELD_DELIMITER.join(parts)
        commit = _parse_single_commit(line)
        assert commit.hash == "h1"
        assert commit.hash_short == "h2"

    def test_handles_invalid_timestamp(self):
        line = _make_log_line(unix_ts="not-a-number")
        commit = _parse_single_commit(line)
        # Falls back to epoch
        assert commit.timestamp == datetime.fromtimestamp(0, tz=timezone.utc)


# ── Tests for GitReader.get_commits ──────────────────────────────────────


class TestGitReaderGetCommits:
    def test_successful_parse(self):
        line1 = _make_log_line(hash="aaa", subject="first commit")
        line2 = _make_log_line(hash="bbb", subject="second commit")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _mock_run(
                returncode=0,
                stdout=line1 + "\n\n" + line2 + "\n",
            )
            reader = GitReader()
            commits = reader.get_commits(count=10)

        assert len(commits) == 2
        assert commits[0].hash == "aaa"
        assert commits[1].hash == "bbb"

    def test_not_a_git_repo_error(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _mock_run(
                returncode=128,
                stderr="fatal: not a git repository (or any of the parent directories): .git",
            )
            reader = GitReader()
            with pytest.raises(NotAGitRepoError):
                reader.get_commits()

    def test_empty_repo_error(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _mock_run(returncode=0, stdout="")
            reader = GitReader()
            with pytest.raises(EmptyRepoError):
                reader.get_commits()

    def test_git_not_found_error(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            reader = GitReader()
            with pytest.raises(GitNotFoundError):
                reader.get_commits()

    def test_empty_repo_stderr_message(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _mock_run(
                returncode=1,
                stderr="fatal: your current branch 'main' does not have any commits yet",
            )
            reader = GitReader()
            with pytest.raises(EmptyRepoError):
                reader.get_commits()

    def test_reverse_flag_passed(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _mock_run(
                returncode=0,
                stdout=_make_log_line() + "\n",
            )
            reader = GitReader()
            reader.get_commits(count=5, reverse=True)

            args = mock_run.call_args[0][0]
            assert "--reverse" in args

    def test_count_passed_to_git(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _mock_run(
                returncode=0,
                stdout=_make_log_line() + "\n",
            )
            reader = GitReader()
            reader.get_commits(count=42)

            args = mock_run.call_args[0][0]
            assert "--max-count=42" in args

    def test_merge_commit_parsing(self):
        line = _make_log_line(
            hash="mergehash",
            subject="Merge branch 'feature'",
            parent_hashes="parent1 parent2",
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _mock_run(returncode=0, stdout=line + "\n")
            reader = GitReader()
            commits = reader.get_commits()
            assert commits[0].is_merge is True

    def test_missing_author_in_parsed_output(self):
        line = _make_log_line(
            author_name="",
            author_email="",
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _mock_run(returncode=0, stdout=line + "\n")
            reader = GitReader()
            commits = reader.get_commits()
            assert commits[0].author_display == "Unknown"

    def test_timeout_error(self):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("git", 30)):
            reader = GitReader()
            with pytest.raises(GitReaderError, match="timed out"):
                reader.get_commits()


# ── Tests for GitReader._parse_shortstat ─────────────────────────────────


class TestParseShortstat:
    def test_all_fields(self):
        result = GitReader._parse_shortstat(
            " 1 file changed, 5 insertions(+), 3 deletions(-)"
        )
        assert result == {"files_changed": 1, "insertions": 5, "deletions": 3}

    def test_multiple_files(self):
        result = GitReader._parse_shortstat(
            " 10 files changed, 200 insertions(+), 50 deletions(-)"
        )
        assert result == {"files_changed": 10, "insertions": 200, "deletions": 50}

    def test_empty_string(self):
        result = GitReader._parse_shortstat("")
        assert result == {"files_changed": 0, "insertions": 0, "deletions": 0}

    def test_insertions_only(self):
        result = GitReader._parse_shortstat(" 1 file changed, 3 insertions(+)")
        assert result == {"files_changed": 1, "insertions": 3, "deletions": 0}

    def test_deletions_only(self):
        result = GitReader._parse_shortstat(" 1 file changed, 2 deletions(-)")
        assert result == {"files_changed": 1, "insertions": 0, "deletions": 2}
