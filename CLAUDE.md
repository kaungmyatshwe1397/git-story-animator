# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

**Git Story Animator** (`git-story`) — a Python CLI tool that reads a local git log and animates recent commits as a clean, progressively-revealed timeline in the terminal. Built with the `rich` library for terminal rendering and live display.

## Common Commands

### Build & Install
```bash
# Create virtual environment (if needed)
uv venv
source .venv/bin/activate

# Install in editable mode with dev dependencies
uv pip install -e ".[dev]"
```

### Running
```bash
# Run the CLI (after install)
git-story [OPTIONS]

# Or run as a module without installing
python3 -m git_story_animator.cli [OPTIONS]
```

### Testing
```bash
# Full test suite
pytest

# With coverage report
pytest --cov=git_story_animator --cov-report=term-missing

# Specific test layers
pytest tests/unit/
pytest tests/integration/
pytest tests/contract/

# Single test file
pytest tests/unit/test_models.py -v
```

### Linting & Formatting
```bash
# The project follows standard Python conventions — no separate formatter configured.
# Use ruff or black if you prefer:
pip install ruff
ruff check src/ tests/
ruff format src/ tests/
```

## Architecture

```
CLI (cli.py)
  ├─ Parse args → AnimationConfig
  ├─ GitReader (git_reader.py) → list[Commit]
  ├─ Animator (animator.py) → generator of AnimationFrame
  ├─ TerminalRenderer (renderer.py) → rich markup strings
  └─ InteractiveController (interactive.py) → keyboard state machine
```

### Modules

| Module | Responsibility |
|--------|---------------|
| `cli.py` | Argument parsing (`argparse`), TTY/pipe detection, wiring all components together |
| `models.py` | Data classes: `Commit`, `AnimationConfig`, enums `Speed`/`Style`/`AnimationState` |
| `git_reader.py` | Wraps `git log` subprocess with custom delimiters (`\x1e` field, `\x1f` record), parses into `Commit` objects |
| `animator.py` | Frame generator with configurable speed delays, pause/stop controls |
| `renderer.py` | Converts commits to `rich` markup strings with deterministic author colors, default/compact layouts, expanded detail view |
| `interactive.py` | Raw terminal input (`termios`/`tty`), ESC sequence parsing, state machine (PLAYING → PAUSED → EXPANDED) |

### Data Flow
1. User runs `git-story [--flags]`
2. `cli.py` parses args → `AnimationConfig`
3. `GitReader.get_commits()` shells out to `git log --format=...` with ASCII delimiters
4. `Animator.animate(commits)` yields `AnimationFrame` objects with timing
5. `Renderer.render_timeline()` converts to `rich` markup
6. `rich.live.Live` handles terminal refresh at 20 FPS
7. `InteractiveController` reads keystrokes non-blocking via `select`

## Code Conventions

- **Python 3.10+** with `from __future__ import annotations` everywhere
- **Type hints** on all public methods and functions
- **Google-style docstrings** (Args/Returns/Raises sections)
- **Data classes** for value objects (`Commit`, `AnimationConfig`, `AnimationFrame`)
- **Enums** for constrained sets (`Speed`, `Style`, `AnimationState`, `KeyEvent`)
- **PEP 8** naming: `snake_case` functions/variables, `PascalCase` classes, `UPPER_CASE` module constants
- Custom exceptions inherit from `GitReaderError` (base) — specific: `NotAGitRepoError`, `GitNotFoundError`, `EmptyRepoError`
- Terminal width detection via `shutil.get_terminal_size()` with 40-char minimum fallback
- Author colors use `hashlib.sha256` on author name → stable index into a 12-color palette
- Subprocess calls use `timeout=` parameters (30s for log, 10s for show)
- Exit codes: `0` success, `1` not-a-repo, `2` git not installed, `3` invalid args

## Testing Strategy

- **Unit tests** (`tests/unit/`) — one file per source module, mocking filesystem/subprocess
- **Integration tests** (`tests/integration/`) — end-to-end with real git repos created in `tmp_path`
- **Contract tests** (`tests/contract/`) — verify exit codes, JSON schema, pipe detection

Conftest (`tests/conftest.py`) provides a `git_repo` fixture that creates a temporary git repo with 3 commits.

## Package Layout

- `src/` layout with `packages.find` in `pyproject.toml`
- Entry point: `git-story` → `git_story_animator.cli:main`
- Single dependency: `rich>=13.0.0`

## Speckit Skills

This project was built with the Spec-Driven Development workflow. Available speckit skills in `.claude/skills/`:
- `speckit-specify` — write feature specifications
- `speckit-plan` — create implementation plans
- `speckit-tasks` — break plans into ordered tasks
- `speckit-implement` — implement tasks
- `speckit-clarify` / `speckit-analyze` / `speckit-checklist` / `speckit-converge` / `speckit-constitution`
