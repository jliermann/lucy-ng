---
phase: 87-final-identity-verification-gate
plan: 02
subsystem: case-team-agents
tags: [identity, naming-hallucination, skill-edit, devils-advocate, solution-analyst, advisory-gate]
requires:
  - "scripts/verify_case_solution.py check-identity subcommand (87-01) — the JSON identity contract these prompts consume"
  - "Bundled dereplication DB (data/reference/lucy-ng-derep.db) reached by the tool at runtime"
provides:
  - ".claude/agents/lucy-solution-analyst.md — Section 6.0 identity-derivation step + Section 6.1 verdict-keyed Identity Rendering Rule + ## Identity report block"
  - ".claude/agents/lucy-devils-advocate.md — G-IDENT post-solution advisory name<->structure gate (independent reasoning layer)"
affects:
  - "CASE final report identity rendering (IDENT-03 consumer side now wired into the analyst prompt)"
  - "Blind CASE re-run behavior — validated by Phase 89 UAT (CASE5 = IDENT acceptance)"
tech-stack:
  added: []
  patterns:
    - "Tool-derived identity: analyst runs check-identity on the top SMILES before writing the report header; verdict is the sole authority for rendering"
    - "Two-layer name<->structure gate: deterministic binding check (87-01 tool) + independent LLM advisory cross-check (G-IDENT) that does NOT call the tool"
    - "Post-solution DA gate lifecycle (operates on final_results.md) distinct from the pre-solver per-iteration gates (operate on compound.lsd)"
key-files:
  created: []
  modified:
    - ".claude/agents/lucy-solution-analyst.md"
    - ".claude/agents/lucy-devils-advocate.md"
decisions:
  - "G-IDENT documented as POST-SOLUTION (fires on final_results.md after solving), explicitly distinct from every other DA gate which is pre-solver on compound.lsd (resolves Open-Question #1 / Pitfall 4)."
  - "G-IDENT does NOT shell out to check-identity/derive_identity — independence is preserved by making the deterministic script the binding tool-agreement layer and G-IDENT a separate human-style reasoning cross-check (D-05)."
  - "All four verdicts (confirmed / confirmed-structure / tentative / novel) are rendered by an explicit verdict-keyed rule; only verdict 'confirmed' (NMRShiftDB) permits stating a trivial name plainly; everything else uses InChIKey + canonical SMILES as primary identity (D-07)."
  - "COCONUT-accession hit (verdict 'confirmed-structure') => structure known, trivial name still tentative."
metrics:
  duration: ~6 min
  completed: "2026-06-23"
  tasks: 2
  files: 2
  commits: 2
---

# Phase 87 Plan 02: Final Identity-Verification Gate (Agent Wiring) Summary

Wired the deterministic identity tool from 87-01 into the two CASE team agents: the solution-analyst now derives the reported identity by running `check-identity` on the solved SMILES before writing the report (never from recalled knowledge) and renders non-confirmed trivial names as `(tentative, unverified)`; the devils-advocate gained an independent post-solution advisory gate (G-IDENT) that sanity-checks the name↔structure mapping as a second reasoning layer — closing IDENT-01, the advisory half of IDENT-02, and the report-rendering half of IDENT-03.

## What Was Built

- **`lucy-solution-analyst.md`** —
  - **Section 6.0 (new, mandatory):** an identity-derivation step that runs `python scripts/verify_case_solution.py check-identity --smiles '<top SMILES>' [--reported-name ...]` on the rank-#1 solution AFTER ranking and BEFORE writing the `# CASE Results:` header. The JSON `verdict`/`derived`/`warning` is the sole authority for the rendered identity. Explicit prohibition: identity is tool-derived, never from recalled/parametric knowledge (names the CASE4/CASE5 failure class).
  - **Section 6.1 (new):** a verdict-keyed Identity Rendering Rule covering all four verdicts — `confirmed` (NMRShiftDB name plain), `confirmed-structure` (COCONUT accession; structure known, trivial name tentative), `novel` (InChIKey + canonical SMILES as primary identity; any trivial name `(tentative, unverified)`), `tentative` (surface the tool's warning prominently; asserted name only `(tentative, unverified)`; structural result still reports — never blocked).
  - **`## Identity` block** added to the report template (verdict, primary identity, InChIKey, canonical SMILES, trivial-name rendering, confidence note, warning).
  - **`[RANKING-COMPLETE]`** "Top solution:" line now carries the tool-derived identity (derived name or InChIKey, never a recalled name) plus a new `Identity:` field with the verdict.
  - Workflow step **6a** (derive identity) inserted before step 7 (write report); fresh-session reload note added.

- **`lucy-devils-advocate.md`** —
  - **G-IDENT gate (new)** in the Check-5 style, with a prominent LIFECYCLE note: it is POST-SOLUTION (fires on `analysis/final_results.md` after a structure is solved), explicitly distinct from every other DA gate which runs pre-solver on `compound.lsd`. Severity WARNING/advisory — never blocks (D-06); a mismatch downgrades the reported name to `(tentative, unverified)`.
  - **Independence (D-05):** the gate does NOT call `derive_identity`/`check-identity`; it reasons independently from the SMILES. Worked triggers encode CASE4 (wrong-isomer/"literature" azulene name asserted for unresolved regiochemistry) and CASE5 (indigo = symmetric 2,2'-bisindolinylidene vs isoindigo 3,3'-linked vs indirubin asymmetric 2,3'-linked — check linkage/symmetry of the drawn structure against the reported name).
  - **Check-5 summary table** split into a "Pre-run gates" sub-table and a new "Post-solution gates" sub-table listing G-IDENT.
  - Workflow **step 13** (post-solution review pass) added; fresh-session reload note added.

## Deviations from Plan

None — plan executed exactly as written. Both `<verify>` grep gates pass on first run; all acceptance criteria met.

## Verification Results

- Task 1 gate: `check-identity` ✓, `(tentative, unverified)` ✓, `confirmed-structure` ✓, `fresh.*session` ✓ — and `novel` present (verdict-keyed rule covers all four verdicts).
- Task 2 gate: `G-IDENT` ✓, `final_results.md` ✓, `post-solution` ✓, `fresh.*session` ✓; `indigo` + `isoindigo` triggers present ✓; advisory/never-blocks language present ✓.
- No instruction remains telling the analyst to name the compound from prior/recalled knowledge as fact (the former `<name if known>` placeholder was replaced with `<tool-derived identity ...>`); the surviving "recalled"/"from memory" strings are all prohibitions.
- These are Markdown prompt edits — agent runtime behavior is NOT testable in this session (a fresh Claude Code session is required to reload edited agents). Functional validation is the Phase 89 blind CASE re-run (CASE5 = IDENT acceptance test).

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: .claude/agents/lucy-solution-analyst.md (check-identity + (tentative, unverified) + confirmed-structure + reload note)
- FOUND: .claude/agents/lucy-devils-advocate.md (G-IDENT + final_results.md + post-solution + indigo/isoindigo + reload note)
- FOUND: commit a0f89ca (Task 1), 9e7e9b9 (Task 2)
- FOUND: .planning/phases/87-final-identity-verification-gate/87-02-SUMMARY.md
