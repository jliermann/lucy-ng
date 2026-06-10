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
- **v9.0 CASE Reliability & Skill Consolidation** - Phases 72-81 (in progress; does not ship until CASE9 passes. Phase 79 eliminated the carbonyl-masking defect, Phase 80 delivered the 4J ELIM mechanism — but the Phase-80 blind UAT exposed a residual peak-picking integrity defect (snr_floor=3 noise flood + no overcount guard) that drops the carbonyl → Phase 81)

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
- [ ] **Phase 80: Long-Range (4J) HMBC Connectivity Defect** - Resolve the blocker the Phase-79 blind CASE9 UAT exposed once carbonyl-masking was removed: false-positive long-range (4J) HMBC correlations (e.g. `HMBC 1 8` = 166.1↔70.2; set 2 3 / 2 9 / 3 8) are enforced as 2-3J, forcing wrong carbonyl connectivity and excluding the correct para-benzoate-with-benzylic-alcohol (`CC(C)OC(=O)c1ccc(C(C)O)cc1`). This is the long-standing 4J-HMBC trap (v4.0 ibuprofen; v7.0 statistical approach abandoned at 100% FP; v8.0 pyLSD `HMBC X Y 2 4` extended-range). (depends on Phase 79) (mechanism delivered + unit-green 2026-06-10: elim_budget, plausibility pre-filter, skill surgery, SC-3 regression guard PASS — but blind UAT GATE FAILED: CASE9 still unsolved. Root cause is UPSTREAM peak-picking, not the solver → Phase 81. See 80-UAT-VERDICT.md. v9.0 does not ship.)
- [x] **Phase 81: Peak-Picking Integrity (FIX-08)** - Fix the upstream peak-picking defect that failed the Phase-80 blind CASE9 UAT: default `snr_floor=3.0` floods the picker with ~50 baseline-ripple peaks (incl. 13 impossible >220 ppm), so the agent's manual curation dropped the genuine ester carbonyl (166.08 ppm, SNR 17) → DBE misallocated, benzene read as monosubstituted, correct para-benzoate excluded. Plus: no overcount guard (`analyze symmetry` only models undercount; 76-vs-12 prints a silent negative and even confirmed the carbonyl-free skeleton). Fixes: snr_floor 3→5, expose `--snr-floor`, overcount guard + `missing_carbons<0` alarm, nmr-chemist SNR/carbonyl rules, CASE9 regression test. Then re-run blind UAT + re-apply AND-gate. (depends on Phase 80) (code complete + VERIFIED 2026-06-10: all 5 fixes a–e shipped, full suite 1077 passed, FIX-08 regression suite green — CASE9/12 @snr_floor=5 → 29 peaks, none >230 ppm, ester carbonyl present. Blind re-UAT is the remaining separate v9.0 ship-gate.)
- [x] **Phase 82: Blind-UAT Skill Hygiene (FIX-09)** - Decontaminate the runtime CASE skill/agent files so a fresh blind instance learns NOTHING about the GSD dev process, the answer compound, or the test's success criteria. Discovered 2026-06-10 mid-CASE9-run: the fresh instance reported "Phase-78 gate passed — aromatic ring emerged (no SKEL, no ring-BONDs)" because the `uat_criteria` step + answer-key examples are baked directly into `case.md` and the team agents. ~52 leak sites inventoried across 6 active files (case.md, loop-patterns.md, advisory-templates.md, lucy-lsd-engineer.md, lucy-diagnostic.md, lucy-solution-analyst.md, lucy-devils-advocate.md; lucy-nmr-chemist.md was clean; lucy-case-agent.md is orphaned/never-loaded). Neutralize: strip L1 dev-meta labels (keep the domain rule), replace L2 answer-key examples (ibuprofen/C13H18O2/COSY 4 7/[44.90,45.03]) with abstract illustrative placeholders, and remove L3 success-criteria from runtime (gate criteria relocated to `.planning/case-uat-gate-criteria.md` + `scripts/verify_case_solution.py`). The 2026-06-10 CASE9 run is invalidated. (depends on Phase 81) (DONE 2026-06-10: 60 edits across 7 files; independent grep = 0 leaks across all 10 active runtime files; gate criteria relocated to .planning/case-uat-gate-criteria.md. See 82-DECONTAMINATION-REPORT.md. Blind re-UAT now safe to run.)
- [ ] **Phase 83: Constraint-Hardness Guard (FIX-10)** - An uncertain structural inference must never become a hard, solution-excluding LSD constraint. Third instance of the recurring meta-failure (after v3.0 Pitfall 6 erosion + the FIX-07 4J trap): uncertain interpretation → hard PROP/BOND → correct structure excluded. CASE9 trigger (isopropyl 4-(1-hydroxyethyl)benzoate, C12H16O3, RDKit-verified ZERO ring-O): the nmr-chemist turned `detect neighbours 150.80`→O 81% into a hard `PROP 2 O 1`, forcing oxygen onto the aromatic C that actually carries a benzylic CH(OH)CH₃ → the true para-alkylbenzoate left the search space. Scope (narrow, constraint-hardness only): (a) nmr-chemist — detect-neighbours O/N is advisory/statistical-prior, 145–160 ppm aromatic C is ambiguous (ring-O vs EDG/benzylic substituent), re-assert Pitfall 6; (b) lsd-engineer — no hard heteroatom PROP/BOND from statistics alone, leave open, let ranking decide; (c) devils-advocate — gate blocking/flagging a hard heteroatom-neighbour PROP/BOND lacking cited direct evidence; (d) optional tooling — `detect neighbours` self-labels advisory + regression test. Out of scope (separate blockers): benzene-ring emergence (D-04), HMBC-pool richness. (depends on Phase 82) (not started)

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

**Plans:** 4/5 plans executed

Plans:
**Wave 0**
- [x] 80-00-PLAN.md — Failing test stubs (TestElimBudget, TestPlausibilityFilter, TestPlausibilityFilterOrdering, TestSchemaV2Phase80) — RED baseline

**Wave 1** *(depends on 80-00; plans 01 and 02 parallel)*
- [x] 80-01-PLAN.md — elim_budget field on LSDProblem + ELIM emission decoupled from pylsd_mode + schema surgery + pyLSD deprecation (FIX-07-A/B/E)
- [x] 80-02-PLAN.md — Chemical plausibility pre-filter in SolutionRanker + is_plausible field on RankedSolution (FIX-07-C/D)

**Wave 2** *(depends on 80-01 + 80-02)*
- [x] 80-03-PLAN.md — Agent skill surgery: lsd-engineer (4J Deferral Rule removed, ELIM escalation + COSY 3 3 protection added), devils-advocate (G1-G4/G8 removed, G-ELIM gates added), solution-analyst, diagnostic, case.md; + Arm A + ELIM 1 0 regression experiment writing 80-ELIM-REGRESSION.md (SC-3)

**Wave 3** *(depends on 80-03; autonomous: false — blind UAT gate)*
- [ ] 80-04-PLAN.md — Blind CASE9 + CASE1 UAT gate (FIX-07-F/G) — v9.0 milestone-ship gate

### Phase 81: Peak-Picking Integrity (FIX-08)

**Goal:** Make 13C peak-picking deterministically separate signal from noise so a fresh blind agent always receives the ~12 real carbons (including weak quaternary carbonyls) and never a 76-peak noise list. The Phase-80 blind CASE9 UAT FAILED on an upstream peak-picking defect, NOT the Phase-80 solver mechanism: with the default `snr_floor=3.0` (IUPAC Limit-of-Detection) the picker returns ~50 baseline-ripple peaks at SNR≈3 — including 13 physically-impossible peaks above 220 ppm (up to 296 ppm) — and the genuine ester carbonyl at 166.08 ppm (SNR 17, ~5× the noise band) was lost during the agent's manual 76→8 curation. With no carbonyl, DBE=5 was misallocated as benzene(4)+O-ring(1) instead of benzene(4)+C=O(1), the aromatic ring was read as monosubstituted, and the correct para-benzoate `CC(C)OC(=O)c1ccc(C(C)O)cc1` was never in the search space. Compounding it: the carbon-count reconciliation (`analyze symmetry` / `symmetry_analysis.py`) only models the UNDERcount direction (`missing_carbons = expected − observed > 0` → equivalence); the OVERcount case (76 vs 12) prints a silent negative and — after 76→8 curation — even *confirmed* the carbonyl-free skeleton (8 signals + 4 equivalences = 12 C). See `80-UAT-VERDICT.md`.

**Scope (5 fixes):**
- (a) Raise 13C peak-picker `snr_floor` default 3.0 → 5.0 in `src/lucy_ng/processing/peak_picker.py` (re-pick of CASE9/12 at k=5 collapses 76→29 peaks, removes all >220 ppm impossibles, leaves the carbonyl as the highest-ppm peak; every real C has SNR ≥ 8, every noise peak SNR ≈ 3.0–3.7).
- (b) Expose `--snr-floor` in `lucy pick 1d` CLI (currently only `-t/--threshold`, which switches to the inferior fraction-of-max path that the Phase-78 postmortem already flagged).
- (c) Overcount sanity guard: compare raw picked-peak count vs expected carbons from formula and ALARM when `missing_carbons < 0` — in `src/lucy_ng/cli/analyze.py` and `src/lucy_ng/analysis/symmetry_analysis.py` (both currently handle only the undercount/equivalence direction).
- (d) nmr-chemist skill (`~/.claude/agents/lucy-nmr-chemist.md`): add "SNR ≥ 5 = signal, SNR < 5 = noise"; "more signals than carbons = noise, not symmetry"; "a 160–180 ppm signal with SNR ≥ 5 is a C=O — never discard it".
- (e) Regression test: CASE9/12 13C @ k=5 yields the carbonyl, ≤ 30 peaks, none > 230 ppm; overcount guard fires on the 76-vs-12 case.

**Requirements**: FIX-08
**Depends on:** Phase 80
**Plans:** 4/4 plans complete

**Exit gate:** After fixes, re-run the blind UAT on CASE9 + CASE1 (fresh instances per `feedback_blind_uat`) and re-apply the Phase-78 AND-gate. v9.0 ships iff both pass.

Plans:
**Wave 1** *(81-01, 81-02, 81-03 are independent and run in parallel)*

- [x] 81-01-PLAN.md — snr_floor default 3→5 in peak_picker.py + expose --snr-floor in lucy pick 1d
- [x] 81-02-PLAN.md — overcount guard + missing_carbons<0 alarm in analyze.py + symmetry_analysis.py
- [x] 81-03-PLAN.md — nmr-chemist skill: SNR≥5 rules, overcount=noise rule, carbonyl-never-discard rule

**Wave 2** *(depends on 81-01 + 81-02)*

- [x] 81-04-PLAN.md — FIX-08 regression test suite (CASE9@k=5 + overcount guard + CASE1 non-regression) + full suite health check

### Phase 83: Constraint-Hardness Guard (FIX-10)

**Goal:** Uncertain structural inferences never become hard, solution-excluding LSD constraints. Statistical single-shift detections (especially `lucy detect neighbours` O/N) are advisory/ranking signals only; heteroatom placement lacking direct connectivity evidence (HMBC/HSQC/exchangeable-H) is left OPEN so LSD explores alternatives and 13C ranking discriminates. This removes the exclusion defect that lost the CASE9 answer — the third instance of "uncertain interpretation → hard constraint → correct structure excluded" (after v3.0 Pitfall 6 erosion and the FIX-07 4J trap).

**Trigger/evidence:** CASE9 = isopropyl 4-(1-hydroxyethyl)benzoate `CC(O)c1ccc(cc1)C(=O)OC(C)C`, C12H16O3 (RDKit-verified: DBE 5, 6 aromatic ring-C, **0 ring-oxygen**). The nmr-chemist read `detect neighbours 150.80` → O 81% (post N-exclusion) and emitted hard `PROP 2 O 1`, forcing oxygen onto the aromatic carbon that actually bears a benzylic CH(OH)CH₃ (a carbon substituent) → every solution from iteration 4 carried ring-O → the true para-alkylbenzoate was excluded. 13C-prediction of the truth fits 8/9 signals; the 150.8 carbon predicts ~144 ppm (HOSE-DB weakness for benzylic-OH-bearing aromatics under a para-ester) — so the O-heuristic is reasonable-but-wrong, the precise reason it must never be a hard constraint.

**Depends on:** Phase 82
**Requirements:** FIX-10
**Success Criteria** (what must be TRUE):

  1. The nmr-chemist agent states explicitly that `detect neighbours` O/N output is a statistical prior / advisory signal, and that a 145–160 ppm aromatic C is ambiguous (ring-O vs EDG/benzylic substituent, esp. when an sp3 C–O at ~65–75 ppm could be benzylic); Pitfall 6 ("don't over-constrain heteroatoms; let ranking decide") is re-asserted.
  2. The lsd-engineer agent forbids emitting `PROP X O n` or a hard heteroatom BOND from statistical detection alone; uncertain heteroatom placement is left open for ranking to discriminate.
  3. The devils-advocate has a gate that BLOCKS or CRITICAL-flags any hard heteroatom-neighbour PROP / heteroatom BOND that lacks a cited direct-evidence basis (HMBC/HSQC/exchangeable-H).
  4. A documented check (test or re-derivation) shows that, with heteroatom placement left open per the above, the CASE9 truth `CC(O)c1ccc(cc1)C(=O)OC(C)C` is NOT excluded by FIX-10-conformant constraints (it can appear in the LSD search space). Optional: `lucy detect neighbours` output self-labels as advisory + regression test.

**Out of scope** (remain separate CASE9 blockers, not addressed here): benzene-ring emergence (the long-standing D-04 complex) and HMBC-pool richness/extraction. FIX-10 removes the hard exclusion; it does not by itself guarantee a full CASE9 solve.

**Exit gate:** A later blind CASE9 re-run (fresh instance) is the milestone gate; FIX-10 verifies the exclusion defect is removed, not that CASE9 fully solves.

**Plans:** 2 plans
Plans:

- [ ] 83-01-PLAN.md — Skill edits: nmr-chemist advisory rule + 145-160 ppm ambiguity, lsd-engineer FIX-10 prohibition, devils-advocate G-PROP-EVIDENCE gate
- [ ] 83-02-PLAN.md — Tooling: NeighbourResult advisory field + CLI advisory note + regression tests (advisory label + CASE9-truth-not-excluded)

---
*Last updated: 2026-06-10 — Phase 81 (FIX-08) code-complete + verified; Phase 82 (FIX-09 blind-UAT skill decontamination) DONE + skills migrated into repo/.claude (symlinked); the 2026-06-10 CASE9 run is invalidated. Phase 83 (FIX-10 constraint-hardness guard) added from the CASE9 C150.80 diagnosis. v9.0 still does not ship.*
