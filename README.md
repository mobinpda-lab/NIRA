# NIRA

**NIRA** is the official and sole canonical name of the autonomous software factory control plane.

**Repository identity:** `mobinpda-lab/NIRA` after the repository rename. The former repository slug is retained only in the historical record and must not be used as an active authority identifier.

## Mission

NIRA is the independent factory control plane for operating multiple software repositories. Product repositories are workloads/clients of NIRA, never containers of the factory core.

## Canonical boundary

```text
NIRA
  Governance / Registry / Intake / Queue / Lease / Fencing
  Workers / Execution / Evidence / Gates / Security
  Promotion / Release / Recovery / Audit / Observability
                    |
          +---------+---------+
          |                   |
       adapters            workloads
          |                   |
       Arvin            YadNegar / NetworkCenterMonitor
```

The factory is generic. Project-specific behavior belongs behind adapters and explicit contracts.

## Core invariants

- No direct main mutation for factory development.
- Exact HEAD and exact base are mandatory for promotion.
- Worker claims are never accepted as independent evidence.
- Missing, stale, invalid or inaccessible evidence is never a PASS.
- One active lease owns a task; stale owners are fenced.
- Recovery is bounded (default: 3 attempts; 5-minute lease TTL; 60-second heartbeat).
- Promotion is serialized per project/task and verified by an independent postcondition read.
- Factory progress and product progress are reported separately.

## Canonical lifecycle

```text
IDEA -> DEFINITION -> ARCHITECTURE -> TASK -> QUEUE -> LEASE
 -> WORKER -> CODE -> TEST -> AUTOFIX -> CI -> EVIDENCE
 -> SECURITY -> GATES -> EXACT-HEAD -> PROMOTION -> RELEASE
 -> MONITOR -> FAILURE/FENCING -> RECOVERY/RESUME -> COMPLETE
```

## Current maturity statement

NIRA has the architectural boundary, production orchestrator bootstrap, canonical contracts, fail-closed lifecycle primitives, evidence model foundation, gate primitives, recovery policy and conformance tests in place.

**L10 remains `UNVERIFIED` until a real registered client task produces reconstructible end-to-end factory evidence, including bounded failure/fencing/recovery and release/promotion evidence.**

The complete historical naming transition is recorded in `docs/history/NIRA_IDENTITY_HISTORY.md`. Historical identifiers are provenance only and are never active factory authority.

See `docs/architecture/NIRA_FACTORY_CONTROL_PLANE_v1.md` and `docs/architecture/NIRA_INDEPENDENT_FACTORY_ARCHITECTURE.md` for the canonical boundary and implementation contract.

## Intelligence pipeline proof

NIRA self-maintenance uses deterministic failure classification, adaptive queue capacity, exact-head change-impact planning, independent CI/security evidence, GitHub-derived operating state, specialized worker-role contracts, and fail-closed promotion. Exhausted AI provider capacity blocks only the AI lane; deterministic factory work remains available.
