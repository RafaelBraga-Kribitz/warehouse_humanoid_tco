---
status: accepted
decision_date: 2026-05-20
superseded_by: null
linked_invariant_test: null
---

# ADR-0002: Ethics Boundary, No Human Activity Sensing

- **Date:** 2026-05-20
- **Status:** Accepted
- **Deciders:** Rafael Braga
- **Supersedes:** None
- **Superseded by:** None

## Context

Earlier project ideation considered combining WiFi-CSI-based human sensing (ruvnet/RuView) with the Unitree UnifoLM-WBT dataset to compute worker-to-humanoid substitution ratios. This combination has multiple critical problems for a portfolio targeting Austrian industrial employers:

1. **Legal:** Austrian Arbeitsverfassungsgesetz §96 grants the Betriebsrat (works council) co-determination rights over any technical measure that monitors workers. Any sensing of worker activity, even anonymized via RF, triggers these rights.

2. **Optical:** the framing "tool to calculate which workers can be replaced by robots" is the worst possible positioning for a job application in Austria, a country with strong industrial relations and consensus-based labor culture.

3. **Practical:** the two datasets do not naturally meet at a schema or semantic level, requiring a heavy ontology-matching layer that becomes its own research project rather than a portfolio piece.

4. **Hardware:** RuView is beta software requiring physical ESP32 deployments, weeks of calibration, and produces low accuracy (PCK@20 ≈ 2.5% with proxy labels). Inappropriate for an 8-10 week portfolio project.

## Decision

The project does not sense, monitor, fingerprint, or otherwise observe humans. Period.

Specifically excluded:

- No WiFi-CSI sensing.
- No RuView integration.
- No camera-based activity recognition.
- No worker time-and-motion data, even from public sources.
- No language framing humanoids as worker "replacements" or "substitutes". Permitted framings: "augmentation", "operations expansion", "shift coverage", "ergonomic relief", "TCO comparison".

Data subjects in this project are robots and warehouses, not humans.

## Consequences

### Positive

- Project is Betriebsrat-compatible by design.
- Project is recruiter-safe and ethically defensible.
- Scope is dramatically simpler; no hardware, no calibration, no sensing pipeline.
- Project can cite Austrian companies (Knapp, TGW, Magna) in materials without giving offense.

### Negative

- One creative angle from earlier ideation (RuView × UnifoLM combination) is foreclosed. This is acceptable; the angle was bad.

### Future Override Path

If a future version of the project wants to incorporate human-side data, it must:

1. Use only published, aggregated, anonymized sources (such as Statistik Austria sectoral data).
2. Frame in terms of ergonomic safety or workforce augmentation, never substitution.
3. Pass a Betriebsrat-language audit before publication.
4. Be documented in a new ADR superseding this one.

## References

- PROJECT_CHARTER.md §3.6 Out of Scope
- PROJECT_CHARTER.md §9.1 The Three Locks (L2)
- Arbeitsverfassungsgesetz §96 (Austrian works council co-determination)
