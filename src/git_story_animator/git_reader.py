"""Git log reader — wraps `git log` subprocess and parses output into Commit objects."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .models import Commit

# Custom field delimiter used to separate fields in `git log --format=...`
_FIELD_DELIMITER = "\x1e"  # ASCII Record Separator
_COMMIT_DELIMITER = "\x1f"  # ASCII Unit Separator

# git log format string producing machine-parseable output.
# Fields: hash, hash_short, author_name, author_email, timestamp (unix), subject,
#         body, parent_hashes (space-separated), files_changed, insertions, deletions
_GIT_LOG_FORMAT = (
    "%H" + _FIELD_DELIMITER +       # full hash
    "%h" + _FIELD_DELIMITER +       # abbreviated hash
    "%an" + _FIELD_DELIMITER +      # author name
    "%ae" + _FIELD_DELIMITER +      # author email
    "%at" + _FIELD_DELIMITER +      # author timestamp (unix)
    "%s" + _FIELD_DELIMITER +       # subject
    "%b" + _FIELD_DELIMITER +       # body
    "%P" + _FIELD_DELIMITER +       # parent hashes
    "" + _FIELD_DELIMITER +         # placeholder for --stat parse
    "" + _FIELD_DELIMITER +         # placeholder
    ""                               # placeholder
)


class GitReaderError(Exception):
    """Base exception for git reading errors."""


class NotAGitRepoError(GitReaderError):
    """Raised when the current directory is not inside a git repository."""


class GitNotFoundError(GitReaderError):
    """Raised when `git` is not found on PATH."""


class EmptyRepoError(GitReaderError):
    """Raised when the repository has no commits."""


def _parse_single_commit(raw: str) -> Commit:
    """Parse a single commit from the delimited log line + stat info.

    Args:
        raw: Raw delimited string for one commit (may contain newlines for body).

    Returns:
        A populated Commit instance.
    """
    parts = raw.split(_FIELD_DELIMITER)

    # We expect at least 11 fields; pad with empty strings if short
    while len(parts) < 11:
        parts.append("")

    (
        full_hash,
        short_hash,
        author_name,
        author_email,
        unix_ts,
        subject,
        body,
        parent_str,
        _stat_placeholder,
        insertions_str,
        deletions_str,
    ) = parts[:11]

    # Parse timestamp
    try:
        ts = int(unix_ts.strip()) if unix_ts.strip() else 0
        timestamp = datetime.fromtimestamp(ts, tz=timezone.utc)
    except (ValueError, OSError):
        timestamp = datetime.fromtimestamp(0, tz=timezone.utc)

    # Parse parent hashes
    parent_hashes = [p for p in parent_str.strip().split() if p]

    # Parse stats
    try:
        files_changed = 0  # We'll count from --name-only if needed
        insertions = int(insertions_str.strip()) if insertions_str.strip() else 0
        deletions = int(deletions_str.strip()) if deletions_str.strip() else 0
    except ValueError:
        insertions = 0
        deletions = 0

    return Commit(
        hash=full_hash.strip(),
        hash_short=short_hash.strip(),
        author_name=author_name.strip(),
        author_email=author_email.strip(),
        timestamp=timestamp,
        subject=subject.strip(),
        body=body.strip(),
        parent_hashes=parent_hashes,
        files_changed=files_changed,
        insertions=insertions,
        deletions=deletions,
    )


class GitReader:
    """Reads commit history from a local git repository via `git log` subprocess.

    Usage:
        reader = GitReader()
        commits = reader.get_commits(count=10)
    """

    def __init__(self, repo_path: str | Path | None = None):
        """Initialize the reader.

        Args:
            repo_path: Path to the git repository. Defaults to current directory.
        """
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()

    def get_commits(
        self,
        count: int = 10,
        reverse: bool = False,
    ) -> list[Commit]:
        """Read the most recent *count* commits from the repository.

        Args:
            count: Number of recent commits to retrieve.
            reverse: If True, return commits oldest-first instead of newest-first.

        Returns:
            List of Commit objects.

        Raises:
            GitNotFoundError: git is not installed or not on PATH.
            NotAGitRepoError: The path is not inside a git repository.
            EmptyRepoError: The repository has no commits.
        """
        # Build the format with stat summary appended
        format_str = _GIT_LOG_FORMAT + "%n"  # stat info will follow

        cmd = [
            "git",
            "log",
            f"--format={format_str}",
            f"--max-count={count}",
            "--shortstat",
        ]

        if reverse:
            cmd.append("--reverse")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.repo_path),
                timeout=30,
            )
        except FileNotFoundError:
            raise GitNotFoundError(
                "git is not installed. Please install git to use git-story."
            )
        except subprocess.TimeoutExpired:
            raise GitReaderError(
                "git log timed out after 30 seconds. The repository may be too large."
            )

        # Check for errors
        stderr = result.stderr.strip()
        if result.returncode != 0:
            if "not a git repository" in stderr.lower():
                raise NotAGitRepoError(
                    f"Not a git repository: {self.repo_path}\n"
                    "Run this command from inside a git repository."
                )
            if "does not have any commits" in stderr.lower():
                raise EmptyRepoError(
                    "No commits yet — make your first commit to see the story."
                )
            raise GitReaderError(f"git log failed: {stderr}")

        stdout = result.stdout.strip()
        if not stdout:
            raise EmptyRepoError(
                "No commits yet — make your first commit to see the story."
            )

        commits = self._parse_combined_output(stdout)
        return commits

    def get_commit_stat(self, commit_hash: str) -> dict[str, int]:
        """Get detailed stat information for a single commit.

        Args:
            commit_hash: Full or abbreviated commit hash.

        Returns:
            Dict with 'files_changed', 'insertions', 'deletions'.
        """
        cmd = [
            "git",
            "show",
            "--shortstat",
            "--format=",
            commit_hash,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.repo_path),
                timeout=10,
            )
        except FileNotFoundError:
            raise GitNotFoundError("git is not installed.")
        except subprocess.TimeoutExpired:
            return {"files_changed": 0, "insertions": 0, "deletions": 0}

        output = result.stdout.strip()
        return self._parse_shortstat(output)

    @staticmethod
    def _parse_shortstat(stat_line: str) -> dict[str, int]:
        """Parse git --shortstat output like:
        '1 file changed, 2 insertions(+), 3 deletions(-)'
        """
        files = 0
        insertions = 0
        deletions = 0

        import re

        m = re.search(r"(\d+)\s+files?\s+changed", stat_line)
        if m:
            files = int(m.group(1))

        m = re.search(r"(\d+)\s+insertions?\(\+\)", stat_line)
        if m:
            insertions = int(m.group(1))

        m = re.search(r"(\d+)\s+deletions?\(\-\)", stat_line)
        if m:
            deletions = int(m.group(1))

        return {"files_changed": files, "insertions": insertions, "deletions": deletions}

    def _parse_combined_output(self, output: str) -> list[Commit]:
        """Parse combined git log output with format + shortstat.

        git log outputs: format line + newline + shortstat line + newline + ...
        We split by the commit delimiter or by detecting format line starts.
        """
        commits: list[Commit] = []
        lines = output.split("\n")

        current_format_line: str | None = None
        current_stat_line: str | None = None

        for line in lines:
            # Format lines contain our field delimiter
            if _FIELD_DELIMITER in line and current_format_line is None:
                current_format_line = line
            elif _FIELD_DELIMITER in line and current_format_line is not None:
                # Previous commit's stat might still be pending
                if current_format_line:
                    commit = _parse_single_commit(current_format_line)
                    if current_stat_line:
                        stats = self._parse_shortstat(current_stat_line)
                        commit.files_changed = stats["files_changed"]
                        commit.insertions = stats["insertions"]
                        commit.deletions = stats["deletions"]
                    commits.append(commit)
                current_format_line = line
                current_stat_line = None
            elif line.strip() and _FIELD_DELIMITER not in line:
                # This is a stat line
                current_stat_line = line

        # Don't forget the last commit
        if current_format_line:
            commit = _parse_single_commit(current_format_line)
            if current_stat_line:
                stats = self._parse_shortstat(current_stat_line)
                commit.files_changed = stats["files_changed"]
                commit.insertions = stats["insertions"]
                commit.deletions = stats["deletions"]
            commits.append(commit)

        return commits
