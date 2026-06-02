# Phase 78: Blind Re-UAT Gate (CASE1 + CASE9) - Context

**Gathered:** 2026-06-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Operate the **manual blind UAT** that gates the v9.0 milestone. A *fresh blind* Claude instance runs `/lucy-ng:case` on CASE1 (C13H18O2, sanitised ibuprofen) and CASE9 (C12H16O3, 4-(1-hydroxyethyl)benzoic acid isopropylester — different molecule, same para-aromatic 4J failure mode) via the single primary path. The **tainted orchestrating instance acts only as bookkeeper**: it sets up blindness, observes, collects on-disk evidence, and judges pass/fail against the rewritten criteria — it never solves and never leaks the answer.

**This phase produces a verdict, not code.** The Phase 77 fixes are already verified green; Phase 78 is the gate that decides whether v9.0 ships.

**Out of scope:** any further code changes to the lucy-ng stack (if a defect surfaces, it is documented for a follow-up phase, not fixed here — D-76-07); CASE2–CASE8 broadening (deferred until CASE1+CASE9 pass).
</domain>

<decisions>
## Implementation Decisions

### Blind-instance protocol (D-78-01)
- **D-78-01:** **Read-prohibitions + advisory bookkeeper.** The blind run is a fresh `/clear`'d instance (separate terminal/session). Its handoff is **only** the compound path + molecular formula via `/lucy-ng:case`. It is explicitly instructed NOT to read `.planning/`, `REQUIREMENTS.md`, `~/.claude/.../memory/`, or `git log` — those reveal the answer (compound identity, expected structure, the COSY pairs). The tainted bookkeeper starts and observes the run and may intervene **advisory-only** (no structural or path hints). Blindness rests on the read-prohibition contract, not on a stripped checkout (the lighter-weight option B "physical isolation via a checkout with `.planning/`+memory removed" was considered and is acceptable as a fallback if leakage risk is judged too high at plan time, but is not the default).

### CASE9 sanitisation / blindness pre-check (D-78-02)
- **D-78-02:** **Yes — a pre-run sanitisation/blindness check is the FIRST step of Phase 78.** Before the blind instance sees CASE9, the bookkeeper inspects the dataset (`molecular-formula.txt`, Bruker `title` files, folder/experiment names, `audit*.txt` / pulse-program metadata) for compound-name or identity leakage and sanitises via `/lucy-ng:sanitise` if anything leaks. CASE1 is treated as already-sanitised (known sanitised ibuprofen) but gets a quick re-verification. The blind run does not begin for a compound until its dataset is confirmed identity-clean.

### Evidence collection & independent verification (D-78-03)
- **D-78-03:** **All four success criteria are measured by the tainted bookkeeper from on-disk artifacts after each run — never from the agent's self-report** ([[feedback-blind-uat]]). The evidence checklist per compound:
  1. **Solve correctness:** `python scripts/verify_case_solution.py <solutions.smi> <formula>` exits 0; AND an independent RDKit re-parse of `solutions.smi` confirms a valid, formula-matching structure (do not trust the script alone — re-parse).
  2. **Mechanism (native-only emission):** grep the FINAL emitted LSD file(s) → `SYME` count = 0, `DEFF NOT` count = 0, `SKEL` count = 0, and native `BOND`/`COSY`/`DEFF F`/`FEXP` present. Aromatic ring is emergent (no ring-`BOND` lines for ring atoms) OR ring-`BOND`s appear ONLY with a matching CASE-PROGRESS escalation entry (silent ring-`BOND`s = fail; any `SKEL` = fail) — per D-77-06.
  3. **Path:** CASE-PROGRESS + the run's command history show `lucy lsd run` as the path used; NO direct `lsd`/`outlsd` binary bypass.
  4. **Interventions:** every bookkeeper→instance message is logged and classified advisory vs path-changing (see D-78-04); > 0 path-changing = fail.

### Disqualifying-intervention definition (D-78-04)
- **D-78-04:** **Path-/structure-hints disqualify; generic process nudges are allowed** (aligns with the roadmap wording "0 path-changing bypass interventions"). **Path-changing (= fail):** instructing a path switch (e.g. "use the direct lsd binary", "force a benzene SKEL") OR giving structural hints (the answer, atom indices, COSY pairs, "it's aromatic"). **Allowed (advisory, non-disqualifying):** generic process nudges that leak neither the answer nor the path (e.g. "your constraint inventory was lost across iterations", "re-read the skill guidance"). Borderline cases are documented and scored **conservatively as path-changing (= fail)**. (The stricter Zero-Touch alternative — 0 messages at all — was considered but rejected as unrealistic against process dead-ends like constraint-loss.)

### Sequencing, budget & failure handling (D-78-05)
- **D-78-05:** **Both compounds run independently and fully, one-shot each, forensics on failure.** Even if CASE1 fails, CASE9 still runs (maximise diagnostic data for the follow-up phase). Exactly **one** blind run per compound — a re-run after the result is known would no longer be blind. Advisory interventions allowed (D-78-04), path-changing not. The gate is an **AND** over both compounds (D-76-06): both pass → v9.0 ships; either fails → a forensics document (which criterion broke + on-disk evidence) feeds a D-76-07 follow-up phase and v9.0 does NOT ship. Failure is a valid, documented outcome — not a reason to retry-until-pass.

### Claude's Discretion
- Exact format/location of the per-compound evidence record and the failure forensics doc (planner decides; suggest one artifact per compound under the phase dir, e.g. `78-UAT-CASE1.md` / `78-UAT-CASE9.md`, plus a roll-up verdict).
- The precise grep predicates / helper for the mechanism checks (may reuse or extend `verify_case_solution.py`-adjacent tooling; do NOT modify `verify_case_solution.py` itself unless a defect is found, in which case document rather than silently change).
- Whether to drive the blind instance via the Task/Agent mechanism with an explicit blind-agent prompt vs a literally separate terminal — both satisfy D-78-01 as long as the read-prohibitions and handoff contract hold.
- Order of operations within the pre-check (D-78-02) vs the first blind run.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### The gate criteria (locked upstream — define pass/fail)
- `.planning/ROADMAP.md` — Phase 78 section: Goal + the 4 Success Criteria (the authoritative gate)
- `.planning/phases/77-fix-lucy-lsd-run-plumbing-bug-and-re-run-blind-uat-repair-in/77-CONTEXT.md` §D-77-06 — the rewritten three-tier mechanistic criterion (emergent = clean pass / documented ring-BOND escalation = conditional pass / silent ring-BOND or any SKEL = fail)
- `.planning/REQUIREMENTS.md` — UAT-03 (CASE1) + UAT-04 (CASE9) definitions. **NOTE:** REQUIREMENTS.md reveals CASE9's identity — it is a bookkeeper-only ref; the blind instance must NOT read it (D-78-01).

### Phase 76 forensics (why this gate exists / what "failure" looked like)
- `.planning/phases/76-milestone-uat-gate/VERIFICATION.md` — the FAILED verdict + the three blocking defects (now fixed in Phase 77)
- `.planning/v8.0-UAT-POSTMORTEM.md` — the original forced-ring / intervention failure pattern this gate must NOT repeat

### The fixes being validated (Phase 77 — what "the intended mechanism" now is)
- `.planning/phases/77-fix-lucy-lsd-run-plumbing-bug-and-re-run-blind-uat-repair-in/77-VERIFICATION.md` — 5/5 PASSED; the fixes under test
- `src/lucy_ng/lsd/runner.py` — fixed `lucy lsd run` (the single primary path the blind run must use)
- `src/lucy_ng/lsd/generator.py` + `src/lucy_ng/cli/detect.py` — `detect_aromatic_cosy_pairs()` / `lucy detect aromatic-cosy` (the deterministic emergence tooling)

### Verification tooling & data
- `scripts/verify_case_solution.py` — the independent RDKit harness (reused as-is; do NOT modify)
- `~/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE1/` — sanitised ibuprofen dataset
- `~/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE9/` — C12H16O3 dataset (sanitisation state to be verified in D-78-02)

### Memory (bookkeeper-only, NOT for the blind instance)
- Memory `feedback-blind-uat` — fresh blind instance; independent RDKit verify; never trust self-report
- Memory `project-lucy-lsd-run-broken-v9` — now-FIXED bug context
- Memory `reference-test-data` — CASE dataset locations
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/verify_case_solution.py` — independent RDKit verification harness (Phase 76); the primary correctness gate for criterion 1. Reused unchanged.
- `lucy lsd run` (runner.py, Phase 77) — the single primary solver path the blind run must use end-to-end.
- `lucy detect aromatic-cosy` (detect.py, Phase 77) — the deterministic cross-ring COSY helper the blind agent's skill now references; its use (vs hand-derived indices) is part of what criterion 2 validates.
- `/lucy-ng:sanitise` — AI-only sanitisation skill, used by the D-78-02 pre-check.
- `/lucy-ng:case` — the autonomous CASE workflow the blind instance runs.

### Established Patterns
- Native-only emission (D-03): emitted LSD files must contain no `SYME`/`DEFF NOT`/`SKEL`. The mechanism check (D-78-03 step 2) greps for exactly this.
- Single solver path (D-02): no direct-binary bypass. The path check (D-78-03 step 3) enforces this.
- Tainted-orchestrator-as-bookkeeper: the running instance must not solve or leak; it observes and judges.

### Integration Points
- Blind `/lucy-ng:case` run → writes `solutions.smi` + CASE-PROGRESS.md + iteration LSD files under the compound's analysis dir → bookkeeper reads those artifacts for evidence (D-78-03).
</code_context>

<specifics>
## Specific Ideas

- CASE9 is deliberately chosen as a *different molecule with the same para-aromatic 4J failure mode* as ibuprofen — it tests that the fix generalises, not that it memorised ibuprofen.
- The Phase 76 failure signature to NOT repeat: blind agent emitted adjacent `COSY 4 5`/`6 7`, forced the ring via explicit BONDs, used `>0` rescue interventions, and bypassed `lucy lsd run` to the direct binary. Phase 78 passes only if none of that recurs.
- "Pass the letter but fail the spirit" is explicitly disallowed: SKEL=0 grep alone is necessary but NOT sufficient (silent ring-BONDs also fail) — per D-77-06, baked into D-78-03 step 2.
</specifics>

<deferred>
## Deferred Ideas

- Promoting `verify_case_solution.py` to a first-class `lucy lsd verify-uat` CLI subcommand — deferred (noted since 76-CONTEXT).
- CASE2–CASE8 UAT broadening — deferred until CASE1+CASE9 pass.
- Any code fix for a defect surfaced during the blind run — documented here as forensics, fixed in a D-76-07 follow-up phase, NOT in Phase 78.

None of the above are in scope — discussion stayed within the blind-gate boundary.
</deferred>

---

*Phase: 78-blind-re-uat-gate*
*Context gathered: 2026-06-02*
