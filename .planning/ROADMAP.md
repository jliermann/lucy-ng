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
- **v8.0 pyLSD Integration** - Phases 65-71 (in progress)

---

## v8.0 pyLSD Integration

**Goal:** Migrate from direct single LSD runs to pyLSD-style multi-run orchestration, enabling systematic exploration of 4J HMBC coupling possibilities. Fix the root cause of the ibuprofen CASE failure (v4.0 UAT).

## Phases

- [x] **Phase 65: Hypothesis Validation Gate** - Manual 30-minute test: run ibuprofen LSD with 3 known 4J correlations removed; confirm aromatic ring solutions appear. Gates entire milestone. (completed 2026-03-16)
- [x] **Phase 66: LSDInputGenerator Extensions** - Add FORM, ELIM, SHIX/SHIH, and extended HMBC bond range emission to LSDInputGenerator; FORM/MULT consistency validator. (completed 2026-03-16)
- [ ] **Phase 67: PyLSDOrchestrator and SolutionMerger** - New Python classes: permutation file generation, N-fold LSD runner invocation, InChI-key deduplication of merged solutions.
- [ ] **Phase 68: Constraint Inventory v2 Schema** - Extend constraint inventory JSON schema with pylsd_mode, deferred_4j metadata; extend devils-advocate checklist with ELIM/FORM/MULT validation rules.
- [ ] **Phase 69: CLI Command and Regression Suite** - `lucy pylsd run` CLI subcommand; regression suite confirming existing `lucy lsd run` unchanged; FORM/LSD binary tolerance confirmed.
- [ ] **Phase 70: Agent Skill Updates** - lsd-engineer and case.md orchestrator skill updates with full pyLSD command reference, `; ELIM` annotation protocol, routing logic for pylsd_mode.
- [ ] **Phase 71: Ibuprofen CASE UAT** - End-to-end CASE run with pyLSD multi-run orchestration; ibuprofen aromatic ring structure at rank 1; milestone-complete gate.

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
**Plans:** 1/2 plans executed
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
**Plans:** TBD

### Phase 69: CLI Command and Regression Suite
**Goal:** `lucy pylsd run` is a working CLI command the agent can invoke; existing `lucy lsd run` behavior is regression-tested and confirmed unchanged; FORM/LSD binary compatibility is empirically confirmed
**Depends on:** Phase 66, Phase 67 (CLI is a thin wrapper over orchestrator + file format)
**Requirements:** CLI-01, CLI-02, CLI-03
**Success Criteria** (what must be TRUE):
  1. `lucy pylsd run compound.lsd` executes multi-run orchestration and prints ranked merged solutions to stdout (same format as `lucy lsd rank`)
  2. Running the same ibuprofen LSD file (without 4J annotations) through `lucy pylsd run` produces the same solution set as `lucy lsd run` — regression confirmed
  3. `lucy lsd run` with a file containing a `FORM` line behaves the same as without it — LSD binary tolerance of unknown commands confirmed; result documented in a findings note
  4. `lucy lsd rank` operates unchanged on `merged.smi` output — two-tier ranking (match count primary, MAE secondary) is the post-merge ranker
**Plans:** TBD

### Phase 70: Agent Skill Updates
**Goal:** lsd-engineer knows the full pyLSD command vocabulary and writes `; ELIM`-annotated HMBC lines for suspect 4J correlations; case.md orchestrator routes to `lucy pylsd run` when pylsd_mode is active
**Depends on:** Phase 68 (schema must be defined), Phase 69 (CLI must exist and be validated)
**Requirements:** AGT-01, AGT-02, AGT-03, AGT-04
**Success Criteria** (what must be TRUE):
  1. lsd-engineer skill contains explicit, unambiguous FORM/ELIM/SHIX/SHIH command reference with the exact LSD syntax; `HMBC X Y 2 4` listed as the correct 4J mechanism
  2. lsd-engineer skill includes the `; ELIM` annotation rule: any HMBC correlation flagged as 4J suspect by nmr-chemist is written as `HMBC X Y ; ELIM` (not removed), so PyLSDOrchestrator can parse it
  3. case.md orchestrator skill includes routing decision: when constraint inventory contains `pylsd_mode: true`, use `lucy pylsd run`; when false, use `lucy lsd run`
  4. devils-advocate checklist includes: verify `pylsd_mode` flag is set when any `; ELIM` annotations exist, verify permutation count <= 8 before approving run
**Plans:** TBD

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

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 65. Hypothesis Validation Gate | 1/1 | Complete    | 2026-03-16 |
| 66. LSDInputGenerator Extensions | 2/2 | Complete    | 2026-03-16 |
| 67. PyLSDOrchestrator and SolutionMerger | 1/2 | In Progress|  |
| 68. Constraint Inventory v2 Schema | 0/1 | Not started | - |
| 69. CLI Command and Regression Suite | 0/1 | Not started | - |
| 70. Agent Skill Updates | 0/1 | Not started | - |
| 71. Ibuprofen CASE UAT | 0/1 | Not started | - |

---
*Last updated: 2026-03-17 — Phase 67 planned (2 plans)*
