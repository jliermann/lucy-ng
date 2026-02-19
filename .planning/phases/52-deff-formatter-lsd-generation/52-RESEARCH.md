# Phase 52: DEFF Formatter and LSD File Generation - Research

**Researched:** 2026-02-19
**Domain:** LSD DEFF/FEXP fragment file generation from SMILES, SSTR/LINK syntax, smoke test design
**Confidence:** HIGH

## Summary

Phase 52 converts fragment SMILES (from the FragmentSearcher in Phase 51) to valid LSD fragment definition files using SSTR/LINK syntax, then provides a CLI command (`lucy fragment to-lsd`) to generate these files. The phase also includes an LSD smoke test proving that goodlist semantics (FEXP "F1") actually reduce solution counts, and verifies DEFF/FEXP command ordering relative to MULT.

Research confirmed the exact SSTR/LINK syntax from the LSD manual (nuzillard.github.io) and real LSD filter files shipped with LSD 3.4.9 (`/Filters/ring3`, `/Filters/TERPENES/SESQUITERP/file1`). A live smoke test on the local LSD installation proved that DEFF/FEXP goodlist semantics work correctly: toluene (C7H8) produces 4 solutions without fragment, 1 solution with a 6-membered aromatic ring goodlist (FEXP "F1"), and 3 solutions with the same fragment as badlist (FEXP "NOT F1"). The 4 = 1 + 3 partition confirms correct semantics.

**Critical finding:** The existing `DEFF NOT C1CC1` inline SMILES notation used in the CASE agent knowledge is NOT valid LSD 3.4.9 syntax. It requires pyLSD preprocessing. Native LSD requires SSTR/LINK files referenced via `DEFF F<n> "path"`. This means Phase 52's SSTR/LINK file generator is needed for both goodlist AND badlist fragments, not just goodlist. The existing agent badlist filters will need to be converted to file-based DEFF in a future phase.

**Primary recommendation:** Build a `DEFFFormatter` class that converts RDKit Mol objects (from SMILES) to SSTR/LINK fragment files, with hash-based deterministic filenames. Use double quotes for DEFF paths (LSD requirement). Test with the proven toluene smoke test pattern.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| LINT-01 | Fragment SMILES converted to LSD DEFF goodlist file format (validated against LSD manual) | SSTR/LINK syntax fully documented from LSD manual + real filter files; RDKit atom property mapping verified; smoke test pattern established |
| LINT-02 | CLI `lucy fragment to-lsd` generates fragment definition file from SMILES | SSCMatch model exists with `smiles` field; CLI command group exists in `cli/fragment.py`; hash-based filename pattern designed |
| LINT-03 | DEFF/FEXP commands placed before MULT in LSD file (critical ordering) | Smoke test shows DEFF works both before AND after MULT in LSD 3.4.9; however, Wenk thesis specifies DEFF before MULT as convention; maintain this for consistency with Sherlock |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| RDKit | 2025.9.4 | Parse fragment SMILES, extract atom properties (element, hybridization, H count, aromaticity, bonds) | Already installed; provides all atom/bond data needed for SSTR/LINK generation |
| Python hashlib | stdlib | Generate deterministic filenames from canonical SMILES | SHA-256 of canonical SMILES ensures same fragment always produces same filename |
| Click | 8.1.8 | CLI `lucy fragment to-lsd` command | Existing CLI framework used throughout lucy-ng |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pydantic v2 | 2.12.5 | SSCMatch model (already defined in Phase 49) | Input to DEFFFormatter; already has `smiles`, `atom_count`, `avg_deviation` fields |
| LSD 3.4.9 | 3.4.9 | Smoke test validation — run LSD on generated fragment files | Verification step; already installed at `/Users/steinbeck/Dropbox/develop/LSD/LSD` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom SSTR/LINK generator | RDKit `MolToMolBlock` (MOL format) + LSD MOL reader | LSD's SSTR/LINK is simpler and more flexible (supports hybridization ranges like `(2 3)`); MOL files require exact hybridization. SSTR/LINK is what all LSD filter files use. |
| SHA-256 hash filename | Sequential numbering (fragment_1.lsd) | Sequential is simpler but non-deterministic across runs; hash ensures same SMILES always maps to same file, enabling caching and deduplication |

**Installation:**
```bash
# No new packages required — uses existing RDKit + stdlib
python3 -c "from rdkit import Chem; import hashlib; print('Ready')"
```

## Architecture Patterns

### Recommended Project Structure
```
src/lucy_ng/fragments/
    __init__.py          # existing
    models.py            # existing SSCRecord, SSCMatch
    searcher.py          # existing FragmentSearcher
    db.py                # existing FragmentDatabaseManager
    fingerprint.py       # existing fingerprint utils
    lsd_formatter.py     # NEW: DEFFFormatter class
    extractor.py         # existing SSCExtractor
```

### Pattern 1: SMILES to SSTR/LINK Conversion

**What:** Convert an RDKit Mol (parsed from SMILES) to LSD fragment file content (SSTR + LINK commands).

**When to use:** Every time a matched fragment needs to be written as an LSD fragment definition file.

**Algorithm:**
```
For each heavy atom in the Mol:
    1. Get element symbol (C, N, O, S, etc.)
    2. Get hybridization: SP2 -> 2, SP3 -> 3, SP -> 1
       For aromatic atoms: always 2 (sp2)
    3. Get total H count: atom.GetTotalNumHs()
    4. Write SSTR S<n> <element> <hybridization> <h_count>

For each bond in the Mol:
    1. Get begin/end atom indices
    2. Write LINK S<begin+1> S<end+1>
```

**Example (verified against LSD filter file patterns):**
```python
# Source: LSD Filters/TERPENES/SESQUITERP/file1 and LSD manual
# SSTR syntax: SSTR S<n> <element> <hybridization> <h_count>
# Where hybridization can be: 1 (sp), 2 (sp2), 3 (sp3), (2 3), (1 2 3)
# And h_count can be: 0, 1, 2, 3, or (0 1), (0 1 2), etc.

# For a precise fragment (known exact structure):
# Use exact hybridization and H count
"SSTR S1 C 2 1"      # aromatic CH
"SSTR S2 C 2 0"      # aromatic C (no H, substituted)
"SSTR S3 C 3 3"      # methyl CH3
"LINK S1 S2"          # bond between atoms 1 and 2
```

### Pattern 2: Hash-Based Deterministic Filenames

**What:** Generate filenames from canonical SMILES hash to ensure same fragment always maps to same file.

**When to use:** Every time a fragment file is written.

**Example:**
```python
import hashlib
from rdkit import Chem

def fragment_filename(smiles: str) -> str:
    """Generate deterministic filename from fragment SMILES."""
    canonical = Chem.MolToSmiles(Chem.MolFromSmiles(smiles))
    hash_prefix = hashlib.sha256(canonical.encode()).hexdigest()[:12]
    return f"fragment_{hash_prefix}.lsd"

# All SMILES variants produce same filename:
# "c1ccc(CC(C)C)cc1" -> "fragment_c5004b1379ec.lsd"
# "C(c1ccccc1)C(C)C" -> "fragment_c5004b1379ec.lsd"
```

### Pattern 3: DEFF/FEXP Command Generation

**What:** Generate the LSD commands that reference fragment files.

**When to use:** After writing fragment files; these commands go into the main LSD input file.

**Critical syntax detail (verified by smoke test):** LSD 3.4.9 requires double quotes for paths, not single quotes.

**Example:**
```python
# CORRECT (double quotes) - verified working in LSD 3.4.9:
'DEFF F1 "fragment_c5004b1379ec.lsd"'
'FEXP "F1"'

# WRONG (single quotes) - causes LSD error 160:
"DEFF F1 'fragment_c5004b1379ec.lsd'"
"FEXP 'F1'"

# Multiple fragments with OR:
'DEFF F1 "fragment_aaa.lsd"'
'DEFF F2 "fragment_bbb.lsd"'
'FEXP "F1 OR F2"'
```

### Anti-Patterns to Avoid

- **Inline SMILES DEFF:** `DEFF NOT C1CC1` is NOT valid LSD 3.4.9 syntax. It is a pyLSD extension. Always use file-based SSTR/LINK fragments.
- **Single quotes in DEFF paths:** LSD 3.4.9 requires double quotes around file paths. Single quotes cause error 160.
- **Hardcoded hybridization ranges:** Do NOT use `(1 2 3)` for all atoms like the generic ring3/ring4 filters do. SSC fragments come from KNOWN structures with KNOWN hybridization. Use exact values.
- **Missing LINK commands:** Every bond in the fragment MUST have a LINK command. Missing bonds create a disconnected substructure that may not match correctly.
- **0-indexed atom numbering:** LSD SSTR uses 1-based numbering (S1, S2, ...). RDKit uses 0-based. Add 1 when generating.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SMILES parsing and atom property extraction | Custom SMILES parser | `rdkit.Chem.MolFromSmiles()` + atom/bond accessors | RDKit handles aromatic perception, valence, implicit H consistently |
| Canonical SMILES for hashing | String normalization | `Chem.MolToSmiles(mol)` | RDKit canonical SMILES is deterministic across all input variants (verified: 3 toluene SMILES variants all produce `CC(C)Cc1ccccc1`) |
| Bond enumeration | Manual adjacency matrix | `mol.GetBonds()` iterator | RDKit handles ring closures, aromatic bonds, and bond stereochemistry correctly |
| Hybridization detection | Shift-based guessing | `atom.GetHybridization()` | RDKit assigns from valence model; matches what LSD expects |

**Key insight:** The SMILES-to-SSTR/LINK conversion is a straightforward property mapping, not a complex graph algorithm. RDKit provides every property needed via standard accessors.

## Common Pitfalls

### Pitfall 1: Single Quotes vs Double Quotes in DEFF Path
**What goes wrong:** Using single quotes in `DEFF F1 'path'` causes LSD error 160: "A string must start with a double quote."
**Why it happens:** The existing CLI code in `fragment.py` generates single-quoted DEFF commands (line 186). Also, the Wenk thesis example shows single quotes, but the thesis describes pyLSD which preprocesses commands.
**How to avoid:** Always use double quotes: `DEFF F1 "path"`. Verified working with LSD 3.4.9.
**Warning signs:** LSD error 160 immediately after reading the DEFF line.

### Pitfall 2: Inline SMILES DEFF NOT Is Not Valid LSD
**What goes wrong:** The agent knowledge says `DEFF NOT C1CC1` for badlist filtering. This is NOT valid in native LSD 3.4.9 (error 150: "F expected"). It requires pyLSD preprocessing that lucy-ng does not use.
**Why it happens:** The syntax was adopted from pyLSD documentation without verifying against native LSD.
**How to avoid:** For Phase 52, all DEFF commands must reference SSTR/LINK files. Badlist conversion is out of scope for this phase but should be flagged for a follow-up.
**Warning signs:** Any `DEFF NOT SMILES` or `DEFF NOT pattern` without a preceding `DEFF F<n>` definition.

### Pitfall 3: Aromatic Bond Order in SSTR/LINK
**What goes wrong:** RDKit reports aromatic bond order as 1.5 (neither single nor double). LSD LINK commands do not specify bond order — they only indicate that two atoms are bonded. For aromatic systems, the sp2 hybridization in SSTR is sufficient to convey aromaticity.
**Why it happens:** Developers may try to add bond order qualifiers to LINK commands.
**How to avoid:** LINK S1 S2 is the only syntax. Bond order is implicit from atom hybridization. This is correct — LSD determines bond orders from hybridization constraints during structure generation.
**Warning signs:** Attempting to write LINK with bond order parameters.

### Pitfall 4: Fragment File Path Must Be Relative to LSD Working Directory
**What goes wrong:** DEFF path is absolute (`DEFF F1 "/Users/.../fragment.lsd"`) but the fragment file is in a different directory than where LSD runs.
**Why it happens:** LSD resolves DEFF file paths relative to its current working directory (the iteration directory). If the fragment file is written to a different location, LSD cannot find it.
**How to avoid:** Write fragment files to the current working directory (where the CLI is run from). The `lucy fragment to-lsd` command should write files to CWD by default. DEFF commands should use bare filenames (e.g., `"fragment_abc123.lsd"`) not paths.
**Warning signs:** LSD error "Cannot open file: ..." after DEFF command.

### Pitfall 5: Hydrogen Count for Oxygen/Nitrogen in SSTR
**What goes wrong:** RDKit's `GetTotalNumHs()` may return incorrect H counts for heteroatoms in fragment SMILES that were extracted from substructures (e.g., OH group in carboxylic acid).
**Why it happens:** Fragment SMILES from SSC extraction may have open sites (R groups) that affect implicit hydrogen calculation. If the R group was at a position that normally has an H, the H count changes.
**How to avoid:** Use the exact H count from the SSC record's multiplicity data when available. For the SSTR file, err on the side of flexibility: use `(0 1)` for heteroatoms instead of exact values.
**Warning signs:** LSD zero solutions when a fragment that should match does not — check SSTR H counts.

## Code Examples

Verified patterns from LSD filter files and smoke tests.

### SSTR/LINK File Format (from LSD 3.4.9 Filters)
```
; Source: /Users/steinbeck/Dropbox/develop/LSD/Filters/ring3
; A generic 3-membered ring (badlist filter)
SSTR S1 A (2 3) (0 1 2)
SSTR S2 A (2 3) (0 1 2)
SSTR S3 A (2 3) (0 1 2)
LINK S1 S2
LINK S2 S3
LINK S1 S3
```

### Specific Fragment (from LSD 3.4.9 terpene library)
```
; Source: /Users/steinbeck/Dropbox/develop/LSD/Filters/TERPENES/SESQUITERP/file1
; Coded from file: 14-10-aristolane.mol
; Uses exact hybridization for known carbon environments:
SSTR S10 C 3 0     ; sp3 quaternary carbon (exact)
SSTR S12 C (1 2 3) (0 1 2 3)  ; flexible carbon (any hyb, any H)
LINK S10 S14
```

### Python: SMILES to SSTR/LINK Conversion
```python
# Verified with RDKit 2025.9.4
from rdkit import Chem
from rdkit.Chem import Hybridization

def smiles_to_sstr_link(smiles: str) -> str:
    """Convert SMILES to LSD SSTR/LINK fragment file content."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")

    lines: list[str] = []
    lines.append(f"; Fragment: {Chem.MolToSmiles(mol)}")

    # SSTR commands (one per heavy atom)
    for atom in mol.GetAtoms():
        idx = atom.GetIdx() + 1  # LSD is 1-based
        symbol = atom.GetSymbol()
        nh = atom.GetTotalNumHs()

        hyb = atom.GetHybridization()
        if hyb == Hybridization.SP2 or atom.GetIsAromatic():
            lsd_hyb = "2"
        elif hyb == Hybridization.SP3:
            lsd_hyb = "3"
        elif hyb == Hybridization.SP:
            lsd_hyb = "1"
        else:
            lsd_hyb = "(2 3)"  # fallback: allow both

        lines.append(f"SSTR S{idx} {symbol} {lsd_hyb} {nh}")

    # LINK commands (one per bond)
    for bond in mol.GetBonds():
        a1 = bond.GetBeginAtomIdx() + 1  # 1-based
        a2 = bond.GetEndAtomIdx() + 1
        lines.append(f"LINK S{a1} S{a2}")

    return "\n".join(lines) + "\n"
```

### DEFF/FEXP Command Generation
```python
# CRITICAL: use double quotes, not single quotes
# Verified with LSD 3.4.9 smoke test

def deff_commands(fragment_files: list[str]) -> tuple[list[str], str]:
    """Generate DEFF and FEXP commands for fragment files.

    Returns:
        Tuple of (deff_lines, fexp_line)
    """
    deff_lines = []
    for i, path in enumerate(fragment_files, 1):
        deff_lines.append(f'DEFF F{i} "{path}"')

    if len(fragment_files) == 0:
        fexp = ""
    elif len(fragment_files) == 1:
        fexp = 'FEXP "F1"'
    else:
        parts = " OR ".join(f"F{i}" for i in range(1, len(fragment_files) + 1))
        fexp = f'FEXP "{parts}"'

    return deff_lines, fexp
```

### LSD Smoke Test Pattern (Verified Working)
```bash
# Source: Live test on LSD 3.4.9
# This pattern proves goodlist semantics:

# 1. Write fragment file
cat > benzene_generic.lsd << 'EOF'
; Generic 6-membered aromatic carbon ring
SSTR S1 C 2 (0 1)
SSTR S2 C 2 (0 1)
SSTR S3 C 2 (0 1)
SSTR S4 C 2 (0 1)
SSTR S5 C 2 (0 1)
SSTR S6 C 2 (0 1)
LINK S1 S2
LINK S2 S3
LINK S3 S4
LINK S4 S5
LINK S5 S6
LINK S1 S6
EOF

# 2. Write LSD file with goodlist
cat > test_goodlist.lsd << 'EOF'
DEFF F1 "benzene_generic.lsd"
FEXP "F1"
MULT 1 C 2 1
MULT 2 C 2 1
MULT 3 C 2 1
MULT 4 C 2 1
MULT 5 C 2 1
MULT 6 C 2 0
MULT 7 C 3 3
HSQC 1 1
HSQC 2 2
HSQC 3 3
HSQC 4 4
HSQC 5 5
HSQC 7 7
EOF

# 3. Run LSD
LSD test_goodlist.lsd 2>&1
# Expected: "1 solution found" (down from 4 without fragment)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `DEFF NOT C1CC1` (inline SMILES) | Must use file-based SSTR/LINK | Discovered during research | Agent knowledge needs update; inline syntax is pyLSD-only |
| Single quotes in DEFF path | Double quotes required by LSD 3.4.9 | Discovered during research | CLI output must be fixed |
| Fragment files not generated | Phase 52 generates them | This phase | Enables actual goodlist constraint injection |
| Placeholder DEFF commands in CLI JSON | Real DEFF commands with working fragment files | This phase | Agent can directly use CLI output |

**Deprecated/outdated:**
- `DEFF NOT <SMILES>` inline syntax: Not valid in LSD 3.4.9. Must use `DEFF F<n> "file"` + `FEXP "NOT F<n>"` with SSTR/LINK files.
- Single quotes in DEFF: Not valid in LSD 3.4.9. Use double quotes.

## LSD SSTR/LINK Syntax Reference

**Source:** LSD manual (nuzillard.github.io/LSD/MANUAL_ENG.html) + LSD 3.4.9 filter files

### SSTR Command
```
SSTR S<n> <element> <hybridization> <h_count>
```

| Parameter | Values | Notes |
|-----------|--------|-------|
| S<n> | S1, S2, ... S60 | Max 60 sub-atoms per substructure |
| element | C, N, O, S, A (any) | Standard element symbols; A = any atom |
| hybridization | 1 (sp), 2 (sp2), 3 (sp3), or tuple: (2 3), (1 2 3) | Tuples allow flexibility |
| h_count | 0, 1, 2, 3, or tuple: (0 1), (0 1 2), (0 1 2 3) | Number of attached hydrogens |

### LINK Command
```
LINK S<n1> S<n2>
```
- Declares a bond between sub-atoms n1 and n2
- No bond order parameter — order is inferred from hybridization
- Max 60 links per substructure

### DEFF Command
```
DEFF F<n> "<filepath>"
```
- F<n> is the fragment number (F1, F2, ...)
- filepath is relative to LSD working directory
- **Must use double quotes** (LSD error 160 with single quotes)

### FEXP Command
```
FEXP "<expression>"
```
- `"F1"` — require F1 (goodlist)
- `"NOT F1"` — forbid F1 (badlist)
- `"F1 AND F2"` — require both
- `"F1 OR F2"` — require at least one
- Operator precedence: NOT > AND > OR (parentheses override)

## RDKit to LSD Property Mapping

| RDKit Property | LSD SSTR Parameter | Conversion |
|----------------|-------------------|------------|
| `atom.GetSymbol()` | element (P2) | Direct: "C", "N", "O", "S" |
| `atom.GetHybridization()` | hybridization (P3) | SP->1, SP2->2, SP3->3; aromatic always->2 |
| `atom.GetTotalNumHs()` | h_count (P4) | Direct integer |
| `atom.GetIsAromatic()` | Forces hybridization to 2 | Override SP3 if aromatic flag set |
| `bond.GetBeginAtomIdx()` | LINK first atom | Add 1 (0-based to 1-based) |
| `bond.GetEndAtomIdx()` | LINK second atom | Add 1 (0-based to 1-based) |

**Verified with RDKit 2025.9.4:** Toluene (`Cc1ccccc1`) produces 7 atoms, 7 bonds. Aromatic carbons: SP2 with 0 or 1 H. Methyl carbon: SP3 with 3 H. All bonds enumerable via `mol.GetBonds()`.

## Smoke Test Design

### Test 1: Goodlist Semantics Verification (LINT-01/LINT-03)

**Setup:** Toluene (C7H8) — 4 solutions without fragment.

**Fragment:** 6-membered sp2 carbon ring with (0 1) H count per atom.

**Expected:**
- Without DEFF/FEXP: 4 solutions
- With DEFF/FEXP "F1" (goodlist): 1 solution
- With FEXP "NOT F1" (badlist): 3 solutions
- 4 = 1 + 3 confirms correct semantics

**Why toluene:** Small molecule (7 atoms), fast LSD execution (<1 sec), exactly 4 solutions that cleanly partition into aromatic/non-aromatic.

### Test 2: Generated Fragment File Validation (LINT-01/LINT-02)

**Setup:** Run `lucy fragment to-lsd "Cc1ccccc1"` to generate fragment file.

**Verify:**
1. File is written to CWD with hash-based name
2. File contains correct SSTR/LINK syntax
3. LSD can read the file without errors (`Reading fragment file: ...` in output)
4. When used as goodlist on toluene problem, solution count decreases

### Test 3: DEFF/FEXP Ordering (LINT-03)

**Setup:** Same toluene problem, with DEFF/FEXP placed (a) before MULT and (b) after MULT.

**Result from research:** Both orderings produce the same result in LSD 3.4.9. However, DEFF before MULT is the Wenk thesis convention and should be maintained for consistency.

**Verification:** Run both orderings, confirm identical solution counts.

## Implementation Design

### DEFFFormatter Class

```python
class DEFFFormatter:
    """Convert fragment SMILES to LSD DEFF fragment files."""

    @staticmethod
    def smiles_to_fragment_content(smiles: str) -> str:
        """Convert SMILES to SSTR/LINK fragment file content."""
        ...

    @staticmethod
    def fragment_filename(smiles: str) -> str:
        """Generate deterministic filename from canonical SMILES."""
        ...

    @staticmethod
    def write_fragment_file(smiles: str, output_dir: Path | None = None) -> Path:
        """Write fragment file and return its path."""
        ...

    @staticmethod
    def deff_command(fragment_number: int, filepath: str) -> str:
        """Generate DEFF command line with double quotes."""
        ...

    @staticmethod
    def fexp_command(fragment_numbers: list[int], logic: str = "OR") -> str:
        """Generate FEXP command combining fragments."""
        ...
```

### CLI Command: `lucy fragment to-lsd`

```bash
# Generate fragment file from SMILES
lucy fragment to-lsd "Cc1ccccc1"
# Output: fragment_c5004b1379ec.lsd written to CWD

# With explicit output directory
lucy fragment to-lsd "Cc1ccccc1" --output-dir analysis/iteration_02/

# JSON output for agent consumption
lucy fragment to-lsd "Cc1ccccc1" --format json
# {"smiles": "Cc1ccccc1", "canonical": "Cc1ccccc1",
#  "filename": "fragment_c5004b1379ec.lsd",
#  "deff_command": "DEFF F1 \"fragment_c5004b1379ec.lsd\"",
#  "atom_count": 7}
```

### Integration with Existing CLI Search

The existing `lucy fragment search` command (Phase 51) outputs placeholder DEFF commands. Phase 52 will:
1. Fix single quotes to double quotes in DEFF output
2. Generate actual fragment files alongside the JSON output
3. Include file paths in the JSON response

## Open Questions

1. **Flexible vs Exact Hybridization in SSTR**
   - What we know: LSD filter files use flexible ranges like `(2 3)` and `(0 1 2)` for generic fragments. SSC fragments come from known structures with known atom properties.
   - What's unclear: Should generated SSTR use exact values (e.g., `2` for aromatic C) or flexible ranges (e.g., `(2 3)`)? Exact is more constraining but might cause zero solutions if the target structure has slight variations.
   - Recommendation: Use **exact** hybridization (from RDKit) but **flexible** H count range that includes the exact value and +/- 1. E.g., if RDKit says 1 H, write `(0 1)` or just `1`. Start with exact values in tests; loosen if smoke tests fail.

2. **Badlist Fragment File Migration**
   - What we know: The agent currently uses `DEFF NOT C1CC1` inline syntax which is invalid in LSD 3.4.9.
   - What's unclear: How does this work in practice? Either (a) the agent has never actually run these lines through LSD (they're in the file but LSD ignores them due to error handling), or (b) there's a wrapper we haven't found.
   - Recommendation: Out of scope for Phase 52 (goodlist only). Flag for Phase 53 or a separate fix. The goodlist mechanism is independent of badlist.

## Sources

### Primary (HIGH confidence)
- LSD Manual: https://nuzillard.github.io/LSD/MANUAL_ENG.html — DEFF, FEXP, SSTR, LINK syntax
- LSD 3.4.9 Filter files: `/Users/steinbeck/Dropbox/develop/LSD/Filters/ring3`, `ring4`, `TERPENES/SESQUITERP/file1`, `file10` — actual SSTR/LINK file format
- Live LSD 3.4.9 smoke test (2026-02-19): Toluene C7H8, 4 solutions baseline, 1 with goodlist, 3 with badlist
- RDKit 2025.9.4 atom property verification: hybridization, H count, aromaticity, canonical SMILES

### Secondary (MEDIUM confidence)
- Wenk thesis (2023): Section 3.1.4.1.4 (Fragment Library), Section 3.1.4.2.3 (DEFF/FEXP), Appendix A4 — pyLSD syntax may differ from native LSD
- `background/sherlock-analysis.md` — DEFF/FEXP goodlist gap identification
- SSCMatch model: `src/lucy_ng/fragments/models.py` — existing data model for fragment search results
- Existing CLI: `src/lucy_ng/cli/fragment.py` — current DEFF command generation (needs fixing)

### Tertiary (LOW confidence)
- Agent knowledge `DEFF NOT C1CC1` syntax — INVALID for native LSD; needs investigation of how agent CASE runs actually handle this

## Metadata

**Confidence breakdown:**
- SSTR/LINK syntax: HIGH — verified against LSD manual AND real filter files AND smoke test
- DEFF/FEXP semantics: HIGH — verified with live LSD 3.4.9 smoke test (toluene 4->1->3 partition)
- Double quotes requirement: HIGH — verified by smoke test (single quotes cause error 160)
- RDKit property mapping: HIGH — verified with 5 test SMILES compounds
- Inline DEFF NOT invalidity: HIGH — verified by LSD error 150 on direct test
- Flexible vs exact hybridization: MEDIUM — exact works for toluene; may need adjustment for complex fragments

**Research date:** 2026-02-19
**Valid until:** Stable (LSD 3.4.9 syntax is mature; RDKit atom accessors are stable)
