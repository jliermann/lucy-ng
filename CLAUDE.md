# lucy-ng

AI-agent powered Computer-Assisted Structure Elucidation for organic natural products.

**For CASE workflow, run /lucy-ng:case. For all commands, run /lucy-ng (routing page).**

---

## Sub-Command Reference

Lucy-ng uses Claude Code sub-command skills for all workflows. Run `/lucy-ng` for the routing page.

| Command | Description |
|---------|-------------|
| `/lucy-ng:status` | Check environment readiness (lucy-ng version, LSD solver, database) |
| `/lucy-ng:dereplicate` | Match 13C NMR spectrum against compound database by molecular formula |
| `/lucy-ng:predict` | Predict 13C chemical shifts for a SMILES structure using HOSE-code database |
| `/lucy-ng:sanitise` | Remove compound identifiers from NMR dataset for blind CASE evaluation |
| `/lucy-ng:case` | Full autonomous CASE workflow — spawns agent, monitors progress, detects loops, intervenes |

**Agent files** (spawned by /lucy-ng:case orchestrator):
- `~/.claude/agents/lucy-case-agent.md` — Autonomous CASE agent with inlined NMR/LSD knowledge
- `~/.claude/agents/lucy-diagnostic.md` — LSD failure diagnostic specialist (spawned after 2 failed interventions)

---

## End-User Setup (First-Time Installation)

When a user asks to set up structure elucidation or perform CASE, run these checks:

### 1. Install lucy-ng
```bash
lucy --version || pip install lucy-ng
```

### 2. Check LSD Solver (REQUIRED)
```bash
lucy lsd check
```

If LSD is not found:
- Download from: http://eos.univ-reims.fr/LSD/
- Extract the archive
- Add the `bin/` directory to PATH (contains `LSD` and `outlsd`)
- Both `LSD` and `outlsd` are required for full functionality

### 3. Verify Setup
```bash
lucy lsd check
```
Should report both LSD and outlsd as available.

### 4. Download Compound Database (REQUIRED)
```bash
lucy database download
```

This downloads the pre-built compound database (~830 MB compressed) from Figshare:
- DOI: 10.6084/m9.figshare.31073554
- Contains 928K compounds (COCONUT + NMRShiftDB) with 13C NMR shifts
- Contains 7.9M HOSE statistics for 13C shift prediction
- Auto-decompresses to `data/reference/lucy-ng-derep.db` (~2.8 GB)

Verify installation:
```bash
lucy database info data/reference/lucy-ng-derep.db
```

---

## CLI Output Reference

All lucy-ng commands support `--format json` for programmatic use. The AI agent uses thin CLI commands via Bash. Domain intelligence is encoded in sub-command skills and agent definitions.

| Command | Key Output Fields (JSON) |
|---------|--------------------------|
| `lucy read 1d` | nucleus, frequency, ppm_range, data_points |
| `lucy read 2d` | experiment_type, nuclei, frequency, shape |
| `lucy pick 1d` | count, peaks (ppm, intensity) |
| `lucy pick 2d` | experiment_type, count, peaks (f1, f2, intensity) |
| `lucy pick hsqc` | experiment_type, count, peaks (f1, f2, intensity) |
| `lucy pick hmbc` | experiment_type, count, peaks (f1, f2, intensity) |
| `lucy analyze symmetry` | formula, expected_carbons, observed_peaks, difference |
| `lucy dereplicate c13` | is_match, top_matches (name, smiles, score) |
| `lucy predict c13` | predictions (atom_index, shift, confidence), success |
| `lucy lsd rank` | ranked_solutions (smiles, mae, quality, deviations) |

---

## CLI Syntax Reference

### Dereplication

**From Bruker Spectrum (preferred)**
```bash
lucy dereplicate c13 <bruker_experiment_path> <formula>
```
Example:
```bash
lucy dereplicate c13 data/compound/2 C14H16 -n 10
```

**From Shift List**
```bash
lucy dereplicate c13 --shifts "139.94,138.51,137.16,136.53" C14H16 -n 10
```

### LSD Integration

**Run LSD**
```bash
lucy lsd run compound.lsd
```

**Convert solutions to SMILES**
```bash
outlsd 5 < compound.sol > solutions.smi
```

**Rank solutions**
```bash
lucy lsd rank solutions.smi --shifts "155.08,151.58,..."
```

**LSD file structure:**

The AI agent writes LSD files directly using skill knowledge (see skill/SKILL.md and skill/diagnostic/SKILL.md for LSD command reference).

Example structure:
```
; Comments start with semicolon
MULT 1 C 2 0    ; Define atoms with MULT
MULT 2 C 2 0
...
HSQC 4 4        ; Define correlations (HSQC FIRST!)
HMBC 2 8        ; Then HMBC
...
; NO ELIM command on first run - only add if needed
```

**Note:** LSD does NOT have a molecular formula command. The formula is defined implicitly by the sum of all MULT atom definitions. Do NOT use `FORM`, `FORMULA`, or similar commands - these are invalid in LSD.

**LSD Runner Notes:**
- LSD writes solution count to **stderr**, not stdout
- Success is determined by finding solutions, not just return code
- Solution files are written as `.sol` files in the working directory

### 13C Shift Prediction

**CLI Usage**
```bash
# Predict shifts for a SMILES string (auto-detects database)
lucy predict c13 "CCO"

# JSON output for programmatic use
lucy predict c13 "CCO" --format json
```

**Python API**
```python
from lucy_ng.prediction import C13Predictor

predictor = C13Predictor.from_database("data/reference/lucy-ng-derep.db")
result = predictor.predict_from_smiles("CCO")  # Ethanol
print(result.summary())
```

---

## Peak Picking API Reference

**Note:** These Python APIs are available for library use. The AI agent uses thin CLI commands via Bash instead — see /lucy-ng:case sub-command for the recommended CASE workflow.

### HSQC: DEPT-Guided Picker

```python
from lucy_ng import BrukerReader
from lucy_ng.processing import DEPTGuidedPicker

hsqc = BrukerReader.read_2d("data/Ibuprofen/6")      # HSQC
dept135 = BrukerReader.read_1d("data/Ibuprofen/3")   # DEPT-135
dept90 = BrukerReader.read_1d("data/Ibuprofen/4")    # DEPT-90 (optional)

# With DEPT-90 for full CH/CH3 disambiguation
result = DEPTGuidedPicker.pick_hsqc_peaks_with_dept90(hsqc, dept135, dept90)

# Or with DEPT-135 only (CH and CH3 remain ambiguous as "CH/CH3")
result = DEPTGuidedPicker.pick_hsqc_peaks(hsqc, dept135)

print(result.summary())
# Access: result.peaks, result.carbon_multiplicities, result.all_carbons_found
```

### HMBC: Guided Picker

```python
from lucy_ng import BrukerReader
from lucy_ng.processing import HMBCGuidedPicker

hmbc = BrukerReader.read_2d("data/Ibuprofen/7")
c13 = BrukerReader.read_1d("data/Ibuprofen/2")
hsqc = BrukerReader.read_2d("data/Ibuprofen/6")
dept135 = BrukerReader.read_1d("data/Ibuprofen/3")  # optional

result = HMBCGuidedPicker.pick_hmbc_peaks_from_spectra(
    hmbc=hmbc,
    carbon_spectrum=c13,
    hsqc=hsqc,
    dept135=dept135,  # optional, adds extra carbon positions
)

print(result.summary())
# Access: result.peaks, result.validated_count, result.rejected_count
```

### Other 2D Spectra (COSY, etc.)

```python
from lucy_ng.processing import PeakPicker2D

cosy = BrukerReader.read_2d("data/Ibuprofen/5")
peaks = PeakPicker2D.pick_peaks(cosy, threshold=0.05)
```

---

## Developer Reference

### Quick Reference

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=lucy_ng

# Type checking
mypy src/lucy_ng

# Linting
ruff check src tests

# Build package
hatch build
```

### Project Structure

```
src/lucy_ng/
├── models/          # Pydantic v2 data models (Spectrum1D, Spectrum2D, Peak1D, etc.)
├── readers/         # NMR file readers (BrukerReader)
├── processing/      # Peak picking, signal processing
├── dereplication/   # Database matching (NMRShiftDBLoader, SpectrumMatcher)
├── solvers/         # LSD/pyLSD integration (future)
└── __init__.py      # Public API exports

tests/               # pytest tests
data/                # Test NMR datasets (Bruker format)
.planning/           # GSD planning files (PROJECT.md, ROADMAP.md, STATE.md)
```

### Technology Stack

- **Python 3.10+** - minimum version
- **Pydantic v2** - data models with validation
- **nmrglue** - Bruker NMR file parsing
- **NumPy/SciPy** - numerical processing
- **RDKit** - SD file parsing for reference databases
- **hatch** - build system
- **pytest** - testing
- **ruff** - linting
- **mypy** - type checking (strict mode)

### Critical Architecture Decisions

#### HOSE Codes: NO Explicit Hydrogens

**All HOSE code operations MUST use molecules WITHOUT explicit hydrogens.**

This is critical for consistency between database generation and prediction. Using inconsistent hydrogen handling causes 100% prediction failures.

| Operation | Correct Approach |
|-----------|------------------|
| Database generation | Read SDF → do NOT call `AddHs()` → generate HOSE |
| Prediction from SMILES | `MolFromSmiles()` (implicit H) → generate HOSE |
| Prediction from MOL | `MolFromMolBlock(removeHs=True)` → generate HOSE |

**Example:**
```python
# CORRECT - no explicit H
mol = Chem.MolFromSmiles("CCO")  # 3 atoms
hose = generate_for_atom(mol, 0, radius=1)  # "C-4;C(//)"

# WRONG - causes mismatch
mol = Chem.AddHs(Chem.MolFromSmiles("CCO"))  # 9 atoms
hose = generate_for_atom(mol, 0, radius=1)  # "C-4;HHHC(//)" - WON'T MATCH!
```

#### COCONUT Atom Indices: 1-Based

COCONUT SDF files use **1-based** atom indices in the `CNMR_SHIFTS` field. When parsing, convert to 0-based for RDKit:

```python
atom_idx_0based = int(atom_idx_from_coconut) - 1
```

---

## Database Reference

The pre-built SQLite database contains:

| Property | Value |
|----------|-------|
| **DOI** | [10.6084/m9.figshare.31073554](https://doi.org/10.6084/m9.figshare.31073554) |
| **Compounds** | 928,443 (COCONUT + NMRShiftDB) |
| **HOSE Statistics** | 7.9M entries for 13C prediction |
| **Formulas** | 111,493 unique |
| **Size** | ~830 MB download, ~2.8 GB uncompressed |

This single database powers **both** dereplication (formula-indexed compound lookup) and 13C prediction (HOSE-based shift calculation for ranking LSD solutions).
