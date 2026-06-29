# lucy-ng Roadmap

## Milestones

- [v1.0 Core CASE Pipeline](milestones/v1.0-ROADMAP.md) - Phases 1-10 (shipped 2026-01-12)
- [v1.1 Database-Backed Dereplication](milestones/v1.1-ROADMAP.md) - Phases 11-15 (shipped 2026-01-15)
- [v1.2 HOSE Database Prediction](milestones/v1.2-ROADMAP.md) - Phases 16-19 (shipped 2026-01-18)
- **v2.0 Robust Multi-Agent CASE** - Phases 20-26 (shipped 2026-02-08)
- **v2.1 Working Multi-Agent CASE** - Phases 27-33 (shipped 2026-02-09)
- [v3.0 Statistical Detection](milestones/v3.0-ROADMAP.md) - Phases 34-40 (shipped 2026-02-16)
- [v4.0 Team-Based CASE](milestones/v4.0-ROADMAP.md) - Phases 41-48 (shipped 2026-02-18)
- [v5.0 Fragment Library](milestones/v5.0-ROADMAP.md) - Phases 49-54 (shipped 2026-02-21)
- [v6.0 Skill Quality Overhaul](milestones/v6.0-ROADMAP.md) - Phases 55-58 (shipped 2026-03-10)
- [v7.0 Statistical 4J Detection](milestones/v7.0-ROADMAP.md) - Phases 59-64 (ABANDONED 2026-03-12)
- **v8.0 pyLSD Integration** - Phases 65-71 (superseded by v9.0 before UAT passed)
- ✅ [v9.0 CASE Reliability & Skill Consolidation](milestones/v9.0-ROADMAP.md) - Phases 72-85 (shipped 2026-06-17)
- ✅ [v9.1 CASE Final-Answer Correctness & Verification Gates](milestones/v9.1-ROADMAP.md) - Phases 86-89 (shipped 2026-06-29)

---

**v9.1 outcome:** Closed three "clean-but-wrong" defect classes — RANK (ranker path unified),
IDENT (`lucy identify` + post-solution G-IDENT gate), MULT (per-family multiplicity search +
MAE-independent coverage gate) — and proved them end-to-end with five blind CASE UATs
(CASE5/6/7/8 PASS; CASE4 conditional). Audit: `milestones/v9.1-MILESTONE-AUDIT.md`.
Non-blocking deferred follow-up: CASE4 azulene-regiochemistry-enumeration gap (4th defect class,
exact chamazulene regiochemistry still unreachable) — todo `2026-06-25-case4-azulene-regiochemistry-enumeration-gap`.

---

## Next Milestone

No active milestone. Run `/gsd-new-milestone` to scope the next version.

Candidate seed (carried from v9.1): **CASE4 azulene-regiochemistry-enumeration gap** — the
di-methyl-ethyl class is now searched, but the exact chamazulene regiochemistry is not enumerated
(suspected azulene/non-benzenoid connectivity enumeration + degraded 2D data + azulene HOSE
unreliability). See `.planning/todos/pending/2026-06-25-case4-azulene-regiochemistry-enumeration-gap.md`.
