# Phase 77: Fix lucy lsd run + Emergent-Aromatic Tooling + Skill Hygiene - Context

**Gathered:** 2026-06-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix the blocking defects the v9.0 milestone UAT (Phase 76) exposed so the intended mechanism actually works end-to-end. **Fixes only — the blind re-UAT is Phase 78.** Three workstreams:
1. `lucy lsd run` plumbing (`_invoke_outlsd`) — produce real solutions.smi, fail loud on error.
2. Emergent-aromatic in practice — make cross-ring COSY equivalence-pair emission deterministic in tooling so the ring emerges without manual atom-index reasoning or forced ring-BONDs.
3. Skill hygiene — retire the deprecated/contradictory agent file; targeted (not full-rewrite) skill-creator audit.

**Out of scope (Phase 78):** running the blind CASE1/CASE9 re-UAT, the manual blind gate, the milestone-complete decision. **Out of scope (deferred):** full skill-complex consolidation rewrite; CASE2–CASE8 broadening.
</domain>

<decisions>
## Implementation Decisions

### Aromatic ring establishment (D-04 reconciliation)
- **D-77-01:** Ring is **emergent primary + documented BOND escalation**. The aromatic ring must emerge from correct native constraints (as Phase 72 Arm A proved: 2/2 aromatic with cross-ring `COSY 4 7` + `COSY 5 6`). Explicit ring-BOND construction is allowed ONLY as a documented escalation after N non-aromatic iterations, logged in CASE-PROGRESS.md. SKEL benzene forcing stays forbidden in the normal flow. Root cause of the Phase-76 failure: the blind agent emitted **adjacent** `COSY 4 5`/`6 7` (topologically wrong) instead of cross-ring equivalence pairs — emergence never had its precondition.
- **D-77-02:** The fix for D-77-01 is **deterministic in tooling, not skill prose**. A CLI/generator helper derives cross-ring aromatic COSY equivalence pairs (e.g. 4≡7, 5≡6) from already-detected symmetry/grouping (`lucy analyze grouping` + symmetry detection) and emits them. The agent no longer hand-assigns atom indices for aromatic equivalence — removing the whole error class regardless of skill size. The skill references the helper rather than re-deriving the rule.

### lucy lsd run plumbing fix
- **D-77-03:** **Fix + fail-loud + regression test.** (1) Repair `_invoke_outlsd` so it invokes outlsd correctly (header-strip / file-arg per the `tail -n +10 compound.sol | outlsd 5` finding in [[project-lsd-native-commands]]) and writes real SMILES. (2) When outlsd output is `outlsd: This is not a file for OUTLSD.` / empty / non-SMILES, the runner exits non-zero with a clear error — never reports false "success". (3) Regression test asserts real SMILES on a known `.sol` AND non-zero exit on the error case. Also: correct the now-false "Phase 73 fix works" claim in `agents/lucy-lsd-engineer.md:124-130`.

### Phase scope
- **D-77-04:** **Split.** Phase 77 = fixes only (verified by tests like normal code). Phase 78 = blind re-UAT (CASE1 + CASE9) in a fresh instance. Rationale: Phase 76 coupled build+UAT and got messy; the orchestrator is always tainted so the blind run needs a fresh session anyway; fixes should be provably green before the expensive manual gate. UAT-03/UAT-04 move to Phase 78; Phase 77 carries FIX-01/02/03.

### Skill hygiene
- **D-77-05:** **Retire deprecated file + targeted audit (no full rewrite).** Retire/archive `~/.claude/agents/lucy-case-agent.md` (1291 lines, active-looking frontmatter, stale manual `outlsd 5` workflow contradicting current lsd-engineer.md). Run a targeted skill-creator audit: dead/contradictory-file detection, verify the v9.0 single-path + emergent/COSY guidance is prominent (not buried), check trigger descriptions. A full ~5275-line consolidation rewrite is explicitly out of scope (deferred).

### UAT criterion rewrite (for Phase 78, decided here)
- **D-77-06:** The D-76 mechanistic UAT criterion is rewritten: **emergent ring = clean pass; ring-BONDs only as a CASE-PROGRESS-documented escalation = conditional pass; silent ring-BONDs or any SKEL = fail.** Phase 78 CONTEXT/criteria inherit this. (Phase 76 treated forced ring-BONDs as a literal SKEL=0 pass — that loophole is closed.)

### Claude's Discretion
- Exact fail-loud detection predicate for FIX-01 (which strings/conditions count as malformed outlsd output beyond the known error string) — planner/researcher decides, but it MUST cover the observed `This is not a file for OUTLSD.` case and empty/non-SMILES output.
- The threshold N for ring-BOND escalation (how many non-aromatic iterations before escalation is documented-legitimate).
- Exact home for the deterministic COSY helper (new CLI subcommand vs generator method vs extension of `lucy analyze grouping`).
- Audit depth of skill-creator within the "targeted, not full-rewrite" bound.
- Whether to re-verify CASE9 sanitisation/workspace cleanliness as part of 77 or defer to 78 (leaning 78).
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### v9.0 design decisions (define the intended mechanism)
- `.planning/phases/72-design-re-validation/72-DECISIONS.md` — D-01 (extended bond range PRIMARY for 4J), D-02 (single solver path), D-03 (native-only emission; SYME→BOND/COSY incl. cross-ring `COSY 4 7`+`COSY 5 6`; DEFF NOT→DEFF F/FEXP), D-04 (aromatic ring EMERGENT — and the COSY-pairing detail that the Phase-76 run violated)

### Phase 76 forensics (define the defects this phase fixes)
- `.planning/phases/76-milestone-uat-gate/VERIFICATION.md` — FAILED verdict, the three blocking defects, forensics section
- `.planning/phases/76-milestone-uat-gate/76-02-SUMMARY.md` — what the blind run did
- `.planning/phases/76-milestone-uat-gate/uat-artifacts/case1/` — CASE-PROGRESS.md (the adjacent-COSY error + forced-ring + interventions), iteration_04 LSD, solutions.smi

### Code loci
- `src/lucy_ng/lsd/runner.py` — `_invoke_outlsd` (line 13), `_run_outlsd` (379), `_find_outlsd` (360) — the FIX-01 target (the `lucy lsd run` path)
- `src/lucy_ng/lsd/orchestrator.py` — `_run_outlsd` (255) — pyLSD path's outlsd usage (check parity)
- `src/lucy_ng/analysis/` (grouping/symmetry) + `lucy analyze grouping` CLI — input for the deterministic cross-ring COSY helper (FIX-02)
- `scripts/verify_case_solution.py` — the committed verification harness (reused by Phase 78, not changed here)

### Skill / agent files (FIX-03 + COSY guidance)
- `~/.claude/agents/lucy-lsd-engineer.md` — false Phase-73 claim (lines 124-130) to correct; COSY/native-constraint guidance; D-04 escalation wording (line 583)
- `~/.claude/agents/lucy-case-agent.md` — DEPRECATED (1291 lines) — to retire/archive
- `~/.claude/commands/lucy-ng/case.md` + `~/.claude/agents/lucy-nmr-chemist.md`, `lucy-devils-advocate.md` — single-path + emergent guidance prominence

### Project decisions / context
- `.planning/v8.0-UAT-POSTMORTEM.md` — original forced-ring / intervention failure pattern
- Memory `project-lucy-lsd-run-broken-v9` and `project-lsd-native-commands` — the bug + the header-strip remedy + native-command constraints
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/verify_case_solution.py` — independent RDKit harness (built Phase 76); Phase 78 reuses as-is.
- `lucy analyze grouping` + symmetry detection — already produce the aromatic equivalence groups the deterministic COSY helper (FIX-02) needs.
- `LSDInputGenerator` (native-only emitter, Phase 74) — likely home for deterministic COSY-pair emission.

### Established Patterns
- D-03 native-only emission: no emitted LSD file may contain SYME or DEFF NOT. The COSY helper must emit native `COSY a b` lines.
- `lucy lsd run` is the single primary path (D-02); the fix must keep it the path the agent uses (no direct-binary bypass).

### Integration Points
- `lucy lsd run` (runner.py) → outlsd → solutions.smi → `lucy lsd rank` / verify_case_solution.py. FIX-01 repairs the outlsd link.
- Deterministic COSY helper output → LSD file generation → emergent aromatic ring.
</code_context>

<specifics>
## Specific Ideas

- The Phase-76 failure signature to fix is concrete and on-disk: `lucy lsd run` wrote `outlsd: This is not a file for OUTLSD.` to solutions.smi while exiting 0; the agent emitted `COSY 4 5`/`6 7` (adjacent) instead of `COSY 4 7`/`5 6` (cross-ring); the ring was then forced via `BOND 2 4/4 6/6 3/3 7/7 5/5 2`.
- Arm A (72-DECISIONS) is the positive reference: full native constraints + cross-ring COSY + no SKEL → 2/2 aromatic, ibuprofen present. FIX-02 must reproduce this end-to-end through the live pipeline (not just the hand-built Arm A file).
- Fail-loud matters specifically because the bug masqueraded as success — the next regression must not be able to hide the same way.
</specifics>

<deferred>
## Deferred Ideas

- Full skill-creator consolidation rewrite of the ~5275-line / 11-file complex — out of scope; revisit if the targeted audit shows it's needed.
- CASE2–CASE8 UAT broadening — defer until CASE1+CASE9 pass (Phase 78).
- Promoting `verify_case_solution.py` to a first-class `lucy lsd verify-uat` CLI subcommand — deferred (noted in 76-CONTEXT).
- Re-running CASE9 sanitisation/workspace blindness check — likely a Phase 78 pre-run step, not 77.
</deferred>

---

*Phase: 77-fix-lucy-lsd-run-plumbing-bug-and-re-run-blind-uat-repair-in*
*Context gathered: 2026-06-01*
