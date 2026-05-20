# Phase 72: Design Re-Validation - Context

**Gathered:** 2026-05-20
**Status:** Ready for planning
**Phase type:** Design decisions + one controlled experiment (gates all v9.0 fixes)

<domain>
## Phase Boundary

The first v9.0 phase. Answers the four open design questions from `.planning/v8.0-UAT-POSTMORTEM.md` BEFORE any fix is built, and runs ONE controlled experiment to resolve the partly-empirical questions (the v8.0 evidence was confounded by the constraint-loss bug). Output: a documented, actionable architecture decision (DESIGN-01, DESIGN-02) that directly shapes Phases 73-76.

**In scope:**
- Lock the 4J/aromatic architecture (Q1, Q4) and the solver-path/translation architecture (Q2, Q3)
- Run ONE controlled experiment on CASE1 with constraints PRESERVED (native-only LSD file, by hand or via a throwaway fix) to settle the empirical questions
- Re-evaluate the Phase-65 hypothesis honestly
- Produce a decision document that Phases 73-75 implement against

**Out of scope:**
- Implementing the fixes (Phases 73-75)
- The blind UAT (Phase 76)
- Production-quality code (the experiment may use throwaway/manual native LSD files)
</domain>

<decisions>
## Architecture Decisions (locked direction; experiment confirms the empirical parts)

### Q1 — 4J handling approach
- **D-01:** Extended HMBC bond range (`HMBC X Y 2 4`) is the **PRIMARY** 4J mechanism — a flagged 4J-suspect correlation is emitted with an extended bond range and LSD explores 2-4 bonds in a SINGLE run. This matches what actually worked in the v8.0 UAT (manual 4J-W-path handling) and removes the 2^K permutation + merge complexity that caused most v8.0 bugs.
- **D-01a:** pyLSD permutation multi-run is **demoted to a narrow fallback** — invoked only when the bond-range single run yields 0 solutions or an intractable count. It is not the default path.

### Q2 — solver-path architecture (follows from Q1)
- **D-02:** Collapse to ONE primary solver path: normal LSD + extended bond range. The permutation fallback is a clearly-subordinate, narrowly-scoped escape hatch. This solves the agent-reversion problem (user hypothesis: agent reverts to the better-documented path) at the root — there is now ONE prominently-documented path, not a balanced choice.
- **D-02a (skill-doc strategy):** Skills document the single primary path prominently; the permutation fallback is documented as subordinate with explicit "use only when ..." conditions. No parallel co-equal documentation of two paths.

### Q3 — constraint translation
- **D-03:** The LSD-file **generator emits native-only commands**. SYME → DUPL; DEFF NOT (ring exclusion) → DEFF F/FEXP filter files (ring3/ring4/...); equivalence handled natively. Translation happens at GENERATION time, so every downstream path (direct binary, permutation fallback, runner) receives native files that no path can strip. No runtime/abstraction translation layer that some paths bypass.
- **D-03a:** No lucy-ng LSD file may contain `SYME` or `DEFF NOT <smarts>` as emitted output — these are author-time abstractions only, resolved before any file is written.

### Q4 — aromatic ring establishment (empirical, decided by the experiment)
- **D-04:** **Test first, force only if needed.** The Phase-72 experiment runs CASE1 with full native constraints PRESERVED (incl. DEFF NOT via filters, DUPL) and NO forced benzene fragment, and observes whether an aromatic-ring solution appears.
  - **Decision rule:** if the ring emerges from correct native constraints → aromatic handling is **emergent** (no forcing; the v8.0 failure was purely the constraint-loss bug). If the ring does NOT emerge even with correct constraints → aromatic handling **forces a benzene SKEL fragment when an aromatic pattern is confidently detected** (6 sp2 C in 110-160 ppm with the right CH/Cq split).
- **D-04a:** The experiment also validates D-01 (does bond-range-primary single-run reach ibuprofen in a rankable set?) and produces an honest Phase-65 re-evaluation.

### Controlled experiment specification (the testable core of this phase)
- **D-05:** On CASE1 (ibuprofen, native-only LSD file with constraints preserved):
  1. Bond-range run: flagged 4J as `HMBC X Y 2 4`, single LSD run, full native constraints, NO forced benzene fragment → record solution count + whether any solution has an aromatic ring (RDKit) + whether ibuprofen is reachable/rankable.
  2. (Optional comparison) the same with a forced benzene fragment, and/or a permutation run, to quantify the delta.
  - Record results in the phase's decision document; they settle D-01 confirmation and D-04.

</decisions>

<canonical_refs>
## Canonical References

- `.planning/v8.0-UAT-POSTMORTEM.md` — THE driver: root causes R1-R4, the 4 questions, hard evidence (merge=0, perm solncounters, forced fragment)
- `.planning/REQUIREMENTS.md` §DESIGN-01, DESIGN-02 — the requirements this phase satisfies
- `.planning/ROADMAP.md` §"Phase 72" — goal + success criteria
- Memory `project_lsd_native_commands.md` — SYME/DEFF NOT non-native; native equivalents (DUPL, DEFF F/FEXP); filter files at `/Users/steinbeck/Dropbox/develop/LSD/Filters/` (ring3, ring4, TERPENES)

### Code the decisions constrain (read for the experiment + downstream phases)
- `src/lucy_ng/lsd/generator.py` — where native-only emission (D-03) must land
- `src/lucy_ng/lsd/orchestrator.py` — PyLSDOrchestrator/SolutionMerger (demoted to fallback per D-01a)
- `src/lucy_ng/lsd/runner.py` — `lucy lsd run` / outlsd plumbing (the keystone bug, Phase 73)
- `src/lucy_ng/lsd/parser.py`, `models.py`
- CASE1 dataset: `~/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE1` (sanitised, C13H18O2)

</canonical_refs>

<code_context>
## Existing Code Insights

- The v8.0 code is shipped and the artifacts are retained (not archived). This phase decides the DIRECTION to repair it, not rewrite it (REQUIREMENTS Out of Scope: no wholesale rewrite).
- The experiment can use a throwaway native-only LSD file (hand-written or a quick generator patch) — production native emission is Phase 74's job. The point here is to OBSERVE behavior, not ship code.
- LSD binary: `/Users/steinbeck/Dropbox/develop/LSD/` (LSD + outlsd). Native command set: MULT, LIST, PROP, BOND, COSY, HMBC, ELIM, DEFF, FEXP, HSQC, ELEM, DUPL.

</code_context>

<specifics>
## Specific Ideas

- The experiment is essentially a rigorous redo of the Phase-65 gate, but with the constraint-loss bug controlled for — that's the honest test the v8.0 run never got.
- Keep the decision document short and actionable: each decision must state its direct implication for Phases 73/74/75 (e.g. "D-03 → Phase 74 rewrites generator emission to native-only").
</specifics>

<deferred>
## Deferred Ideas
- Parallel LSD execution (PERF-01, v2 requirements) — out of scope until UAT shows speed is a problem.
- Whether to eventually delete the pyLSD permutation code entirely — defer; keep as fallback for now, revisit after v9.0 UAT.
</deferred>

---

*Phase: 72-design-re-validation*
*Context gathered: 2026-05-20 — design decisions + controlled experiment; gates v9.0 fixes*
