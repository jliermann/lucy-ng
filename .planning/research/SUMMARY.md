# Project Research Summary

**Project:** lucy-ng v8.0 — pyLSD Integration and 4J HMBC Exploration
**Domain:** Computer-Assisted Structure Elucidation (CASE) — LSD solver extension for 4J HMBC handling
**Researched:** 2026-03-13
**Confidence:** HIGH

## Executive Summary

The v8.0 milestone solves the root cause of the ibuprofen CASE failure (v4.0 UAT): three HMBC correlations through the aromatic ring are 4-bond (4J) couplings, but the LSD solver enforces them as 2-3J, producing wrong ring systems. The solution is pyLSD-based multi-run orchestration with per-correlation extended bond ranges (`HMBC X Y 2 4`) — the solver explores all valid bond distance configurations rather than the agent having to manually decide which correlations to drop. This is the approach used by Sherlock (the only published system to solve this problem), validated by the Wenk thesis with a complete ibuprofen worked example.

The recommended architecture builds on top of the existing stack without replacing anything. pyLSD is not a new binary to install — it is a file format superset and a Python multi-run driver. The critical architectural finding is that lucy-ng should implement the multi-run permutation logic directly in Python (`PyLSDOrchestrator` + `SolutionMerger`) rather than calling pyLSD as a subprocess. pyLSD-a8 is not pip-installable, has hardcoded paths, and includes an nmrshiftdb2 ranker that conflicts with lucy-ng's HOSE-based ranking. The LSD binary already supports the `ELIM` command natively; the only new capabilities needed are (1) per-correlation extended HMBC bond range syntax and (2) permutation orchestration over suspect 4J correlations. Total new Python: ~230 lines across two new classes.

The critical risk is repeating the v7.0 failure: spending multiple phases building infrastructure before validating the core hypothesis. The hypothesis — that removing 4J suspect correlations from the LSD constraint set produces solutions containing the correct aromatic ring — must be validated manually on ibuprofen before any code is written. A 30-minute test with the existing LSD binary gates the entire roadmap. The v7.0 post-mortem is explicit on this: approach first, infrastructure second.

---

## Key Findings

### Recommended Stack

No new Python packages are required. The `PyLSDOrchestrator` class (~150 lines) and `SolutionMerger` class (~80 lines) implement the equivalent multi-run behavior directly using the existing `LSDRunner`, which already invokes the LSD binary. The existing HOSE-based ranking pipeline (`lucy lsd rank`) is preserved unchanged and applied to the merged solution pool. pyLSD-a8 should not be installed as a subprocess dependency.

**Core technologies (all existing):**
- `LSDRunner` (subprocess): calls LSD binary — extended by `PyLSDOrchestrator`, never replaced
- `LSDInputGenerator`: LSD file writer — extended with `emit_form()`, `emit_elim()`, extended HMBC bond range support, `; ELIM` annotation parsing
- `SolutionRanker` (HOSE-based): two-tier ranking (match count primary, MAE secondary) — applied to merged solutions; pyLSD's built-in nmrshiftdb2 ranking explicitly bypassed
- RDKit (already a dependency): used by `SolutionMerger` for InChI-key deduplication across runs

**New dependencies:** None.

### Expected Features

**Must have (v8.0 core — table stakes):**
- `LSDInputGenerator` extension: emit `FORM C13 H18 O2`, `PIEC 1`, `ELIM N M`, `SHIX atom shift`, `SHIH atom shift`, extended `HMBC X Y 2 4` bond range — without this, nothing else works
- `PyLSDOrchestrator`: parse `; ELIM`-annotated HMBC lines, generate permutation files (include/exclude each suspect correlation), run LSD via `LSDRunner` once per permutation, collect `.sol` files — core new machinery
- `SolutionMerger`: deduplicate SMILES from multiple runs using RDKit InChI keys, write `merged.smi` and `run_report.json` — required to prevent duplicate structures distorting ranking
- `lucy pylsd run` CLI command: thin wrapper over `PyLSDOrchestrator` — agent-facing interface for multi-run mode
- Constraint inventory v2 schema: add `pylsd_mode`, `elim_value`, `elim_annotated` fields to JSON block — devils-advocate verification gate
- lsd-engineer agent skill update: full pyLSD command reference (FORM, PIEC, ELIM semantics, `HMBC X Y 2 4` syntax, `; ELIM` annotation rule, constraint inventory v2) — highest-leverage single change
- case.md orchestrator skill update: route to `lucy pylsd run` when `pylsd_mode: true`, use `run_report.json` in CASE-PROGRESS.md
- UAT: ibuprofen CASE with pyLSD — only milestone-complete criterion that matters

**Should have (v8.x after ibuprofen validated):**
- `PROP` constraints from neighbourhood detection — translate `lucy detect neighbours` JSON output into `LIST`/`PROP` LSD constraints (currently advisory-only)
- `HETE`/`PROP` for heteroatom isolation — forbid heteroatom-heteroatom bonds by default
- Atom exchange for grouped signals — verify `HMBC (C1 C2) H` grouped syntax works correctly post-migration
- Multi-file 4J exploration (exhaustive 2^K subsets) — sequential runs for K≤3, cap at 3 suspects

**Defer to v9+:**
- Multi-fragment injection + pyLSD combined
- Multi-compound UAT (six test compounds with 4J risk)
- Parallel multi-run subprocess pool (only needed for K>4)
- pyLSD binary invocation as alternative execution path

### Architecture Approach

The architecture is additive: `PyLSDOrchestrator` wraps `LSDRunner` (calling it N times per permutation), `SolutionMerger` deduplicates SMILES by InChI key, and `lucy lsd rank` operates on `merged.smi` unchanged. The `; ELIM` comment in lsd-engineer-written files is the contract between agent reasoning and Python orchestration: the agent annotates which HMBC lines are suspect, Python generates and runs the permutations. This division preserves chemical reasoning in the agent layer and combinatorial execution in the Python layer. Confirmed by examining a real project pyLSD file (`C13H6O8_pyLSD_Michael.lsd`) showing `ELIM 4 4` and `HMBC X Y 3 4 ; ELIM` as the actual format.

**Major components:**
1. `LSDInputGenerator` (extended in `src/lucy_ng/lsd/generator.py`) — adds `emit_form()`, `emit_elim()`, extended HMBC bond range; all existing LSD output unchanged; backward compatible
2. `PyLSDOrchestrator` (new, `src/lucy_ng/lsd/pylsd_orchestrator.py`) — permutation file generation, N-fold `LSDRunner` invocation, solution collection, `run_report.json` output
3. `SolutionMerger` (new, `src/lucy_ng/lsd/solution_merger.py`) — InChI-key deduplication, `merged.smi` writer, fallback to SMILES comparison on InChI failure
4. `lucy pylsd run` CLI (new subcommand in `src/lucy_ng/cli/lsd.py`) — thin agent interface, preserves `lucy lsd run` unchanged
5. lsd-engineer agent skill (update) — writes constraint inventory v2 with pyLSD fields, annotates suspect HMBC with `; ELIM`
6. case.md orchestrator skill (update) — routes to `lucy pylsd run` when `pylsd_mode: true`

### Critical Pitfalls

1. **ELIM does not extend bond ranges — it drops correlations entirely.** `ELIM N M` allows LSD to discard up to N correlations entirely; it does NOT let correlations satisfy 4J paths. Use `HMBC X Y 2 4` (per-correlation explicit bond range) for 4J handling. Using ELIM for 4J silently drops genuine 4J connectivity, producing wrong structures that pass all checks. This is the single most dangerous semantic confusion in the entire v8.0 design.

2. **FORM/MULT mismatch causes zero solutions with no diagnostic.** If `FORM C13H18O2` is present but MULT defines 12 carbons (off-by-one typo), pyLSD generates zero LSD files — LSD is never called. The existing zero-solution diagnostic does not apply. Requires FORM/MULT atom-count consistency validation as a pre-run gate in the `PyLSDOrchestrator` and as a devils-advocate checklist item.

3. **Combinatorial explosion from ambiguous MULT hybridisation.** Without explicit sp2/sp3 in every MULT line, pyLSD enumerates all hybridisation combinations — 56,829 LSD files in the documented Caripyrin case (15+ hours). Always specify hybridisation explicitly; abort if >50 LSD files are generated.

4. **4J combination space grows exponentially without a cap.** For N suspect correlations, exhaustive exploration is 2^N runs. Cap at 3 suspects per run (max 8 combinations). Use sequential strategy (add back one at a time) for N>3. Abort after 8 runs without solution and escalate to diagnostic agent.

5. **Build-before-validate failure (v7.0 recurrence).** v7.0 spent 5 phases building infrastructure before discovering 100% false positive rate at calibration. Validate the core hypothesis manually on ibuprofen (run LSD with 3 suspect correlations removed — does it produce an aromatic ring solution?) before writing any v8.0 code. This is Phase 1 of the roadmap.

---

## Implications for Roadmap

### Phase 1: Manual Hypothesis Validation
**Rationale:** The entire v8.0 approach rests on one empirical claim: removing the 3 suspect 4J HMBC correlations (atoms 4↔8, 6↔9, 8↔4) from the ibuprofen LSD file produces solutions that include an aromatic ring. This must be confirmed before any code is written. The v7.0 post-mortem mandates approach validation before infrastructure.
**Delivers:** Go/no-go gate. A `validation_result.md` documenting: which correlations were removed, solution count, aromatic ring presence in top-ranked solution.
**Avoids:** Pitfall 5 (build-before-validate), entire v7.0 failure mode.
**No code required.** 30-minute manual test using existing `lucy lsd run` and `lucy lsd rank`.

### Phase 2: LSDInputGenerator Extensions (Wave 1, parallel-safe)
**Rationale:** Everything downstream depends on the file format being correct. This phase adds `FORM`, `ELIM N M`, `SHIX`, `SHIH`, and extended `HMBC X Y min max` emission as additive methods. No existing behavior changes. FORM/MULT consistency validator prevents Pitfall 2.
**Delivers:** `emit_form()`, `emit_elim()`, `parse_elim_annotations()` static methods; extended HMBC bond range field in `LSDCorrelation` model; `validate_pylsd_input()` pre-run consistency check. Unit tests for each.
**Avoids:** Pitfall 1 (per-correlation bond range is the documented 4J mechanism, not ELIM), Pitfall 2 (consistency validator).

### Phase 3: PyLSDOrchestrator and SolutionMerger (Wave 1, parallel-safe)
**Rationale:** Core new Python machinery, independent of CLI and agent updates. Builds on Phase 2's annotation-parsing. No agent changes needed for this phase.
**Delivers:** `PyLSDOrchestrator` (~150 lines) generating permutation .lsd files and running `LSDRunner` N times; `SolutionMerger` (~80 lines) with InChI-key deduplication; `run_report.json` format. Unit tests on mock LSD inputs.
**Uses:** `LSDRunner` (unchanged), RDKit InChI (existing dependency).
**Avoids:** Pitfall 3 (generated-file count abort guard: >50 files = abort), Pitfall 4 (K≤3 cap built into orchestrator), Pitfall 7 (pyLSD ranking bypassed — solutions always go through `lucy lsd rank`).

### Phase 4: Constraint Inventory v2 Schema (Wave 1, parallel-safe)
**Rationale:** Agent-facing metadata schema — independent of Python runtime. Must be defined before agent skill updates reference it. Devils-advocate verification gates on `pylsd_mode`, `elim_value`, `elim_annotated` fields.
**Delivers:** Updated constraint inventory JSON schema documented in agent skill files; devils-advocate checklist extended with ELIM/FORM/MULT validation rules; explicit semantic test: "ELIM is for artifact correlations, `HMBC X Y 2 4` is for 4J."
**Avoids:** Pitfall 7 (DA verifies `lucy lsd rank` is used post-merge, not pyLSD's built-in ranking).

### Phase 5: CLI Command and Regression Suite (Wave 2, depends on 2+3)
**Rationale:** `lucy pylsd run` is the agent-facing interface; it depends on Phase 2 (file format) and Phase 3 (orchestrator). Regression suite must run before agent integration to catch any behavioral regressions on existing test cases.
**Delivers:** `lucy pylsd run <file>` CLI subcommand; regression test: `ibuprofen.lsd` through pyLSD multi-run mode produces same solution set as direct `lucy lsd run` (before 4J-removal changes); `lucy lsd check` extended to report multi-run availability.
**Avoids:** Pitfall 5 (migration regression as blocking acceptance criterion). Also validates FORM command is harmlessly handled by LSD binary (MEDIUM confidence gap resolved here).

### Phase 6: Agent Skill Updates (Wave 2, depends on 4+5)
**Rationale:** lsd-engineer and case.md orchestrator skill updates come after Python infrastructure and CLI are validated — direct application of the v7.0 lesson. Agent updates for a non-viable approach waste skill-writing effort.
**Delivers:** lsd-engineer skill with full pyLSD command reference (FORM, PIEC, ELIM semantics, `HMBC X Y 2 4` syntax, `; ELIM` annotation rule, constraint inventory v2 fields, explicit ELIM-vs-bond-range disambiguation); case.md orchestrator routing rule for `pylsd_mode: true`; solution-analyst skill updated to reference `run_report.json`.
**Avoids:** Pitfall 1 (explicit ELIM distinction in skill), Pitfall 8 (deferral-only-after-zero-solution rule mandatory in skill).

### Phase 7: Ibuprofen CASE UAT (Wave 3, depends on 6)
**Rationale:** End-to-end validation that the full stack (Python infrastructure + agent skills + CLI) correctly solves the ibuprofen case. Milestone-complete criterion.
**Delivers:** CASE run producing ibuprofen as top-ranked solution with aromatic ring verified. CASE-PROGRESS.md documenting which permutation yielded the solution. `run_report.json` showing solution distribution across permutations.
**Gate:** Mark v8.0 complete only when ibuprofen SMILES with aromatic ring appears at rank #1.

### Phase Ordering Rationale

- Phase 1 before all others: hypothesis validation gates the entire approach. If the manual test fails, the roadmap changes before a single line of code is written.
- Phases 2, 3, 4 run in parallel (Wave 1): generator extension, orchestrator/merger, and constraint inventory schema have no dependencies on each other.
- Phase 5 depends on Phases 2 and 3: CLI requires both file format and orchestrator.
- Phase 6 depends on Phases 4 and 5: agents need both the schema and the CLI command to exist and be validated.
- Phase 7 depends on Phase 6: UAT requires all agent updates complete.

### Research Flags

Phases with well-documented patterns (skip research-phase):
- **Phase 2 (LSDInputGenerator extension):** LSD manual and Wenk thesis provide exact command syntax. FORM, ELIM, SHIX semantics are fully specified with command grammar. No additional research needed.
- **Phase 3 (PyLSDOrchestrator):** Design is clear; implementation is straightforward Python (permutation generation via `itertools.combinations`, subprocess calls via existing `LSDRunner`, InChI deduplication via RDKit). All APIs confirmed.
- **Phase 4 (Constraint inventory schema):** Additive to existing JSON schema. No research needed.

Phases that need targeted validation during execution:
- **Phase 1 (Hypothesis validation):** The result of this test is unknown. If ibuprofen does NOT produce an aromatic ring solution after 4J removal, deeper diagnosis is needed before continuing. This is the gating question of the entire milestone.
- **Phase 5 (Regression suite):** Whether `FORM` is harmlessly ignored by the LSD binary (MEDIUM confidence) must be confirmed in this phase before proceeding to agent integration. If LSD rejects FORM as an unknown command, the file format design changes.
- **Phase 7 (UAT):** Whether the devils-advocate ELIM-vs-bond-range verification correctly catches agent confusion in practice is untested. May require one iteration of skill refinement.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | No new dependencies. pyLSD architecture confirmed by GitHub repo, official docs, Wenk thesis, and real project email archive example file. LSD ELIM semantics confirmed by official manual. |
| Features | HIGH | MVP feature set derived directly from Wenk thesis §4.3 with complete ibuprofen pyLSD example. Sherlock is the reference implementation. All command syntax fully documented. |
| Architecture | HIGH | Examined existing `runner.py`, `generator.py`, `models.py`. New component sizes estimated from code review (~150 + ~80 lines). Real pyLSD file format confirmed by project email archive example (`C13H6O8_pyLSD_Michael.lsd`). `; ELIM` annotation already appears informally in `iteration_07/compound.lsd`. |
| Pitfalls | HIGH | ELIM semantics from LSD manual (authoritative). Combinatorial explosion figures from Wenk thesis (Caripyrin example: 56,829 LSD files). v7.0 failure documented in post-mortem. SMILES deduplication issue from confirmed RDKit InChI canonical behavior. |

**Overall confidence:** HIGH

### Gaps to Address

- **FORM command tolerated by LSD binary (MEDIUM confidence):** Documented as pyLSD-only, but whether `lsd` ignores unknown commands gracefully is not confirmed from official LSD docs. Must verify in Phase 5 regression before agents use FORM unconditionally. If LSD rejects FORM, it must be omitted from files passed to `LSDRunner` directly (only used in files passed to pyLSD mode).

- **Permutation count in practice for aromatic natural products:** Ibuprofen has 3-4 suspect 4J correlations (8-16 permutations). Larger aromatic natural products may flag 6+ suspects. The K≤3 cap in `PyLSDOrchestrator` and the sequential (not exhaustive) fallback strategy handle this architecturally, but the appropriate cap value should be reviewed after multi-compound UAT in v8.x.

- **SHIX interaction with python-level multi-run (no pyLSD):** The `PyLSDOrchestrator` calls LSD directly (not pyLSD), so SHIX lines in the LSD file affect only LSD's internal atom-equivalence detection, not pyLSD's ranking (which is not used). This is intentional but must be documented explicitly in the lsd-engineer skill to prevent confusion about why SHIX appears in files that don't go through pyLSD's ranking algorithm.

---

## Sources

### Primary (HIGH confidence)
- `background/wenk-thesis.txt` lines 2069–2268, 4640–4664, 5491–5625 — Complete pyLSD command reference, ibuprofen example with exact atom numbering, ELIM semantics, Caripyrin combinatorial explosion example (56,829 LSD files), default heteroatom MULT values (Table A16), Sherlock's Java ranking explicitly disabled in favour of HOSE
- [LSD Manual (nuzillard.github.io)](https://nuzillard.github.io/LSD/MANUAL_ENG.html) — ELIM `P1 P2` semantics ("eliminate up to P1 correlations through up to P2 bonds" — eliminates, does NOT extend), SHIX/SHIH native commands, DUPL semantics
- [PyLSD official site](https://nuzillard.github.io/PyLSD/) and [Installation](https://nuzillard.github.io/PyLSD/INSTALL.html) — Python 3 requirement from a8, Java optional (ranking only), three-directory structure, `python lsd.py FILE` invocation
- [GitHub: nuzillard/PyLSD](https://github.com/nuzillard/PyLSD) — confirmed distributions (pylsd-linux-a8.tar.gz, pylsd-windows-a8.zip), no 2024/2025 releases visible (a8 is latest)
- `data/nmrdata/active-lucy-ng-testprojects/CASE1/analysis/iteration_07/compound.lsd` — confirmed agents already write `; ELIM` annotations informally
- `src/lucy_ng/lsd/runner.py`, `generator.py`, `models.py` — existing component boundaries confirmed by direct code inspection

### Secondary (MEDIUM confidence)
- Real pyLSD file `/Users/steinbeck/Dropbox/Private/Mail/.../C13H6O8_pyLSD_Michael.lsd` (project email archive) — confirmed `ELIM 4 4` and `HMBC X Y 3 4 ; ELIM` annotation pattern as actual usage
- [Sherlock PMC paper (PMC9920390)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9920390/) — pyLSD as primary solver, built-in ranking disabled in favour of HOSE prediction
- [WebCocon 4J paper (PMC8398166)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8398166/) — 4J-Flag semantics, 1000x runtime explosion risk for uncapped 4J exploration
- [PyLSD HISTORY.html](https://nuzillard.github.io/PyLSD/HISTORY.html) — a5 bug: two-letter atomic symbols (Cl, Br) not accepted in MULT

### Tertiary (project post-mortem)
- `.planning/milestones/v7.0-ROADMAP.md` — v7.0 failure (100% false positive rate, statistical 4J abandoned after 5 phases of infrastructure)
- `.planning/PROJECT.md` — v4.0 UAT findings (three 4J correlations identified: C4a↔C6, C5a↔C7, exact atom indices documented)

---
*Research completed: 2026-03-13*
*Ready for roadmap: yes*
*Next step: gsd-roadmapper agent uses this SUMMARY.md to structure v8.0 milestone roadmap*
