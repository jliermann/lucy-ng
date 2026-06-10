# Phase 82 / FIX-09 — Blind-UAT Skill Hygiene: Decontamination Report

**Date:** 2026-06-10
**Trigger:** Mid-CASE9 blind run, the fresh instance reported *"Phase-78-Gate bestanden — aromatischer Ring emergent (kein SKEL, keine Ring-BONDs)"*. A blind elucidation instance cannot know about "Phase 78" or any success criterion — it had read them out of its own runtime skill files.

## Root cause
The runtime CASE skill/agent files (hand-maintained under `~/.claude/`, NOT git-tracked, no repo source) accumulated three classes of blind-test contaminant as prior phases (72–81) annotated fixes with development metadata and worked examples drawn from the actual test compound:
- **L1 dev-meta** — GSD phase numbers, decision IDs (D-xx/FIX-xx), milestone versions (v2.1–v9.0), "UAT/gate/milestone/postmortem", experiment-arm labels (Arm A/B/C).
- **L2 answer-key** — the test compound (ibuprofen) named outright, its formula `C13H18O2`, its solution atom mappings (`COSY 4 7`, `BOND 10 11`, "iter3"), its actual 13C shifts (`[44.90, 45.03]`, `129.38/127.26…`), and the label "CASE9 trap".
- **L3 success-criteria** — pass/fail gate definitions baked into the runtime (`case.md` `uat_criteria` step: "EMERGENT RING = CLEAN PASS"; lsd-engineer "fails the Phase 78 UAT gate"; "Arm A: 2/2 aromatic solutions, ibuprofen found").

A fresh CASE instance loading these files therefore knew it was inside a numbered dev process, that the answer was an ibuprofen-like para-disubstituted benzene, and that "success" = an emergent aromatic ring. **The 2026-06-10 CASE9 run is INVALIDATED.**

## Blast radius (what a blind CASE9 run loads)
`/lucy-ng:case` → `case.md` orchestrator, which spawns 4 team agents (`lucy-nmr-chemist`, `lucy-lsd-engineer`, `lucy-solution-analyst`, `lucy-devils-advocate`) and loads 3 references (`loop-patterns.md`, `advisory-templates.md`, `progress-format.md`); `lucy-diagnostic` is spawned on escalation. `lucy-case-agent.md` is **orphaned** (never spawned; deprecated v4.0) — left in place, recommend deletion.

## What was changed (60 edits across 7 files; ~/.claude is not git-tracked)
| File | Edits | Notable |
|------|-------|---------|
| `commands/lucy-ng/case.md` | 5 | **Removed entire `uat_criteria` step** (relocated to `.planning/case-uat-gate-criteria.md`); smoke-test defaults `data/Ibuprofen`/`C13H18O2` → neutral `data/example_compound`/`C9H10O2` |
| `references/loop-patterns.md` | 2 | "CASE9 trap" → neutral; drop `(D-12)` |
| `references/advisory-templates.md` | 8 | drop v3.0 Ibuprofen-UAT baseline + v3.0-comparison template lines + Phase/v2.1 labels |
| `agents/lucy-lsd-engineer.md` | 20 | ibuprofen `compound_native.lsd`/atom-mapping examples → abstract illustrative; "Arm A: 2/2 … ibuprofen found" deleted; "fails the Phase 78 UAT gate" → "is a protocol violation"; phase/FIX/D-labels stripped; `C13H18O2` → `C9H10O2` |
| `agents/lucy-diagnostic.md` | 7 | ibuprofen iter3 atom mappings → abstract; Phase/D-labels stripped |
| `agents/lucy-solution-analyst.md` | 5 | 13-shift ibuprofen CLI example → placeholder; `13/13 | 2.23` table → `N/N | X.XX`; Phase 80 D-04 label dropped |
| `agents/lucy-devils-advocate.md` | 14 | **"live ibuprofen UAT" → "prior live testing"**; `[44.90,45.03]` → illustrative; real COSY atom indices → abstract; v8.0-postmortem rationale neutralized; D-IDs dropped from warning strings (LSD-manual citations kept) |

**Neutralization policy:** L1 → strip label, keep the domain rule. L2 → replace with abstract/illustrative placeholders teaching the same pattern, no test compound named. L3 → remove from runtime; the compound-agnostic methodological rule ("don't force connectivity you haven't derived; forcing is a documented last-resort escalation; SKEL forbidden") is kept, the expected-outcome presupposition and verification claims removed.

## Verification
Independent central grep across all 10 active runtime files: **0 matches** for every pattern (`Phase [0-9]`, `D-0x`, `FIX-0`, `vX.Y`, `UAT`, `Arm [ABC]`, `ibuprofen`, `C13H18O2`, `CASE9`, `CASE1`, `benzoate`, `iter3`, `postmortem`). All frontmatter valid; file structures intact; no dangling `uat_criteria` reference. `lucy-nmr-chemist.md` was already clean.

## Follow-ups (out of scope for FIX-09)
- **Skill-creator bloat findings** (observation only): `lucy-diagnostic.md` ~1146 lines (≈2× the ~500 guideline), `lucy-lsd-engineer.md` 524, `lucy-devils-advocate.md` 488, `case.md` 608. Candidates for progressive-disclosure refactor (move reference material to `references/`, dedupe inline advisory templates). Several agent `description:` fields lack explicit "Use when:" spawn triggers. Backlog, not blocking.
- **`lucy-case-agent.md`** — **DELETED 2026-06-10.** Closes a FIX-03 loose end: Phase 77 / plan 77-03 (2026-06-01) "retired" it only by renaming the frontmatter `name:` to `DEPRECATED-lucy-case-agent` + a deprecation blockquote ("archive in place"), leaving the 1291-line file on disk with an active-looking `description:`. It was confirmed orphaned (never spawned by any active command/agent), so not a live blind-UAT vector, but it was dead weight and latent risk. Note the irony: the same plan 77-03 that "retired" it also INTRODUCED the `uat_criteria` (D-77-06) leak into case.md that FIX-09 just removed — "skill hygiene" that left dead files and added a contaminant. Lesson now codified in FIX-09: hygiene must mean concrete deletion + grep-verification, not archive-in-place.
- **Repo `skill/` dir** is stale v2.x structure (not the source of the current team agents) — separate cleanup.

## Gate status
v9.0 ship-gate (blind re-UAT CASE9 + CASE1, fresh instances per `feedback_blind_uat`) is now safe to run on decontaminated skills. The invalidated 2026-06-10 run does not count.
