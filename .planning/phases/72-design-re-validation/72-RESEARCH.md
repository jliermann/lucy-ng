# Phase 72: Design Re-Validation — Research

**Researched:** 2026-05-20
**Domain:** LSD-3.4.9 native command semantics; controlled CASE1 experiment design; architecture decision documentation
**Confidence:** HIGH (all critical findings verified from LSD source code, manual, and real on-disk UAT artifacts)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01:** Extended HMBC bond range (`HMBC X Y 2 4`) is the PRIMARY 4J mechanism. A flagged 4J-suspect correlation is emitted with an extended bond range and LSD explores 2-4 bonds in a SINGLE run.
**D-01a:** pyLSD permutation multi-run is demoted to a narrow fallback — invoked only when the bond-range single run yields 0 solutions or an intractable count.

**D-02:** Collapse to ONE primary solver path: normal LSD + extended bond range. The permutation fallback is a clearly-subordinate, narrowly-scoped escape hatch.
**D-02a:** Skills document the single primary path prominently; the permutation fallback is documented as subordinate with explicit "use only when ..." conditions.

**D-03:** The LSD-file generator emits native-only commands. SYME → DUPL; DEFF NOT (ring exclusion) → DEFF F/FEXP filter files; translation happens at GENERATION time. No emitted file may contain `SYME` or `DEFF NOT <smarts>`.
**D-03a:** These are author-time abstractions only, resolved before any file is written.

**D-04:** Test first, force only if needed. Run CASE1 with full native constraints and NO forced benzene fragment; observe whether an aromatic-ring solution appears. Decision rule: emergent → no forcing; does not emerge → force a benzene SKEL fragment when aromatic pattern confidently detected.

**D-05:** On CASE1 (ibuprofen):
  1. Bond-range run: flagged 4J as `HMBC X Y 2 4`, single LSD run, full native constraints, NO forced benzene fragment.
  2. (Optional comparison) same + SKEL benzene fragment and/or a permutation run.

### Claude's Discretion

None specified.

### Deferred Ideas (OUT OF SCOPE)

- Parallel LSD execution (PERF-01, v2 requirements)
- Whether to eventually delete the pyLSD permutation code entirely
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DESIGN-01 | 4J-handling and aromatic-ring approach decided and documented, Phase-65 hypothesis re-evaluated | Sections: Native Command Reference, Experiment Design, D-04 Evidence |
| DESIGN-02 | Solver-path architecture decided (single vs dual path) with skill-documentation strategy preventing agent reversion | Sections: Architecture Patterns, Decision Document Structure, Pitfalls |
</phase_requirements>

---

## Summary

Phase 72 is a design + experiment phase. It does not write production code. Its entire executable core is one controlled experiment: run CASE1 (ibuprofen, C13H18O2) via a hand-crafted native-only LSD file with full constraints preserved, observe whether an aromatic-ring solution appears without forcing, and record the result as the empirical input for four locked architecture decisions (D-01 to D-04). The DESIGN-01 and DESIGN-02 deliverables are a decision document, not code.

The v8.0 UAT produced real on-disk artifacts that are invaluable: `iteration_03/compound_native.lsd` found ibuprofen (2 solutions) using DEFF F1/F2 (ring exclusion) + SKEL benzene + COSY + bond constraints with a direct LSD binary call. This file is the experiment's starting point. Arm A of the experiment is derived from it by removing the SKEL benzene fragment and keeping everything else; Arm B retains SKEL as a comparison. The design question (D-04) is whether Arm A produces an aromatic-ring solution independently.

The key verified finding is that SYME and DEFF NOT are not native LSD-3.4.9 commands (error 102 / error 150 respectively from the command table in `lecture.c`). The native equivalents are DUPL (for duplicate/equivalence removal), DEFF F/FEXP (for substructure filtering including ring exclusion). These have been verified directly against the LSD source code and manual. The iter2 constraint inventory in `compound.lsd` confirms what went wrong: SYME/DEFF NOT were written but then stripped when the agent ran the direct binary, yielding 90 solutions without any aromatic ring enforcement.

**Primary recommendation:** Use `iteration_03/compound_native.lsd` as the template, strip the SKEL/PATH/FEXP lines to create Arm A, run both arms via direct LSD binary, record results in the decision document. This settles D-04 empirically and confirms D-01 (bond-range primary). The decision document must map each decision to its direct Phase 73-75 implication.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| LSD command emission | Python generator (`generator.py`) | — | D-03: translation at generation time |
| Ring exclusion (DEFF F/FEXP) | LSD binary (native commands) | Generator writes the file paths | Filter files must exist on disk at absolute paths |
| Symmetry / duplicate removal | LSD binary (DUPL command) | — | DUPL is native; SYME is not |
| 4J bond-range handling | LSD binary (`HMBC X Y 2 4`) | — | D-01: single-run extended range |
| Aromatic ring forcing (if needed) | LSD binary (SKEL + FEXP) | Generator writes SKEL/PATH lines | Benzene mol file must exist on disk |
| Solution conversion to SMILES | `outlsd 5 < compound.sol` subprocess | — | Must use stdin redirection, not LSD input file |
| Permutation fallback | `PyLSDOrchestrator` | Demoted per D-01a | Only when single-run yields 0 solutions |
| Decision documentation | Phase 72 output file | — | No code; markdown artifact consumed by Phases 73-75 |

---

## Native LSD-3.4.9 Command Reference

### Verified Native Command Set

Source: `/Users/steinbeck/Dropbox/develop/LSD/LsdSrc/lecture.c` command table (lines 56-113). [VERIFIED: LSD source code]

The complete native command list (case-sensitive, uppercase required):

```
VALE, MULT, LIST, CARB, HETE, SP3, SP2, QUAT, CH, CH2, CH3, FULL,
GREQ, LEEQ, GRTH, LETH, UNIO, INTE, DIFF, PROP, BOND, HMQC, COSY,
HMBC, ENTR, HIST, DISP, VERB, PART, STEP, WORK, MLEV, SSTR, ASGN,
LINK, DUPL, SUBS, ELIM, FILT, DEFF, FEXP, CNTD, MAXS, MAXT, HSQC,
CCLA, PATH, SKEL, COUF, STOF, SP, CHAR, CPOS, CNEG, ELEM, SHIX,
SHIH, BRUL
```

**SYME is NOT in this list.** [VERIFIED: LSD source code]
**DEFF NOT is NOT in this list.** DEFF takes a fragment index + path, not a SMARTS. [VERIFIED: LSD source code]

Error behavior:
- Unknown command → `error 102 - Unknown command name: <command>` (lecture.c line 433) [VERIFIED: LSD source code]
- Wrong fragment index syntax (`F` expected but not found) → `error 150 - F expected` (lecture.c line 465) [VERIFIED: LSD source code]

### DUPL — Duplicate/Equivalence Removal

Source: LSD manual (`/Users/steinbeck/Dropbox/develop/LSD/MANUAL_ENG.html`, line 783); confirmed in `lsd.c` comments (lines 1187-1197). [VERIFIED: LSD source + manual]

```
DUPL I: elimination of duplicate solutions

P1 = 0: duplicate structures may be produced.
P1 = 1: duplicate solutions are removed.
P1 = 2: duplicate structures are removed (default).
```

**What it does:** DUPL controls LSD's own deduplication of the solution output. The DEFAULT (`DUPL 2`) already removes duplicate structures. `DUPL 1` removes duplicate solutions (topologically identical atom-label assignments).

**Critical semantics note:** DUPL is an output-deduplication command, NOT a symmetry-constraint command. It does not tell LSD that atoms N and M are chemically equivalent. The v8.0 agent used SYME to mean "these two atoms are equivalent" — but SYME does not exist natively. In the iteration_03 file, the agent's workaround was to encode gem-dimethyl equivalence via `BOND 10 11` and `BOND 10 12` (forcing the connectivity) and use COSY for aromatic equivalence — which worked for this compound but is not a general translation of SYME. [VERIFIED: LSD source code, on-disk artifacts]

**D-03 implication:** SYME → DUPL is the CONTEXT.md description, but the semantics differ. DUPL does not replace SYME's role of marking two atoms as structurally equivalent (affecting which HMBC correlations LSD considers). For Phase 74, the generator will need to decide: use DUPL (dedup only) plus LIST/PROP constraints to encode equivalence, or accept that structural equivalence is enforced through connectivity (BOND) and correlation constraints. This is an open sub-question for the decision document to note explicitly. [ASSUMED: the correct native translation of SYME]

### DEFF + FEXP — Substructure Filtering (Ring Exclusion and Forcing)

Source: LSD manual lines 970-1051; `lecture.c` command table entry #39 and #40. [VERIFIED: LSD source + manual]

```
DEFF Fn C: define fragment from its file name.
  P1: fragment index (F1, F2, F3, ...; must start with F followed by integer >= 1)
  P2: path to the fragment file (quoted string)

Example: DEFF F1 "/Users/steinbeck/Dropbox/develop/LSD/Filters/ring3"
         Fragment F1 is a generic 3-membered ring.
```

```
FEXP C: fragment (logical) expression.
  P1: logical expression combining fragment results using NOT, AND, OR
      Precedence: NOT > AND > OR. Use parentheses to override.

Examples:
  FEXP "NOT F1 AND F2"      (equivalent to (NOT F1) AND F2)
  FEXP "F1 AND F2 OR F3"    (equivalent to (F1 AND F2) OR F3)
```

**DEFF NOT does not exist.** The `DEFF` command takes a fragment INDEX (Fn syntax) and a file path. It does not accept SMARTS strings. [VERIFIED: LSD source code]

**Existing filter files on disk** (verified at `/Users/steinbeck/Dropbox/develop/LSD/Filters/`):
- `ring3` — 3-membered ring (cyclopropane/azetidine etc.) [VERIFIED: on disk]
- `ring4` — 4-membered ring (cyclobutane etc.) [VERIFIED: on disk]
- `TERPENES` — terpene skeleton database directory [VERIFIED: on disk]

**ring3 file content:**
```
; a generic 3-membered ring
SSTR S1 A (2 3) (0 1 2)
SSTR S2 A (2 3) (0 1 2)
SSTR S3 A (2 3) (0 1 2)
LINK S1 S2
LINK S2 S3
LINK S1 S3
```

**ring4 file content:**
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

**Translation of DEFF NOT patterns (D-03):** The v8.0 agent used `DEFF NOT C1CC1` to exclude 3-membered rings. The native equivalent is:
```
DEFF F1 "/Users/steinbeck/Dropbox/develop/LSD/Filters/ring3"
DEFF F2 "/Users/steinbeck/Dropbox/develop/LSD/Filters/ring4"
FEXP "NOT F1 AND NOT F2"
```
This is exactly what `iteration_03/compound_native.lsd` uses. [VERIFIED: on-disk artifact]

**IMPORTANT:** DEFF file paths must be absolute OR relative to the working directory from which LSD is invoked. The UAT used absolute paths. The experiment must ensure these paths exist. [VERIFIED: on-disk artifact]

### SKEL — Skeleton (Named Fragment) Forcing

Source: LSD manual lines 980-988; `lecture.c` command table entry #47. [VERIFIED: LSD source + manual]

```
SKEL Fn C: define fragment from its skeleton name.
  P1: fragment index (Fn)
  P2: skeleton name (quoted string)

Example: SKEL F4 "PINANE"
         Fragment F4 is the pinane skeleton.
```

From the manual: "From version 3.4.1 included, this command is not mandatory. An external substructure could be referred to directly by the skeleton name without using a fragment number."

**SKEL with a benzene .mol file** requires the mol file to be findable via PATH. The UAT used:
```
PATH "/Users/steinbeck/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE1/analysis/iteration_03/filters"
SKEL F3 "benzene"
```
This tells LSD to look for a file named `benzene` in that PATH directory. The file found is `benzene.mol`. [VERIFIED: on-disk artifact + filters directory contents]

**Benzene mol file content** (at `iteration_03/filters/benzene.mol`):
```

  benzene ring substructure for LSD (Kekule form)

  6  6  0  0  0  0            999 V2000
    1.2124    0.7000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    2.4249    0.7000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    3.0311    1.9124    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    2.4249    3.1249    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.2124    3.1249    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    0.6062    1.9124    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  2  0  0  0  0
  2  3  1  0  0  0  0
  3  4  2  0  0  0  0
  4  5  1  0  0  0  0
  5  6  2  0  0  0  0
  6  1  1  0  0  0  0
M  END
```

The alternating single/double bonds (Kekule form) represent benzene. LSD uses this as a substructure template. [VERIFIED: on-disk artifact]

**FEXP combining exclusion + forcing:**
```
FEXP "NOT F1 AND NOT F2 AND F3"
```
where F1=ring3, F2=ring4, F3=benzene. This passes only structures that contain benzene AND lack 3- and 4-membered rings. This is exactly the expression in `iteration_03/compound_native.lsd`. [VERIFIED: on-disk artifact]

### PATH — Fragment Search Directory

Source: LSD manual lines 992-997. [VERIFIED: LSD manual]

```
PATH C: defines where to search for skeletons.
  P1: path to skeleton database (quoted string)

Example: PATH "Filters/TERPENES/MONOTERP"
```

Adds a directory to LSD's skeleton search path. Multiple PATH commands accumulate. [VERIFIED: LSD manual]

### HMBC — Extended Bond Range Syntax

Source: `lecture.c` command table line 79: `{ "HMBC", 4, "VIOO", 9 }`. The format string "VIOO" indicates: V=vertex/atom, I=integer, O=optional integer, O=optional integer. [VERIFIED: LSD source code]

```
HMBC carbon_idx hydrogen_idx [min_bonds [max_bonds]]

Default (2-arg form):   HMBC 4 8         (2-3 bonds, LSD default)
Extended bond range:    HMBC 4 8 2 4     (2-4 bonds, D-01 primary 4J mechanism)
```

The `LSDCorrelation.to_lsd_line()` already emits this correctly when `min_bonds=2, max_bonds=4`. [VERIFIED: `src/lucy_ng/lsd/models.py` line 152-153]

---

## The Two Real Ibuprofen LSD Files

### iteration_03/compound_native.lsd — The Working Native File

This file produced 2 solutions (both aromatic ring, C13H18O2). It is the gold standard for Arm B and the starting point for Arm A. [VERIFIED: on-disk artifact, RDKit-verified solutions]

**Full content:**
```
; compound_native.lsd -- Iter3 final
MULT 1 C 2 0      ; C1  180.56 ppm  Cq sp2 (COOH carbonyl)
MULT 2 C 2 0      ; C2  140.84 ppm  Cq sp2 (arene ipso, benzyl side)
MULT 3 C 2 0      ; C3  136.96 ppm  Cq sp2 (arene ipso, CH3 side)
MULT 4 C 2 1      ; C4a 129.38 ppm  CH sp2 (arene, COSY pair with 5)
MULT 5 C 2 1      ; C4b 129.38 ppm  CH sp2 (arene, symmetry partner)
MULT 6 C 2 1      ; C5a 127.26 ppm  CH sp2 (arene, COSY pair with 7)
MULT 7 C 2 1      ; C5b 127.26 ppm  CH sp2 (arene, symmetry partner)
MULT 8 C 3 2      ; C6  45.03  ppm  CH2 sp3 (benzyl CH2)
MULT 9 C 3 1      ; C7  44.90  ppm  CH sp3 (alpha-CH)
MULT 10 C 3 1     ; C8  30.14  ppm  CH sp3 (isobutyl CH)
MULT 11 C 3 3     ; C9a 22.37  ppm  CH3 sp3 (gem-dimethyl)
MULT 12 C 3 3     ; C9b 22.37  ppm  CH3 sp3 (gem-dimethyl partner)
MULT 13 C 3 3     ; C10 18.09  ppm  CH3 sp3 (alpha-CH3)
MULT 14 O 2 0     ; O1  sp2  (carbonyl O)
MULT 15 O 3 1     ; O2  sp3  (COOH hydroxyl)

HSQC 4 4
HSQC 5 5
HSQC 6 6
HSQC 7 7
HSQC 8 8
HSQC 9 9
HSQC 10 10
HSQC 11 11
HSQC 12 12
HSQC 13 13

BOND 1 14          ; C=O (carbonyl)
BOND 1 15          ; C-OH (carboxylic acid)
BOND 10 11         ; isobutyl CH-CH3 (gem-dimethyl)
BOND 10 12         ; isobutyl CH-CH3 (gem-dimethyl partner)

COSY 9 13          ; alpha-CH -- alpha-CH3
COSY 4 7           ; arene CH(129.38) -- CH(127.26) ortho neighbor
COSY 5 6           ; arene CH(129.38) -- CH(127.26) other pair
COSY 8 10          ; benzyl CH2 -- isobutyl CH (KEY: excludes ethyl isomer)
COSY 10 11         ; isobutyl CH -- gem-dimethyl CH3

HMBC 1 9           ; COOH C -- alpha-CH (2J)
HMBC 1 13          ; COOH C -- alpha-CH3 (3J)
HMBC 2 9           ; arene ipso -- alpha-CH (3J)
HMBC 10 11         ; isobutyl CH -- gem-dimethyl CH3 (2J)
HMBC 13 9          ; alpha-CH3 -- alpha-CH (2J)
HMBC (8 9) 6       ; benzyl/alpha-CH(2) -- arene CH 127.26 (3J grouped)
HMBC (8 9) 4       ; benzyl/alpha-CH(2) -- arene CH 129.38 (3J grouped)
HMBC (8 9) 11      ; benzyl/alpha-CH(2) -- gem-dimethyl CH3 (3J grouped)
HMBC 3 6           ; arene ipso -- arene CH 127.26 (3J, para relationship)
HMBC 2 4           ; arene ipso -- arene CH 129.38 (para-specific)

DEFF F1 "/Users/steinbeck/Dropbox/develop/LSD/Filters/ring3"
DEFF F2 "/Users/steinbeck/Dropbox/develop/LSD/Filters/ring4"
PATH "/Users/steinbeck/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE1/analysis/iteration_03/filters"
SKEL F3 "benzene"
FEXP "NOT F1 AND NOT F2 AND F3"
```

**Solutions produced:** 2 (both aromatic ring)
- Solution 2 (line 2 of solutions.smi): InChI key HEFNNWSXXWATRW = IBUPROFEN (para isomer) [VERIFIED: RDKit]
- Solution 1 (line 1): InChI key UYHNNWQKLGPQQX = ortho-ibuprofen isomer [VERIFIED: RDKit]

**NOTE on comment in file:** The comment says "HMBC 10 9 + HMBC 11 9 entfernt: 4J/5J-Artefakte" — these were present in iteration_02 but removed for iteration_03 because `BOND 10 11` and `BOND 10 12` already encode the isobutyl connectivity. [VERIFIED: comparison of iter02 vs iter03 files]

### iteration_02/compound.lsd — The Pre-Benzene File (SYME/DEFF NOT version)

This is what the agent wrote with the lucy-ng abstractions. It contains SYME and `DEFF NOT` which caused error 102/150 when run against the direct binary. Running it through `lucy lsd run` (which internally translates) would strip these constraints, yielding 90 solutions — none aromatic. [VERIFIED: on-disk artifact + iter2 solutions.smi RDKit check]

**Aromatic ring count in iter2 solutions (RDKit-verified):** 5/90 solutions had >=6 aromatic atoms. The 85/90 without aromatic ring were the dominant output — validating that without the SKEL/FEXP fragment, LSD places sp2 carbons in non-aromatic arrangements. [VERIFIED: Python/RDKit analysis of solutions.smi]

---

## Experiment Design (D-05) — Detailed Specification

### Arm A: Emergent Test (the key question)

**Goal:** Does a native-only ibuprofen LSD file with FULL constraints preserved (HSQC + correct-bond-range HMBC + DEFF F ring exclusion + DUPL) but NO SKEL benzene fragment produce an aromatic-ring solution?

**Starting file:** `iteration_03/compound_native.lsd`

**Modification to create Arm A:** Remove these 4 lines:
```
PATH "/Users/steinbeck/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE1/analysis/iteration_03/filters"
SKEL F3 "benzene"
```
And modify FEXP to remove the benzene requirement:
```
; CHANGE FROM:
FEXP "NOT F1 AND NOT F2 AND F3"
; TO:
FEXP "NOT F1 AND NOT F2"
```

**Arm A file:** Write to `analysis/experiment/arm_a.lsd`

**What's preserved in Arm A:**
- All MULT definitions (same atom set)
- All HSQC correlations
- BOND 1 14, BOND 1 15 (carboxylic acid)
- BOND 10 11, BOND 10 12 (gem-dimethyl)
- All COSY correlations (including the aromatic COSY 4 7 / 5 6)
- All HMBC correlations
- DEFF F1 ring3 + DEFF F2 ring4 + FEXP "NOT F1 AND NOT F2" (ring exclusion, no forcing)

**What's removed:** SKEL F3 "benzene" + PATH + F3 reference in FEXP

**Critical open question:** The COSY 4 7 / 5 6 lines encode that sp2 CH atoms couple through space. LSD interprets COSY as a 3J H-H coupling constraint — it requires 3 bonds between the H atoms. For aromatic CH atoms 4 and 7 (both at 129.38 ppm, para-related), COSY 4 7 implies 3 bonds between H4 and H7 — which is only satisfiable in a 4-membered ring or an aromatic ring system. This may be the constraint that forces LSD toward a 6-membered ring arrangement even without SKEL. [ASSUMED — needs empirical verification by the experiment]

### Arm B: Forced Comparison

**Goal:** Verify the working state (iteration_03 baseline) and produce a solution-count benchmark.

**File:** Use `iteration_03/compound_native.lsd` directly (or a copy). No modifications.

**Expected result:** 2 solutions, both aromatic (verified already). Arm B should reproduce this exactly.

### Optional Arm C: Bond-Range 4J Test (D-01 validation)

**Goal:** Validate that the D-01 primary mechanism (`HMBC X Y 2 4`) works for the known ibuprofen 4J correlations.

**Modification:** Take Arm A and change the three formerly-deferred 4J correlations from removed/absent to present with extended bond range:
```
HMBC 3 8 2 4    ; Cq(136.96) -- CH2(45.03), 4J W-path
HMBC 3 13 2 4   ; Cq(136.96) -- CH3(18.09), 4J W-path  
HMBC 3 9 2 4    ; Cq(136.96) -- CH(44.90), 4J W-path (was removed in iter3 as 4J)
```
The question: does adding `HMBC X Y 2 4` for these correlations still yield solutions? And are they aromatic?

**Note:** In the actual ibuprofen CASE, the agent removed these correlations rather than using extended bond range (the D-01 approach had not been decided yet). Arm C tests whether the D-01 approach would have worked.

### LSD Invocation (Direct Binary — the only working method)

Source: CASE-PROGRESS.md line confirming "direktes lsd-Binär" + investigation of runner.py vs what actually worked. [VERIFIED: on-disk artifacts]

```bash
# Run from the directory containing the LSD file
cd /path/to/analysis/experiment/
/Users/steinbeck/Dropbox/develop/LSD/lsd < arm_a.lsd > /dev/null 2>arm_a.err
cat solncounter   # LSD writes solution count to solncounter file in cwd
```

**Why NOT `lucy lsd run`:** The runner (`LSDRunner._execute_lsd`) passes the input file content via `subprocess.run(..., input=input_file.read_text(), ...)` — this is stdin mode. LSD in stdin mode writes `.sol` files to the CWD. The runner then calls `_run_outlsd` which feeds back the LSD input file (not the `.sol` file) to outlsd — that is the bug. The working invocation from the UAT is:

```bash
# LSD: writes compound.sol in current directory
/Users/steinbeck/Dropbox/develop/LSD/lsd < arm_a.lsd > /dev/null

# outlsd: read from .sol file, write SMILES (5 = SMILES mode)
/Users/steinbeck/Dropbox/develop/LSD/outlsd 5 < arm_a.sol > arm_a_solutions.smi
```

[VERIFIED: CASE-PROGRESS.md line 125 "outlsd 5 < compound.sol"; orchestrator.py `_run_outlsd` method correctly uses `stdin=open(sol_file)` and passes "5" as argument — the bug in `runner.py` `_run_outlsd` is that it passes the LSD input file, not the .sol file]

**The exact outlsd bug in runner.py** (lines 340-347):
```python
proc = subprocess.run(
    [str(self.outlsd_path)],          # MISSING: the "5" argument
    input=input_file.read_text(),      # WRONG: should be sol_file content, not lsd input
    ...
)
```
outlsd with no argument prints usage and exits. This is why the UAT saw the 10-line header. [VERIFIED: runner.py source + `iteration_02/outlsd.out` content showing the usage message]

### RDKit Aromatic Check

```python
from rdkit import Chem

def has_aromatic_ring(smiles: str) -> bool:
    """Return True if SMILES contains at least one 6-membered aromatic ring."""
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
```

**Ibuprofen InChI key:** `HEFNNWSXXWATRW-UHFFFAOYSA-N` (verified RDKit). [VERIFIED: Python/RDKit analysis]

**Verification of iter3 solutions:**
- Solution 2 (para): `CC(C)Cc1ccc(C(C)C(=O)O)cc1` — InChI key HEFNNWSXXWATRW = ibuprofen [VERIFIED: RDKit]
- Solution 1 (ortho): `CC(C)Cc1ccccc1C(C)C(=O)O` — InChI key UYHNNWQKLGPQQX = ortho-isomer [VERIFIED: RDKit]

**What Arm A experiment must check:**
1. Solution count (from `solncounter` file in cwd)
2. For each SMILES in `solutions.smi`: `has_aromatic_ring(smiles)` — True/False
3. InChI key match against HEFNNWSXXWATRW (ibuprofen)
4. RDKit formula check: must be C13H18O2

---

## Architecture Patterns

### D-04 Decision Rule (to be filled by experiment)

```
IF Arm A solution count > 0 AND any(has_aromatic_ring(s) for s in arm_a_solutions):
    D-04 = EMERGENT
    → Phase 74 does NOT implement SKEL forcing
    → Phase 75 documents: "correct constraints without SKEL yield aromatic ring"

ELIF Arm A solution count > 0 AND NOT any(has_aromatic_ring(s) for s in arm_a_solutions):
    D-04 = FORCE-REQUIRED
    → Phase 74 implements SKEL fragment forcing when aromatic pattern detected
    → Trigger condition: 4+ sp2 C in 110-160 ppm range in MULT definitions

ELIF Arm A solution count == 0:
    D-04 = UNDETERMINED (over-constrained without SKEL)
    → Remove one COSY at a time to find conflicting constraint
    → Document which constraint caused zero solutions
```

### D-01 Validation Expected Outcome

From the UAT evidence, the known ibuprofen 4J correlations are:
- `HMBC 3 8 2 4` (Cq 136.96 — CH2 45.03, 4J W-path through aromatic ring)
- `HMBC 3 13 2 4` (Cq 136.96 — CH3 18.09, 4J W-path)
- `HMBC 3 9 2 4` (Cq 136.96 — CH 44.90, 4J W-path)

The v8.0 agent identified and deferred these; they were never included with extended bond range. Arm C tests the D-01 mechanism directly.

### Recommended Experiment File Structure

```
analysis/experiment/
├── arm_a.lsd            # Emergent test (no SKEL)
├── arm_a.sol            # Output from LSD (written by LSD to cwd)
├── arm_a_solutions.smi  # Output from outlsd 5
├── arm_b.lsd            # Copy of iteration_03/compound_native.lsd
├── arm_b.sol
├── arm_b_solutions.smi
├── arm_c.lsd            # Bond-range 4J test (optional)
├── arm_c.sol
├── arm_c_solutions.smi
└── results.md           # Decision record
```

### Native Translation: DEFF NOT SMARTS → DEFF F/FEXP

The v8.0 agent wrote 8 `DEFF NOT <SMARTS>` lines. The native translation uses the pre-built filter files:

```
; BEFORE (non-native, lucy-ng abstraction):
DEFF NOT C1CC1
DEFF NOT C1CCC1
DEFF NOT C1NC1
DEFF NOT C1NCC1
DEFF NOT C1SC1
DEFF NOT C1SCC1
DEFF NOT C1OC1
DEFF NOT C1OCC1

; AFTER (native, D-03 compliant):
DEFF F1 "/Users/steinbeck/Dropbox/develop/LSD/Filters/ring3"
DEFF F2 "/Users/steinbeck/Dropbox/develop/LSD/Filters/ring4"
FEXP "NOT F1 AND NOT F2"
```

The native filter files use LSD's own `SSTR`/`LINK` substructure language, not SMARTS. They are more general than specific SMARTS patterns — `ring3` matches ANY 3-membered ring regardless of heteroatom composition. This is appropriate (stricter coverage). [VERIFIED: filter file contents]

Note: The 8 DEFF NOT patterns cover C, N, S, O variants — the native ring3/ring4 filters cover all atom types. The translation is therefore equally restrictive or more so for non-carbon strained rings.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Ring exclusion filter | Custom SMARTS evaluator | DEFF F1 + existing ring3/ring4 files | Files already exist, LSD handles natively |
| Benzene fragment file | mol2ab conversion script | Copy from iteration_03/filters/benzene.mol | File already exists and was verified to work |
| SMILES → aromatic check | Custom ring detector | RDKit `GetRingInfo().AtomRings()` + `GetIsAromatic()` | One-liner, already in codebase (SolutionMerger uses RDKit) |
| InChI-based comparison | String matching SMILES | `InchiToInchiKey(MolToInchi(mol))` | Already in SolutionMerger._smiles_to_inchi_key() |
| outlsd invocation | Custom solution parser | `outlsd 5 < compound.sol` subprocess | Standard tool, correct mode argument is "5" |

---

## Common Pitfalls

### Pitfall 1: LSD stdin mode does NOT write .sol files to an arbitrary location

**What goes wrong:** `lsd < file.lsd > output` — the `.sol` file is written to the CURRENT WORKING DIRECTORY, not to the directory containing `file.lsd`. If LSD is invoked from a different directory, the .sol file appears in an unexpected location.

**How to avoid:** Always `cd` to the working directory before invoking LSD, or invoke with `cwd=output_dir` in subprocess.

**Warning sign:** `solncounter` shows N > 0 but no `.sol` file found in the expected location.

### Pitfall 2: outlsd requires the .sol FILE as stdin, not the LSD input file

**What goes wrong:** `outlsd 5 < compound.lsd` → 10-line usage header, 0 SMILES. This is the exact bug in `runner.py`.

**Correct invocation:**
```bash
outlsd 5 < compound.sol > solutions.smi
```
NOT:
```bash
outlsd 5 < compound.lsd > solutions.smi
```

**Warning sign:** `outlsd.out` or solutions file contains only the 10-line usage message ending in `p = 9: SDF 3D format with H atoms (.mol)`.

### Pitfall 3: DEFF filter file paths must be valid at LSD invocation time

**What goes wrong:** DEFF uses the PATH as written in the file. Relative paths are resolved from the CWD of the LSD invocation, not from the file's location.

**How to avoid:** Use absolute paths in DEFF commands OR ensure LSD is invoked from the correct directory.

**The experiment files use absolute paths** — this is the safe pattern. Phase 74 generator must emit absolute paths or paths relative to a known working directory.

### Pitfall 4: SYME is error 102, DEFF NOT is error 150 — silently wrong output, not crash

**What goes wrong:** When `lucy lsd run` runs the translation layer, it strips SYME/DEFF NOT silently and produces solutions WITHOUT the intended constraints. The return code is 0 (solutions found), so the caller has no indication constraints were lost. This is how 90 solutions appeared in iter2 without any aromatic ring.

**How to avoid:** D-03 compliance: never emit SYME or DEFF NOT in generated files. Phase 74 is the fix. The experiment bypasses this by using hand-crafted native files.

### Pitfall 5: DUPL ≠ SYME (different semantics)

**What goes wrong:** The CONTEXT.md says "SYME → DUPL" but DUPL is output-deduplication, not structural equivalence marking. DUPL 2 (the default) removes isomorphic structures from the output. SYME (if it existed) would tell LSD that two atoms are interchangeable in HMBC interpretation.

**How to avoid:** In the experiment, use BOND constraints to enforce equivalence structurally (as done in iter3 for the gem-dimethyl: `BOND 10 11` and `BOND 10 12`). For the decision document, note this as an open sub-question: what is the correct native translation of SYME for Phase 74.

**Warning sign:** Solution count jumps unexpectedly when SYME is removed vs. added, in a way inconsistent with deduplication alone.

### Pitfall 6: COSY 4 7 and COSY 5 6 may implicitly force ring topology

**What goes wrong:** COSY in LSD means "3J H-H coupling exists between these H atoms." For two sp2 CH atoms at 129.38 and 127.26 ppm to be COSY-connected, they must be 3 bonds apart (H-C-C-H). This is satisfiable in an aromatic ring (H4-C4-C5-H5 through the ring) but also in non-ring sp2 systems. Whether LSD interprets this as forcing a ring is unclear from the manual. [ASSUMED — the experiment itself must resolve this]

### Pitfall 7: iter2 had 5/90 aromatic solutions — the postmortem count "0/90" was imprecise

**What went wrong in the postmortem summary:** The CASE-PROGRESS.md says "0/90 Lösungen besitzen einen Benzolring". The on-disk `iteration_02/solutions.smi` actually shows 5/90 solutions with >=6 aromatic atoms (RDKit-verified). The 85/90 dominant non-aromatic result still supports the postmortem conclusion (aromatic solutions were a small minority without SKEL), but the exact number matters for Arm A comparison. [VERIFIED: Python/RDKit analysis of iteration_02/solutions.smi]

The 5 aromatic ones in iter2 resulted from SYME and DEFF NOT being stripped (lucy-ng translation bug) — NOT from the constraint set adequately enforcing aromaticity. The 85 non-aromatic ones confirm the core problem.

---

## Decision Document Structure

The DESIGN-01 and DESIGN-02 deliverable is `.planning/phases/72-design-re-validation/72-DECISIONS.md`. The planner should create ONE plan that produces this file plus the experiment result.

### Required Sections

```markdown
# Phase 72: Architecture Decisions

## Experiment Results (CASE1, from compound_native.lsd variants)

| Arm | Description | Solution Count | Aromatic Ring? | Ibuprofen Found? |
|-----|-------------|---------------|----------------|-----------------|
| A   | No SKEL, full constraints | [N] | [Y/N] | [Y/N] |
| B   | With SKEL benzene | 2 | Yes | Yes (solution 2) |
| C   | Arm A + HMBC X Y 2 4 for 3 4J suspects | [N] | [Y/N] | [Y/N] |

## Q1 Answer: 4J Handling Approach (D-01)

**Decision:** Extended bond range (`HMBC X Y 2 4`) is PRIMARY; permutation multi-run is FALLBACK.

**Evidence from experiment:** [Arm C result]

**Phase-65 hypothesis re-evaluation:** [Was "removing 4J → ring appears" correct?]
- Phase 65 claim: removing 4J HMBC makes aromatic ring appear → confirmed/refuted
- Actual finding: ring appeared only with SKEL forcing (iter3), not from constraint removal alone (iter2)
- But: iter2 ran WITHOUT SYME/DEFF NOT (constraint-loss bug) — the confound that Phase 72 controls for
- Arm A result: [empirical answer]

## Q2 Answer: Solver-Path Architecture (D-02)

**Decision:** Single primary path (normal LSD + bond range). Permutation fallback documented as subordinate.

**Agent-reversion hypothesis:** [Confirmed/Refuted — did the agent revert because normal-LSD was better-documented?]

**Skill-documentation strategy:** [How Phase 75 addresses this]
  - Implication for Phase 75: ...

## Q3 Answer: Constraint Translation (D-03)

**Decision:** Generator emits native-only. SYME → [native equivalent]. DEFF NOT → DEFF F/FEXP.

**SYME native translation open question:** [Is DUPL sufficient, or do BOND constraints provide the right semantics?]
  - Implication for Phase 74 generator: ...

## Q4 Answer: Aromatic Ring Establishment (D-04)

**Decision:** [EMERGENT / FORCE-REQUIRED] (from Arm A result)

**If EMERGENT:**
  - Phase 74 does NOT implement SKEL forcing
  - Implication: Phase 74 focuses on constraint preservation, not fragment insertion

**If FORCE-REQUIRED:**
  - Phase 74 implements aromatic detection + SKEL fragment insertion
  - Trigger condition: 4+ sp2 C in 110-160 ppm range in MULT definitions
  - Fragment file: benzene.mol (from iteration_03/filters/benzene.mol)
  - Implication for Phase 74: implement detect_aromatic_pattern() + emit SKEL/PATH/FEXP

## Direct Phase Implications

| Decision | Phase | Required Change |
|----------|-------|-----------------|
| D-01 (bond-range primary) | Phase 73 | Fix outlsd plumbing to make single-run work |
| D-02 (single path) | Phase 75 | Rewrite skill docs to single primary path |
| D-03 (native-only generator) | Phase 74 | Generator emits DEFF F/FEXP instead of DEFF NOT |
| D-03 (SYME translation) | Phase 74 | Decide and implement SYME native equivalent |
| D-04 (aromatic handling) | Phase 74 | Either skip or implement SKEL emission |
| Phase-65 re-evaluation | Phase 75 | Update skill knowledge of 4J/aromatic interaction |
```

---

## Validation Architecture

`workflow.nyquist_validation` is not explicitly set to `false` in `.planning/config.json` (key absent). Treat as enabled.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | None needed — phase produces a document artifact, not code |
| Quick run command | N/A (no code written) |
| Full suite command | `pytest` (regression only) |

### Phase Requirements → Verification Map

| Req ID | Behavior | Verification | Automated? |
|--------|----------|-------------|------------|
| DESIGN-01 | Decision document answers 4J + aromatic question with YES/NO + rationale | Check document exists with all required sections | Manual |
| DESIGN-01 | Phase-65 hypothesis re-evaluated against Arm A evidence | Arm A result in results.md | Manual + RDKit script |
| DESIGN-02 | Solver-path decision documented with agent-reversion remedy | Decision document section Q2 completed | Manual |

### Verifiable Experiment Gates

The experiment is complete and verifiable when:
1. `analysis/experiment/arm_a.sol` exists and `solncounter` contains a number
2. `analysis/experiment/arm_a_solutions.smi` is non-empty (or deliberately empty with 0 in solncounter)
3. RDKit aromatic check has been run on each SMILES in arm_a_solutions.smi and result recorded
4. Decision document `72-DECISIONS.md` contains explicit YES/NO for all four design questions
5. Each decision records its direct implication for Phases 73-75

### Wave 0 Gaps

- [ ] No new test files needed (phase produces documents, not code)
- [ ] Existing pytest suite must still pass (regression check on existing code)
- [ ] Experiment script (throwaway Python or bash) to run LSD binary + outlsd + RDKit check

---

## Security Domain

No authentication, persistence, or network access involved. Security domain does not apply to this phase (document + experiment only).

---

## State of the Art

| Old Approach (v8.0) | Current Approach (v9.0) | Impact |
|---------------------|------------------------|--------|
| SYME in emitted files | DUPL (or BOND constraints) in emitted files | Constraint-loss bug resolved at generation time |
| DEFF NOT SMARTS in emitted files | DEFF F + FEXP with existing filter files | Runs natively without translation layer |
| outlsd fed LSD input file | outlsd fed .sol file | Actual SMILES output instead of usage header |
| Dual-path documentation (LSD vs pyLSD) | Single primary path + subordinate fallback | Agent no longer reverts to better-documented path |
| Aromatic ring from SKEL fragment (forced) | Aromatic ring from constraints (empirical — D-04) | Whether SKEL still needed: experiment decides |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | COSY 4 7 and COSY 5 6 may implicitly force LSD toward ring topology even without SKEL | Experiment Design (Arm A), Pitfall 6 | If wrong: Arm A may produce 0 aromatic solutions even though the correct approach is emergent — would be misdiagnosed as FORCE-REQUIRED |
| A2 | DUPL is not an adequate translation of SYME (different semantics: dedup vs atom equivalence) | Native Command Reference (DUPL section) | If wrong: DUPL alone is sufficient and no additional constraint is needed for equivalence — simplifies Phase 74 |
| A3 | The 3 deferred 4J correlations (HMBC 3 8/3 13/3 9) are the only 4J suspects in ibuprofen CASE1 | Arm C design | If wrong: additional 4J correlations exist that are not flagged, affecting D-01 validation |
| A4 | `lucy lsd run` exit-255 is caused by the outlsd bug (not a fundamental LSD binary issue) | Pitfall 2 | If wrong: Phase 73 fix scope is different from runner._run_outlsd repair |

---

## Open Questions

1. **Is DUPL the correct native translation of SYME?**
   - What we know: DUPL is native and controls deduplication; SYME does not exist natively
   - What's unclear: Whether LSD uses SYME semantics (atom interchangeability) internally to prune the search space, or just for deduplication
   - Recommendation: The decision document should note "SYME translation is open — Phase 74 implements and tests"

2. **Does Arm A produce aromatic solutions? (D-04 empirical question)**
   - What we know: iter2 (without SKEL but also without SYME/DEFF NOT) → 5/90 aromatic; the confound was constraint loss
   - What's unclear: With SYME-equivalent BOND constraints + COSY aromatic constraints present, does LSD find the aromatic solution naturally?
   - Recommendation: This is exactly what the experiment settles. Run Arm A first.

3. **What file path strategy should Phase 74 generator use for DEFF filter files?**
   - What we know: iter3 used absolute paths; this works but is not portable
   - What's unclear: Whether Phase 74 should bundle filter files with the package or reference the LSD installation
   - Recommendation: Defer to Phase 74; the decision document should note this as an implementation detail for Phase 74.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| LSD binary | Experiment Arm A/B/C | Yes | 3.4.9 | None — required |
| outlsd binary | Solution conversion | Yes | (same as LSD) | None — required |
| ring3 filter file | Arm A/B/C DEFF F1 | Yes (at `/Users/steinbeck/Dropbox/develop/LSD/Filters/ring3`) | — | None — use absolute path |
| ring4 filter file | Arm A/B/C DEFF F2 | Yes (at `/Users/steinbeck/Dropbox/develop/LSD/Filters/ring4`) | — | None — use absolute path |
| benzene.mol fragment | Arm B SKEL F3 | Yes (at `iteration_03/filters/benzene.mol`) | — | Hand-copy to experiment dir |
| RDKit | Aromatic check | Yes (in existing venv, used by SolutionMerger) | — | Manual SMILES inspection |
| pytest | Regression suite | Yes | — | — |

**Missing dependencies with no fallback:** None — all required tools verified present.

---

## Sources

### Primary (HIGH confidence)
- `/Users/steinbeck/Dropbox/develop/LSD/LsdSrc/lecture.c` — complete native command table (lines 56-113); error message table (lines 433-632)
- `/Users/steinbeck/Dropbox/develop/LSD/MANUAL_ENG.html` — DUPL, DEFF, FEXP, SKEL, PATH, ELIM command documentation
- `iteration_03/compound_native.lsd` — verified working LSD file producing ibuprofen (2 solutions)
- `iteration_03/solutions.smi` + RDKit verification — confirmed ibuprofen InChI key HEFNNWSXXWATRW-UHFFFAOYSA-N
- `iteration_02/compound.lsd` — v8.0 agent file with SYME/DEFF NOT (non-native)
- `iteration_02/solutions.smi` + RDKit — 5/90 aromatic solutions without SKEL

### Secondary (MEDIUM confidence)
- `CASE-PROGRESS.md` (full UAT log) — outlsd invocation details, constraint loss forensics, intervention sequence
- `/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/v8.0-UAT-POSTMORTEM.md` — hard evidence table (on-disk vs log narrative)
- `iteration_02/outlsd.out` — confirmed 10-line usage header (the bug)

### Tertiary (LOW confidence — none in this research)

---

## Metadata

**Confidence breakdown:**
- Native command set: HIGH — verified from LSD source code (`lecture.c` command table)
- DEFF/FEXP/SKEL syntax: HIGH — verified from manual + on-disk working example
- DUPL vs SYME semantics: MEDIUM — source confirmed DUPL exists and SYME doesn't; exact equivalence semantics [ASSUMED]
- Experiment design: HIGH — derived from real on-disk artifacts with RDKit verification
- Arm A outcome: NOT KNOWN — this is the experiment's purpose

**Research date:** 2026-05-20
**Valid until:** Stable (LSD 3.4.9 source code is the version installed; no version change expected)
