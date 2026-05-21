# Contributing to warehouse_humanoid_tco

This is a single-contributor portfolio project. "Contributing" here means: rules future-you (or Claude Code in any session) must follow when working on this repo.

## The Single Source of Truth Rule

**`PROJECT_CHARTER.md` is the SSOT.** All project facts (goals, scope, requirements, architecture, decisions) live there or in `docs/ADR/`. Nowhere else.

If you need to write a project-level fact:

1. Look in `PROJECT_CHARTER.md`. Is it already there? If yes, link to that section.
2. Is it a decision that changes scope, architecture, or requirements? Write an ADR.
3. Otherwise, add it to the relevant section of `PROJECT_CHARTER.md` AND log it in the Change Log.

**Forbidden:**

- Creating new `.md` files outside the allowlist (see below).
- Writing requirements in GitHub Issues.
- Writing design decisions in commit messages instead of ADRs.
- Adding "TODO" comments to code instead of backlog entries in PROJECT_CHARTER.md §5.3.
- Letting `PROJECT_CHARTER.md` go stale.

## Allowed Markdown Files

CI enforces this list. Anything else fails the build.

```
README.md
PROJECT_CHARTER.md
CONTRIBUTING.md
LICENSE
docs/ADR/NNNN-*.md          # ADRs only
docs/glossary.md
reports/*.md
reports/*.qmd
.github/**/*.md
```

Notebooks may have inline markdown cells; that is not a `.md` file.

## ADR Discipline

ADRs are append-only and immutable.

- Numbered sequentially: `0001`, `0002`, ...
- Filename pattern: `NNNN-kebab-case-title.md`
- Once status is "Accepted", the file is frozen. Future changes use a new ADR that supersedes the old one.
- All ADRs include: Date, Status, Deciders, Context, Decision, Consequences, References.

## Coding Standards

See `PROJECT_CHARTER.md` §8.3. CI enforces.

- Python: snake_case for variables/functions/modules, PascalCase for classes, SCREAMING_SNAKE_CASE for constants. **No camelCase in Python.**
- All `src/` code passes Ruff, Black, and pyright strict.
- Tests required for new logic in `src/features/` and `src/models/`.
- No magic numbers; constants live in `config/*.yaml`.
- No business logic in notebooks; notebooks call `src/` functions only.

## Reproducibility

- Pin every dependency in `pyproject.toml`.
- Pin the UnifoLM-WBT dataset revision SHA in code, never use `main`.
- Seed every RNG. Seeds live in `config/seeds.yaml`.
- `make all` must produce identical outputs on two runs.

## Scope Discipline

Before adding any feature or task, run through PROJECT_CHARTER.md §9.2 Scope Creep Checklist. All five questions must have clear answers.

The "I will just add one thing" rule (§9.4): when you catch yourself thinking it, stop and apply §9.2.

The "Shiny new thing" rule (§9.3): add it to the Backlog, do not start coding.

## Working with Claude Code

When using Claude Code in this repo, paste this at the start of any new session:

> Read `PROJECT_CHARTER.md` and `CONTRIBUTING.md` before any other action. Follow the SSOT rule and ADR discipline. If a request would require updating the SSOT or creating an ADR, do that first before any code changes. Honor the locks in PROJECT_CHARTER.md §9.1 unless an ADR override exists.

## Daily Discipline

End-of-session checklist:

- [ ] Did anything in scope change today? If yes, update PROJECT_CHARTER.md and Change Log.
- [ ] Did I make a non-trivial architectural decision? If yes, write an ADR.
- [ ] Did I add a TODO comment? If yes, move it to the Backlog in PROJECT_CHARTER.md §5.3 and delete the comment.
- [ ] Does `make ci-local` pass?

Skipping these for a day or two does not break the project. Skipping for a week creates exactly the sprawl this discipline is designed to prevent.
