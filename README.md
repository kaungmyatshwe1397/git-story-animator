# git-story-animator

> Animate your git commit history as a clean, progressively-revealed timeline — right in your terminal.

`git-story` turns raw `git log` output into an engaging, scannable visual story. Commits appear one-by-one with author colors, merge markers, relative dates, and change stats. Pause, navigate, and expand commits interactively — or pipe plaintext/JSON output to other tools.

---

## Features

- **Animated Timeline** — commits reveal progressively with configurable speed (slow / normal / fast)
- **Author Colors** — each author gets a deterministic color for at-a-glance recognition
- **Two Layout Styles** — `default` (full detail) or `compact` (narrow terminals)
- **Interactive Mode** — pause, navigate with arrow keys, expand commits for full details
- **Merge Commit Markers** — merge commits get a distinct `⟐` indicator
- **JSON Export** — `--json` for machine-parseable output (great for scripts and CI)
- **Pipe-Friendly** — automatically detects non-TTY output and emits plaintext
- **Clear Exit Codes** — distinct codes for success, not-a-repo, git-not-found, and invalid-args
- **Smart Truncation** — long commit messages get `…` with full text available on expand
- **Reverse Order** — `--reverse` to display oldest-to-newest

---

## Installation

### Prerequisites

- **Python 3.10+**
- **git** installed and on your `PATH`

### Via pip (recommended)

```bash
pip install git-story-animator
```

### From source

```bash
git clone https://github.com/kaung-myat-shwe/git-story-animator.git
cd git-story-animator
pip install .
```

### Development install

```bash
git clone https://github.com/kaung-myat-shwe/git-story-animator.git
cd git-story-animator
pip install -e ".[dev]"
```

---

## Quick Start

```bash
# Navigate to any git repository
cd my-project

# Show the last 10 commits as an animated timeline
git-story

# Show 20 commits at fast speed
git-story --count 20 --speed fast

# Show in reverse (oldest first) with compact layout
git-story --reverse --style compact

# Export commit data as JSON (no animation)
git-story --json | jq '.[] | {hash: .hash_short, msg: .subject}'
```

---

## CLI Reference

```
git-story [OPTIONS]
```

### Options

| Flag | Short | Description | Default |
|------|-------|-------------|---------|
| `--count` | `-n` | Number of recent commits to display | `10` |
| `--speed` | — | Animation speed: `slow`, `normal`, `fast` | `normal` |
| `--style` | — | Layout style: `default`, `compact` | `default` |
| `--reverse` | — | Display oldest to newest | off |
| `--json` | — | Output commit data as JSON (no animation) | off |
| `--no-interactive` | — | Disable interactive keyboard controls | off |
| `--version` | — | Print version and exit | — |
| `--help` | — | Show help and exit | — |

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Not inside a git repository |
| `2` | `git` is not installed |
| `3` | Invalid arguments |

---

## Interactive Mode

While the animation is playing (TTY mode, interactive enabled), you can control playback with your keyboard:

| Key | Action |
|-----|--------|
| <kbd>Space</kbd> | Pause / Resume the animation |
| <kbd>↑</kbd> <kbd>↓</kbd> | Navigate between commits (when paused) |
| <kbd>Enter</kbd> | Expand the selected commit — shows full hash, author email, absolute date, full message, and change stats |
| <kbd>Esc</kbd> | Collapse expanded commit (return to paused view) |
| <kbd>Q</kbd> | Quit the animation |

> **Tip:** To disable interactive mode (e.g., for recordings or scripts), use `--no-interactive`.

---

## Output Modes

`git-story` adapts its output based on context:

| Context | Output |
|---------|--------|
| **TTY (terminal)** | Rich animated timeline with author colors, live rendering |
| **Pipe / Redirect** | Plaintext: `hash | author | relative_date | subject` |
| **`--json`** | JSON array of commit objects (TTY or piped) |

### JSON Output Schema

Each commit object:

```json
{
  "hash": "abc123...",
  "hash_short": "abc1234",
  "author_name": "Jane Doe",
  "author_email": "jane@example.com",
  "timestamp": "2026-06-20T12:34:56+00:00",
  "relative_date": "2h ago",
  "subject": "Fix login redirect bug",
  "body": "The redirect was passing an invalid...",
  "parent_hashes": ["def567..."],
  "is_merge": false,
  "files_changed": 3,
  "insertions": 42,
  "deletions": 7
}
```

---

## Example Timeline

```
Git Story — last 10/10 commits (normal)
────────────────────────────────────────────────────────────────
abc1234  Jane Doe       3h ago   Fix login redirect bug
⟐ 7fa2b1  Mike Chen      5h ago   Merge pull request #42 — Add dark mode
93ab5e1  Sarah Park     8h ago   Update README with setup instructions
d4a092c  Mike Chen      1d ago   Refactor auth middleware
...
```

- Each author gets a unique color
- Merge commits show the `⟐` symbol and italic subject
- Relative dates (`3h ago`, `1d ago`) are human-friendly

---

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run the full test suite
pytest

# With coverage
pytest --cov=git_story_animator --cov-report=term-missing

# Run specific test layers
pytest tests/unit/
pytest tests/integration/
pytest tests/contract/
```

### Project Structure

```
git-story-animator/
├── src/git_story_animator/
│   ├── __init__.py       # Package version
│   ├── cli.py            # CLI entry point & argument parsing
│   ├── models.py         # Commit, AnimationConfig, enums
│   ├── git_reader.py     # git log subprocess wrapper
│   ├── animator.py       # Frame sequencing & animation timing
│   ├── renderer.py       # Rich terminal rendering
│   └── interactive.py    # Keyboard input & state machine
├── tests/
│   ├── unit/             # Unit tests per module
│   ├── integration/      # End-to-end tests
│   └── contract/         # CLI contract tests (exit codes, JSON, pipe)
├── specs/                # Specification documents
├── pyproject.toml        # Project metadata & dependencies
└── README.md
```

---

## Dependencies

- **[rich](https://github.com/Textualize/rich)** ≥ 13.0 — terminal rendering, colors, live display
- Standard library only otherwise — no other third-party dependencies

---

## License

MIT © Kaung Myat Shwe

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Ensure the test suite passes (`pytest`)
5. Commit your changes
6. Push and open a pull request

---

## Acknowledgments

Built with [Rich](https://github.com/Textualize/rich) for beautiful terminal rendering. Inspired by the desire to make git history more visual and approachable.
