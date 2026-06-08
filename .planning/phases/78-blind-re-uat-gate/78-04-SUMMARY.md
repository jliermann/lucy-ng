# 78-04 Summary — AND-gate Verdict Roll-up (v9.0 milestone gate)

**Status:** Complete
**Plan:** 78-04 (wave 3, autonomous: true — terminal plan of Phase 78 and the v9.0 gate)

## What happened

Applied the D-78-05 AND-gate to the two per-compound evidence records and wrote the authoritative
milestone verdict.

## AND-gate result

| UAT req | Compound | Verdict |
|---------|----------|---------|
| UAT-03 | CASE1 (C13H18O2) | PASS (emergent, clean) |
| UAT-04 | CASE9 (C12H16O3) | FAIL (correct structure never reached; ring forced; carbonyl missed) |
| **AND-GATE** | — | **FAIL** |

## Milestone outcome

**v9.0 DOES NOT SHIP.** The gate fails on UAT-04.

## Artifacts

- `78-UAT-VERDICT.md` — AND-gate roll-up, SC-1..SC-4 mapping, forensics-on-fail, follow-up seed

## Follow-up

Phase 79 added to ROADMAP: fix the upstream peak-picking / symmetry-detection defect (SNR-based
threshold / CDCl₃ exclusion + 13C intensity-symmetry), then re-run CASE9 blind and re-apply the
AND-gate.
