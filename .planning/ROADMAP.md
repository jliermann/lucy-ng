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
- 🚧 **v9.1 CASE Final-Answer Correctness & Verification Gates** - Phases 86-89 (active)

---

**v9.0 outcome:** AND-gate met cleanly on Opus 4.8 — CASE9 (UAT-04) solved and CASE1 (UAT-03)
a CLEAN EMERGENT PASS (ibuprofen rank 1, exact InChIKey, RDKit-verified; benzene ring emerged
with 0 ring-BONDs / SKEL / SYME / DEFF NOT). D-04 resolved to "emergent". Non-gating residual
carried to v9.1: `lucy lsd rank` scoring defect (see `.planning/todos/pending/`).

---

# v9.1 — CASE Final-Answer Correctness & Verification Gates

**Goal:** Ensure the final reported structure is correct AND independently verified — close the
three "clean-but-wrong" defect classes (low MAE, plausible, but wrong) that slip through every
existing safety net, proven by blind UATs.

**Granularity:** standard
**Coverage:** 13/13 requirements mapped ✓

**Sequencing rationale:** RANK is an isolated tooling fix (Python, unit-testable, no blind
instance) and goes first. IDENT and MULT are independent skill-level fixes (edits to
`repo/.claude/` agent definitions) that change agent behavior — they can only be *fully*
validated by blind UAT, so a single UAT gate phase follows and depends on both. UAT-01 is the
acceptance test for MULT (CASE4), UAT-02 the acceptance test for IDENT (CASE5); UAT-03 adds
first blind runs of CASE6/7/8 to surface any 4th defect.

## Phases

- [x] **Phase 86: Ranker Path Unification (RANK)** - Make `lucy lsd rank` and `lucy predict c13` share one prediction path so the ranker stops under-scoring the truth. (completed 2026-06-23)
- [x] **Phase 87: Final Identity-Verification Gate (IDENT)** - Tool-derived identity + an independent name↔structure gate that blocks naming hallucination. (completed 2026-06-23)
- [ ] **Phase 88: Aliphatic Multiplicity Robustness (MULT)** - Enumerate all viable multiplicity families when multiplicity is not hard-determinable; MAE-independent clean-but-wrong guardrail.
- [ ] **Phase 89: Blind-UAT Validation Gate (UAT)** - Blind CASE4/5 re-runs + CASE6/7/8 first runs prove the IDENT/MULT fixes and surface any 4th defect.

## Phase Details

### Phase 86: Ranker Path Unification
**Goal**: `lucy lsd rank` ranks the correct structure using the same prediction it would get from `lucy predict c13`, so the truth is no longer systematically under-scored.
**Depends on**: Nothing (first phase of v9.1; isolated Python tooling, no blind instance needed)
**Requirements**: RANK-01, RANK-02, RANK-03
**Success Criteria** (what must be TRUE):
  1. For an identical molecule, `lucy lsd rank` and `lucy predict c13` produce the same per-shift 13C prediction (a developer can run both and diff the predicted shifts — they match).
  2. On the CASE1 (ibuprofen) and CASE3 (pulegone) molecules where divergence was measured, the ranker's MAE/match-count for the correct structure agrees with `lucy predict c13` within a defined tolerance (ranker no longer reports 2.23/8-of-10 where predict reports 0.27/10-of-10).
  3. The ranker places the correct structure ahead of the wrong isomer it previously ranked #1 on those molecules.
  4. A committed regression test pins ranker↔predict agreement on the CASE1 and CASE3 molecules; `pytest` is green.
**Plans**: 2 plans
  - [x] 86-01-PLAN.md — Add SolutionRanker.from_database + shared resolve_c13_predictor() DB-first backend helper (RANK-01 building blocks)
  - [x] 86-02-PLAN.md — Wire lsd rank + predict c13 through the shared resolver (--db/--max-radius parity) + RANK-01/02/03 regression on CASE1/CASE3

### Phase 87: Final Identity-Verification Gate
**Goal**: The reported compound name is derived from the structure by a tool and independently checked, so a recalled-from-memory wrong trivial name can no longer be asserted as fact.
**Depends on**: Nothing (independent skill-level fix; can run in parallel with Phase 88)
**Requirements**: IDENT-01, IDENT-02, IDENT-03
**Success Criteria** (what must be TRUE):
  1. The solution-analyst derives identity from the solution SMILES via a tool (InChIKey / structure lookup) and never states a recalled trivial name as established fact.
  2. An independent final gate (devils-advocate and/or `verify_case_solution.py`) checks the analyst's name↔structure mapping before results are reported; a detected mismatch blocks or flags the report rather than passing silently.
  3. When identity cannot be tool-confirmed, the report marks the name as tentative with a confidence qualifier instead of asserting it.
  4. The CASE4/CASE5 naming-hallucination pattern (wrong "literature" reference; indigo↔isoindigo mislabel) is demonstrably caught by the gate on those structures.
**Plans**: 4 plans (2 original + 2 gap-closure for GAP-87-A runtime reachability)
  - [x] 87-01-PLAN.md — Extend `verify_case_solution.py` with `derive_identity()` + `check-identity` subcommand (InChIKey-first / SMILES-fallback two-path lookup, tentative/novel verdicts) + CASE4/CASE5 regression tests — the deterministic binding gate (IDENT-01/02/03)
  - [x] 87-02-PLAN.md — Wire the tool into the CASE agents: solution-analyst derivation + tentative-name rendering; devils-advocate post-solution advisory gate G-IDENT (IDENT-01/02/03)
  - [x] 87-03-PLAN.md — Gap closure (GAP-87-A): move the deterministic identity core into the installed package (`lucy_ng.identity`) + add a `lucy identify --format json` subcommand reachable from a CASE data dir; repoint `verify_case_solution.py` to import it (one shared path, D-05) (IDENT-01/02)
  - [x] 87-04-PLAN.md — Gap closure (GAP-87-A): repoint the solution-analyst + devils-advocate G-IDENT from the repo-relative `scripts/...` path to the installed `lucy identify` command; IDENT-03 rendering + advisory gate preserved (IDENT-01/02/03)

### Phase 88: Aliphatic Multiplicity Robustness
**Goal**: When aliphatic CH/CH2/CH3 multiplicity cannot be hard-determined, the search covers every viable multiplicity family so the correct constitution is reachable — hardening v9.0 FIX-10 which does not cover multiplicity.
**Depends on**: Nothing (independent skill-level fix; can run in parallel with Phase 87)
**Requirements**: MULT-01, MULT-02, MULT-03, MULT-04
**Success Criteria** (what must be TRUE):
  1. When multiplicity is not hard-determinable (non-multiplicity-edited HSQC and/or unreliable/phase-distorted APT/DEPT), the lsd-engineer searches ALL viable multiplicity families (e.g. iPr-path 3×CH3+CH AND ethyl-path 2×CH3+CH2+CH2) instead of hard-coding one.
  2. The nmr-chemist emits an explicit "multiplicity-ambiguous → enumerate families" signal when HSQC is not multiplicity-edited, and the lsd-engineer acts on it deterministically.
  3. An MAE-independent clean-but-wrong guardrail fires: if ≥2 viable multiplicity families exist but only one was searched, the run does not accept — it reopens and searches the other(s).
  4. A devils-advocate "evidence FOR model X" multiplicity flag forces model X into the search space and cannot be dismissed by the convergence narrative.
**Plans**: TBD

### Phase 89: Blind-UAT Validation Gate
**Goal**: Independent blind CASE runs prove the RANK/IDENT/MULT fixes hold end-to-end and surface any remaining "clean-but-wrong" defect class.
**Depends on**: Phase 87 (IDENT), Phase 88 (MULT). (Phase 86 RANK is also in effect by this point.)
**Requirements**: UAT-01, UAT-02, UAT-03
**Success Criteria** (what must be TRUE):
  1. CASE4 blind re-run reaches chamazulene's di-methyl-ethyl constitution in the solution set (truth reachable), regardless of which regioisomer ranks #1 — the direct acceptance test for MULT.
  2. CASE5 blind re-run on sanitised data passes: correct structure at rank 1 AND the name correctly derived from structure — the acceptance test for IDENT.
  3. CASE6, CASE7, and CASE8 first blind runs are executed and bookkept; any new defect class surfaced is captured as a todo (it need not be fixed in v9.1).
  4. Every reported structure is independently RDKit-verified by InChIKey (never agent self-report).
**Plans**: TBD
**Note**: Execution requires FRESH BLIND Claude instances per the project blind-UAT rule (`feedback_blind_uat`). The orchestrator only bookkeeps — it must never run the CASE itself, and answer-key identities must stay out of the runtime CASE skill. Run via the `case-blind` alias.

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 86. Ranker Path Unification | 2/2 | Complete    | 2026-06-23 |
| 87. Final Identity-Verification Gate | 4/4 | Complete    | 2026-06-24 |
| 88. Aliphatic Multiplicity Robustness | 0/? | Not started | - |
| 89. Blind-UAT Validation Gate | 0/? | Not started | - |
