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
- **v9.0 CASE Reliability & Skill Consolidation** - Phases 72-80 (in progress; does not ship until CASE9 passes. Phase 79 eliminated the peak-picking/symmetry defect — verified in a live CASE9 run — but exposed the deeper 4J-HMBC connectivity trap → Phase 80)

---

## v8.0 pyLSD Integration

**Goal:** Migrate from direct single LSD runs to pyLSD-style multi-run orchestration, enabling systematic exploration of 4J HMBC coupling possibilities. Fix the root cause of the ibuprofen CASE failure (v4.0 UAT).

## Phases

- [x] **Phase 65: Hypothesis Validation Gate** - Manual 30-minute test: run ibuprofen LSD with 3 known 4J correlations removed; confirm aromatic ring solutions appear. Gates entire milestone. (completed 2026-03-16)
- [x] **Phase 66: LSDInputGenerator Extensions** - Add FORM, ELIM, SHIX/SHIH, and extended HMBC bond range emission to LSDInputGenerator; FORM/MULT consistency validator. (completed 2026-03-16)
- [x] **Phase 67: PyLSDOrchestrator and SolutionMerger** - New Python classes: permutation file generation, N-fold LSD runner invocation, InChI-key deduplication of merged solutions. (completed 2026-03-17)
- [x] **Phase 68: Constraint Inventory v2 Schema** - Extend constraint inventory JSON schema with pylsd_mode, deferred_4j metadata; extend devils-advocate checklist with ELIM/FORM/MULT validation rules. (completed 2026-05-19)
- [x] **Phase 69: CLI Command and Regression Suite** - `lucy pylsd run` CLI subcommand; regression suite confirming existing `lucy lsd run` unchanged; FORM/LSD binary tolerance confirmed. (completed 2026-05-19)
- [x] **Phase 70: Agent Skill Updates** - lsd-engineer and case.md orchestrator skill updates with full pyLSD command reference, `; ELIM` annotation protocol, routing logic for pylsd_mode. (completed 2026-05-19)
- [ ] **Phase 71: Ibuprofen CASE UAT** - End-to-end CASE run with pyLSD multi-run orchestration; ibuprofen aromatic ring structure at rank 1; milestone-complete gate. (superseded — UAT revealed systemic bugs, v9.0 repairs before re-running)

## Phase Details

### Phase 65: Hypothesis Validation Gate

**Goal:** Confirm the core v8.0 hypothesis before writing any code — that removing 3 known 4J HMBC correlations from the ibuprofen LSD input produces solutions containing an aromatic ring
**Depends on:** Nothing (first phase; all v8.0 work gates on this result)
**Requirements:** GATE-01
**Success Criteria** (what must be TRUE):

  1. Ibuprofen LSD file is run with correlations HMBC 4 8, HMBC 6 9, HMBC 8 4 removed, using existing `lucy lsd run`
  2. At least one solution in the output contains an aromatic ring (6-membered sp2 system), confirmed by `outlsd` + RDKit aromatic atom count
  3. A `validation_result.md` file exists documenting: which correlations were removed, solution count, aromatic ring presence, decision to proceed
  4. Go decision is recorded in `.planning/phases/65-hypothesis-gate/` before any Phase 66+ work begins

**Plans:** 1/1 plans complete
Plans:

- [x] 65-01-PLAN.md — Remove 3 known 4J HMBC correlations from ibuprofen LSD, run solver, confirm aromatic ring solutions, record GO/NO-GO decision

### Phase 66: LSDInputGenerator Extensions

**Goal:** LSDInputGenerator can emit all pyLSD-format commands needed for multi-run orchestration — FORM, ELIM header, SHIX/SHIH, and per-correlation extended HMBC bond range
**Depends on:** Phase 65 (hypothesis validated — proceed decision required)
**Requirements:** INPUT-01, INPUT-02, INPUT-03, INPUT-04
**Success Criteria** (what must be TRUE):

  1. `LSDInputGenerator.emit_form("C13H18O2")` produces a valid `FORM C13H18O2` line in the output file
  2. `LSDInputGenerator.emit_elim(4, 4)` produces `ELIM 4 4` in the header section
  3. `LSDInputGenerator.emit_shix(atom_idx, shift)` and `emit_shih` produce `SHIX`/`SHIH` lines; existing output unchanged
  4. An HMBC correlation with `min_bonds=2, max_bonds=4` produces `HMBC X Y 2 4` in the output file (not the default `HMBC X Y`)
  5. `validate_pylsd_input()` raises a clear error when FORM atom count does not match MULT atom count; all existing tests pass

**Plans:** 2/2 plans complete
Plans:

- [x] 66-01-PLAN.md — Extend LSDCorrelation.to_lsd_line() for HMBC bond range; add pylsd_mode/elim_commands to LSDProblem
- [x] 66-02-PLAN.md — Add emit_form/emit_elim/emit_shih methods; integrate into generate(); add validate_pylsd_input()

### Phase 67: PyLSDOrchestrator and SolutionMerger

**Goal:** A Python orchestrator generates permutation LSD files for suspect 4J correlations, runs the LSD binary once per permutation, and merges deduplicated solutions with provenance tracking
**Depends on:** Phase 66 (extended file format required for permutation generation)
**Requirements:** ORCH-01, ORCH-02, ORCH-03, ORCH-04
**Success Criteria** (what must be TRUE):

  1. `PyLSDOrchestrator` with 3 suspect correlations generates 2^3=8 permutation files (one per include/exclude combination), each a valid LSD input file
  2. `PyLSDOrchestrator` aborts with a clear error if K>3 suspect correlations are identified (combinatorial explosion guard)
  3. `SolutionMerger` reading solutions from 3 separate runs deduplicates by InChI key — a structure appearing in runs 1, 2, and 3 appears once in `merged.smi`
  4. `run_report.json` records for each solution: which permutation produced it and which correlations were active in that run

**Plans:** 2/2 plans complete
Plans:

- [ ] 67-01-PLAN.md — PyLSDOrchestrator: permutation generation, K-cap guard, LSD execution with outlsd bypass (TDD)
- [ ] 67-02-PLAN.md — SolutionMerger: InChI deduplication, provenance tracking, merged.smi + run_report.json, package exports (TDD)

### Phase 68: Constraint Inventory v2 Schema

**Goal:** The constraint inventory JSON schema in agent skill files is extended with pyLSD-specific fields; devils-advocate validation gates cover FORM/MULT consistency and ELIM-vs-bond-range semantics
**Depends on:** Phase 65 (hypothesis validated — schema only needs definition after go decision)
**Requirements:** INPUT-05
**Success Criteria** (what must be TRUE):

  1. Constraint inventory JSON block includes `pylsd_mode` (bool), `deferred_4j` (list of HMBC pair strings), and `elim_annotated` (bool) fields documented in skill files
  2. The devils-advocate checklist explicitly distinguishes `ELIM N M` (artifact removal) from `HMBC X Y 2 4` (4J bond range) — the single most dangerous semantic confusion in v8.0
  3. A devils-advocate checklist item verifies FORM atom count matches MULT atom sum before approving any LSD run in pylsd_mode
  4. The schema definition is testable: an agent writing a correct v2 inventory can be verified against the schema documentation without ambiguity

**Plans:** 4/4 plans complete
Plans:
**Wave 1**

- [x] 68-01-PLAN.md — schemas/constraint_inventory_v2.json JSON Schema Draft 2020-12 + jsonschema dependency + schema validation tests

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 68-02-PLAN.md — lucy lsd validate-inventory CLI subcommand + CLI integration tests (TestValidateInventoryCLI, TestGateLogic)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 68-03-PLAN.md — lucy-lsd-engineer.md Section 5 v1→v2 rewrite (delimiters, schema table, inline example, procedures)
- [x] 68-04-PLAN.md — lucy-devils-advocate.md Section 5A/5B update (CLI extraction, G1/G2/G3 gates)

### Phase 69: CLI Command and Regression Suite

**Goal:** `lucy pylsd run` is a working CLI command the agent can invoke; existing `lucy lsd run` behavior is regression-tested and confirmed unchanged; FORM/LSD binary compatibility is empirically confirmed
**Depends on:** Phase 66, Phase 67 (CLI is a thin wrapper over orchestrator + file format)
**Requirements:** CLI-01, CLI-02, CLI-03
**Success Criteria** (what must be TRUE):

  1. `lucy pylsd run compound.lsd` executes multi-run orchestration and prints ranked merged solutions to stdout (same format as `lucy lsd rank`)
  2. Running the same ibuprofen LSD file (without 4J annotations) through `lucy pylsd run` produces the same solution set as `lucy lsd run` — regression confirmed
  3. `lucy lsd run` with a file containing a `FORM` line behaves the same as without it — LSD binary tolerance of unknown commands confirmed; result documented in a findings note
  4. `lucy lsd rank` operates unchanged on `merged.smi` output — two-tier ranking (match count primary, MAE secondary) is the post-merge ranker

**Plans:** 4/4 plans complete
Plans:

**Wave 1**

- [x] 69-01-PLAN.md — Extract _perform_ranking() and _validate_and_parse_inventory() helpers from cli/lsd.py (pure refactor, Wave 1)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 69-02-PLAN.md — Implement lucy pylsd run command in cli/pylsd.py, register in main.py, CLI integration tests
- [x] 69-03-PLAN.md — FORM tolerance test + .planning/findings/form-tolerance.md audit trail
- [x] 69-04-PLAN.md — Ibuprofen regression test + baseline fixture (InChI-set comparison)

### Phase 70: Agent Skill Updates

**Goal:** lsd-engineer knows the full pyLSD command vocabulary and writes `; ELIM`-annotated HMBC lines for suspect 4J correlations; case.md orchestrator routes to `lucy pylsd run` when pylsd_mode is active
**Depends on:** Phase 68 (schema must be defined), Phase 69 (CLI must exist and be validated)
**Requirements:** AGT-01, AGT-02, AGT-03, AGT-04
**Success Criteria** (what must be TRUE):

  1. lsd-engineer skill contains explicit, unambiguous FORM/ELIM/SHIX/SHIH command reference with the exact LSD syntax; `HMBC X Y 2 4` listed as the correct 4J mechanism
  2. lsd-engineer skill includes the `; ELIM` annotation rule: any HMBC correlation flagged as 4J suspect by nmr-chemist is written as `HMBC X Y ; ELIM` (not removed), so PyLSDOrchestrator can parse it
  3. case.md orchestrator skill includes routing decision: when constraint inventory contains `pylsd_mode: true`, use `lucy pylsd run`; when false, use `lucy lsd run`
  4. devils-advocate checklist includes: verify `pylsd_mode` flag is set when any `; ELIM` annotations exist, verify permutation count <= 8 before approving run

**Plans:** 2/2 plans complete

Plans:

- [x] 70-01-PLAN.md — lsd-engineer §1 pyLSD vocabulary subsection, §"Run LSD" conditional routing block, ITERATION-COMPLETE pylsd_mode extension
- [x] 70-02-PLAN.md — devils-advocate G4 permutation cap check, summary line update, VALIDATION-PASSED template extension

### Phase 71: Ibuprofen CASE UAT

**Goal:** The full stack (Python infrastructure + agent skills + CLI) correctly solves the ibuprofen CASE using pyLSD multi-run orchestration, producing the correct aromatic ring structure as the top-ranked solution
**Depends on:** Phase 70 (all agent and Python changes must be complete)
**Requirements:** UAT-01, UAT-02
**Success Criteria** (what must be TRUE):

  1. Ibuprofen CASE run completes using `lucy pylsd run` with at least 2 permutations covering the 3 known 4J correlations (atoms 4-8, 6-9, 8-4 in standard numbering)
  2. Ibuprofen (or a structure with verified aromatic ring and correct molecular formula C13H18O2) appears in the top 3 ranked solutions in `merged.smi`
  3. `CASE-PROGRESS.md` documents which permutation configuration produced the correct solution and which correlations were deferred as 4J suspects
  4. `run_report.json` is written and shows solution distribution across permutations — at least one permutation produces an aromatic ring solution

**Plans:** TBD

## Progress Table (v8.0)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 65. Hypothesis Validation Gate | 1/1 | Complete    | 2026-03-16 |
| 66. LSDInputGenerator Extensions | 2/2 | Complete    | 2026-03-16 |
| 67. PyLSDOrchestrator and SolutionMerger | 2/2 | Complete    | 2026-03-17 |
| 68. Constraint Inventory v2 Schema | 4/4 | Complete   | 2026-05-19 |
| 69. CLI Command and Regression Suite | 4/4 | Complete   | 2026-05-19 |
| 70. Agent Skill Updates | 2/2 | Complete   | 2026-05-19 |
| 71. Ibuprofen CASE UAT | 0/1 | Superseded (v9.0) | - |

---

## v9.0 CASE Reliability & Skill Consolidation

**Goal:** Make the pyLSD CASE system actually work end-to-end — fix the tooling bugs exposed by the v8.0 UAT postmortem, consolidate the skill/tool architecture, and re-answer the open 4J/aromatic design question — verified by passing blind UAT on CASE1 and CASE9 via the intended mechanism, not a manual bypass.

**Driver:** v8.0 UAT found ibuprofen but bypassed the entire pyLSD system. Per-permutation outlsd conversion emits only a 10-line header (no SMILES), SolutionMerger collects 0, permutation files drop BOND/SYME/DEFF NOT, and the correct answer came from direct lsd binary + forced benzene fragment + ~7 manual coordinator interventions. Full forensics: `.planning/v8.0-UAT-POSTMORTEM.md`.

**Root causes to address:** R1 (outlsd conversion / `lucy lsd run` plumbing), R2 (permutation constraint loss + empty merge), R3 (SYME/DEFF NOT are lucy-ng abstractions not native LSD — translation must be lossless across all paths), R4 (skill/architecture — normal-LSD vs pyLSD documentation imbalance causes agent regression to the better-documented path).

## Phases

- [x] **Phase 72: Design Re-Validation** - Answer the 4 open design questions from the postmortem before any fix is built: is pyLSD multi-run the right 4J approach? single vs dual solver path? where does constraint translation live? how is the aromatic ring established? (first phase; gates all fixes) (completed 2026-05-20)
- [x] **Phase 73: Solution Plumbing Fix** - Fix `lucy lsd run` / outlsd conversion so LSD solutions reliably become SMILES: the exit-255 / header-only bug means nothing downstream works. (depends on Phase 72) (completed 2026-05-21)
- [x] **Phase 74: Constraint Preservation and Merge** - Fix permutation file generation to carry the full constraint set (BOND/SYME/DEFF NOT/grouped), and fix SolutionMerger to collect non-empty results from per-permutation runs. (depends on Phase 73) (completed 2026-05-24)
- [x] **Phase 75: Skill Consolidation** - Audit all agent skills against actual LSD-3.4.9 behavior; eliminate the normal-LSD vs pyLSD documentation imbalance; encode the DESIGN-02 solver-path decision as unambiguous single-path guidance; update devils-advocate gates to catch the v8.0 failure modes. (depends on Phase 72, Phase 74)
- [x] **Phase 76: Milestone UAT Gate** - Blind CASE re-run on CASE1 (ibuprofen) AND CASE9 (4-(1-hydroxyethyl)benzoic acid isopropylester, C12H16O3) via the intended mechanism; all Phase-71 criteria verified against on-disk artifacts by independent RDKit check. (depends on Phase 75) (executed 2026-06-01 — **GATE VERDICT: FAILED**; CASE1 spirit-fail, CASE9 deferred. v9.0 does NOT ship. See 76-milestone-uat-gate/VERIFICATION.md → Phase 77)
- [x] **Phase 77: Fix lucy lsd run + Emergent-Aromatic Tooling + Skill Hygiene** - Fix the blocking defects the v9.0 UAT exposed: repair `lucy lsd run`/`_invoke_outlsd` (real solutions.smi + fail-loud + regression test); make cross-ring COSY equivalence-pair emission deterministic in tooling so the aromatic ring emerges; retire deprecated lucy-case-agent.md + targeted skill-creator audit. Fixes only — no UAT. (depends on Phase 76) (completed 2026-06-01)
- [x] **Phase 78: Blind Re-UAT Gate (CASE1 + CASE9)** - Re-run the v9.0 milestone blind UAT on CASE1 + CASE9 via the now-fixed intended mechanism; independent RDKit verification with rewritten criteria (emergent ring = clean pass, documented BOND escalation = conditional pass, silent ring-BOND/SKEL = fail). Milestone-complete gate. (depends on Phase 77) (executed 2026-06-08 — **GATE VERDICT: FAILED**; CASE1 UAT-03 PASS, CASE9 UAT-04 FAIL → v9.0 DOES NOT SHIP. See 78-UAT-VERDICT.md → Phase 79)
- [x] **Phase 79: Peak-Picking & Symmetry Detection Fix** - Fix the upstream defect the CASE9 UAT exposed: weak quaternary carbonyls masked by the CDCl₃-dominated max-relative peak-picking threshold (carbonyl at 166.08 ppm, SNR≈17, dropped); and 13C peak-intensity symmetry (2C signals) not used to detect equivalent aromatic carbons (so `lucy detect aromatic-cosy` gets no input and the emergent ring is disabled). Then re-run CASE9 blind and re-apply the AND-gate. (depends on Phase 78) (completed 2026-06-09 — all deliverables verified + targeted defect ELIMINATED: blind CASE9 re-run picked the carbonyl @ SNR 17, detected 3 symmetry pairs, ring emerged via COSY with no SKEL/ring-BOND, DBE+quality-loop fired. BUT CASE9 still unsolved — a NEW root cause surfaced → Phase 80. v9.0 still does not ship.)
- [ ] **Phase 80: Long-Range (4J) HMBC Connectivity Defect** - Resolve the blocker the Phase-79 blind CASE9 UAT exposed once carbonyl-masking was removed: false-positive long-range (4J) HMBC correlations (e.g. `HMBC 1 8` = 166.1↔70.2; set 2 3 / 2 9 / 3 8) are enforced as 2-3J, forcing wrong carbonyl connectivity and excluding the correct para-benzoate-with-benzylic-alcohol (`CC(C)OC(=O)c1ccc(C(C)O)cc1`). This is the long-standing 4J-HMBC trap (v4.0 ibuprofen; v7.0 statistical approach abandoned at 100% FP; v8.0 pyLSD `HMBC X Y 2 4` extended-range). Start with discuss/research to choose the approach. (depends on Phase 79) (not started)

## Phase Details

### Phase 72: Design Re-Validation

**Goal:** The 4 open design questions from the v8.0 postmortem are answered and documented before any code is written, so downstream phases build the right thing
**Depends on:** Nothing (first v9.0 phase; gates all fix phases)
**Requirements:** DESIGN-01, DESIGN-02
**Success Criteria** (what must be TRUE):

  1. A decision document exists in `.planning/phases/72-design-revalidation/` with explicit YES/NO answers to all four open design questions (is pyLSD multi-run the right 4J approach? single vs dual solver path? where does constraint translation live? how is the aromatic ring established?)
  2. The Phase-65 hypothesis ("removing 4J HMBC makes aromatic ring appear") is re-evaluated against the v8.0 UAT evidence — specifically the fact that iteration-2 (4J handled, SYME/DEFF NOT dropped) produced 0 aromatic solutions out of 90, and the ring only appeared when forced via SKEL fragment in iteration-3
  3. The DESIGN-02 decision on solver path explicitly addresses why the agent reverted to normal-LSD during the v8.0 run (documentation imbalance hypothesis confirmed or refuted) and specifies a concrete remedy
  4. Each decision records the rationale and its direct implication for Phases 73-75 (i.e., the decision is actionable, not aspirational)

**Plans:** 2/2 plans complete
Plans:
**Wave 1**

- [x] 72-01-PLAN.md — Build 3-arm LSD experiment files + run_experiment.py, execute controlled LSD runs, record per-arm results.json

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 72-02-PLAN.md — Write 72-DECISIONS.md answering Q1-Q4 with experiment evidence; human approval checkpoint

**UI hint**: no

### Phase 73: Solution Plumbing Fix

**Goal:** When the LSD solver finds N solutions, those solutions reliably convert to ranked SMILES — the outlsd exit-255 / header-only conversion bug that caused every per-permutation run to produce an empty output is fixed
**Depends on:** Phase 72 (solver-path architecture decision determines what gets fixed and what gets discarded)
**Requirements:** RELI-01
**Success Criteria** (what must be TRUE):

  1. `lucy lsd run` on a valid LSD input file completes without exit code 255 and writes a `.sol` file to disk
  2. Running outlsd against a `.sol` file that contains N LSD solutions produces a SMILES output with exactly N entries (not a 10-line header with 0 SMILES)
  3. `SolutionMerger` receiving per-permutation outlsd output from a run that produced 2584 raw solutions (the documented ibuprofen perm_00 case) assembles a non-empty `merged.smi` — zero solutions is no longer possible when the solver found solutions
  4. All existing `lucy lsd run` regression tests pass (no behavioral regression on working paths)

**Plans:** 1/1 plans complete
Plans:

- [x] 73-01-PLAN.md — Fix _execute_lsd (file-arg), _run_outlsd (shared _invoke_outlsd helper), success semantics; TestLSDRunnerFixed tests

**UI hint**: no

### Phase 74: Constraint Preservation and Merge

**Goal:** Every solver invocation runs with the complete validated constraint set, and the merge step collects all per-permutation results — no silent loss of BOND/SYME/DEFF NOT/grouped constraints, no empty merge despite per-run solutions
**Depends on:** Phase 73 (outlsd conversion must work before merge correctness can be verified end-to-end)
**Requirements:** RELI-02, RELI-03
**Success Criteria** (what must be TRUE):

  1. Each permutation LSD file generated by `PyLSDOrchestrator` contains the full non-HMBC constraint set from the master file — BOND, DEFF NOT, grouped HMBC notation, and the losslessly-translated native equivalents of SYME and DEFF NOT (i.e., no permutation file is HMBC-only, which was the v8.0 failure: perm_00/compound.lsd = 542 B)
  2. SYME and DEFF NOT in the master constraint inventory are translated to native LSD-3.4.9 commands (MULT/LIST/PROP/ELEM as appropriate per DESIGN-01 decision) before any permutation file is written, so no permutation relies on non-native commands
  3. After a multi-run with permutations that each produce solutions, `merged.smi` is non-empty and `run_report.json` records per-permutation solution counts that sum to at least the count from the most-productive permutation
  4. An aromatic compound processed through the full pyLSD pipeline (or the DESIGN-01-decided mechanism) produces at least one aromatic-ring solution in the ranked output — the benzene ring emerges from constraints, not from a forced SKEL fragment

**Plans:** 2/2 plans complete
Plans:

**Wave 1**

- [x] 74-01-PLAN.md — Extend LSDProblem with ring_exclusion_enabled + add_equivalence_pair/add_aromatic_equivalence_pair; bundle ring3/ring4 filter files; native DEFF F/FEXP emission + _write_filter_files in generator; TestNativeConstraintEmission (TDD)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 74-02-PLAN.md — Permutation constraint preservation tests (deepcopy proof) + SolutionMerger correctness test + end-to-end emergent-aromatic integration test (skipif LSD)

**UI hint**: no

### Phase 75: Skill Consolidation

**Goal:** All agent skills reflect actual LSD-3.4.9 behavior, give unambiguous single-path guidance per the DESIGN-02 decision, and encode devils-advocate gates that would have caught the v8.0 failure modes before the run
**Depends on:** Phase 72 (design decisions determine which commands to teach and which path to document), Phase 74 (fixed tooling must be reflected in skill documentation)
**Requirements:** SKILL-01, SKILL-02, SKILL-03
**Success Criteria** (what must be TRUE):

  1. All agent skills (lsd-engineer, devils-advocate, nmr-chemist, solution-analyst, case.md, diagnostic) are audited against native LSD-3.4.9 commands (MULT/LIST/PROP/BOND/COSY/HMBC/ELIM/DEFF/FEXP/HSQC/ELEM); SYME and DEFF NOT are documented as lucy-ng abstractions that require native translation — no skill teaches them as directly passable to the LSD binary
  2. Skills give unambiguous single-solver-path guidance per DESIGN-02: the path that the agent reverted to in the v8.0 UAT is either removed from skills (if DESIGN-02 decides single path) or documented with equally-specific routing conditions (if dual path)
  3. The devils-advocate checklist includes gates that would have failed the v8.0 run early: (a) detect that permutation files drop non-HMBC constraints, (b) detect empty `merged.smi` despite non-zero `solncounter` files, (c) flag any LSD file modification after DA approval (the post-validation edit violation documented in the v8.0 postmortem)
  4. A developer reading the agent skills can determine, for any given solver invocation, exactly which constraints will be passed to the LSD binary and via which CLI command — no ambiguity about native vs abstraction layer

**Plans:** 5/5 plans executed
**Wave 1**

- [x] 75-01-lsd-engineer-native-singlepath-PLAN.md — SYME→BOND/COSY, DEFF NOT→DEFF F/FEXP, single-path step 11, outlsd pipe removal, SKEL escalation note in lsd-engineer.md

**Wave 2** *(all depend on 75-01; independent of each other)*

- [x] 75-02-devils-advocate-native-gates-PLAN.md — native-command sync in DA §1/§2/§5, add G5/G6/G7/G8 v8.0-failure-mode gates
- [x] 75-03-case-references-analyst-PLAN.md — outlsd pipe removal in case.md task descriptions, native vocab in spawn prompts, progress-format.md + solution-analyst.md updates
- [x] 75-04-python-schema-followups-PLAN.md — fragment to-lsd --filter-index 3 default, new tests, pytest green; all fragment F1→F3 refs in lsd-engineer.md
- [x] 75-05-diagnostic-native-PLAN.md — lucy-diagnostic.md SYME section → native BOND/COSY; fix template and grep check updated

*(75-02, 75-03, 75-04, 75-05 all depend on 75-01 and are independent of each other)*

**UI hint**: no

### Phase 76: Milestone UAT Gate

**Goal:** The complete v9.0 system (fixed tooling + consolidated skills) solves two different aromatic compounds via the intended mechanism, verified against on-disk artifacts by independent RDKit check — not by agent self-report
**Depends on:** Phase 75 (all tooling fixes and skill updates must be complete before UAT)
**Requirements:** UAT-03, UAT-04
**Success Criteria** (what must be TRUE):

  1. CASE1 (ibuprofen, C13H18O2) re-run produces a solution via `lucy pylsd run` (or the DESIGN-02-decided solver path) with at least 2 permutations; the correct structure or a RDKit-verified aromatic-ring C13H18O2 isomer is in the top-3 of `merged.smi`; all four Phase-71 success criteria pass against on-disk artifacts (not agent self-report)
  2. CASE9 (4-(1-hydroxyethyl)benzoic acid isopropylester, C12H16O3) first-ever blind run completes via the intended mechanism; the correct structure or a RDKit-verified aromatic-ring C12H16O3 isomer is in the top-3 ranked solutions; `merged.smi` is non-empty
  3. Neither run required manual coordinator intervention to bypass the pipeline — the 7-intervention rescue pattern from the v8.0 UAT is absent from `CASE-PROGRESS.md`
  4. `run_report.json` for both runs documents per-permutation solution counts; at least one permutation per compound produces solutions that include an aromatic ring (independently verified by RDKit aromatic atom count, not relying on agent annotation)

**Plans:** 2/2 plans complete

Plans:
**Wave 1**

- [x] 76-01-PLAN.md — Build verify_case_solution.py (RDKit harness, TDD), pytest tests, sanitisation re-verification

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 76-02-PLAN.md — Blind CASE run gate (CASE1 + CASE9) + independent artifact verification, write VERIFICATION.md

**UI hint**: no

## Progress Table (v9.0)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 72. Design Re-Validation | 2/2 | Complete   | 2026-05-20 |
| 73. Solution Plumbing Fix | 1/1 | Complete   | 2026-05-21 |
| 74. Constraint Preservation and Merge | 2/2 | Complete   | 2026-05-24 |
| 75. Skill Consolidation | 5/5 | Complete   | 2026-05-24 |
| 76. Milestone UAT Gate | 2/2 | Executed — **GATE FAILED** | 2026-06-01 |
| 77. Fix lucy lsd run + Emergent Tooling + Hygiene | 3/3 | Complete    | 2026-06-01 |
| 78. Blind Re-UAT Gate (CASE1 + CASE9) | 4/4 | Executed — **GATE FAILED** | 2026-06-08 |
| 79. Peak-Picking & Symmetry Detection Fix | 4/4 | Complete    | 2026-06-09 |

**v9.0 milestone gate: FAILED at Phase 78 (does not ship).** CASE1 UAT-03 = **PASS** (ibuprofen found as #2, ring fully emergent via cross-ring COSY, no ring-BOND/SKEL, clean). CASE9 UAT-04 = **FAIL** (correct structure — 4-(1-hydroxyethyl)benzoic acid isopropyl ester — never reached; ring forced via 6 ring-BONDs; correct para-disubstituted reading blocked by an upstream peak-picking defect). AND-gate = FAIL. Root cause: `lucy pick 1d` drops the ester carbonyl (166.08 ppm, SNR≈17) because the CDCl₃ triplet dominates the max-relative threshold, and 13C intensity-symmetry (2C signals) is not used to detect equivalent aromatic carbons → `lucy detect aromatic-cosy` has no input → emergent ring disabled. The Phase-77 LSD mechanism is **not** refuted; it never received correct input. Blocking defects → **Phase 79**. See `.planning/phases/78-blind-re-uat-gate/78-UAT-VERDICT.md`.

### Phase 77: Fix lucy lsd run + Emergent-Aromatic Tooling + Skill Hygiene

**Goal:** The blocking defects exposed by the Phase 76 UAT are fixed so the intended v9.0 mechanism actually works end-to-end — `lucy lsd run` produces real solutions and fails loud on error, the aromatic ring emerges from deterministically-emitted cross-ring COSY constraints (no manual atom-index reasoning, no forced ring), and the skill is free of the deprecated/contradictory agent file. Fixes are verified by tests; the blind re-UAT is Phase 78.
**Requirements:** FIX-01 (lucy lsd run plumbing), FIX-02 (deterministic cross-ring COSY emission / emergent-aromatic), FIX-03 (skill hygiene)
**Depends on:** Phase 76 (forensics define the defects — see 76-VERIFICATION.md)
**Success Criteria** (what must be TRUE):

  1. `lucy lsd run` on a valid `.lsd` produces a `solutions.smi` containing real SMILES (not `outlsd: This is not a file for OUTLSD.`); when outlsd output is the error string / empty / non-SMILES, the runner exits non-zero with a clear error (no false "success"); a regression test asserts both the happy path and the error path
  2. A CLI/generator helper derives cross-ring aromatic COSY equivalence pairs (e.g. 4≡7, 5≡6) from detected symmetry/grouping and emits them, so the agent no longer hand-assigns atom indices; on the CASE1 constraint set this yields an aromatic ring without explicit ring-BOND forcing (re-confirms Arm A emergence end-to-end)
  3. Ring-BOND forcing is documented in the skill ONLY as an escalation after N non-aromatic iterations, logged in CASE-PROGRESS; the false Phase-73 "fix works" claim in lucy-lsd-engineer.md is corrected
  4. Deprecated `~/.claude/agents/lucy-case-agent.md` is retired/archived; a targeted skill-creator audit confirms the v9.0 single-path + emergent/COSY guidance is prominent (not buried) and flags dead/contradictory content — no full rewrite
  5. D-76 mechanistic UAT criterion is rewritten for Phase 78 (emergent = clean pass, documented BOND escalation = conditional pass, silent ring-BOND/SKEL = fail)

**Plans:** 3/3 plans complete

Plans:
**Wave 1** *(FIX-01 and FIX-03 are independent — run in parallel)*

- [x] 77-01-PLAN.md — Fix _execute_lsd filter-file copy + harden _invoke_outlsd fail-loud + regression tests
- [x] 77-03-PLAN.md — Skill hygiene: retire lucy-case-agent.md, correct lsd-engineer Phase-73 claim, add aromatic-cosy reference, D-77-06 criteria in case.md

**Wave 2** *(depends on 77-01)*

- [x] 77-02-PLAN.md — detect_aromatic_cosy_pairs() in generator.py + lucy detect aromatic-cosy CLI + emergence integration test

### Phase 78: Blind Re-UAT Gate (CASE1 + CASE9)

**Goal:** The fixed v9.0 stack solves CASE1 and CASE9 via the intended mechanism in a fresh blind instance, verified independently against on-disk artifacts with the rewritten criteria — the v9.0 milestone-complete gate.
**Requirements:** UAT-03 (CASE1), UAT-04 (CASE9)
**Depends on:** Phase 77 (all fixes verified green before the manual blind gate)
**Success Criteria** (what must be TRUE):

  1. Fresh blind instance runs `/lucy-ng:case` on CASE1 (C13H18O2) and CASE9 (C12H16O3) via the single primary path; `verify_case_solution.py` exits 0 on each `solutions.smi`
  2. Emitted LSD files: native constraints present (BOND/COSY, DEFF F/FEXP), SYME=0, DEFF NOT=0, SKEL=0; aromatic ring emergent OR ring-BONDs only as a CASE-PROGRESS-documented escalation (silent ring-BONDs = fail)
  3. 0 path-changing bypass interventions; `lucy lsd run` used as the primary path (no direct-binary bypass)
  4. Both compounds pass (D-76-06 AND-gate) → v9.0 ships; failure is a valid result documented for a follow-up phase (D-76-07)

**Plans:** 4/4 plans executed

Plans:
**Wave 1**
- [x] 78-01-PLAN.md — Dataset identity-leakage audit (CASE1 + CASE9 sanitisation pre-check)

**Wave 2** *(depends on 78-01)*
- [x] 78-02-PLAN.md — CASE1 blind run + evidence collection (UAT-03 PASS)
- [x] 78-03-PLAN.md — CASE9 blind run + evidence collection (UAT-04 FAIL)

**Wave 3** *(depends on 78-02 + 78-03)*
- [x] 78-04-PLAN.md — AND-gate verdict roll-up + forensics-on-fail (v9.0 DOES NOT SHIP)

**UI hint**: no

### Phase 79: Peak-Picking & Symmetry Detection Fix

**Goal:** The CASE9 failure mode is eliminated at both layers — the peak-picker no longer masks
weak quaternary carbonyls under a solvent-dominated threshold, 13C intensity-symmetry is used to
detect equivalent aromatic carbons (feeding the emergent-COSY mechanism), AND the CASE skill gains
a feedback loop so a clean-but-wrong convergence triggers a return to the spectrum instead of
silently terminating. Verified by a blind CASE9 re-run that reaches a para-disubstituted ester
solution via the emergent path, then re-applying the Phase-78 AND-gate.
**Depends on:** Phase 78 (forensics define the two-layer defect — see 78-UAT-CASE9.md and
79-SCOPE-SEED.md)
**Requirements:** FIX-04 (peak-picker threshold / solvent masking), FIX-05 (intensity-symmetry
detection), FIX-06 (skill feedback loop: DBE self-check + quality loop-pattern)
**Success Criteria** (what must be TRUE):

  1. `lucy pick 1d` on the CASE9 13C spectrum lists the ester carbonyl at ~166 ppm (SNR≈17) — the
     CDCl₃ solvent multiplet no longer suppresses weak quaternary peaks (SNR-based and/or
     solvent-aware threshold); a regression test asserts the carbonyl is picked and that existing
     CASE1 picking is unchanged
  2. 13C peak intensity is used as a 2C-equivalence indicator so a para-disubstituted ring yields
     equivalence pairs from `lucy analyze symmetry` / `lucy detect aromatic-cosy` on the CASE9 set
     (e.g. 129.94≡, 125.31≡) — the emergent-ring mechanism receives correct input
  3. The nmr-chemist skill performs a DBE-insaturation self-check after picking: a DBE deficit
     coinciding with an empty 160–220 ppm region triggers a targeted low-threshold re-pick before
     [SETUP-COMPLETE]; the intensity-symmetry check is procedural, not an optional note
  4. A quality-based loop-pattern exists (best MAE > tier threshold OR all top solutions
     IMPLAUSIBLE/QUESTIONABLE across N iterations) wired into case.md detect_loops +
     loop-patterns.md + advisory-templates.md, with a bounded re-pick budget to avoid infinite
     loops; it reactivates the nmr-chemist to re-inspect the spectrum
  5. A blind CASE9 re-run (fresh instance, per feedback_blind_uat) reaches a RDKit-verified
     para-disubstituted aromatic-ester C12H16O3 solution via the emergent path (no forced
     ring-BONDs as the primary mechanism); the Phase-78 AND-gate is re-applied and recorded

**Plans:** 4/4 plans complete

Plans:
**Wave 0**
- [x] 79-00-PLAN.md — Add FIX-04/05/06 to REQUIREMENTS.md + create failing test stubs (Wave 0 foundation)

**Wave 1** *(depends on 79-00)*
- [x] 79-01-PLAN.md — SNR/MAD threshold, solvent exclusion, per-peak SNR annotation (FIX-04)
- [x] 79-02-PLAN.md — detect_intensity_symmetry for aromatic CH 2C-equivalence detection (FIX-05)

**Wave 2** *(depends on 79-01 + 79-02)*
- [x] 79-03-PLAN.md — Skill feedback loop: DBE self-check + QUALITY_CONVERGENCE_FAILURE 5th loop-pattern (FIX-06)

**UI hint**: no

## Progress Table (v9.0, cont.)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 79. Peak-Picking & Symmetry Detection Fix | 0/4 | In progress | — |

### Phase 80: Long-Range (4J) HMBC Connectivity Defect

**Goal:** False-positive long-range (4J) HMBC correlations no longer force incorrect 2-3J
connectivity that excludes the correct structure. The CASE9 compound
(4-(1-hydroxyethyl)benzoic acid isopropyl ester, `CC(C)OC(=O)c1ccc(C(C)O)cc1`) becomes
reachable via the emergent path, with the benzylic carbon correctly resolved as a free
secondary alcohol rather than bonded into the carbonyl. Verified by a blind CASE9 re-run that
reaches the RDKit-verified para-benzoate solution and re-applies the Phase-78 AND-gate.
**Requirements:** FIX-07 (long-range / 4J HMBC connectivity handling)
**Depends on:** Phase 79 (its blind CASE9 UAT exposed this defect — see 79-HUMAN-UAT.md and
CASE9/analysis/final_results.md + CASE-PROGRESS.md)

**Discovery context (Phase 79 blind CASE9 UAT, 2026-06-09):** Phase-79 fixes all engaged and
worked (carbonyl 166.1 picked @ SNR 17; 3 intensity-symmetry 2C-pairs detected; benzene ring
emerged via COSY equivalence pairs with no SKEL / no ring-BOND; DBE self-check 5/5 + quality
reexamination advisory fired). CASE9 nonetheless converged to a wrong benzylic-carbonate
(meta, MAE 9.09, PLAUSIBLE-but-wrong). Agent self-diagnosis (iterations 6–7): the correlations
`HMBC 1 8` (166.1↔70.2), `2 3`, `2 9`, `3 8` are 4J / long-range artifacts; enforcing them as
2-3J bonds the ester carbonyl to the para benzylic carbon, which is geometrically impossible in
the true para-benzoate and excludes it from the LSD solution space. Even forcing ester topology
(iteration 7) could not recover because the spurious `HMBC 1 8` remained.

**Success Criteria** (what must be TRUE):

  1. The pipeline distinguishes (statistically, structurally, or via solver-side range relaxation)
     long-range/4J HMBC correlations from genuine 2-3J ones, so a spurious `166.1↔70.2`-class
     correlation no longer forces an impossible bond — without reintroducing the v7.0 100%-FP failure.
  2. On the CASE9 constraint set, the correct para-benzoate-with-benzylic-alcohol is generated as
     an LSD solution via the emergent path (no forced ring-BONDs / SKEL as the primary mechanism).
  3. A regression guard exists (test or documented experiment) that locks the 4J-handling behavior
     for both CASE9 and the historical ibuprofen 4J case (v4.0), so prior wins do not regress.
  4. A blind CASE9 re-run (fresh instance, per feedback_blind_uat) reaches the RDKit-verified
     C12H16O3 para-benzoate solution; the Phase-78 AND-gate is re-applied and recorded. This is the
     v9.0 milestone-ship gate.

**Open approach question (resolve in discuss/research):** extend the emergent HMBC bond range
(`HMBC X Y 2 4`) selectively for suspect quaternary↔distant-CH pairs? solver-side multi-run over
suspect-correlation subsets (pyLSD-style, repaired)? a narrower statistical/heuristic 4J flag than
the abandoned v7.0 one? The phase should NOT start coding before this is decided.

**Plans:** 1/5 plans executed

Plans:
**Wave 0**
- [x] 80-00-PLAN.md — Failing test stubs (TestElimBudget, TestPlausibilityFilter, TestPlausibilityFilterOrdering, TestSchemaV2Phase80) — RED baseline

**Wave 1** *(depends on 80-00; plans 01 and 02 parallel)*
- [ ] 80-01-PLAN.md — elim_budget field on LSDProblem + ELIM emission decoupled from pylsd_mode + schema surgery + pyLSD deprecation (FIX-07-A/B/E)
- [ ] 80-02-PLAN.md — Chemical plausibility pre-filter in SolutionRanker + is_plausible field on RankedSolution (FIX-07-C/D)

**Wave 2** *(depends on 80-01 + 80-02)*
- [ ] 80-03-PLAN.md — Agent skill surgery: lsd-engineer (4J Deferral Rule removed, ELIM escalation + COSY 3 3 protection added), devils-advocate (G1-G4/G8 removed, G-ELIM gates added), solution-analyst, diagnostic, case.md; + Arm A + ELIM 1 0 regression experiment writing 80-ELIM-REGRESSION.md (SC-3)

**Wave 3** *(depends on 80-03; autonomous: false — blind UAT gate)*
- [ ] 80-04-PLAN.md — Blind CASE9 + CASE1 UAT gate (FIX-07-F/G) — v9.0 milestone-ship gate

---
*Last updated: 2026-06-08 — Phase 78 closed (GATE FAILED: CASE1 PASS, CASE9 FAIL); Phase 79 planned: 4 plans in 3 waves (Wave 0 foundation, Wave 1 Python tooling FIX-04/05, Wave 2 skill markdown FIX-06)*
