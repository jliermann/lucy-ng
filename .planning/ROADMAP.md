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
- **v9.0 CASE Reliability & Skill Consolidation** - Phases 72-76 (in progress)

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
- [ ] **Phase 74: Constraint Preservation and Merge** - Fix permutation file generation to carry the full constraint set (BOND/SYME/DEFF NOT/grouped), and fix SolutionMerger to collect non-empty results from per-permutation runs. (depends on Phase 73)
- [ ] **Phase 75: Skill Consolidation** - Audit all agent skills against actual LSD-3.4.9 behavior; eliminate the normal-LSD vs pyLSD documentation imbalance; encode the DESIGN-02 solver-path decision as unambiguous single-path guidance; update devils-advocate gates to catch the v8.0 failure modes. (depends on Phase 72, Phase 74)
- [ ] **Phase 76: Milestone UAT Gate** - Blind CASE re-run on CASE1 (ibuprofen) AND CASE9 (4-(1-hydroxyethyl)benzoic acid isopropylester, C12H16O3) via the intended mechanism; all Phase-71 criteria verified against on-disk artifacts by independent RDKit check. (depends on Phase 75)

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

**Plans:** 2 plans
Plans:

- [ ] 74-01-PLAN.md — Extend LSDProblem with ring_exclusion_enabled + add_equivalence_pair/add_aromatic_equivalence_pair; bundle ring3/ring4 filter files; native DEFF F/FEXP emission + _write_filter_files in generator; TestNativeConstraintEmission (TDD)
- [ ] 74-02-PLAN.md — Permutation constraint preservation tests (deepcopy proof) + SolutionMerger correctness test + end-to-end emergent-aromatic integration test (skipif LSD)

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

**Plans:** TBD
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

**Plans:** TBD
**UI hint**: no

## Progress Table (v9.0)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 72. Design Re-Validation | 2/2 | Complete   | 2026-05-20 |
| 73. Solution Plumbing Fix | 1/1 | Complete   | 2026-05-21 |
| 74. Constraint Preservation and Merge | 0/2 | Not started | - |
| 75. Skill Consolidation | 0/TBD | Not started | - |
| 76. Milestone UAT Gate | 0/TBD | Not started | - |

---
*Last updated: 2026-05-22 — Phase 74 planned (2 plans)*
