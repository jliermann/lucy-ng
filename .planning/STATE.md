---
gsd_state_version: 1.0
milestone: v9.1
milestone_name: CASE Final-Answer Correctness & Verification Gates
status: executing
stopped_at: Phase 88 context gathered
last_updated: "2026-06-25T09:49:01.374Z"
last_activity: 2026-06-25 -- Phase 88 planning complete
progress:
  total_phases: 4
  completed_phases: 2
  total_plans: 9
  completed_plans: 6
  percent: 50
---

# lucy-ng State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-23)

**Core value:** AI agent autonomously determines compound structures from NMR, with a multi-agent team that uses the intended solver pipeline — not a manual bypass
**Current focus:** Phase 88 — aliphatic multiplicity robustness

## Current Position

Phase: 88
Plan: Not started
Status: Ready to execute
Last activity: 2026-06-25 -- Phase 88 planning complete

## Milestone v9.1 Phases

| Phase | Goal | Requirements | Depends on |
|-------|------|--------------|------------|
| 86. Ranker Path Unification | One shared prediction path; ranker stops under-scoring the truth | RANK-01..03 | — |
| 87. Final Identity-Verification Gate | Tool-derived identity + independent name↔structure gate | IDENT-01..03 | — |
| 88. Aliphatic Multiplicity Robustness | Enumerate all viable multiplicity families; clean-but-wrong guardrail | MULT-01..04 | — |
| 89. Blind-UAT Validation Gate | Blind CASE4/5 re-run + CASE6/7/8 first runs prove fixes | UAT-01..03 | 87, 88 |

**Sequencing:** 86 (RANK) is isolated Python tooling — unit-testable, no blind instance — and goes first. 87 (IDENT) and 88 (MULT) are independent skill-level fixes (`repo/.claude/` agent edits) and can proceed in parallel. 89 (UAT) gates on 87+88: UAT-01=CASE4 is the acceptance test for MULT, UAT-02=CASE5 the acceptance test for IDENT. Phase 89 must run on FRESH BLIND instances (orchestrator only bookkeeps).

## Deferred Items

Items acknowledged and deferred at v9.0 milestone close on 2026-06-17 (the rank-scoring todo is now ACTIVE as Phase 86):

| Category | Item | Status | Note |
|----------|------|--------|------|
| todo | 2026-06-17-lucy-lsd-rank-scoring-defect | active → Phase 86 | now in scope as RANK |
| uat | 54-UAT.md | unknown | v5.0-era artifact, not v9.0 |
| uat | 78-UAT-CASE1.md / 78-UAT-CASE9.md / 78-UAT-VERDICT.md | superseded | failed gate later overcome (CASE9 solved + CASE1 emergent pass) |
| uat | 79-HUMAN-UAT.md | superseded | resolved by 2026-06-17 CASE1 emergent pass |
| uat | 80-UAT-VERDICT.md | superseded | resolved by Phase 81 (FIX-08) |
| uat | v2.1-UAT.md | testing | v2.1-era artifact (4 open scenarios), not v9.0 |
| verification | 28-VERIFICATION.md | human_needed | v2.0-era artifact |
| verification | 54-VERIFICATION.md | gaps_found | v5.0-era artifact |
| verification | 75-VERIFICATION.md | human_needed | live-run check satisfied by v9.0 blind UATs |
| verification | 79-VERIFICATION.md | human_needed | live-run check satisfied by 2026-06-17 CASE1 emergent pass |

## Completed Milestones

| Milestone | Phases | Shipped |
|-----------|--------|---------|
| v1.0 Core CASE Pipeline | 1-10 | 2026-01-12 |
| v1.1 Database-Backed Dereplication | 11-15 | 2026-01-15 |
| v1.2 HOSE Database Prediction | 16-19 | 2026-01-18 |
| v2.0 Robust Multi-Agent CASE | 20-26 | 2026-02-08 |
| v2.1 Working Multi-Agent CASE | 27-33 | 2026-02-09 |
| v3.0 Statistical Detection | 34-40 | 2026-02-16 |
| v4.0 Team-Based CASE | 41-48 | 2026-02-18 |
| v5.0 Fragment Library | 49-54 | 2026-02-21 |
| v6.0 Skill Quality Overhaul | 55-58 | 2026-03-10 |
| v7.0 Statistical 4J Detection | 59-64 | ABANDONED 2026-03-12 |
| v8.0 pyLSD Integration | 65-71 | Superseded by v9.0 (UAT failed as mechanism validation) |
| v9.0 CASE Reliability & Skill Consolidation | 72-85 | 2026-06-17 |

## Performance Metrics

**Velocity:**

- Total plans completed: 160 across 11 milestones (10 shipped + 1 abandoned) — v9.0 added 34 plans
- v9.0: 14 phases (72-85), 34 plans, 41 tasks; shipped 2026-06-17
- v9.1 Phase 86 (Ranker Path Unification): 2 plans, 4 tasks; 86-02 ~8 min, 3 files, 2 commits
- v9.1 Phase 87 (Final Identity-Verification Gate): 2 plans + 2 gap-closure (87-03/04); 87-02 ~6 min, 2 files; 87-03 ~3 min, 6 files (3 created), 3 commits
- Cumulative: 87 phases total

## Accumulated Context

### Roadmap Evolution

- v9.1 roadmap created (2026-06-23): phases 86-89. Derived from the three post-v9.0 blind-UAT defect todos (`2026-06-{17,21,23}-*.md`). RANK (Phase 86) is the carried-forward v9.0 non-gating residual now made gating. IDENT (87) and MULT (88) are new skill-level defect classes surfaced by CASE4/CASE5 blind runs (naming hallucination; aliphatic multiplicity ambiguity). UAT (89) is the blind validation gate (CASE4=MULT acceptance, CASE5=IDENT acceptance, CASE6/7/8 first runs).

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.

- [86-01]: Ranker gained `SolutionRanker.from_database` + a shared `resolve_c13_predictor()` DB-first 4-tier backend ladder (in `prediction/resolver.py`, never importing from `cli/`). `_match_shifts`/MAE left byte-identical. The JSON fallback replicates lsd.py's three shipped-table candidate paths to defeat the `hose_nmrshiftdb.json.gz` filename trap. CLI wiring (`lucy lsd rank --db/--table/--max-radius`) is Plan 86-02.

- [86-02]: `lucy lsd rank` and `lucy predict c13` now share ONE prediction path via `resolve_c13_predictor` (RANK-01) — `_perform_ranking` and `predict_c13` both call the helper; rank gained `--db`/`--max-radius` parity. Backend selection lives only in the helper (no CLI re-branch). RANK-01/02/03 regression tests pin per-shift parity (abs diff <1e-6), MAE/match-count agreement (≤0.05 ppm), and the wrong-isomer ordering fix on ibuprofen (real-DB MAE 0.24 / 13-13 vs old 2.23 / 8-13) + pulegone (ordering-fix). Deterministic test seeds only r6 HOSE codes to keep ordering non-circular. mypy/ruff clean-delta; 110 ranking+prediction tests green.

- [87-03]: GAP-87-A closed — the 87-01 deterministic identity core was moved VERBATIM into the installed package as `lucy_ng.identity` and exposed via a new `lucy identify` subcommand (`--smiles/--reported-name/--database/--format json`), reachable from any data dir (cf. `lucy lsd rank`). D-05 upheld: exactly one implementation; both `cli/identify.py` and the thinned `scripts/verify_case_solution.py check-identity` import it (back-compat preserved). `check_identity_result` is a pure no-print/no-exit verdict function; `lucy identify` always exits 0 (D-06). 27 identity+CLI tests green; ruff/mypy clean on touched src. 87-04 (skill wiring of `lucy identify` into the analyst/binding gate) remains.

- [v9.1-roadmap]: All three v9.1 defects are "clean-but-wrong" — low MAE, plausible, but wrong. None is caught by an existing mechanism (identity gate doesn't help when the structure is wrong; rank/analyst override can't recover a structure absent from the solution set; the MAE>4 quality loop stays silent at MAE 1.75). The fixes target reachability (MULT), independent verification (IDENT), and scoring fidelity (RANK).
- [v9.1-roadmap]: RANK sequenced first because it is self-contained Python tooling — reproducible without a CASE run, fully unit-testable, no blind instance required. IDENT and MULT are skill-level (agent-definition) edits and therefore can only be fully validated by the blind UAT gate, not unit tests → they precede Phase 89 and gate it.
- [v9.1-roadmap]: Azulene regiochemistry (CASE4) is explicitly OUT OF SCOPE to resolve by 13C alone — physically unresolvable (top isomers within 0.26 ppm MAE). UAT-01 only requires the correct di-methyl-ethyl *constitution class* to be reachable in the solution set, not unique regiochemistry.
- [Phase ?]: [87-01]: derive_identity + check-identity added to scripts/verify_case_solution.py — deterministic InChIKey/canonical-SMILES identity with complementary two-path DB lookup (InChIKey-first nmrshiftdb, canonical-SMILES fallback coconut); tolerant token-set name_match over synonyms (not exact/substring); name<->structure mismatch -> 'tentative' + warning, exit 0 always (D-06). CASE4/CASE5 regressions pinned. IDENT-01/02/03 done.
- [Phase 87]: [87-02]: Wired check-identity into the CASE agents. Analyst derives identity from the tool before writing the report header (verdict-keyed: confirmed name plain; confirmed-structure/novel/tentative => InChIKey+canonical SMILES primary, trivial name '(tentative, unverified)'). Devils-advocate gained G-IDENT, a POST-SOLUTION advisory gate on final_results.md (distinct lifecycle from pre-solver gates) that reasons independently about name<->structure and does NOT call the deterministic tool (preserving D-05 independence); CASE4/CASE5 worked triggers. Markdown prompt edits; fresh session needed to reload; functional validation by Phase 89 blind UAT. IDENT-01/02(advisory)/03 done.
- [Phase ?]: [87-04]: Re-pointed both CASE agents from scripts/verify_case_solution.py check-identity to the installed lucy identify --format json (GAP-87-A runtime closure); invocation-path-only edit, JSON verdict contract + IDENT-03 rendering + G-IDENT independence (D-05) preserved. Validated by next blind CASE5 UAT, not unit tests.

### Pending Todos

- **[2026-06-17] Fix `lucy lsd rank` scoring defect** — now ACTIVE as Phase 86 (RANK). Ranker scores the correct structure 2.23/8-of-10 vs `lucy predict c13` 0.27/10-of-10 (same molecule, Kekulé & canonical alike; NOT a Kekulé/FIX-11 issue). Divergent prediction/matching paths.
- **[2026-06-21] / [2026-06-23] defect todos** — folded into IDENT (Phase 87, naming hallucination CASE4/5) and MULT (Phase 88, aliphatic multiplicity robustness). See `.planning/todos/pending/`.

### Blockers/Concerns

None. Roadmap created. Phase 86 may begin immediately (`/gsd-plan-phase 86`).

Note: Phase 89 (UAT) MUST be executed by fresh BLIND Claude instances — never the orchestrator (`feedback_blind_uat`). Answer-key identities (CASE-DATASET-IDENTITIES.md) stay orchestrator-only and out of the runtime CASE skill. Some CASE datasets leak the compound name in Bruker metadata and must be sanitised before a valid blind run (CASE5/8 affected — see [[project_case_datasets_not_sanitised]]); blind-safe as-is: CASE6/7.

### Strategic Reference

See `background/sherlock-analysis.md` for full Sherlock vs lucy-ng comparison. Fragment library built (2.4M SSCs); v9.0 closed the end-to-end-mechanism gap (CASE1 emergent pass + CASE9 solved).

Key v9.0 constraint (still in force): SYME and DEFF NOT are lucy-ng abstractions. Native LSD-3.4.9 commands are: MULT, LIST, PROP, BOND, COSY, HMBC, ELIM, DEFF, FEXP, HSQC, ELEM. Any solver path that bypasses lucy-ng's translation layer loses SYME/DEFF NOT silently.

## Session Continuity

Last session: 2026-06-25T09:28:19.271Z
Stopped at: Phase 88 context gathered
Resume with: `/gsd-plan-phase 86` (RANK — ranker path unification; isolated Python tooling, unit-testable).

---
*Last updated: 2026-06-23 — v9.1 roadmap created (phases 86-89: RANK → IDENT/MULT → UAT gate)*

## Operator Next Steps

- Plan the first phase with `/gsd-plan-phase 86`
