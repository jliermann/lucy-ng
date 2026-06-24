---
phase: 87-final-identity-verification-gate
plan: 04
subsystem: case-agents
tags: [identity, gap-closure, reachability, skill-edit, ident-01, ident-02, ident-03, d-05]
requires:
  - "lucy identify installed CLI subcommand (delivered 87-03; --smiles/--reported-name/--format json, reachable from any data dir)"
  - "Existing 87-02 wiring: analyst Section 6.0/6.1 identity rendering + devils-advocate G-IDENT post-solution gate"
provides:
  - "solution-analyst identity derivation repointed to the installed `lucy identify --format json` (runtime-reachable from a CASE NMR data dir) — GAP-87-A closed end to end"
  - "devils-advocate G-IDENT prose names `lucy identify` as the analyst's binding tool (independence preserved)"
affects:
  - "Next blind CASE5 UAT (Phase 89, UAT-02) — `lucy identify` should now actually fire instead of the missing-script fallback"
tech-stack:
  added: []
  patterns:
    - "CASE-agent prompt edit: invocation-path-only change, verdict/JSON contract and rendering rule untouched"
key-files:
  created: []
  modified:
    - ".claude/agents/lucy-solution-analyst.md"
    - ".claude/agents/lucy-devils-advocate.md"
decisions:
  - "Invocation-path-only edit: the JSON contract (mode/reported_name/derived/name_match/verdict/warning) is identical to the old check-identity output, so Section 6.1 verdict-keyed rendering, the `## Identity` block, the [RANKING-COMPLETE] Identity field, and IDENT-03 `(tentative, unverified)` were left verbatim."
  - "Independence (D-05) preserved: G-IDENT still must NOT call `lucy identify`/`derive_identity` — only the NAME of the analyst's binding tool changed in the prose; the do-not-call instruction stays."
  - "The descriptive [RANKING-COMPLETE] `verdict from check-identity` mention was updated to `verdict from lucy identify` for naming consistency (not a script-path live call, but renamed to avoid stale tool names)."
metrics:
  duration_min: 4
  tasks_completed: 2
  files_created: 0
  files_modified: 2
  completed: 2026-06-24
---

# Phase 87 Plan 04: Agent Repoint to lucy identify (GAP-87-A Runtime Closure) Summary

Closed the runtime half of GAP-87-A by re-pointing both CASE team agents from the repo-relative
`python scripts/verify_case_solution.py check-identity` invocation (unreachable when a CASE run
executes in an NMR data dir outside the repo) to the installed `lucy identify --format json`
command delivered by 87-03 — invocation path only, with the deterministic verdict contract,
IDENT-03 tentative rendering, and the G-IDENT advisory gate left exactly as 87-02 set them.

## What Was Built

- **`.claude/agents/lucy-solution-analyst.md`** — three identity-call sites repointed:
  - Section 6.0 fenced bash block now calls `lucy identify --smiles ... [--reported-name ...] --format json`.
  - The relative-path caveat ("if the script is not on the relative path… use its absolute repo path")
    was replaced with a note that `lucy identify` is an installed subcommand reachable from the CASE
    data directory like `lucy lsd rank` — no repo-relative/absolute path needed; it always exits 0.
  - Workflow step 6a one-liner now names `lucy identify --format json`.
  - The [RANKING-COMPLETE] template's descriptive "verdict from check-identity" updated to
    "verdict from `lucy identify`".
  - PRESERVED verbatim: the JSON-parsing prose, the Section 6.1 verdict-keyed Identity Rendering
    Rule, the `## Identity` report block, the `(tentative, unverified)` IDENT-03 string, and the
    fresh-Claude-Code-session reload maintenance note.
- **`.claude/agents/lucy-devils-advocate.md`** — G-IDENT prose repointed:
  - G-IDENT purpose paragraph names the installed `lucy identify` command as the analyst's BINDING
    name↔structure check (was `scripts/verify_case_solution.py check-identity`).
  - Workflow step 13's independence instruction now reads "do NOT call the deterministic
    `lucy identify` tool — that is the analyst's binding layer".
  - PRESERVED: the independence semantics (G-IDENT still must NOT call the tool; reasons
    independently from SMILES), the post-solution lifecycle on `final_results.md`, the
    advisory/WARNING/never-blocks severity, the CASE4/CASE5 worked triggers, and the
    fresh-session reload note.

## Verification

- Task 1 (analyst): `grep -c 'lucy identify'` ≥ 2; non-comment `scripts/verify_case_solution.py check-identity` count = 0; `fresh.*session` present; `(tentative, unverified)` present → OK.
- Task 2 (devils-advocate): `lucy identify` present; `G-IDENT` present; `post-solution` present; `final_results.md` present; `fresh.*session` present; non-comment `scripts/verify_case_solution.py check-identity` count = 0 → OK. No remaining `check-identity` mentions in the file.
- These are Markdown CASE-agent prompt edits — a FRESH Claude Code session is required to reload the edited agents; functional behavior is validated by the next blind CASE5 UAT (Phase 89, UAT-02), not by unit tests in this session.

## Deviations from Plan

None — plan executed exactly as written. (The one extra edit — renaming the descriptive
"verdict from check-identity" string in [RANKING-COMPLETE] to "verdict from `lucy identify`" — is
within the Task 1 action's "any other `scripts/verify_case_solution.py` mention used for the LIVE
identity call" / naming-consistency scope, not a deviation.)

## Self-Check: PASSED

- FOUND: .claude/agents/lucy-solution-analyst.md (modified)
- FOUND: .claude/agents/lucy-devils-advocate.md (modified)
- FOUND commit: 602f54c (Task 1 — solution-analyst repoint)
- FOUND commit: 8cb6ef5 (Task 2 — devils-advocate G-IDENT repoint)
