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
- ✅ [v9.2 CASE Web-View](milestones/v9.2-ROADMAP.md) - Phases 90-92 (shipped 2026-07-07)

---

## No active milestone

**v9.2 CASE Web-View shipped 2026-07-07** (Stage 1): a read-only dashboard makes a CASE run
observable — three auto-refreshing widgets (run status, top RDKit-rendered structures, run log),
auto-launched by the orchestrator and kept alive after the run. Full detail:
[`milestones/v9.2-ROADMAP.md`](milestones/v9.2-ROADMAP.md).

**Next up — Stage-2 milestone (v9.3):** the deferred webview work — formatted run log (render
`CASE-PROGRESS.md` markdown) + rendered spectra tabs (1D ¹³C/¹H/DEPT, 2D HSQC/HMBC/COSY) + data
tables (peak lists, constraint inventory, HMBC usage). See STATE.md § Deferred Items and
`docs/superpowers/specs/2026-07-02-case-webview-design.md` § Stage 2. The v9.2 architecture was
built to accommodate it ("tabs dock in without a rewrite"). Start with `/gsd-new-milestone`.

Also outstanding (unrelated to webview, carried from v9.1): CASE4 azulene-regiochemistry
enumeration gap — todo `2026-06-25-case4-azulene-regiochemistry-enumeration-gap`.
