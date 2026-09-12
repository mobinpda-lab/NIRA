# NIRA Roadmap Queue

> Generated from live GitHub Issues. Issue state/labels are authoritative.

## NOW

| Task | Goal | Priority | Status | Evidence/Labels |
|---|---|---:|---|---|
| #86 | dogfood(nira): exact-main intelligence pipeline completion proof | P1 | READY | automation, factory, factory:ready, nira, priority:core |
| #160 | [NIRA SELF SC-01] NIRA self diagnostics and health snapshot | P1 | QUEUED | factory:queued, factory:ready, priority:core |
| #161 | [NIRA SELF SC-02] NIRA reconstructible evidence chain | P1 | QUEUED | factory:queued, factory:ready, priority:core |
| #162 | [NIRA SELF SC-03] NIRA bounded recovery decision hardening | P1 | QUEUED | factory:queued, factory:ready, priority:core |
| #184 | NIRA Autonomous Global Reconcile upgrade | P1 | QUEUED | factory:queued, factory:ready, priority:core |

## NEXT

| Task | Goal | Priority | Status | Evidence/Labels |
|---|---|---:|---|---|
| #25 | feat(nira): activate real cross-repository execution plane from migrated Arvin factory patterns | P2 | QUEUED | factory:queued, factory:ready, priority:automation |
| #29 | feat(nira): establish Future Projects registration boundary | P2 | READY | factory:ready, priority:automation |

## LATER

| Task | Goal | Priority | Status | Evidence/Labels |
|---|---|---:|---|---|
| #27 | feat(nira): provision real cross-repository execution plane | P4 | QUEUED | enhancement, factory:queued |
| #97 | [AUTO-FIX] NIRA Factory Conformance failed at a9e7e8f9f385 | P4 | QUEUED | factory:queued, factory:ready |
| #98 | [AUTO-FIX] NIRA Factory Conformance failed at b09515921454 | P4 | QUEUED | factory:queued, factory:ready |
| #102 | [AUTO-FIX] NIRA Factory Conformance failed at bb623564d33c | P4 | QUEUED | factory:queued, factory:ready |
| #105 | [AUTO-FIX] NIRA Factory Conformance failed at 863264dff418 | P4 | QUEUED | factory:queued, factory:ready |
| #108 | [AUTO-FIX] NIRA Factory Conformance failed at a06477c15df6 | P4 | QUEUED | factory:queued, factory:ready |
| #112 | [AUTO-FIX] NIRA Factory Conformance failed at 6dadc2d0c27e | P4 | QUEUED | factory:queued, factory:ready |
| #114 | [AUTO-FIX] NIRA Factory Conformance failed at 11ab21bd0856 | P4 | QUEUED | factory:queued, factory:ready |
| #117 | [AUTO-FIX] NIRA Factory Conformance failed at 40c2c7b6bc62 | P4 | QUEUED | factory:queued, factory:ready |
| #118 | [AUTO-FIX] NIRA Factory Conformance failed at 3e4f4502a36e | P4 | QUEUED | factory:queued, factory:ready |
| #120 | [AUTO-FIX] NIRA Factory Conformance failed at 95ad0ad3fbc8 | P4 | QUEUED | factory:queued, factory:ready |
| #122 | [AUTO-FIX] NIRA Factory Conformance failed at 9eda0a68543b | P4 | QUEUED | factory:queued, factory:ready |
| #124 | [AUTO-FIX] NIRA Factory Conformance failed at adf775c73a05 | P4 | QUEUED | factory:queued, factory:ready |
| #126 | [AUTO-FIX] NIRA Factory Conformance failed at b646c9d4f04d | P4 | QUEUED | factory:queued, factory:ready |
| #128 | [AUTO-FIX] NIRA Factory Conformance failed at 4c47cba2a391 | P4 | QUEUED | factory:queued, factory:ready |
| #129 | [AUTO-FIX] NIRA Factory Conformance failed at 7f09e9432e8d | P4 | QUEUED | factory:queued, factory:ready |
| #134 | [AUTO-FIX] NIRA Factory Conformance failed at 1b213b6a799f | P4 | QUEUED | factory:queued, factory:ready |
| #138 | [AUTO-FIX] NIRA Factory Conformance failed at 2e3b77695eec | P4 | QUEUED | factory:queued, factory:ready |
| #143 | [AUTO-FIX] NIRA Factory Conformance failed at b9ab05b8fb66 | P4 | QUEUED | factory:queued, factory:ready |
| #147 | [AUTO-FIX] NIRA Factory Conformance failed at 3f9b428e40e5 | P4 | QUEUED | factory:queued, factory:ready |
| #150 | [AUTO-FIX] NIRA Factory Conformance failed at 1b0d14d038f5 | P4 | QUEUED | factory:queued, factory:ready |
| #152 | [AUTO-FIX] NIRA Factory Conformance failed at 12a58a3772cb | P4 | QUEUED | factory:queued, factory:ready |
| #170 | [AUTO-FIX] NIRA Factory Conformance failed at 831ebede6484 | P4 | QUEUED | factory:queued, factory:ready |
| #174 | [AUTO-FIX] NIRA Factory Conformance failed at bd416025ba99 | P4 | QUEUED | factory:queued, factory:ready |
| #181 | [AUTO-FIX] NIRA Factory Conformance failed at c6d9b3e76c40 | P4 | QUEUED | factory:queued, factory:ready |
| #186 | [AUTO-FIX] NIRA Factory Conformance failed at 24fddf495f23 | P4 | QUEUED | factory:queued, factory:ready |
| #188 | [AUTO-FIX] NIRA Factory Conformance failed at e15057efe08e | P4 | QUEUED | factory:queued, factory:ready |

## Queue Contract

- Existing code/issues/PRs/branches must be reused before new work is created.
- Independent repositories may execute in parallel; competing mutations against one client main are serialized.
- Failure is routed through classification/recovery; it is never counted as completion.
- Completion requires exact-SHA execution evidence.
