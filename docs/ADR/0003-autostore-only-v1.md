# ADR-0003: Ship AutoStore-Only in v1.0 with Extensible Configs

- **Date:** 2026-05-20
- **Status:** Accepted
- **Deciders:** Rafael Braga
- **Supersedes:** None

## Context

The project's primary recruiter audience is Austrian intralogistics companies, primarily Knapp AG (AutoStore-style cube storage) and TGW Logistics (Stingray and FlashPick shuttle systems), with Magna Steyr (automotive line) as a secondary audience.

Fully calibrating all three reference architectures within a 10-week budget is unrealistic. Each requires its own layout parameters, throughput benchmarks, and validation against published industry data.

A "do all three" approach trades depth for breadth and risks shipping nothing well.

## Decision

v1.0 ships with AutoStore fully calibrated. Stingray and Magna line architectures ship as stub configurations that demonstrate the simulation engine generalizes but are not validated.

Architectural implication: the SimPy simulation in `src/warehouse_humanoid_tco/models/simulation.py` is built with a `WarehouseScenario` configuration object pattern. The simulation engine is architecture-agnostic. Configs in `config/*.yaml` parameterize each architecture.

This signals architectural maturity to recruiters (you know how to design for extension) without paying the cost of full calibration.

## Consequences

### Positive

- v1.0 ships in 8-10 weeks instead of 16-20.
- The most important Austrian audience (Knapp, via AutoStore) is well-served.
- Stub configs for Stingray and Magna line are honest signals that the framework generalizes.
- v1.1 has a clear, scoped next step.

### Negative

- TGW recruiters may notice the Stingray config is a stub and discount the project. Mitigation: the README explicitly states the v1.0 scope and roadmap.
- Magna Steyr is even further from being addressed. Acceptable, since they are the tertiary audience.

### Anti-Creep Tripwire

Adding full Stingray or Magna calibration to v1.0 requires an ADR explicitly named `ADR-XXXX-scope-lock-override.md` per PROJECT_CHARTER.md §9.1.

## References

- PROJECT_CHARTER.md §9.1 Lock L1
- PROJECT_CHARTER.md §5.1 FR-10 (Should, not Must)
- Knapp AG public AutoStore case studies
