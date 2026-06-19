"""CLI entry point for Git Story Animator.

Parses arguments, wires up GitReader -> Animator -> TerminalRenderer,
and handles TTY vs non-TTY output modes.
"""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .models import AnimationConfig, Speed, Style
from .git_reader import (
    GitReader,
    GitNotFoundError,
    NotAGitRepoError,
    EmptyRepoError,
)
from .renderer import TerminalRenderer
from .animator import Animator


def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with all CLI flags."""
    parser = argparse.ArgumentParser(
        prog="git-story",
        description="Animate git commit history as a clean timeline in your terminal",
    )

    parser.add_argument(
        "--count", "-n",
        type=int,
        default=10,
        help="Number of recent commits to display (default: 10)",
    )

    parser.add_argument(
        "--speed",
        choices=["slow", "normal", "fast"],
        default="normal",
        help="Animation playback speed (default: normal)",
    )

    parser.add_argument(
        "--style",
        choices=["default", "compact"],
        default="default",
        help="Timeline display style (default: default)",
    )

    parser.add_argument(
        "--reverse",
        action="store_true",
        help="Display commits from oldest to newest",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output commit data as JSON (no animation)",
    )

    parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Disable interactive mode (keyboard controls)",
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Print version and exit",
    )

    return parser


def _build_config(args: argparse.Namespace) -> AnimationConfig:
    """Build AnimationConfig from parsed arguments."""
    speed_map = {
        "slow": Speed.SLOW,
        "normal": Speed.NORMAL,
        "fast": Speed.FAST,
    }
    style_map = {
        "default": Style.DEFAULT,
        "compact": Style.COMPACT,
    }

    return AnimationConfig(
        count=args.count,
        speed=speed_map[args.speed],
        style=style_map[args.style],
        reverse=args.reverse,
        json_mode=args.json,
        interactive=not args.no_interactive,
    )


def _format_plaintext(commits) -> str:
    """Format commits as plain tab-separated text for non-TTY output.

    Format: hash | author | date | subject
    """
    lines = []
    for c in commits:
        lines.append(
            f"{c.hash_short} | {c.author_display} | "
            f"{c.relative_date} | {c.subject_truncated()}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Main entry point for git-story.

    Args:
        argv: Command-line arguments (uses sys.argv if None).

    Returns:
        Exit code: 0 success, 1 not a git repo, 2 git not installed, 3 invalid args.
    """
    parser = _build_parser()

    # Add exit code documentation to help output
    parser.epilog = (
        "Exit codes: 0 (success), 1 (not a git repo), "
        "2 (git not installed), 3 (invalid arguments)"
    )

    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        # argparse raises SystemExit(2) on invalid arguments
        # Convert to our exit code 3
        if e.code == 0:
            return 0
        return 3

    # --version flag
    if args.version:
        print(f"git-story {__version__}")
        return 0

    # Build config
    config = _build_config(args)

    # Read commits
    reader = GitReader()
    try:
        commits = reader.get_commits(count=config.count, reverse=config.reverse)
    except GitNotFoundError:
        print("Error: git is not installed.", file=sys.stderr)
        return 2
    except NotAGitRepoError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except EmptyRepoError as e:
        print(str(e))
        return 0

    if not commits:
        print("No commits yet — make your first commit to see the story.")
        return 0

    # --json mode: output JSON and exit
    if config.json_mode:
        data = []
        for c in commits:
            data.append({
                "hash": c.hash,
                "hash_short": c.hash_short,
                "author_name": c.author_name,
                "author_email": c.author_email,
                "timestamp": c.timestamp.isoformat(),
                "relative_date": c.relative_date,
                "subject": c.subject,
                "body": c.body,
                "parent_hashes": c.parent_hashes,
                "is_merge": c.is_merge,
                "files_changed": c.files_changed,
                "insertions": c.insertions,
                "deletions": c.deletions,
            })
        json.dump(data, sys.stdout, indent=2)
        return 0

    # Non-TTY output: plaintext
    if not sys.stdout.isatty():
        print(_format_plaintext(commits))
        return 0

    # TTY output: animated timeline
    renderer = TerminalRenderer(style=config.style)
    animator = Animator(config)

    try:
        # Import rich for TTY rendering
        from rich.console import Console
        from rich.live import Live
        from rich.text import Text

        console = Console()

        # Collect all visible commits as animation progresses
        visible_commits: list = []
        state_map: dict[int, AnimationState] = {}

        with Live(console=console, refresh_per_second=20, screen=False) as live:
            for frame in animator.animate(commits):
                # Add commit to visible list when it enters
                if frame.state == AnimationState.ENTERING:
                    visible_commits.append(frame.commit)
                    state_map[len(visible_commits) - 1] = AnimationState.VISIBLE

                # Render the current timeline
                output = renderer.render_timeline(visible_commits, state_map)

                # Render header
                header = (
                    f"[bold]Git Story[/bold] — "
                    f"last {len(visible_commits)}/{len(commits)} commits "
                    f"({args.speed})"
                )
                if args.reverse:
                    header += " [dim]reversed[/dim]"

                full_output = header + "\n" + ("─" * console.width) + "\n" + output

                live.update(Text.from_markup(full_output))

    except ImportError:
        # Fallback: non-animated output if rich Live isn't available
        print(_format_plaintext(commits))

    return 0


if __name__ == "__main__":
    sys.exit(main())
