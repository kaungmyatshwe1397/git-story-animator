# Tasks: Git Story Animator

**Input**: Design documents from `/specs/001-git-story-animator/`

**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Included — constitution mandates Test-First (NON-NEGOTIABLE) per Principle IV.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths based on plan.md structure: `src/git_story_animator/` package

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure: `src/git_story_animator/`, `tests/unit/`, `tests/integration/`, `tests/contract/`
- [X] T002 Create `pyproject.toml` with project metadata, `rich>=13.0.0` dependency, pytest config, and `[project.scripts]` entry point (`git-story = git_story_animator.cli:main`)
- [X] T003 [P] Create `src/git_story_animator/__init__.py` with package version (`__version__ = "0.1.0"`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `Commit` dataclass and enums (`Speed`, `Style`, `AnimationState`) in `src/git_story_animator/models.py` with all fields from data model: hash, hash_short, author_name, author_email, timestamp, subject, body, parent_hashes, files_changed, insertions, deletions, and computed properties (is_merge, is_initial, relative_date, author_display)
- [X] T005 [P] Create `AnimationConfig` dataclass in `src/git_story_animator/models.py` with fields: count, speed, style, reverse, json_mode, interactive (all with defaults per spec)
- [X] T006 [P] Implement `GitReader` class in `src/git_story_animator/git_reader.py` — wraps `subprocess.run(['git', 'log', ...])` with custom format delimiters, parses output into `Commit` objects, handles non-repo and empty-repo errors
- [X] T007 [P] Write unit tests for `Commit` model validation and computed properties in `tests/unit/test_models.py` — verify is_merge detection, relative_date formatting, author_display fallback chain
- [X] T008 [P] Write unit tests for `GitReader` in `tests/unit/test_git_reader.py` — mock subprocess to test parsing of valid log output, empty repo, non-repo errors, merge commits, missing author
- [X] T009 [P] Write unit tests for `AnimationConfig` defaults and `Speed`/`Style` enum values in `tests/unit/test_models.py` — verify default count=10, speed=NORMAL, style=DEFAULT

**Checkpoint**: Foundation ready — all models and git reading are test-covered. User story implementation can now begin.

---

## Phase 3: User Story 1 - View Animated Commit Timeline (Priority: P1) 🎯 MVP

**Goal**: Running the tool in any git repo renders a progressive, chronologically-ordered commit timeline in the terminal with animated commit entries showing hash, author, date, and message. Authors are visually distinguished. Merge commits have distinct markers. Final timeline persists after animation completes.

**Independent Test**: Run `git-story` (no args) in a repo with 10 commits and verify commits appear one-by-one in order with correct fields, author colors, and merge markers.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Write contract test for basic CLI execution in `tests/contract/test_cli_contract.py` — verify exit code 0 for valid repo, non-zero for non-repo, stdout contains expected commit fields
- [X] T011 [P] [US1] Write integration test for animated timeline in `tests/integration/test_e2e.py` — create a test git repo with 5 commits (multi-author, one merge), invoke tool in plaintext mode, verify all commits appear in expected order with correct data
- [X] T012 [P] [US1] Write unit test for renderer timeline layout in `tests/unit/test_renderer.py` — verify commit entries render with correct fields (hash, author, date, subject), author colors differ, merge commits get branch marker

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `TerminalRenderer` class in `src/git_story_animator/renderer.py` — uses `rich.console.Console`, `rich.table.Table`, `rich.panel.Panel` to render a single commit as a timeline row with: abbreviated hash, colored author name, relative date, truncated subject line; assigns deterministic colors per unique author; marks merge commits with a visual indicator
- [X] T014 [US1] Implement `Animator` class in `src/git_story_animator/animator.py` — iterates over commit list, yields `AnimationFrame` objects with progressive timing; uses `time.sleep()` for frame delay; sets each frame's state (ENTERING → VISIBLE); final frame leaves timeline fully displayed
- [X] T015 [US1] Implement `main()` function and argparse setup in `src/git_story_animator/cli.py` — parse `--count/-n` (default 10), wire up: GitReader → Animator → TerminalRenderer loop; detect non-TTY via `sys.stdout.isatty()` and output plain text if piped; handle "not a git repo" error with message to stderr and exit code 1; handle empty repo with friendly message and exit code 0
- [X] T016 [US1] Add plaintext (non-TTY) output path in `src/git_story_animator/cli.py` — when stdout is not a terminal, print commit list without animation as tab-separated text: hash | author | date | subject
- [X] T017 [US1] Write unit tests for `TerminalRenderer` in `tests/unit/test_renderer.py` — verify author color assignment is deterministic, merge commits render with branch marker, message truncation for long subjects (>80 chars)
- [X] T018 [US1] Write unit tests for `Animator` in `tests/unit/test_animator.py` — verify frame count equals commit count, frame states progress correctly, timing respects configured delay

**Checkpoint**: At this point, `git-story` (no args) produces an animated timeline in any git repo — the MVP is functional and independently testable.

---

## Phase 4: User Story 2 - Customize Animation Display (Priority: P2)

**Goal**: Users can control commit count, animation speed, visual style (default vs compact), and commit order (reverse) via CLI flags. Compact style adapts layout for narrower terminals.

**Independent Test**: Run `git-story --count 5 --speed fast --style compact --reverse` and verify output respects all four flags.

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T019 [P] [US2] Write unit tests for CLI flag parsing in `tests/unit/test_cli.py` — verify `--count/-n`, `--speed` (slow/normal/fast), `--style` (default/compact), `--reverse`, `--json` are all accepted and produce correct `AnimationConfig`
- [X] T020 [P] [US2] Write integration test for customization flags in `tests/integration/test_e2e.py` — create repo with 30 commits, run with `--count 5 --reverse` in plaintext mode and verify exactly 5 oldest commits shown in oldest-first order

### Implementation for User Story 2

- [X] T021 [P] [US2] Add `--speed` flag to CLI in `src/git_story_animator/cli.py` — accept choices: slow, normal, fast; pass to `Animator` which maps to frame delays (0.8s / 0.3s / 0.1s)
- [X] T022 [P] [US2] Add `--reverse` flag to CLI in `src/git_story_animator/cli.py` — when set, reverse commit list before animating; update `GitReader` to pass `--reverse` to `git log` for efficiency
- [X] T023 [US2] Add `--style` flag to CLI in `src/git_story_animator/cli.py` — accept choices: default, compact; pass to `TerminalRenderer`; implement `render_compact()` method in `src/git_story_animator/renderer.py` that shows single-line entries (hash + subject only) fitting narrower terminals
- [X] T024 [US2] Implement terminal width detection in `src/git_story_animator/renderer.py` — use `console.width` to warn when terminal < 80 columns for default style; auto-switch to compact if `console.width < 60`
- [X] T025 [US2] Write unit tests for compact renderer in `tests/unit/test_renderer.py` — verify compact layout stays within provided width constraint, no wrapping artifacts at 60 columns

**Checkpoint**: All customization flags work. User Stories 1 AND 2 are both functional.

---

## Phase 5: User Story 3 - Inspect Commit Details During Animation (Priority: P3)

**Goal**: While the animation plays, user can press Space to pause, arrow keys to navigate between commits, Enter to expand a commit showing full message + diff stats, and Escape to collapse back to timeline view.

**Independent Test**: Run `git-story`, press Space to pause, arrow down twice, press Enter — verify full commit message and diff stats appear; press Escape — verify timeline returns.

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T026 [P] [US3] Write unit tests for keyboard input parser in `tests/unit/test_interactive.py` — mock stdin bytes for Space, arrow keys, Enter, Escape; verify correct key events parsed from raw terminal input
- [X] T027 [P] [US3] Write unit tests for interactive state machine in `tests/unit/test_interactive.py` — verify state transitions: PLAYING → PAUSED (Space), PAUSED → PLAYING (Space), PAUSED → EXPANDED (Enter), EXPANDED → PAUSED (Escape), and cursor navigation bounds

### Implementation for User Story 3

- [X] T028 [P] [US3] Implement `KeyParser` in `src/git_story_animator/interactive.py` — sets terminal to raw mode via `tty.setraw()` / `termios`, reads individual bytes from stdin, maps escape sequences to key events: Space (pause), ↑/↓ (navigate), Enter (select), Escape (collapse/quit), q (quit)
- [X] T029 [US3] Implement `InteractiveController` in `src/git_story_animator/interactive.py` — manages animation state machine: playing, paused, commit-expanded; tracks cursor position in commit list; dispatches state transitions on key events
- [X] T030 [US3] Add `--no-interactive` flag to CLI in `src/git_story_animator/cli.py` to disable interactive mode (for scripting/CI)
- [X] T031 [US3] Integrate `InteractiveController` into `Animator` in `src/git_story_animator/animator.py` — during each frame delay, check for keyboard input; if Space pressed, pause loop; call renderer with current frame state (VISIBLE / SELECTED)
- [X] T032 [US3] Implement commit expansion view in `src/git_story_animator/renderer.py` — `render_expanded()` method shows: full commit message body, list of changed files, insertion/deletion counts; data fetched via `GitReader` method that appends `--stat` to `git log` for the selected commit
- [X] T033 [US3] Add `--json` flag handling in `src/git_story_animator/cli.py` — when set, read commits, serialize to JSON, print to stdout, exit (no animation, no interaction); supports piped consumption per FR-009

**Checkpoint**: All user stories functional — animated timeline with customization and interactive inspection. Full feature complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T034 [P] Add `--version` flag in `src/git_story_animator/cli.py` — prints package version from `__init__.__version__` and exits
- [X] T035 [P] Add distinct exit codes in `src/git_story_animator/cli.py` — code 0: success, code 1: not a git repo, code 2: git not installed, code 3: invalid arguments; document in `--help` output
- [X] T036 [P] Write contract test for JSON output in `tests/contract/test_cli_contract.py` — verify `--json` produces valid JSON array with correct commit fields
- [X] T037 [P] Write contract test for pipe detection in `tests/contract/test_cli_contract.py` — verify redirecting stdout produces plaintext (no ANSI escape codes)
- [X] T038 Run full test suite (`pytest tests/`) and verify all tests pass, correct any failures
- [X] T039 Validate against quickstart scenarios — run tool in real git repos (varying sizes, merge patterns, author counts)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001, T002) — BLOCKS all user stories
- **User Stories (Phase 3–5)**: All depend on Foundational phase completion
  - User stories proceed sequentially in priority order (P1 → P2 → P3) due to shared files (`cli.py`, `renderer.py`, `animator.py`)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P2)**: Extends US1's `cli.py`, `animator.py`, `renderer.py` — requires US1 implementation complete
- **User Story 3 (P3)**: Extends US1's `animator.py`, `renderer.py` — requires US1 implementation complete; independent of US2

### Within Each User Story

- Tests MUST be written and MUST FAIL before implementation (TDD per constitution)
- Models/utilities before integration
- Core rendering before interactive features
- Story complete before moving to next priority

### Parallel Opportunities

- T002, T003 can run in parallel
- T004, T005 (both models.py) — serial (same file)
- T006, T007, T008, T009 — all different files, all parallel
- T010, T011, T012 (US1 tests) — all different files, all parallel
- T013, T014 are foundational to US1, rest of US1 tests (T017, T018) can run parallel
- T019, T020 (US2 tests) — different files, parallel
- T021, T022 (different concerns in cli.py) — separate concerns but same file, consider serial
- T026, T027 (US3 tests) — different test scopes in same file, can parallel if split or careful
- T028, T033 — different files, parallel
- T034, T035, T036, T037 (Polish) — all different files, all parallel

---

## Parallel Example: Foundational Phase

```bash
# Launch all Foundational tests in parallel (different files):
Task: "Write unit tests for Commit model in tests/unit/test_models.py"
Task: "Write unit tests for GitReader in tests/unit/test_git_reader.py"

# Launch all US1 tests in parallel (different files):
Task: "Contract test for basic CLI execution in tests/contract/test_cli_contract.py"
Task: "Integration test for animated timeline in tests/integration/test_e2e.py"
Task: "Unit test for renderer timeline layout in tests/unit/test_renderer.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T009)
3. Complete Phase 3: User Story 1 (T010–T018) — first write tests and verify they FAIL
4. **STOP and VALIDATE**: Run `git-story` in a real repo; verify animated timeline with author colors and merge markers
5. Demo/deploy as MVP — this is a working, valuable tool on its own

### Incremental Delivery

1. Setup + Foundational → Foundation ready (models + git reader tested)
2. User Story 1 → Animated timeline MVP (core value delivered)
3. User Story 2 → Customization flags (personalization layer)
4. User Story 3 → Interactive inspection (power-user depth)
5. Polish → Exit codes, version flag, full suite pass
6. Each story adds value without breaking previous stories

### TDD Workflow (Mandated by Constitution)

For each phase (US1, US2, US3):
1. Write the test tasks in that phase — run `pytest` and confirm they FAIL (Red)
2. Implement the corresponding source tasks
3. Run `pytest` and confirm tests PASS (Green)
4. Refactor while keeping tests green
5. Commit the working checkpoint

---

## Notes

- [P] tasks = different files, no dependencies — can be launched together
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD Red → Green → Refactor per constitution Principle IV)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
