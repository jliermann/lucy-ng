---
phase: 88-aliphatic-multiplicity-robustness
plan: 03
subsystem: case-skill
tags: [case-agents, multiplicity, coverage-gate, devils-advocate, orchestrator, prompt-edit]

# Dependency graph
requires:
  - phase: 88-02
    provides: "nmr-chemist [MULTIPLICITY-AMBIGUOUS] + viable_families; lsd-engineer per-family iteration_NN_<family>/ runs + SEARCHED-not-RANKED coverage rule + deduped union rank"
provides:
  - "Deterministic, MAE-independent pre-accept coverage gate in case.md: the run cannot accept until viable_families ⊆ searched_families AND every DA-mandated model was searched (MULT-02)"
  - "Binding devils-advocate G-MULT gate emitting [MULT-EVIDENCE-FOR] model=X — closeable ONLY by an actual iteration_NN_X/ search, never by the convergence narrative (MULT-03)"
  - "## Multiplicity Coverage ledger in CASE-PROGRESS.md (viable/searched/DA-mandated/verdict) + Multiplicity Coverage Gap reopen pattern + WHAT-not-HOW reopen advisory"
affects: [89-blind-uat]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pre-accept COVERAGE gate (set-containment, MAE-independent) sitting at the identity_gate lifecycle point and guarded by a [MULTIPLICITY-AMBIGUOUS] record — distinct from the MAE-triggered Quality Convergence Failure reopen"
    - "BINDING devils-advocate severity class (above WARNING): a flag closeable ONLY by an actual search, never by argument — enforced downstream by the orchestrator's coverage gate"

key-files:
  created: []
  modified:
    - .claude/agents/lucy-devils-advocate.md
    - .claude/commands/lucy-ng/case.md
    - .claude/commands/lucy-ng/references/loop-patterns.md
    - .claude/commands/lucy-ng/references/advisory-templates.md

key-decisions:
  - "Coverage gate is COVERAGE-triggered and explicitly MAE-INDEPENDENT — it does not read MAE/plausibility/rank; the CASE4 wrong class scored MAE 1.75 PLAUSIBLE and the MAE>4 loop stayed silent, so keying off MAE would re-create the defeat"
  - "Coverage counts SEARCHED-not-RANKED: a family with its own iteration_NN_<family>/ run + [ITERATION-COMPLETE] counts even if solutions.smi conversion was skipped for size (do not require a ranked solutions.smi)"
  - "G-MULT is a new BINDING severity class — it blocks ACCEPT (not the per-run solver) until model X is searched; the convergence narrative is structurally forbidden from closing it"
  - "Gate is guarded by a [MULTIPLICITY-AMBIGUOUS] record and SKIPPED otherwise — the single-family flow is completely unaffected"

patterns-established:
  - "coverage_gate runs BEFORE identity_gate at the same pre-accept lifecycle point (it may REOPEN the run, so it must resolve first); [RANKING-COMPLETE] routes through coverage_gate (when ambiguous) → identity_gate → present_results"
  - "DA [MULT-EVIDENCE-FOR] model=X is recorded by the coordinator as a DA-mandated model in the ## Multiplicity Coverage ledger and enforced by the coverage gate's DA-mandated-models check"

requirements-completed: [MULT-02, MULT-03]

# Metrics
duration: ~11min
completed: 2026-06-25
---

# Phase 88 Plan 03: Aliphatic Multiplicity Robustness (MAE-independent coverage guardrails) Summary

**Two MAE-independent guardrails now make multiplicity coverage binding: a deterministic pre-accept coverage gate in the orchestrator (case.md) that refuses to accept until every viable multiplicity family AND every devils-advocate-mandated model has been ACTUALLY SEARCHED (counted SEARCHED-not-RANKED, never by MAE), and a binding devils-advocate `G-MULT` gate that emits `[MULT-EVIDENCE-FOR] model=X` and is closeable ONLY by an actual `iteration_NN_X/` search — never by the convergence narrative. Together they close the exact CASE4 defeat where a wrong-class iPr structure scored MAE 1.75 "PLAUSIBLE", the MAE>4 guardrail stayed silent, and the DA's "evidence for ethyl" flag was rationalized away as gem-dimethyl coupling.**

## Performance

- **Duration:** ~11 min (incl. full pytest no-regression run)
- **Tasks:** 3
- **Files modified:** 4 (devils-advocate agent, case.md orchestrator, 2 references)

## Accomplishments

- **Task 1 (MULT-03, devils-advocate):** Added a new `G-MULT: Multiplicity Evidence — BINDING mandatory-search flag` gate, structurally modeled on G-IDENT but explicitly different on BOTH axes (PRE-accept not post-solution; BINDING not advisory). It emits a structured `[MULT-EVIDENCE-FOR] model=<X>` naming the model and the supporting correlation when a measured HMBC/COSY is a genuine 2–3J under model X that the leading model cannot explain. Stated the binding rule plainly: model X becomes a mandatory-search item, closeable ONLY by an `iteration_NN_X/` run with `[ITERATION-COMPLETE]`, never by a better MAE/plausibility/convergence narrative. Embedded the CASE4 HMBC 11→13 ethyl example verbatim (two methyls of 1,4-dimethylazulene are far apart; a CH₃–CH₂ gives 2–3J; MUST NOT be re-explained as gem-dimethyl coupling). Added a new BINDING severity row to the gate summary table. Fresh-session reload note present.
- **Task 2 (MULT-02, case.md):** Added a `## Multiplicity Coverage` ledger to write_progress (viable_families / searched_families / DA-mandated models / gate verdict, present only when a `[MULTIPLICITY-AMBIGUOUS]` record exists, with the SEARCHED-not-RANKED counting rule encoded). Added a new `coverage_gate` step at the identity_gate lifecycle point, GUARDED to run only when a `[MULTIPLICITY-AMBIGUOUS]` record exists (single-family flow explicitly skips it). The gate is deterministic and MAE-INDEPENDENT: PASS iff `viable_families ⊆ searched_families` AND every DA-mandated model ∈ searched_families; otherwise FAIL → do NOT accept, REOPEN to search the missing family(ies)/model(s), re-run the deduped union rank, re-enter the gate. Wired the completion-signal flow so `[RANKING-COMPLETE]` routes through coverage_gate (when ambiguous) before identity_gate. Fresh-session note present.
- **Task 3 (references):** Added a `Multiplicity Coverage Gap` pattern to loop-patterns.md alongside Quality Convergence Failure (COVERAGE-triggered reopen, SEARCHED-not-RANKED, data from the CASE-PROGRESS.md `## Multiplicity Coverage` section, explicit contrast with the MAE-triggered Pattern 5). Added a `multiplicity_coverage_reopen_advisory` to advisory-templates.md with WHAT-not-HOW wording (names the missing family/model and that it must be searched in its own `iteration_NN_<family>/` dir; does not dictate the MULT lines; states the DA flag is closeable only by an actual search). Both references carry fresh-session notes.

## Task Commits

Each task was committed atomically:

1. **Task 1: binding DA G-MULT gate emitting [MULT-EVIDENCE-FOR]** — `d1810d0` (feat)
2. **Task 2: pre-accept coverage gate + ## Multiplicity Coverage ledger in case.md** — `b9d6f9f` (feat)
3. **Task 3: Multiplicity Coverage Gap reopen pattern + advisory wording** — `a090ae0` (feat)

## Files Created/Modified

- `.claude/agents/lucy-devils-advocate.md` — New `G-MULT` BINDING pre-accept gate emitting `[MULT-EVIDENCE-FOR] model=X`; CASE4 ethyl example embedded; gate summary table updated.
- `.claude/commands/lucy-ng/case.md` — New `coverage_gate` step (guarded, deterministic, MAE-independent, reopens); `## Multiplicity Coverage` ledger in write_progress; completion-signal flow routes `[RANKING-COMPLETE]` through coverage_gate → identity_gate.
- `.claude/commands/lucy-ng/references/loop-patterns.md` — New `Multiplicity Coverage Gap` pattern (coverage-triggered reopen, SEARCHED-not-RANKED).
- `.claude/commands/lucy-ng/references/advisory-templates.md` — New `multiplicity_coverage_reopen_advisory` (WHAT-not-HOW reopen wording targeting lsd-engineer).

## Decisions Made

- **MAE-independence is stated, not implied.** The gate prose repeatedly asserts it does NOT read MAE/plausibility/rank, citing the CASE4 MAE 1.75 "PLAUSIBLE" silent-guardrail failure — keying off MAE would re-create the exact defeat the phase exists to fix.
- **SEARCHED-not-RANKED is carried through end-to-end** from Plan 88-02: the ledger, the gate, and the reopen pattern all count a conversion-skipped large family as searched. A family is never dropped from coverage for lacking a ranked `solutions.smi`.
- **G-MULT introduced as a new BINDING severity** (above WARNING) — it does not block a per-run solver call (it is not a per-iteration constraint defect like the pre-run CRITICAL gates); it blocks ACCEPT, enforced by the orchestrator's coverage gate's DA-mandated-models check. This keeps the DA read-only/no-write contract intact while making its flag binding.
- **Guarded skip preserves the single-family flow:** with no `[MULTIPLICITY-AMBIGUOUS]` record, the coverage_gate step is skipped and the `## Multiplicity Coverage` ledger is omitted — zero behavior change for unambiguous runs.

## Deviations from Plan

None — plan executed exactly as written. All three grep gates exit 0; all four edited files carry fresh-session reload notes; token cross-consistency (`[MULT-EVIDENCE-FOR]`, `[MULTIPLICITY-AMBIGUOUS]`, `## Multiplicity Coverage`) verified across devils-advocate, case.md, loop-patterns, advisory-templates, and the Plan 88-02 producer agents.

## Issues Encountered

None. No Python changed in this plan; the pytest suite is a clean no-regression check: **1128 passed, 7 skipped, 1 xfailed, 0 failed** in ~6 min.

## Known Stubs

None — these are CASE-agent/orchestrator MARKDOWN PROMPT edits; no stub data sources introduced.

## Threat Flags

None — prompt edits only; no new network/auth/file-access/schema surface. The threat register's three mitigate dispositions (T-88-05 silent accept, T-88-06 flag rationalized away, T-88-07 coverage miscount) are all addressed by the coverage gate (MAE-independent set-containment), the G-MULT binding rule (closeable only by a search), and the SEARCHED-not-RANKED ledger respectively.

## Validation Note (functional acceptance deferred)

These are CASE-skill MARKDOWN PROMPT edits to repo `.claude/` files symlinked into `~/.claude`. A **fresh Claude Code session is required to reload** the edited orchestrator, agent, and references (note embedded in every edited file). Runtime behavior is NOT unit-tested this session — functional acceptance is the **blind CASE4 re-run (UAT-01, Phase 89)**: chamazulene's di-methyl-ethyl constitution must be reachable in the searched solution set, and the coverage gate must reopen rather than accept the iPr-only run. This plan is grep-asserted now (all three gates pass).

## Next Phase Readiness

- Phase 88 is COMPLETE: 88-01 (detector), 88-02 (producer-agent wiring), 88-03 (coverage + binding guardrails) all grep-asserted. MULT-01..04 satisfied at the prompt level.
- Phase 89 (Blind-UAT Validation Gate) can now run: UAT-01 = blind CASE4 is the acceptance test for the whole multiplicity-robustness chain. Phase 89 MUST run on a FRESH BLIND instance (orchestrator bookkeeps only).

## Self-Check: PASSED

- .claude/agents/lucy-devils-advocate.md: FOUND
- .claude/commands/lucy-ng/case.md: FOUND
- .claude/commands/lucy-ng/references/loop-patterns.md: FOUND
- .claude/commands/lucy-ng/references/advisory-templates.md: FOUND
- Commit d1810d0: FOUND
- Commit b9d6f9f: FOUND
- Commit a090ae0: FOUND
- Task 1 grep gate (MULT-EVIDENCE-FOR + binding/mandatory + narrative + fresh): PASS
- Task 2 grep gate (Multiplicity Coverage + coverage + searched + MULTIPLICITY-AMBIGUOUS + MAE-independent + fresh): PASS
- Task 3 grep gate (Multiplicity Coverage + reopen in loop-patterns; multiplicity/coverage in advisory; fresh in both): PASS

---
*Phase: 88-aliphatic-multiplicity-robustness*
*Completed: 2026-06-25*
