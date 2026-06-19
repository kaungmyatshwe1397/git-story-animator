# Implementation Plan: Git Story Animator

**Branch**: `001-git-story-animator` | **Date**: 2026-06-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-git-story-animator/spec.md`

## Summary

Build a CLI tool that reads a local git repository's commit history and renders it as an animated, progressively-revealed timeline in the terminal. The tool supports customizable counts, speeds, layout styles, interactive inspection of commits, and pipe-safe plaintext output. Implemented in Python 3.10+ using the `rich` library for terminal rendering, git subprocess for data sourcing, and argparse for the CLI contract.

## Technical Context

**Language/Version**: Python 3.10+ (3.12 available in dev environment)

**Primary Dependencies**: `rich` (terminal display, colors, Live rendering), stdlib (`argparse`, `subprocess`, `dataclasses`, `sys`, `os`, `json`, `datetime`)

**Storage**: N/A — reads from git repository on demand; no persistent storage

**Testing**: `pytest` with `unittest.mock` for git subprocess mocking; integration tests against real git repos created in test fixtures

**Target Platform**: Linux (primary), macOS (secondary); terminals with ANSI/VT100 support

**Project Type**: CLI tool (single package)

**Performance Goals**: Sub-500ms startup + data loading for repos up to 10k commits; animation frame timing configurable

**Constraints**: Zero-config required (no setup beyond having git installed); must detect non-TTY and degrade gracefully

**Scale/Scope**: Single-user CLI tool; reads last N commits (default 10, configurable)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|---|---|---|
| I. Git-Native Integration | ✅ PASS | Uses `git log --format=...` subprocess for all commit data; never reimplements git internals |
| II. CLI-First Interface | ✅ PASS | argparse flags, stdout/stderr separation, exit codes, `--json` for machine output, pipe detection |
| III. Visual Story Clarity | ✅ PASS | Every visual element maps to commit data (author=color, merge=marker, hash=identifier); no purely decorative elements |
| IV. Test-First | ✅ PLAN | pytest with git repo fixtures; unit tests for parsing/rendering; integration tests for animation; contract tests for CLI |
| V. Simplicity & YAGNI | ✅ PASS | Single package, 1 runtime dependency (`rich`), argparse from stdlib, video export deferred to future spec |

**Gate Result**: All principles pass. No violations requiring justification in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/001-git-story-animator/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── cli-interface.md
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/git_story_animator/
├── __init__.py          # Package init, version
├── cli.py               # argparse setup, main(), dispatch logic
├── git_reader.py        # Git subprocess calls, commit log parsing
├── models.py            # Commit dataclass, AnimationConfig, Speed enum
├── animator.py          # Animation engine (frame sequencing, timing)
├── renderer.py          # Terminal rendering (rich-based layouts)
└── interactive.py       # Keyboard input capture, pause/nav/expand

tests/
├── unit/
│   ├── test_git_reader.py
│   ├── test_models.py
│   ├── test_animator.py
│   ├── test_renderer.py
│   └── test_cli.py
├── integration/
│   └── test_e2e.py
└── contract/
    └── test_cli_contract.py

pyproject.toml           # Project metadata, dependencies, entry point
```

**Structure Decision**: Single-package CLI tool (Option 1). No separate frontend/backend — terminal rendering and git reading are both in-process. The `src/` layout prevents accidental imports of the package during development without installing it.

## Complexity Tracking

> No violations to justify.
