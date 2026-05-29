---
status: accepted
decision_date: 2026-05-21
superseded_by: null
linked_invariant_test: null
---

# ADR-0005: DiverseManip Episode Format Incompatibility

**Date:** 2026-05-21
**Status:** Resolved
**Decider:** Rafael Braga

## Context

Initial capability extraction logic (Module 1) read task descriptions from WBT episode metadata using a flat key structure: `episode["task"]`. The WBT datasets worked correctly — 644 episodes classified on first run.

When the same parser was applied to the two DiverseManip datasets (`G1_Dex1_DiverseManip_DualArm_256x256`, `G1_Dex1_DiverseManip_SingleArm_256x256`), it produced **0 classified episodes**. No error was raised. The classification loop silently skipped all 1,715 DiverseManip episodes because `episode.get("task")` returned `None` for all of them.

## Investigation

The DiverseManip datasets use LeRobot V2.0+ format, which stores task annotations in a nested `meta/tasks.json` file rather than inline episode metadata. The task key inside that file is `task_index` mapped to a string description, not a flat `"task"` field on the episode dict.

WBT datasets use LeRobot V1.0 format with inline task strings. Format detection by filename convention (`WBT` vs `Dex`) would be fragile; the correct detection is by schema presence.

## Decision

Refactored `src/warehouse_humanoid_tco/parsers.py` to detect format by inspecting the dataset schema:
- If `episode["task"]` (string) is present → V1.0 flat format, read directly
- If `episode["task_index"]` (int) is present → V2.0 nested format, load from `meta/tasks.json` and join by index

The format detection is now data-driven, not filename-driven. Both parsers are exercised by `tests/test_taxonomy.py`.

## Outcome

After refactor: 2,359 episodes classified across all 5 datasets. DiverseManip contributed 1,715 episodes, nearly 3× the WBT count.

## Consequences

- Both LeRobot V1.0 (WBT flat format) and V2.0 (DiverseManip nested format) are supported.
- 2,359 episodes classified across all 5 datasets instead of 644.
- Future parsers in this project must use schema-presence detection rather than filename conventions.

## Lesson

Relying on a single dataset structure assumption across a multi-dataset pipeline will silently produce zero-output for formats that differ. The fix is schema-presence detection, not filename or convention matching. Applied to all future multi-dataset parsers in this project.
