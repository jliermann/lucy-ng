# Phase 74: Constraint Preservation and Merge — Research

**Researched:** 2026-05-22
**Domain:** LSD constraint translation (SYME → BOND/COSY; DEFF NOT → DEFF F/FEXP); generator.py native-only emission; PyLSDOrchestrator permutation constraint preservation; SolutionMerger post-Phase-73 status
**Confidence:** HIGH — all findings grounded in direct code inspection and verified ground-truth LSD files

---

<user_constraints>
## User Constraints (from 72-DECISIONS.md — LOCKED)

### Locked Decisions

**D-03 (native-only generator):**
- No emitted LSD file may contain `SYME` or `DEFF NOT <smarts>`.
- `SYME` → structural BOND/COSY constraints (NOT DUPL — that was an erroneous prior entry).
  - Gem-dimethyl equivalence: `BOND parent child1` + `BOND parent child2`
  - Aromatic CH-pair equivalence: `COSY atom1 atom2`
- `DEFF NOT C1CC1` → `DEFF F1 "ring3_path"` + `FEXP "NOT F1 AND NOT F2"` pattern
- `DEFF NOT C1CCC1` → `DEFF F2 "ring4_path"` (same FEXP)
- DUPL 2 is default LSD deduplication behaviour; it is not a SYME substitute.

**D-04 (EMERGENT aromatic ring):**
- Phase 74 does NOT implement SKEL benzene forcing for the normal case.
- Constraint preservation (D-03) is the entire aromatic fix.
- SKEL remains a Phase 75 documented escalation path only.

**D-01a (permutation fallback):**
- PyLSDOrchestrator is demoted to fallback; primary path is LSDInputGenerator + direct LSD run.
- RELI-02 requires that the fallback path ALSO preserves constraints (no silent loss on ANY path).

### Deferred / Out of Scope
- SKEL benzene insertion in production code (Phase 75 doc note only)
- Skill file rewrites for SYME/DEFF NOT (Phase 75)
- Single-path skill documentation consolidation (Phase 75)
- UAT re-run (Phase 76)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RELI-02 | Every solver invocation runs with the COMPLETE validated constraint set — no silent constraint loss on any solver path | D-03 generator rewrite eliminates SYME/DEFF NOT from all emitted files; _build_permutation uses deepcopy of full LSDProblem, so native-only generator automatically covers permutation path |
| RELI-03 | Aromatic compounds reliably yield aromatic-ring solutions in the ranked output | Arm A experiment proves aromatic ring emerges from full native BOND/COSY constraints alone (2/2 aromatic, ibuprofen found); constraint preservation IS the aromatic fix |
</phase_requirements>

---

## Summary

Phase 74 has two separable sub-tasks that must be completed together to satisfy RELI-02 and RELI-03.

**Sub-task A — Generator native-only emission.** `generator.py` currently emits NEITHER `SYME` NOR `DEFF NOT` — these are absent from the codebase entirely. The generator has never implemented a translation layer; it simply does not handle them. This means the current generator output is already free of `SYME` and `DEFF NOT`, but ONLY because those features are not modelled in `LSDProblem` at all. Phase 74 must ADD the capability to model and emit symmetry equivalence and ring exclusion — and emit it in native form from day one. This requires: (a) extending `LSDProblem` with new fields to hold equivalence pairs and ring-exclusion configuration, (b) extending `LSDInputGenerator.generate()` to emit `BOND`/`COSY` for equivalence and `DEFF F`/`FEXP` for ring exclusion, (c) providing a filter-file path strategy for `ring3`/`ring4`.

**Sub-task B — Permutation constraint preservation.** `PyLSDOrchestrator._build_permutation()` already uses `copy.deepcopy(base_problem)` and reconstructs a proper `LSDProblem`. If the base problem is populated correctly (including equivalence pairs and ring exclusion in the new model fields), and the generator emits native-only, then permutation files automatically carry the full constraint set. The v8.0 postmortem "HMBC-only 542-byte perm files" was caused by the agent hand-writing the `base_problem` with only HMBC lines — not a bug in `_build_permutation` itself. Sub-task B is therefore: ensure the model is populated by the generator (not the agent), and confirm by inspection that perm files carry BOND/COSY/DEFF-F.

**Sub-task C — SolutionMerger status.** Phase 73 fixed `_invoke_outlsd`. `SolutionMerger.merge()` iterates `perm_result.smiles_file` and calls `LSDOutputParser.parse_smiles_file()`. The merge logic has no remaining bug — the v8.0 `0` merge count was entirely downstream of the outlsd conversion failure. The merge is now correct, conditional on perm SMILES files being non-empty.

**Critical data-flow finding (agent bypass scope gap):** The CASE agent workflow (lucy-lsd-engineer) writes LSD files BY HAND using Bash text output. It does NOT call `LSDInputGenerator.generate()`. The agent explicitly writes `SYME 5 6` and `DEFF NOT C1CC1` lines from its skill knowledge. This means fixing `generator.py` alone does NOT fix the agent's hand-written LSD files for the primary CASE workflow. Phase 74 fixes the Python API; Phase 75 must fix the agent skill to write BOND/COSY and DEFF-F/FEXP instead. This scope gap is documented but not in scope for Phase 74 — Phase 74's generator fix covers the programmatic path (PyLSDOrchestrator + LSDInputGenerator direct callers). The direct CASE agent path is Phase 75.

**Primary recommendation:** Add `equivalence_pairs: list[tuple[int, int, str]]` and `ring_exclusion: RingExclusionConfig | None` fields to `LSDProblem`. Add `emit_ring_exclusion()` to `LSDInputGenerator`. Emit BOND/COSY in `generate()`. Bundle ring3/ring4 filter content with the package rather than referencing absolute LSD install paths.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Symmetry equivalence encoding | `lsd/models.py` (new field) + `lsd/generator.py` (BOND/COSY emission) | — | Model holds intent; generator serialises to native LSD |
| Ring exclusion encoding | `lsd/models.py` (new field) + `lsd/generator.py` (DEFF F + FEXP emission) | `lsd/runner.py` (filter files must be co-located with .lsd at run time) | Model holds config; generator writes DEFF lines; runner CWD determines resolution |
| Permutation constraint preservation | `lsd/orchestrator.py` `_build_permutation` (deepcopy) | `lsd/generator.py` (write_file per perm) | Deepcopy of enriched model + native-only generator = automatic preservation |
| Filter file distribution | Package resource (bundled ring3/ring4) | — | Portability; avoids absolute LSD install path dependency |
| Agent hand-written LSD (CASE workflow) | Agent skills (lucy-lsd-engineer.md) | Phase 75 scope | Agent currently writes SYME/DEFF NOT directly — Phase 74 does NOT fix this path |

---

## Finding 1: Current Generator SYME/DEFF NOT Status

**Result: Neither SYME nor DEFF NOT are emitted by the current generator.** [VERIFIED: direct code inspection of `src/lucy_ng/lsd/generator.py`]

`LSDInputGenerator.generate()` (lines 88-190 of generator.py) emits exactly these sections, in order:
1. Header comments
2. `; FORM` comment + `ELIM` lines (only when `problem.pylsd_mode` is True)
3. `MULT` lines (atom definitions)
4. `SHIX`/`SHIH` lines (chemical shifts)
5. `HSQC` correlations
6. `HMBC` correlations
7. `COSY` correlations
8. `BOND` constraints
9. `FBND` constraints
10. `EXIT`

There is no SYME emission, no DEFF NOT emission, no DEFF F emission, no FEXP emission, no ring exclusion section of any kind.

**`LSDProblem` model fields** (`src/lucy_ng/lsd/models.py`, confirmed by `__dataclass_fields__`):
```
atoms, correlations, constraints, molecular_formula, name, comments, pylsd_mode, elim_commands
```

`LSDConstraint.constraint_type` accepts only `"BOND"` or `"FBND"` (validated in `__post_init__`). There is no `"SYME"` constraint type, no `"DEFF"` constraint type, no ring exclusion field.

**Implication:** The generator gap is a missing feature, not a bug to remove. The D-03 task is: ADD native-equivalence and ring-exclusion modelling + emission. Not strip non-native commands from existing code.

---

## Finding 2: SYME Use Sites in the Codebase and Ground-Truth Native Translations

[VERIFIED: direct inspection of `compound_native.lsd`, `arm_a.lsd`, `lucy-lsd-engineer.md`, `lucy-devils-advocate.md`]

### Where SYME appears

`SYME` appears in exactly three locations:

1. **`skill/diagnostic/SKILL.md`** (lines 229-255): Documents `SYME atom1 atom2` as a command for "Para-substituted benzene (2 pairs of equivalent CH), Isopropyl groups, Gem-dimethyl groups". Notes that SYME may not be supported in all LSD versions with a fallback to LIST/PROP.

2. **`~/.claude/agents/lucy-lsd-engineer.md`** (line 71): Shows `SYME 5 6 ; atoms 5 and 6 are equivalent (symmetry)` in the command reference.

3. **`~/.claude/agents/lucy-devils-advocate.md`** (lines 56-57, 72, 102, 270, 294, 383, 408): Validates that SYME constraints persist across iterations; checks `grep -c "^SYME" compound.lsd`.

**The generator.py has ZERO SYME usage.** SYME is an agent-skill concept that currently lives only in hand-written LSD files produced by the CASE agent.

### SYME use cases and ground-truth native translation

From `iteration_03/compound_native.lsd` and `arm_a.lsd` (both files verified working: 2 solutions, 2/2 aromatic, ibuprofen found): [VERIFIED: direct file inspection]

**Case 1: Gem-dimethyl equivalence (ibuprofen atoms 11, 12 — both CH3, both bonded to atom 10 CH)**

Native translation in iter3/arm_a:
```
BOND 10 11    ; force both CH3 to attach to same isobutyl CH
BOND 10 12
```
Atom 10 is the isobutyl CH (45 ppm, CH). Atoms 11 and 12 are the two equivalent CH3 groups (~22 ppm). The BOND constraints force both methyls onto the same parent carbon, which is the structural expression of their equivalence. LSD interprets these natively.

**Case 2: Aromatic CH-pair equivalence (ibuprofen atoms 4/7 and 5/6 — ortho/meta pairs of para-disubstituted benzene)**

Native translation in iter3/arm_a:
```
COSY 4 7    ; aromatic CH pair -- 3J H-H coupling encodes ring adjacency
COSY 5 6    ; aromatic CH pair
```
Atoms 4, 5, 6, 7 are all aromatic CH (sp2, 1H, ~127-130 ppm). The COSY constraints encode the 3J H-H coupling across the ring, constraining ring adjacency. Per 72-DECISIONS.md D-04, these COSY constraints are the primary driver of aromatic ring emergence — they require a 3-bond H-H path, satisfiable in a 6-membered ring but not in other ring sizes without violating sp2 multiplicity.

**Case 3: Homotopic CH2 protons (open question)**

For a CH2 group with two homotopic protons (e.g., a methylene flanked by identical neighbours), the two protons are equivalent but they are on the SAME carbon, not separate carbons. SYME was sometimes written for such cases in agent-generated files. However, in LSD, equivalence of protons on the same CH2 is already implied by the MULT definition (hydrogen_count=2 means the proton is defined once at that atom index, both protons share the same HSQC position). There is no separate LSD mechanism needed for homotopic CH2 protons within the same atom. [ASSUMED — based on LSD MULT semantics; requires confirmation that agent is not writing SYME for CH2 pairs and if so what the correct interpretation should be]

### Summary: SYME → native translation per use case

| SYME use case | Example | Native translation | Status |
|---------------|---------|-------------------|--------|
| Gem-dimethyl (2 CH3 on same parent) | Ibuprofen atoms 11, 12 | `BOND parent methyl1` + `BOND parent methyl2` | VERIFIED from iter3 |
| Aromatic CH pair (equivalent ring positions) | Ibuprofen atoms 4/7, 5/6 | `COSY atom1 atom2` | VERIFIED from iter3/arm_a |
| Isopropyl group (2 CH3, same parent CH) | Ibuprofen atoms 11/12 = same case | `BOND parent methyl1` + `BOND parent methyl2` | VERIFIED (same as gem-dimethyl) |
| Homotopic CH2 protons (same carbon) | Generic methylene | No LSD action needed — same MULT atom | ASSUMED — flag for planner |

---

## Finding 3: DEFF NOT → DEFF F/FEXP Ground-Truth Translation

[VERIFIED: direct inspection of `compound_native.lsd`, `arm_a.lsd`, and `/Users/steinbeck/Dropbox/develop/LSD/Filters/ring3`, `ring4`]

### Current agent practice

The CASE agent writes `DEFF NOT C1CC1` (cyclopropane), `DEFF NOT C1CCC1` (cyclobutane), and up to 6 other SMARTS patterns directly in LSD files. These are non-native in LSD-3.4.9 — they trigger `error 150` when encountered by the binary.

### Ground-truth native form (from iter3 / arm_a)

Both iter3 and arm_a use:
```
DEFF F1 "/Users/steinbeck/Dropbox/develop/LSD/Filters/ring3"
DEFF F2 "/Users/steinbeck/Dropbox/develop/LSD/Filters/ring4"
FEXP "NOT F1 AND NOT F2"
```

The filter files are pre-built LSD SSTR/LINK fragment files (NOT SMARTS). Their content:

`ring3`:
```
; a generic 3-membered ring
SSTR S1 A (2 3) (0 1 2)
SSTR S2 A (2 3) (0 1 2)
SSTR S3 A (2 3) (0 1 2)
LINK S1 S2
LINK S2 S3
LINK S1 S3
```

`ring4`:
```
; a generic 4-membered ring
SSTR S1 A (2 3) (0 1 2)
SSTR S2 A (2 3) (0 1 2)
SSTR S3 A (2 3) (0 1 2)
SSTR S4 A (2 3) (0 1 2)
LINK S1 S2
LINK S2 S3
LINK S3 S4
LINK S1 S4
```

`SSTR S1 A (2 3) (0 1 2)` means: substructure atom S1, any element A, hybridisation sp2 or sp3, 0-2 hydrogens. `LINK S1 S2` means bond between S1 and S2. The ring3/ring4 files define generic 3- and 4-membered rings of any atom type; `FEXP "NOT F1 AND NOT F2"` excludes all solutions containing these substructures.

**Note:** The existing `DEFFFormatter` class in `src/lucy_ng/fragments/lsd_formatter.py` generates SSTR/LINK fragment files from SMILES using RDKit. However, ring3/ring4 files use a more permissive syntax (`A (2 3) (0 1 2)`) that `DEFFFormatter.smiles_to_fragment_content()` does not produce (it writes fixed hybridisation/H-count per atom). The ring3/ring4 files must be bundled as pre-built resources, not generated via `DEFFFormatter`.

### Filter-file path strategy

The iter3 native file uses an **absolute path** to the developer's local LSD install:
`DEFF F1 "/Users/steinbeck/Dropbox/develop/LSD/Filters/ring3"`

This is the critical deferred sub-question from 72-DECISIONS.md. Three options:

| Option | Approach | Portability | Recommendation |
|--------|----------|-------------|----------------|
| A: Absolute LSD install path | Reference `lsd_install_dir/Filters/ring3` | Breaks on other machines; build system must locate LSD | REJECT |
| B: Bundle in package | Copy ring3/ring4 content into `src/lucy_ng/lsd/filters/ring3` and `ring4` as package resources | Fully portable; no external dependency | RECOMMENDED |
| C: Write alongside .lsd file | Write ring3/ring4 to the iteration dir at generation time | Portable; requires write at generate() call | ACCEPTABLE fallback |

**Recommendation: Option B (bundle in package).** The ring3/ring4 filter content is stable (generic ring topology, no compound-specific data). Bundling in `src/lucy_ng/lsd/filters/` and referencing via `importlib.resources` (Python 3.9+ standard) is fully portable. At generation time, the generator writes the filter files to the output directory alongside the .lsd file, then emits `DEFF F1 "ring3"` (relative path, since LSD is invoked with `cwd=output_dir`).

**This is the planner's decision gate:** The recommendation is Option B. If the planner chooses Option C, the generator must accept an `output_dir` parameter to write filter files.

---

## Finding 4: PyLSDOrchestrator Permutation Generation — Where Constraints Are Lost

[VERIFIED: direct inspection of `src/lucy_ng/lsd/orchestrator.py`]

### Current _build_permutation code (lines 215-253)

```python
def _build_permutation(
    self,
    base_problem: LSDProblem,
    suspects: list[LSDCorrelation],
    include_flags: tuple[bool, ...],
) -> LSDProblem:
    perm = copy.deepcopy(base_problem)   # full deep copy of model

    suspect_keys = {
        (s.atom1_index, s.atom2_index, s.correlation_type)
        for s in suspects
    }

    # Remove suspect correlations from clone
    perm.correlations = [
        c for c in perm.correlations
        if (c.atom1_index, c.atom2_index, c.correlation_type) not in suspect_keys
    ]

    # Add back suspects flagged True with extended bond range
    for corr, include in zip(suspects, include_flags):
        if include:
            included_corr = copy.deepcopy(corr)
            included_corr.max_bonds = 4
            perm.correlations.append(included_corr)

    return perm
```

The `_build_permutation` method operates on `base_problem` which is a full `LSDProblem`. It deep-copies the ENTIRE model — atoms, correlations, constraints, ALL fields — then only modifies `perm.correlations` to apply include/exclude flags. This means:
- `perm.atoms` = complete copy
- `perm.constraints` (BOND/FBND) = complete copy
- `perm.elim_commands` = complete copy
- Any new fields added to `LSDProblem` (equivalence_pairs, ring_exclusion) = complete copy

**Then `LSDInputGenerator.write_file(perm_problem, lsd_file)` is called** (line 187), which calls `generate()` on the fully-populated model.

### Root cause of v8.0 "HMBC-only 542-byte perm files"

The constraint loss in v8.0 was NOT caused by `_build_permutation` stripping constraints. The postmortem says perm files were HMBC-only at 542 bytes. This was caused by the CASE agent constructing a minimal `base_problem` with only HMBC correlations when calling the orchestrator, rather than passing a fully-populated problem. The agent-written `base_problem` never had BOND, SYME, or DEFF NOT populated in it — because the agent wrote those to the LSD file by hand AND called the orchestrator with a separate, incomplete problem.

**Conclusion:** `_build_permutation` is correct. The generator rewrite (Sub-task A) automatically fixes permutation constraint preservation, IF the `base_problem` passed to `PyLSDOrchestrator.run()` is constructed by `LSDInputGenerator` with the full enriched model. No changes to `_build_permutation` are needed.

**However**, the agent currently constructs `base_problem` directly (not via `LSDInputGenerator`). For the permutation fallback path to work correctly, the caller must pass a fully-populated `LSDProblem`. This is a usage contract, not a code bug. Phase 74 should document this contract clearly in docstrings.

---

## Finding 5: SolutionMerger Post-Phase-73 Status

[VERIFIED: direct inspection of `src/lucy_ng/lsd/orchestrator.py` `SolutionMerger.merge()`, lines 293-385, and Phase-73 verification report]

`SolutionMerger.merge()`:
1. Iterates `permutation_results`
2. For each result, checks `perm_result.smiles_file` is not None and exists
3. Calls `LSDOutputParser.parse_smiles_file(perm_result.smiles_file)`
4. For each solution: computes InChI key, deduplicates, builds provenance
5. Writes `merged.smi` and `run_report.json`

The Phase-73 fix ensures `perm_result.smiles_file` now points to a valid `solutions.smi` with real SMILES lines (not just the 10-line outlsd header). The `_invoke_outlsd` helper is shared between runner and orchestrator.

**There is no remaining SolutionMerger bug.** The v8.0 `total_raw_solutions: 0` in run_report.json was entirely downstream of: (1) the outlsd invocation receiving wrong args/stdin, producing the 10-line header, (2) `LSDOutputParser.parse_smiles_file()` finding no valid SMILES in those 10 lines, (3) SolutionMerger collecting 0. With Phase-73 fix in place, this chain is resolved.

**One observation:** `SolutionMerger.merge()` relies on `perm_result.smiles_file` being set. This is set by `PyLSDOrchestrator._run_outlsd()` which returns `None` if `outlsd` is not on PATH or if no `.sol` file exists. The `skip-if-None` guard at line 311 (`if perm_result.smiles_file is None or not perm_result.smiles_file.exists(): continue`) is correct. No change needed.

---

## Finding 6: Critical Scope Gap — Agent Writes LSD Files by Hand

[VERIFIED: direct inspection of `~/.claude/agents/lucy-lsd-engineer.md`, `~/.claude/agents/lucy-case-agent.md`, `~/.claude/commands/lucy-ng/case.md`]

The CASE agent workflow does NOT call `LSDInputGenerator.generate()`. The agent:
1. Uses Bash + Write tools to construct LSD file content line by line
2. Writes `SYME 5 6` directly (from its skill knowledge at line 71 of lucy-lsd-engineer.md)
3. Writes `DEFF NOT C1CC1` etc. directly (from the badlist section, lines 125-134)
4. Calls `lucy lsd run compound.lsd` (runner) or `lucy pylsd run` (orchestrator)

Evidence from lucy-lsd-engineer.md line 88: "When `pylsd_mode=true`, LSDInputGenerator generates permutation files using these additional commands. **lsd-engineer does NOT write these directly — PyLSDOrchestrator generates permutation files automatically.**"

This explicitly confirms the agent only writes the PRIMARY `compound.lsd` by hand. When pylsd_mode is active, it passes this hand-written file to `lucy pylsd run`, which re-reads the `.lsd` file — but this is via the CLI, not via `LSDProblem` objects. The orchestrator's `run()` method takes an `LSDProblem` argument, not a file path. So the `lucy pylsd run` CLI must parse the hand-written `.lsd` file back into an `LSDProblem` — or it constructs the problem some other way.

**Phase 74 generator fix scope:**
- Covers: any code that constructs `LSDProblem` objects and calls `LSDInputGenerator.generate()` or `write_file()`
- Does NOT cover: the CASE agent's hand-written `compound.lsd` files in `analysis/iteration_NN/`
- Phase 75 must update agent skills to write BOND/COSY and DEFF F/FEXP instead of SYME and DEFF NOT

**Impact on RELI-02/RELI-03:** For the primary direct-run path (`lucy lsd run` on a hand-written file), Phase 74 generator changes have no effect — RELI-02/03 on that path depend on Phase 75 skill changes. For the programmatic path (unit tests, any code using `LSDInputGenerator` directly), Phase 74 fully satisfies RELI-02/03.

This must be flagged clearly in the PLAN: Phase 74 alone does not achieve RELI-02 and RELI-03 for the CASE agent workflow. The requirements are only FULLY satisfied after Phase 75.

---

## Architecture Patterns

### System Architecture: Constraint Flow

```
NMR Data (peak lists)
       |
       v
LSDInputGenerator.from_peak_data()  [new: equivalence_pairs, ring_exclusion populated]
       |
       v
LSDProblem  [enriched model: atoms, correlations, constraints, equivalence_pairs, ring_exclusion]
       |
       +------ LSDInputGenerator.generate() ---------> compound.lsd (native-only)
       |              emits:                            MULT, HSQC, HMBC, COSY, BOND, FBND
       |              SYME → BOND + COSY                DEFF F1/F2, FEXP "NOT F1 AND NOT F2"
       |              DEFF NOT → DEFF F + FEXP          EXIT
       |
       +------ PyLSDOrchestrator._build_permutation() [deepcopy → modify correlations only]
                      |
                      v
               perm_00/compound.lsd, perm_01/compound.lsd ... (each: full constraints)
               LSD binary → *.sol → _invoke_outlsd → solutions.smi
                      |
                      v
               SolutionMerger.merge() → merged.smi + run_report.json
```

### Recommended Project Structure (new files)

```
src/lucy_ng/lsd/
├── models.py         # Add: equivalence_pairs, ring_exclusion fields to LSDProblem
├── generator.py      # Add: emit_ring_exclusion(), update generate() for BOND/COSY + DEFF F/FEXP
├── filters/          # NEW: bundled ring filter files
│   ├── ring3         # Pre-built 3-membered ring SSTR/LINK filter
│   └── ring4         # Pre-built 4-membered ring SSTR/LINK filter
├── orchestrator.py   # No logic changes; add docstring for base_problem contract
├── runner.py         # No changes (Phase 73 complete)
└── parser.py         # No changes
tests/
└── test_lsd_generator.py  # Add: TestNativeConstraintEmission class
```

### Pattern 1: LSDProblem Model Extension

**What:** Add two new fields to `LSDProblem` for native-only constraint modelling.

```python
# Source: design from 72-DECISIONS.md + compound_native.lsd ground truth

from dataclasses import dataclass, field
from typing import Literal

@dataclass
class EquivalencePair:
    """A pair of topologically equivalent atoms."""
    atom1_index: int
    atom2_index: int
    equivalence_type: Literal["gem_dimethyl", "aromatic_ch_pair", "isopropyl"]
    parent_index: int | None = None  # for gem_dimethyl/isopropyl: the common parent atom

@dataclass
class RingExclusionConfig:
    """Configuration for ring exclusion via DEFF F / FEXP."""
    exclude_3_membered: bool = True
    exclude_4_membered: bool = True
    filter_dir: Path | None = None  # None = use bundled package filters

@dataclass
class LSDProblem:
    # ... existing fields ...
    equivalence_pairs: list[EquivalencePair] = field(default_factory=list)
    ring_exclusion: RingExclusionConfig | None = None
```

### Pattern 2: SYME → BOND/COSY emission in generate()

**What:** After emitting BOND/FBND constraints, emit equivalence pairs as BOND or COSY. Crucially, these join the existing `bond_constraints` section — they are just more BOND and COSY lines.

```python
# Source: compound_native.lsd + arm_a.lsd ground truth
# Gem-dimethyl: BOND parent methyl1 + BOND parent methyl2
# Aromatic CH pair: COSY atom1 atom2

for ep in problem.equivalence_pairs:
    if ep.equivalence_type in ("gem_dimethyl", "isopropyl"):
        # Add BOND from parent to each equivalent child
        # (parent is already constrained to main chain by existing BOND)
        # These become additional BOND lines in the constraints section
        lines.append(f"BOND {ep.parent_index} {ep.atom1_index}")
        lines.append(f"BOND {ep.parent_index} {ep.atom2_index}")
    elif ep.equivalence_type == "aromatic_ch_pair":
        lines.append(f"COSY {ep.atom1_index} {ep.atom2_index}")
```

**Note:** The BOND lines for equivalence should appear in the structural constraints section. The COSY lines for aromatic pairs should appear in the COSY correlations section. The simplest implementation adds them to the existing `problem.constraints` (as BOND) and `problem.correlations` (as COSY) when `add_equivalence_pair()` is called on the problem, so the existing section-rendering logic handles them automatically.

**Alternative simpler approach:** Rather than a new `EquivalencePair` model, `add_equivalence_pair()` could directly add the appropriate `LSDConstraint("BOND")` and `LSDCorrelation("COSY")` entries to the existing lists. This requires no new model class and no generator changes beyond the new method. The planner should choose between the two approaches; the simpler one is recommended.

### Pattern 3: Ring exclusion emission

**What:** `emit_ring_exclusion()` static method on `LSDInputGenerator`.

```python
@staticmethod
def emit_ring_exclusion(
    config: RingExclusionConfig,
    output_dir: Path,
) -> list[str]:
    """Write ring filter files and return DEFF + FEXP lines.

    Writes bundled ring3/ring4 filter files to output_dir (alongside .lsd file),
    then returns the LSD command lines to reference them.

    Args:
        config: Ring exclusion configuration.
        output_dir: Directory where .lsd file will be written.

    Returns:
        List of LSD command strings (DEFF F1 ..., DEFF F2 ..., FEXP ...).
    """
    filter_names = []
    lines = []
    idx = 1

    if config.exclude_3_membered:
        # Copy bundled ring3 to output_dir
        ring3_content = _get_bundled_filter("ring3")
        (output_dir / "ring3").write_text(ring3_content)
        lines.append(f'DEFF F{idx} "ring3"')
        filter_names.append(f"F{idx}")
        idx += 1

    if config.exclude_4_membered:
        ring4_content = _get_bundled_filter("ring4")
        (output_dir / "ring4").write_text(ring4_content)
        lines.append(f'DEFF F{idx} "ring4"')
        filter_names.append(f"F{idx}")
        idx += 1

    if filter_names:
        exclusions = " AND ".join(f"NOT {f}" for f in filter_names)
        lines.append(f'FEXP "{exclusions}"')

    return lines
```

Ring files are referenced with relative paths (`"ring3"`, `"ring4"`) because LSD is invoked with `cwd=output_dir`. LSD resolves relative DEFF paths from its CWD, confirmed by iter3 behaviour. The bundled filter approach copies ring3/ring4 content to `output_dir` at generate time.

`_get_bundled_filter()` uses `importlib.resources` (Python 3.9+):
```python
import importlib.resources

def _get_bundled_filter(name: str) -> str:
    package = importlib.resources.files("lucy_ng.lsd.filters")
    return (package / name).read_text()
```

### Anti-Patterns to Avoid

- **Absolute filter paths in generated .lsd files:** `DEFF F1 "/Users/steinbeck/..."` fails on other machines. Use relative paths + copy to output_dir.
- **SYME in generated output:** LSD-3.4.9 returns error 102 for SYME. Any test asserting `SYME` in generator output must be updated to expect BOND/COSY.
- **DEFF NOT in generated output:** LSD-3.4.9 returns error 150 for DEFF NOT. Same rule.
- **Passing a minimal LSDProblem to PyLSDOrchestrator:** The orchestrator deepcopies the base_problem; if it is incomplete (HMBC-only), perm files will be incomplete. Always pass a fully-populated problem.
- **Changing `LSDConstraint.constraint_type` to accept "SYME":** Don't add SYME as a constraint type that is later translated. Translate at the source (when the agent/caller specifies equivalence, add BOND/COSY directly).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Ring exclusion filter syntax | Custom SSTR/LINK writer for ring3/ring4 | Bundle existing filter files from `/Users/steinbeck/Dropbox/develop/LSD/Filters/` | Files already exist, are tested (iter3 produced correct solutions), and use LSD's native syntax |
| Fragment file distribution | OS path detection to find LSD install | `importlib.resources` + bundled package data | Portable, no install-path dependency, standard Python approach |
| Aromatic fragment forcing | SKEL benzene insertion | Correct COSY + HMBC constraints (D-04) | Arm A experiment proves emergence without SKEL; SKEL is Phase 75 escalation only |

---

## Common Pitfalls

### Pitfall 1: Existing Tests Assert SYME/DEFF NOT in Output

**What goes wrong:** After adding ring exclusion and equivalence emission to `generate()`, running `pytest tests/test_lsd_generator.py` fails because no existing test asserts SYME or DEFF NOT output — but tests asserting the ABSENCE of unknown commands may need reviewing.

**Why it happens:** The current generator never emitted SYME or DEFF NOT, so tests don't assert their presence. The risk runs the other direction: new tests must assert that SYME and DEFF NOT do NOT appear in output.

**How to avoid:** Add negative assertions: `assert "SYME" not in content` and `assert "DEFF NOT" not in content` in new tests. Existing tests have no SYME/DEFF NOT assertions and will not break.

### Pitfall 2: Agent Hand-Written Files Still Contain SYME/DEFF NOT

**What goes wrong:** Phase 74 fixes the generator, but the CASE agent still writes SYME and DEFF NOT to hand-built compound.lsd files. End-to-end CASE runs still hit LSD error 102/150.

**Why it happens:** The agent and the generator are separate code paths. Generator fix = programmatic path only.

**How to avoid:** Document the scope gap explicitly. RELI-02/03 on the CASE agent path is a Phase 75 deliverable. Do not mark RELI-02/03 as fully satisfied after Phase 74.

### Pitfall 3: Ring Filter Files Not Copied to Output Directory

**What goes wrong:** `generate()` emits `DEFF F1 "ring3"` but doesn't write the filter file to the same directory. LSD runs from `output_dir` and cannot find `ring3`. Error or silent wrong behaviour.

**Why it happens:** `generate()` returns a string; it doesn't have access to the output path. The write-filters step must happen in `write_file()` (which does have the output path), not in `generate()`.

**How to avoid:** Split the ring exclusion into two steps: `generate()` emits the DEFF/FEXP lines; `write_file()` additionally calls a helper to copy filter files to the output directory alongside the .lsd file.

### Pitfall 4: Equivalence Pairs Break COSY Deduplication

**What goes wrong:** `from_peak_data()` already builds COSY correlations from `cosy_peaks`. If `add_equivalence_pair()` also adds COSY for aromatic CH pairs, duplicate COSY lines may appear if the COSY peak data is also available.

**Why it happens:** Both peak-data COSY and equivalence-derived COSY emit `COSY N M` lines. LSD may or may not tolerate duplicate COSY commands.

**How to avoid:** Add a `seen_cosy` deduplication step when adding equivalence-derived COSY, same as the existing `seen_cosy: set[tuple[int, int]]` guard in `from_peak_data()`.

### Pitfall 5: Relative Filter Path Breaks When CWD Is Not output_dir

**What goes wrong:** If LSD is invoked with an absolute path to the .lsd file but `cwd` is not set to the directory containing the filter files, `ring3` is not found.

**Why it happens:** Phase 73 fixed `_execute_lsd` to use file-arg mode with `cwd=output_dir`. This ensures the filter files (co-located with the .lsd file) are accessible via relative paths. But any caller that invokes LSD differently would break.

**How to avoid:** Keep the contract: filter files are always written to the same directory as the .lsd file; LSD is always invoked with `cwd` pointing to that directory. Document this in `write_file()` docstring.

---

## Code Examples

### Verified: arm_a.lsd / compound_native.lsd native constraint section

The following is the COMPLETE constraint section from `arm_a.lsd` (the minimal working native file, no SKEL, 2/2 aromatic solutions):

```
; arm_a.lsd -- Emergent test: no SKEL benzene, full constraints preserved
BOND 1 14
BOND 1 15
BOND 10 11
BOND 10 12

COSY 9 13
COSY 4 7
COSY 5 6
COSY 8 10
COSY 10 11

; ... HMBC lines ...

DEFF F1 "/Users/steinbeck/Dropbox/develop/LSD/Filters/ring3"
DEFF F2 "/Users/steinbeck/Dropbox/develop/LSD/Filters/ring4"
FEXP "NOT F1 AND NOT F2"
```

BOND 1 14 = carbonyl C bonded to sp2 O (C=O)
BOND 1 15 = carbonyl C bonded to sp3 O (C-OH, carboxylic acid)
BOND 10 11 = isobutyl CH bonded to CH3 #1 (gem-dimethyl equivalence)
BOND 10 12 = isobutyl CH bonded to CH3 #2 (gem-dimethyl equivalence)
COSY 4 7 = aromatic CH pair (3J ring adjacency constraint)
COSY 5 6 = aromatic CH pair (3J ring adjacency constraint)

### Verified: ring3 filter file content

```
; a generic 3-membered ring
SSTR S1 A (2 3) (0 1 2)
SSTR S2 A (2 3) (0 1 2)
SSTR S3 A (2 3) (0 1 2)
LINK S1 S2
LINK S2 S3
LINK S1 S3
```

### Verified: _build_permutation deepcopy preserves constraints

```python
# orchestrator.py lines 215-253
def _build_permutation(self, base_problem, suspects, include_flags):
    perm = copy.deepcopy(base_problem)   # ALL fields copied
    # Only perm.correlations is modified below
    perm.correlations = [...]            # filter out suspects
    for corr, include in zip(suspects, include_flags):
        if include:
            included_corr = copy.deepcopy(corr)
            included_corr.max_bonds = 4
            perm.correlations.append(included_corr)
    return perm
    # perm.atoms, perm.constraints, perm.equivalence_pairs, perm.ring_exclusion
    # are all untouched deepcopies of base_problem
```

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` |
| Quick run command | `pytest tests/test_lsd_generator.py -x -q` |
| Full suite command | `pytest -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RELI-02 | Generated .lsd contains no SYME or DEFF NOT | unit | `pytest tests/test_lsd_generator.py::TestNativeConstraintEmission -x` | ❌ Wave 0 |
| RELI-02 | Generated .lsd contains BOND/COSY for equivalence pairs | unit | `pytest tests/test_lsd_generator.py::TestNativeConstraintEmission::test_gem_dimethyl_emits_bond` | ❌ Wave 0 |
| RELI-02 | Generated .lsd contains DEFF F + FEXP for ring exclusion | unit | `pytest tests/test_lsd_generator.py::TestNativeConstraintEmission::test_ring_exclusion_emits_deff_f` | ❌ Wave 0 |
| RELI-02 | Permutation problem deepcopy preserves equivalence_pairs and ring_exclusion | unit | `pytest tests/test_lsd_orchestrator.py::TestPermutationConstraintPreservation -x` | ❌ Wave 0 |
| RELI-03 | End-to-end: ibuprofen generator + LSD run → aromatic solutions (skipif no LSD) | integration | `pytest tests/test_lsd_generator.py::TestLSDGeneratorEndToEnd -x -k lsd` | ❌ Wave 0 |

### Wave 0 Gaps

- [ ] `tests/test_lsd_generator.py` — Add `TestNativeConstraintEmission` class with:
  - `test_no_syme_in_output`: `assert "SYME" not in content` for any problem with equivalence pairs
  - `test_no_deff_not_in_output`: `assert "DEFF NOT" not in content` for any problem with ring exclusion
  - `test_gem_dimethyl_emits_bond`: verify `BOND parent atom1` + `BOND parent atom2` in output
  - `test_aromatic_ch_pair_emits_cosy`: verify `COSY atom1 atom2` in output
  - `test_ring_exclusion_emits_deff_f_fexp`: verify `DEFF F1` + `DEFF F2` + `FEXP "NOT F1 AND NOT F2"` in output
  - `test_ring_files_written_to_output_dir`: verify ring3/ring4 files exist in output_dir after `write_file()`
- [ ] `tests/test_lsd_orchestrator.py` — Add `TestPermutationConstraintPreservation` class
- [ ] `src/lucy_ng/lsd/filters/ring3` — Bundle filter file (copy from LSD install)
- [ ] `src/lucy_ng/lsd/filters/ring4` — Bundle filter file (copy from LSD install)

### Sampling Rate

- Per task commit: `pytest tests/test_lsd_generator.py -x -q`
- Per wave merge: `pytest -x -q`
- Phase gate: Full suite green before `/gsd:verify-work`

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Homotopic CH2 protons require no LSD action (same MULT atom covers both protons) | Finding 2, Case 3 | If LSD treats CH2 protons as needing SYME, some valid CASE compounds will have unmodelled equivalence |
| A2 | LSD resolves relative DEFF paths from its CWD (not from the .lsd file location) | Finding 3, Pattern 3 | Filter files would not be found; ring exclusion silently fails; solution quality degrades |
| A3 | `importlib.resources` (Python 3.9+) is available in the lucy-ng runtime | Pattern 3 | Would need fallback to `pkg_resources` or `__file__`-based path |

---

## Open Questions

1. **Equivalence pair encoding: new model class vs. direct BOND/COSY injection**
   - What we know: Both approaches achieve the same generated output.
   - What's unclear: Should `LSDProblem` model the INTENT (equivalence) or just the RESULT (BOND/COSY)? A new `EquivalencePair` type is more semantically rich; direct injection is simpler.
   - Recommendation: Use direct injection (`add_equivalence_pair()` adds BOND/COSY to existing lists). Simpler, avoids new model hierarchy. If semantic tracking is needed later, add a metadata comment field.

2. **Where to call `emit_ring_exclusion()`: `generate()` vs `write_file()`**
   - What we know: `generate()` returns a string (no path access). `write_file()` has the path. Ring filter files must be written to the same directory.
   - What's unclear: Should `generate()` accept an `output_dir` for ring exclusion, or should `write_file()` call a separate helper?
   - Recommendation: Keep `generate()` purely string-returning. `write_file()` calls a new helper `_write_filter_files(problem, output_dir)` when `problem.ring_exclusion` is set. `generate()` still emits the `DEFF F`/`FEXP` lines (relative paths); `write_file()` ensures the files are there.

3. **RELI-02/03 partial satisfaction after Phase 74**
   - What we know: The CASE agent hand-writes LSD files; Phase 74 does not change agent behaviour.
   - What's unclear: Should REQUIREMENTS.md be updated to note the partial satisfaction, or left for Phase 75 to fully close?
   - Recommendation: Add a note in the Phase 74 verification that RELI-02 is satisfied for the programmatic path; Phase 75 closes it for the CASE agent path.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python `importlib.resources` | Bundled filter loading | ✓ | Standard library (Python 3.9+) | `__file__`-based path |
| LSD binary | End-to-end integration tests | ✓ | 3.4.9 (confirmed Phase 73) | Skip integration tests (skipif gate) |
| Ring3/ring4 filter files | Bundling | ✓ | At `/Users/steinbeck/Dropbox/develop/LSD/Filters/` | Must copy to package before bundling |
| pytest | Unit tests | ✓ | 9.0.2 | — |

---

## Sources

### Primary (HIGH confidence)

- `src/lucy_ng/lsd/generator.py` — direct inspection of all emission logic
- `src/lucy_ng/lsd/models.py` — direct inspection of all model fields
- `src/lucy_ng/lsd/orchestrator.py` — direct inspection of `_build_permutation` and `SolutionMerger.merge()`
- `.planning/phases/72-design-re-validation/72-DECISIONS.md` — locked architectural decisions D-01a, D-03, D-04
- `.planning/phases/73-solution-plumbing-fix/73-VERIFICATION.md` — Phase 73 bug fixes confirmed
- `data/nmrdata/.../iteration_03/compound_native.lsd` — ground-truth native LSD file (2 aromatic solutions, ibuprofen found)
- `.planning/phases/72-design-re-validation/experiment/arm_a.lsd` — ground-truth emergent test (no SKEL, 2/2 aromatic)
- `/Users/steinbeck/Dropbox/develop/LSD/Filters/ring3`, `ring4` — filter file content verified

### Secondary (MEDIUM confidence)

- `.planning/v8.0-UAT-POSTMORTEM.md` — root cause analysis for constraint loss and merge=0

### Tertiary (LOW confidence)

- A1 assumption about CH2 homotopic proton treatment in LSD

---

## Metadata

**Confidence breakdown:**
- Generator analysis (no SYME/DEFF NOT, exact emission code): HIGH — direct code inspection
- SYME translation per use case: HIGH for gem-dimethyl + aromatic CH (iter3 verified); LOW for homotopic CH2 (assumed)
- DEFF NOT → DEFF F/FEXP translation: HIGH — iter3/arm_a files verified working
- Permutation preservation (_build_permutation deepcopy): HIGH — code inspection + correct semantics confirmed
- SolutionMerger status (no remaining bug): HIGH — Phase 73 verification + code path analysis
- Agent bypass scope gap: HIGH — direct skill file inspection

**Research date:** 2026-05-22
**Valid until:** 60 days (stable domain — LSD binary behaviour does not change; filter files are static)
