"""Terminal renderer for commit timeline.

Uses the `rich` library to render commit entries with author colors,
merge markers, and configurable layout styles.
"""

from __future__ import annotations

from .models import Commit, AnimationState, Style

# Rich color palette for deterministic author color assignment
_AUTHOR_COLORS = [
    "cyan",
    "green",
    "yellow",
    "magenta",
    "bright_cyan",
    "bright_green",
    "bright_yellow",
    "bright_magenta",
    "blue",
    "bright_blue",
    "red",
    "bright_red",
]


class TerminalRenderer:
    """Renders commit timeline entries to strings using rich markup.

    Usage:
        renderer = TerminalRenderer(style=Style.DEFAULT)
        output = renderer.render_timeline(commits)
    """

    def __init__(
        self,
        style: Style = Style.DEFAULT,
        width: int | None = None,
    ):
        """Initialize the renderer.

        Args:
            style: Layout style (DEFAULT or COMPACT).
            width: Terminal width. Detected automatically if None.
        """
        self.style = style
        self._width = width

    @property
    def width(self) -> int:
        """Get terminal width, with fallback to 80."""
        if self._width is not None:
            return self._width
        import shutil

        size = shutil.get_terminal_size()
        return max(size.columns, 40)

    def get_author_color(self, commit: Commit) -> str:
        """Get a deterministic color for a commit's author.

        Args:
            commit: The commit to get a color for.

        Returns:
            A rich color name string.
        """
        key = commit.author_color_key
        # Use the first 4 hex chars as an index
        idx = int(key[:4], 16) % len(_AUTHOR_COLORS)
        return _AUTHOR_COLORS[idx]

    def render_commit(
        self,
        commit: Commit,
        state: AnimationState = AnimationState.VISIBLE,
    ) -> str:
        """Render a single commit as a timeline entry.

        Args:
            commit: The commit to render.
            state: Animation state affecting display style.

        Returns:
            A string with rich markup for the commit entry.
        """
        if self.style == Style.COMPACT:
            return self.render_compact(commit, state)

        return self.render_default(commit, state)

    def render_default(
        self,
        commit: Commit,
        state: AnimationState = AnimationState.VISIBLE,
    ) -> str:
        """Render a commit in default (full) layout.

        Format: [hash] [author] [rel_date] subject
        """
        color = self.get_author_color(commit)

        # Truncate subject for display
        subject = commit.subject_truncated(max_len=72)

        # Hash display
        hash_str = f"[dim]{commit.hash_short}[/dim]"

        # Author with color
        author_str = f"[{color} bold]{commit.author_display}[/{color} bold]"

        # Relative date
        date_str = f"[dim]{commit.relative_date}[/dim]"

        # Subject (truncated)
        subject_str = subject

        # Merge indicator
        prefix = ""
        if commit.is_merge:
            prefix = "[bold bright_yellow]⟐[/bold bright_yellow] "
            subject_str = f"[italic]{subject_str}[/italic]"

        # Build the line
        line = f"{prefix}{hash_str}  {author_str}  {date_str}  {subject_str}"

        return line

    def render_compact(
        self,
        commit: Commit,
        state: AnimationState = AnimationState.VISIBLE,
    ) -> str:
        """Render a commit in compact layout (narrow terminals).

        Format: [hash] subject
        """
        color = self.get_author_color(commit)

        hash_str = f"[dim]{commit.hash_short}[/dim]"
        subject = commit.subject_truncated(max_len=40)

        prefix = ""
        if commit.is_merge:
            prefix = "[bold bright_yellow]⟐[/bold bright_yellow] "

        author_short = commit.author_display[:12].ljust(12)
        author_str = f"[{color}]{author_short}[/{color}]"

        line = f"{prefix}{hash_str} {author_str} {subject}"

        return line

    def render_timeline(
        self,
        commits: list[Commit],
        states: dict[int, AnimationState] | None = None,
    ) -> str:
        """Render all commits as a full timeline.

        Args:
            commits: List of commits to display.
            states: Optional mapping of commit index → AnimationState.

        Returns:
            Full timeline string with rich markup.
        """
        if not commits:
            return ""

        if states is None:
            states = {}

        lines: list[str] = []

        for i, commit in enumerate(commits):
            state = states.get(i, AnimationState.VISIBLE)
            line = self.render_commit(commit, state)
            lines.append(line)

        return "\n".join(lines)

    def render_expanded(
        self,
        commit: Commit,
        files_changed: int = 0,
        insertions: int = 0,
        deletions: int = 0,
    ) -> str:
        """Render a commit in expanded view with full details.

        Args:
            commit: The commit to expand.
            files_changed: Number of files changed.
            insertions: Number of lines inserted.
            deletions: Number of lines deleted.

        Returns:
            Expanded view string with rich markup.
        """
        color = self.get_author_color(commit)

        lines = [
            f"[bold white]Commit:[/bold white] {commit.hash}",
            f"[bold white]Author:[/bold white] [{color}]{commit.author_display}[/{color}] "
            f"[dim]<{commit.author_email}>[/dim]",
            f"[bold white]Date:[/bold white] {commit.timestamp.strftime('%Y-%m-%d %H:%M:%S %z')}",
            f"[bold white]Subject:[/bold white] [bold]{commit.subject}[/bold]",
        ]

        if commit.body:
            lines.append("")
            lines.append("[bold white]Message:[/bold white]")
            for body_line in commit.body.strip().split("\n"):
                lines.append(f"  {body_line}")

        lines.append("")
        lines.append(
            f"[bold white]Changes:[/bold white] "
            f"{files_changed} files, "
            f"[green]+{insertions}[/green] "
            f"[red]-{deletions}[/red]"
        )

        if commit.is_merge:
            lines.append("")
            parents = ", ".join(commit.parent_hashes)
            lines.append(
                f"[bold bright_yellow]Merge commit[/bold bright_yellow] "
                f"— parents: [dim]{parents}[/dim]"
            )

        return "\n".join(lines)
