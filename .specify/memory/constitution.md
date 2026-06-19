<!--
  ============================================================================
  Sync Impact Report
  ============================================================================
  Version change: (none) → 1.0.0 (initial ratification)
  Modified principles: N/A (initial creation)
  Added sections:
    - Core Principles (I–V)
    - Technical Constraints
    - Development Workflow
    - Governance
  Removed sections: None
  Templates requiring updates:
    - .specify/templates/plan-template.md    ✅ No changes needed (generic gates)
    - .specify/templates/spec-template.md    ✅ No changes needed (generic spec)
    - .specify/templates/tasks-template.md   ✅ No changes needed (generic tasks)
    - .specify/templates/checklist-template.md ✅ No changes needed (generic)
  Follow-up TODOs: None
  ============================================================================
-->

# Git Story Animator Constitution

## Core Principles

### I. Git-Native Integration

Every data operation MUST use git's own commands or plumbing APIs. The tool reads
from real git repositories and never reimplements git internals (object model,
diff engine, DAG traversal). Supported data sources: `git log`, `git diff`,
`git blame`, and `git rev-list`. External git libraries (libgit2 bindings) are
acceptable only when git CLI incurs unacceptable performance overhead, and the
choice MUST be justified with benchmarks.

**Rationale**: Git's internals are complex and subtle. Reimplementing them
introduces bugs that are invisible until edge cases surface. Leaning on git
itself guarantees correctness and makes the tool compatible with any git
repository.

### II. CLI-First Interface

Every feature MUST be exposed through a command-line interface following Unix
conventions:

- **Input**: positional arguments, flags, or stdin (text or structured data)
- **Output**: results to stdout, diagnostics to stderr
- **Formats**: human-readable terminal output by default; `--json` flag for
  machine-parseable output
- **Exit codes**: 0 for success, non-zero for errors (distinct codes for
  distinct failure modes)

A GUI or web UI MAY exist as an optional layer on top of the CLI, but the CLI
MUST remain the canonical interface.

**Rationale**: A CLI-first tool composes with shell pipelines, CI/CD systems,
and automation scripts. It is debuggable by inspection (no hidden state) and
remains the universal interface for all developer tools.

### III. Visual Story Clarity

Every animation or visual output MUST prioritize clarity and information
density over decoration. Each visual element MUST convey meaningful data about
the repository's history. Decorative or purely aesthetic elements MUST NOT
obscure or distract from the underlying data story.

Design decisions for visuals MUST be justified in terms of the narrative they
communicate: commit activity, branching patterns, contribution heatmaps, etc.

**Rationale**: The tool's purpose is to tell the story of a git repository's
evolution. Visual noise that does not contribute to understanding wastes
attention and undermines the tool's value proposition.

### IV. Test-First (NON-NEGOTIABLE)

Test-Driven Development is mandatory:

1. Write tests that define the expected behavior
2. Verify tests fail against the current codebase
3. Implement the feature or fix
4. Verify tests pass (Red → Green)
5. Refactor while keeping tests green

Tests MUST cover: new features, bug fixes, error paths, and edge cases
identified during development. Contract tests and integration tests are required
for any feature that processes git repository data. Unit tests are required for
all parsing, transformation, and rendering logic.

**Rationale**: Git data is unpredictable across repositories. Only thorough
testing catches edge cases before users do. TDD ensures tests exist and are
coupled to requirements, not after-the-fact rationalizations of implementation.

### V. Simplicity & YAGNI

Start with the simplest implementation that satisfies the requirements. Features
MUST be justified by a concrete use case before implementation. Speculative
generality, premature optimization, and "nice to have" abstractions MUST be
deferred until evidence (usage data, performance profiling, user feedback)
demonstrates need.

When choosing between approaches, prefer the one with fewer lines of code,
fewer dependencies, and less indirection, unless the simpler approach violates
another constitutional principle.

**Rationale**: Every line of code is a liability. Complexity compounds across
features. YAGNI (You Aren't Gonna Need It) keeps the codebase maintainable and
reduces the surface area for bugs.

## Technical Constraints

- **Language**: Python 3.10 or later (broad ecosystem for git tooling and media
  processing)
- **Video Rendering**: ffmpeg, invoked as a subprocess (NOT a Python binding
  that may lag behind ffmpeg releases)
- **Git Data**: git CLI (`git log`, `git diff`, `git blame`, `git rev-list`)
  or libgit2 bindings with benchmark justification
- **Output Formats**: Animated GIF, MP4, WebM (configurable)
- **Platform**: Linux, macOS (primary); Windows support is optional for v1
- **Dependencies**: MUST be declared with minimum version pins; transitive
  dependency count MUST be reviewed for each addition (prefer stdlib when
  feasible)

## Development Workflow

- **Spec-Driven**: All features begin with a specification document (spec.md)
  defining user stories, acceptance criteria, and success metrics
- **Branch-Per-Feature**: Each feature is developed on a dedicated branch;
  `main` is always deployable
- **Code Review**: All changes land via pull request with at least one review;
  constitution compliance is verified in review
- **Commit Hygiene**: Commits are atomic, well-described, and reference their
  feature spec
- **Agent Guidance**: Runtime development guidance lives in `CLAUDE.md` at the
  repository root

## Governance

This constitution supersedes all other project practices and conventions.
Where a practice conflicts with a constitutional principle, the principle
takes precedence.

**Amendment Procedure**:
1. Propose the amendment with rationale in a feature spec or dedicated document
2. Update the constitution text reflecting the change
3. Increment the version according to semantic versioning rules
4. Update all dependent templates and guidance (CLAUDE.md, spec/plan/task
   templates) to align with the amended constitution
5. Document the change in the Sync Impact Report

**Versioning Policy**:
- MAJOR: Backward-incompatible principle removal or redefinition
- MINOR: New principle, section, or materially expanded guidance
- PATCH: Clarifications, wording fixes, typo corrections, non-semantic
  refinements

**Compliance Review**:
- Every pull request MUST include a brief constitution-compliance note
  confirming the change aligns with all applicable principles
- Any violation MUST be explicitly justified in the plan's Complexity
  Tracking section with a simpler alternative that was rejected and why
- Periodic audits (every 5 features or every quarter, whichever comes first)
  review the codebase for principle drift

**Version**: 1.0.0 | **Ratified**: 2026-06-20 | **Last Amended**: 2026-06-20
