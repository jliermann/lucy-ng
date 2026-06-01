# Phase 77: Fix lucy lsd run + Emergent-Aromatic Tooling + Skill Hygiene - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-01
**Phase:** 77-fix-lucy-lsd-run-plumbing-bug-and-re-run-blind-uat-repair-in
**Areas discussed:** D-04 ring establishment, COSY-pair reliability, phase scope, lucy lsd run fix-contract, skill hygiene

---

## D-04: Aromatic ring establishment

| Option | Description | Selected |
|--------|-------------|----------|
| Emergent primary + BOND escalation | Fix guidance so cross-ring COSY emits; ring emerges (Arm A); ring-BONDs only as documented escalation; rewrite UAT criterion | ✓ |
| Only emergent, no forcing | Strict — emergence failure = fail, dig deeper at generator | |
| Ring-BOND as documented path | Accept forcing; rewrite D-04 + criterion to expect ring-BONDs | |

**User's choice:** Emergent primary + BOND escalation.
**Notes:** Evidence: Arm A proved emergence with cross-ring COSY 4 7/5 6; Phase-76 failure was the agent using adjacent COSY 4 5/6 7 — a guidance gap, not a disproof of emergence.

## D-04 follow-up: ensuring correct cross-ring COSY pairs

| Option | Description | Selected |
|--------|-------------|----------|
| Deterministic in tooling | CLI/generator helper derives + emits cross-ring pairs from detected symmetry; agent stops hand-assigning indices | ✓ |
| Sharpen skill guidance | Explicit prose + devils-advocate gate; still agent-reasoning-dependent | |
| Both | Tooling helper + DA gate safety net | |

**User's choice:** Deterministic in tooling.
**Notes:** Removes the error class regardless of skill size — directly addresses the "instructions get buried" concern.

## Phase scope

| Option | Description | Selected |
|--------|-------------|----------|
| Split: 77 fixes, 78 re-UAT | Clean separation; no tainted orchestrator; fixes green before manual gate | ✓ |
| Together in 77 (like 76) | Fixes + re-UAT one phase with manual checkpoint | |

**User's choice:** Split — Phase 77 fixes, Phase 78 re-UAT.

## lucy lsd run fix-contract

| Option | Description | Selected |
|--------|-------------|----------|
| Fix + fail-loud + regression test | Repair invocation, non-zero exit on outlsd error, test happy + error paths | ✓ |
| Only fix + fail-loud | No dedicated regression test | |
| Only fix invocation | Minimal, leaves false-success masking open | |

**User's choice:** Fix + fail-loud + regression test.

## Skill hygiene depth

| Option | Description | Selected |
|--------|-------------|----------|
| Retire deprecated + targeted audit | Remove lucy-case-agent.md; targeted skill-creator audit (dead files, guidance prominence, triggers); no full rewrite | ✓ |
| Only retire deprecated | Defer all skill-creator work | |
| Full consolidation pass | Whole ~5275-line complex through skill-creator | |

**User's choice:** Retire deprecated + targeted audit.

## Claude's Discretion

- Exact fail-loud detection predicate (which malformed-output conditions trigger non-zero exit).
- Threshold N for documented ring-BOND escalation.
- Home for the deterministic COSY helper (CLI subcommand vs generator method vs grouping extension).
- skill-creator audit depth within "targeted, not full-rewrite".
- Whether CASE9 sanitisation re-check belongs in 77 or 78 (leaning 78).

## Deferred Ideas

- Full skill-creator consolidation rewrite (~5275 lines) — revisit only if targeted audit shows need.
- CASE2–CASE8 UAT broadening — after CASE1+CASE9 pass.
- `verify_case_solution.py` → `lucy lsd verify-uat` CLI subcommand.
