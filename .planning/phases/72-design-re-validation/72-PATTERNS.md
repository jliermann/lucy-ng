# Phase 72: Design Re-Validation — Pattern Map

**Mapped:** 2026-05-20
**Files analyzed:** 3 deliverables (experiment arm files, experiment runner script, decision document)
**Analogs found:** 3 / 3

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `.planning/phases/72-design-re-validation/experiment/arm_a.lsd` | config (LSD input) | batch (LSD solver input) | `CASE1/analysis/iteration_03/compound_native.lsd` | exact — same compound, same constraint set, benzene lines removed |
| `.planning/phases/72-design-re-validation/experiment/arm_b.lsd` | config (LSD input) | batch (LSD solver input) | `CASE1/analysis/iteration_03/compound_native.lsd` | exact — verbatim copy |
| `.planning/phases/72-design-re-validation/experiment/arm_c.lsd` | config (LSD input) | batch (LSD solver input) | `CASE1/analysis/iteration_03/compound_native.lsd` | role-match — arm_a base + 3 HMBC X Y 2 4 lines added |
| `.planning/phases/72-design-re-validation/experiment/run_experiment.py` | utility (throwaway script) | batch (subprocess + RDKit) | `tests/test_lsd_regression.py` + `src/lucy_ng/lsd/orchestrator.py` `_run_outlsd` | role-match — same outlsd 5 + RDKit InChI/aromatic pattern |
| `.planning/phases/72-design-re-validation/72-DECISIONS.md` | decision document | N/A | `.planning/v8.0-UAT-POSTMORTEM.md` | role-match — structured evidence + decisions doc |

---

## Pattern Assignments

### `.planning/phases/72-design-re-validation/experiment/arm_a.lsd` (LSD input, batch)

**Analog:** `/Users/steinbeck/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE1/analysis/iteration_03/compound_native.lsd`

**Core structure pattern** (lines 1–61 of the analog — full file):

```
; compound_native.lsd -- Iter3 final (rebuild mit COSY 8 10 + COSY 10 11 + BOND 10 11+12)
; SYME nicht nativ: 4-5/6-7 durch COSY 4 7 + COSY 5 6 abgedeckt
; SYME 11 12: durch BOND 10 11 + BOND 10 12 erzwungen (gem-Dimethyl nativ)
; HMBC 10 9 + HMBC 11 9 entfernt: 4J/5J-Artefakte mit BOND 10 11+12
; Ergebnis: 2 Loesungen (para-Ibuprofen + ortho-Isomer; Ibuprofen = Loesung 1)
;
MULT 1 C 2 0
... [MULT 2–13 C, MULT 14 O 2 0, MULT 15 O 3 1]

HSQC 4 4
... [HSQC 5 5 through HSQC 13 13]

BOND 1 14
BOND 1 15
BOND 10 11
BOND 10 12

COSY 9 13
COSY 4 7
COSY 5 6
COSY 8 10
COSY 10 11

HMBC 1 9
HMBC 1 13
HMBC 2 9
HMBC 10 11
HMBC 13 9
HMBC (8 9) 6
HMBC (8 9) 4
HMBC (8 9) 11
HMBC 3 6
HMBC 2 4

DEFF F1 "/Users/steinbeck/Dropbox/develop/LSD/Filters/ring3"
DEFF F2 "/Users/steinbeck/Dropbox/develop/LSD/Filters/ring4"
PATH "/Users/steinbeck/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE1/analysis/iteration_03/filters"
SKEL F3 "benzene"
FEXP "NOT F1 AND NOT F2 AND F3"
```

**Arm A modification — remove these 3 lines and update FEXP:**

Lines to remove from the analog to create arm_a.lsd:
```
PATH "/Users/steinbeck/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE1/analysis/iteration_03/filters"
SKEL F3 "benzene"
```
FEXP change:
```
; FROM (analog):
FEXP "NOT F1 AND NOT F2 AND F3"
; TO (arm_a):
FEXP "NOT F1 AND NOT F2"
```

**Everything else is preserved verbatim.** Comment header should be updated to identify the arm:
```
; arm_a.lsd -- Emergent test: no SKEL benzene, full constraints preserved
; D-04 question: does aromatic ring emerge from COSY/HMBC constraints alone?
; Derived from iteration_03/compound_native.lsd by removing SKEL/PATH/F3 from FEXP
```

---

### `.planning/phases/72-design-re-validation/experiment/arm_b.lsd` (LSD input, batch)

**Analog:** `/Users/steinbeck/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE1/analysis/iteration_03/compound_native.lsd`

**Pattern:** Verbatim copy of the analog. No modifications. Header comment updated only:
```
; arm_b.lsd -- Forced comparison: SKEL benzene present (baseline, 2-solution reference)
; Expected: 2 solutions (para-ibuprofen + ortho-isomer). If count != 2, environment issue.
; Verbatim copy of iteration_03/compound_native.lsd
```

All 61 lines of the analog file are retained unchanged.

---

### `.planning/phases/72-design-re-validation/experiment/arm_c.lsd` (LSD input, batch)

**Analog:** Same as arm_a (arm_a.lsd is the base for arm_c)

**Arm C modification — add 3 HMBC X Y 2 4 lines after existing HMBC block:**

Starting from arm_a.lsd, append to the HMBC block:
```
HMBC 3 8 2 4    ; Cq(136.96) -- CH2(45.03), 4J W-path through aromatic ring (D-01 test)
HMBC 3 13 2 4   ; Cq(136.96) -- CH3(18.09), 4J W-path
HMBC 3 9 2 4    ; Cq(136.96) -- CH(44.90), 4J W-path (removed in iter3, re-added as extended range)
```

Header comment:
```
; arm_c.lsd -- Bond-range 4J test: arm_a base + HMBC X Y 2 4 for 3 known 4J suspects
; D-01 validation: does extended bond range work? Does aromatic ring still emerge?
; Derived from arm_a.lsd + 3 HMBC X Y 2 4 lines for 4J W-path correlations
```

---

### `.planning/phases/72-design-re-validation/experiment/run_experiment.py` (utility script, batch)

**Analogs:**
1. `tests/test_lsd_regression.py` — outlsd 5 invocation pattern + RDKit SMILES-to-InChI loop (lines 52–78 and 169–238)
2. `src/lucy_ng/lsd/orchestrator.py` `PyLSDOrchestrator._run_outlsd` — the CORRECT outlsd invocation (lines 255–295)

**LSD invocation pattern** (from RESEARCH.md experiment design and analog behavior):

```python
import subprocess
from pathlib import Path

EXPERIMENT_DIR = Path(__file__).parent
LSD_BIN = Path("/Users/steinbeck/Dropbox/develop/LSD/lsd")
OUTLSD_BIN = Path("/Users/steinbeck/Dropbox/develop/LSD/outlsd")

def run_lsd_arm(arm_name: str) -> dict:
    lsd_file = EXPERIMENT_DIR / f"{arm_name}.lsd"
    sol_file = EXPERIMENT_DIR / f"{arm_name}.sol"
    smi_file = EXPERIMENT_DIR / f"{arm_name}_solutions.smi"

    # Run LSD — .sol written to CWD (must run from EXPERIMENT_DIR)
    result = subprocess.run(
        [str(LSD_BIN)],
        stdin=lsd_file.open(),
        capture_output=True,
        text=True,
        cwd=EXPERIMENT_DIR,      # .sol written here
    )

    # Read solution count from solncounter (LSD writes this to cwd)
    solncounter = EXPERIMENT_DIR / "solncounter"
    solution_count = int(solncounter.read_text().strip()) if solncounter.exists() else 0

    # Rename sol file to arm-specific name (LSD writes compound.sol)
    default_sol = EXPERIMENT_DIR / "compound.sol"
    if default_sol.exists():
        default_sol.rename(sol_file)

    if solution_count == 0 or not sol_file.exists():
        return {"arm": arm_name, "solution_count": 0, "smiles": [], "aromatic": []}

    # Run outlsd — CORRECT pattern from orchestrator.py lines 281-291
    # Key: pass sol_file as stdin, include "5" as mode argument
    proc = subprocess.run(
        [str(OUTLSD_BIN), "5"],          # "5" = SMILES output mode
        stdin=sol_file.open(),           # .sol file as stdin (NOT the .lsd file)
        capture_output=True,
        text=True,
        timeout=60,
        cwd=EXPERIMENT_DIR,
    )
    smi_file.write_text(proc.stdout)
    ...
```

**RDKit aromatic check pattern** (from RESEARCH.md lines 437–453, confirmed in test_lsd_regression.py lines 52–78):

```python
from rdkit import Chem
from rdkit.Chem.inchi import MolToInchi

IBUPROFEN_INCHI_KEY = "HEFNNWSXXWATRW-UHFFFAOYSA-N"

def has_aromatic_ring(smiles: str) -> bool:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return False
    rings = mol.GetRingInfo().AtomRings()
    for ring in rings:
        if len(ring) == 6 and all(mol.GetAtomWithIdx(a).GetIsAromatic() for a in ring):
            return True
    return False

def count_aromatic_atoms(smiles: str) -> int:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return 0
    return sum(1 for atom in mol.GetAtoms() if atom.GetIsAromatic())

def smiles_to_inchi_key(smiles: str) -> str | None:
    """Pattern from SolutionMerger._smiles_to_inchi_key (orchestrator.py)."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    inchi = MolToInchi(mol)
    if inchi is None:
        return None
    from rdkit.Chem.inchi import InchiToInchiKey
    return InchiToInchiKey(inchi)

def parse_smiles_file(smi_path: Path) -> list[str]:
    """Pattern from test_lsd_regression.py _smiles_to_inchis (lines 52-78).
    Take first whitespace-delimited field per line; skip empty/invalid."""
    smiles = []
    for raw_line in smi_path.read_text().splitlines():
        parts = raw_line.strip().split()
        if not parts:
            continue
        smiles.append(parts[0])
    return smiles
```

**Results record pattern** (write after each arm):

```python
def record_arm_results(arm_name: str, solution_count: int, smiles: list[str]) -> dict:
    results = []
    for s in smiles:
        aromatic = has_aromatic_ring(s)
        inchi_key = smiles_to_inchi_key(s)
        is_ibuprofen = (inchi_key == IBUPROFEN_INCHI_KEY)
        results.append({
            "smiles": s,
            "aromatic_ring": aromatic,
            "aromatic_atom_count": count_aromatic_atoms(s),
            "inchi_key": inchi_key,
            "is_ibuprofen": is_ibuprofen,
        })
    return {
        "arm": arm_name,
        "solution_count": solution_count,
        "solutions": results,
        "any_aromatic": any(r["aromatic_ring"] for r in results),
        "ibuprofen_found": any(r["is_ibuprofen"] for r in results),
    }
```

**Anti-pattern to avoid** (the runner.py bug, lines 340–347):

```python
# WRONG — do not copy this pattern from runner.py:
proc = subprocess.run(
    [str(self.outlsd_path)],        # Missing "5" argument
    input=input_file.read_text(),   # WRONG: LSD input file, not .sol file
    ...
)
# This produces the 10-line usage header, not SMILES.
```

---

### `.planning/phases/72-design-re-validation/72-DECISIONS.md` (decision document)

**Analog:** `/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/v8.0-UAT-POSTMORTEM.md`

**Document structure pattern** (from postmortem analog — top-level sections):

```markdown
# [Title]

**Date:** [date]
**[Context field]:** [value]

> [One-sentence verdict / executive summary]

---

## [Evidence section] (hard data table first, before interpretation)

| Artifact | Expected | Actual |
|----------|----------|--------|
...

---

## [Analysis section] (organized by severity or decision)

### [Sub-section with explicit YES/NO or CONFIRMED/REFUTED]
...

---

## [Implications section] (maps decisions to downstream actions)

| Decision | Phase | Required Change |
|----------|-------|-----------------|
...
```

**Phase 72 DECISIONS.md required skeleton** (from RESEARCH.md lines 619–682):

```markdown
# Phase 72: Architecture Decisions

**Experiment run:** 2026-05-20
**Compound:** CASE1 / Ibuprofen / C13H18O2
**LSD version:** 3.4.9

## Experiment Results

| Arm | Description | Solution Count | Aromatic Ring? | Ibuprofen Found? |
|-----|-------------|----------------|----------------|-----------------|
| A   | No SKEL, full constraints | [N] | [Y/N] | [Y/N] |
| B   | With SKEL benzene (baseline) | 2 | Yes | Yes (solution 2) |
| C   | Arm A + HMBC X Y 2 4 for 3 4J suspects | [N] | [Y/N] | [Y/N] |

## Q1 Answer: 4J Handling Approach (D-01)

**Decision:** Extended bond range (`HMBC X Y 2 4`) is PRIMARY. Permutation multi-run is FALLBACK.
**Evidence from experiment:** [Arm C result]
**Phase-65 hypothesis re-evaluation:** [Was "removing 4J → ring appears" correct?]

## Q2 Answer: Solver-Path Architecture (D-02)

**Decision:** Single primary path. Permutation fallback documented as subordinate.
**Agent-reversion hypothesis:** [Confirmed/Refuted]
**Implication for Phase 75:** [Skill-documentation strategy]

## Q3 Answer: Constraint Translation (D-03)

**Decision:** Generator emits native-only. SYME → [native equivalent]. DEFF NOT → DEFF F/FEXP.
**SYME native translation open question:** [DUPL sufficient, or BOND constraints needed?]
**Implication for Phase 74 generator:** ...

## Q4 Answer: Aromatic Ring Establishment (D-04)

**Decision:** [EMERGENT / FORCE-REQUIRED] (from Arm A result)
[Branch for each outcome — see RESEARCH.md D-04 decision rule]

## Direct Phase Implications

| Decision | Phase | Required Change |
|----------|-------|-----------------|
| D-01 (bond-range primary) | Phase 73 | Fix outlsd plumbing |
| D-02 (single path) | Phase 75 | Rewrite skill docs |
| D-03 (native-only generator) | Phase 74 | Generator emits DEFF F/FEXP |
| D-03 (SYME translation) | Phase 74 | Decide and implement native equivalent |
| D-04 (aromatic handling) | Phase 74 | Either skip or implement SKEL emission |
| Phase-65 re-evaluation | Phase 75 | Update 4J/aromatic skill knowledge |
```

---

## Shared Patterns

### outlsd correct invocation
**Source:** `src/lucy_ng/lsd/orchestrator.py` lines 269–293 (`PyLSDOrchestrator._run_outlsd`)
**Apply to:** `run_experiment.py` (and future Phase 73 fix of `runner.py`)

```python
proc = subprocess.run(
    [outlsd_path, "5"],        # "5" = SMILES output mode — REQUIRED argument
    stdin=open(sol_file),      # .sol file as stdin — NOT the .lsd input file
    capture_output=True,
    text=True,
    timeout=30,
    cwd=perm_dir,
)
if proc.stdout.strip():
    smiles_file.write_text(proc.stdout)
    return smiles_file
```

### LSD binary invocation with cwd discipline
**Source:** RESEARCH.md experiment design section (lines 403–419); on-disk UAT artifact pattern
**Apply to:** `run_experiment.py`

```bash
# LSD writes .sol to CWD — always set cwd explicitly
subprocess.run([str(LSD_BIN)], stdin=lsd_file.open(), cwd=EXPERIMENT_DIR)
# solncounter appears in EXPERIMENT_DIR after run
```

### RDKit SMILES file parsing
**Source:** `tests/test_lsd_regression.py` `_smiles_to_inchis` (lines 52–78)
**Apply to:** `run_experiment.py`

```python
for raw_line in smiles_path.read_text().splitlines():
    parts = raw_line.strip().split()
    if not parts:
        continue
    smiles = parts[0]   # first field only; rest may be index/name
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        continue
    ...
```

### Decision document: evidence table first, decisions second
**Source:** `.planning/v8.0-UAT-POSTMORTEM.md` structure (postmortem analog)
**Apply to:** `72-DECISIONS.md`

Hard evidence table (what was observed, with artifact citations) appears BEFORE the interpretation / decision narrative. Each decision section has a mandatory YES/NO or CONFIRMED/REFUTED verdict on its first line.

---

## No Analog Found

None. All three deliverable types have close analogs in the codebase or planning directory.

---

## Metadata

**Analog search scope:**
- `/Users/steinbeck/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE1/analysis/iteration_03/`
- `/Users/steinbeck/Dropbox/develop/lucy-ng/tests/test_lsd_regression.py`
- `/Users/steinbeck/Dropbox/develop/lucy-ng/src/lucy_ng/lsd/orchestrator.py`
- `/Users/steinbeck/Dropbox/develop/lucy-ng/src/lucy_ng/lsd/runner.py`
- `/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/v8.0-UAT-POSTMORTEM.md`

**Files scanned:** 5 analog files
**Pattern extraction date:** 2026-05-20
