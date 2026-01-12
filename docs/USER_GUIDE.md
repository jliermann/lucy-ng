# User Guide

This guide provides comprehensive documentation for using lucy-ng through the CLI, Python API, and MCP server.

## Table of Contents

- [Overview](#overview)
- [Command-Line Interface](#command-line-interface)
- [Python API](#python-api)
- [Workflow Examples](#workflow-examples)
- [Best Practices](#best-practices)

## Overview

Lucy-ng provides three interfaces:

1. **CLI** (`lucy` command): Best for quick analysis and scripting
2. **Python API**: Best for custom workflows and integration
3. **MCP Server** (`lucy-mcp`): Best for AI agent integration

All three interfaces share the same underlying functionality.

## Command-Line Interface

### Global Options

```bash
lucy [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show version and exit
  --help     Show help message and exit
```

### Command Groups

| Group | Description |
|-------|-------------|
| `lucy read` | Read NMR spectra |
| `lucy pick` | Pick peaks |
| `lucy analyze` | Analyze spectra |
| `lucy dereplicate` | Match against databases |
| `lucy lsd` | LSD solver integration |
| `lucy predict` | 13C shift prediction |

---

### Reading Spectra

#### Read 1D Spectrum

```bash
lucy read 1d PATH [OPTIONS]

Arguments:
  PATH  Path to Bruker 1D experiment directory

Options:
  --format [text|json]  Output format (default: text)
```

**Examples:**
```bash
# Basic usage
lucy read 1d data/Ibuprofen/2

# JSON output for scripting
lucy read 1d data/Ibuprofen/2 --format json
```

**Output:**
```
Spectrum: 13C
Frequency: 125.76 MHz
Solvent: CDCl3
Points: 32768
PPM range: -10.00 to 230.00
```

#### Read 2D Spectrum

```bash
lucy read 2d PATH [OPTIONS]

Arguments:
  PATH  Path to Bruker 2D experiment directory

Options:
  --format [text|json]  Output format (default: text)
```

**Examples:**
```bash
lucy read 2d data/Ibuprofen/6
lucy read 2d data/Ibuprofen/7 --format json
```

---

### Peak Picking

#### Pick 1D Peaks

```bash
lucy pick 1d PATH [OPTIONS]

Arguments:
  PATH  Path to Bruker 1D experiment

Options:
  --threshold FLOAT     Intensity threshold (0-1, default: 0.05)
  --format [text|json]  Output format
```

**Example:**
```bash
lucy pick 1d data/Ibuprofen/2 --threshold 0.03
```

#### Pick 2D Peaks

```bash
lucy pick 2d PATH [OPTIONS]

Arguments:
  PATH  Path to Bruker 2D experiment

Options:
  --threshold FLOAT     Intensity threshold (default: 0.05)
  --format [text|json]  Output format
```

#### DEPT-Guided HSQC Picking (Recommended)

```bash
lucy pick hsqc HSQC_PATH [OPTIONS]

Arguments:
  HSQC_PATH  Path to HSQC experiment

Options:
  --dept135 PATH        Path to DEPT-135 experiment (required)
  --dept90 PATH         Path to DEPT-90 experiment (optional)
  --format [text|json]  Output format
```

**Examples:**
```bash
# With DEPT-135 only
lucy pick hsqc data/Ibuprofen/6 --dept135 data/Ibuprofen/3

# With DEPT-90 for CH/CH3 disambiguation
lucy pick hsqc data/Ibuprofen/6 --dept135 data/Ibuprofen/3 --dept90 data/Ibuprofen/4
```

**Output:**
```
DEPT-Guided HSQC Peak Picking
-----------------------------
DEPT peaks (ground truth): 10
HSQC peaks found: 10
Threshold used: 0.0125
Iterations: 3
All carbons found: Yes

Carbon Multiplicities:
  CH3: 3
  CH2: 1
  CH: 4
  CH/CH3: 2

Peaks:
  45.12 ppm (C) / 1.84 ppm (H) - CH
  ...
```

#### Guided HMBC Picking

```bash
lucy pick hmbc HMBC_PATH [OPTIONS]

Arguments:
  HMBC_PATH  Path to HMBC experiment

Options:
  --c13 PATH            Path to 13C experiment (required)
  --hsqc PATH           Path to HSQC experiment (required)
  --dept135 PATH        Path to DEPT-135 (optional)
  --format [text|json]  Output format
```

**Example:**
```bash
lucy pick hmbc data/Ibuprofen/7 --c13 data/Ibuprofen/2 --hsqc data/Ibuprofen/6 --dept135 data/Ibuprofen/3
```

---

### Analysis

#### Symmetry Analysis

```bash
lucy analyze symmetry DATA_DIR FORMULA [OPTIONS]

Arguments:
  DATA_DIR  Directory containing Bruker experiments
  FORMULA   Molecular formula (e.g., C13H18O2)

Options:
  --format [text|json]  Output format
```

**Example:**
```bash
lucy analyze symmetry data/Ibuprofen C13H18O2
```

**Output:**
```
Symmetry Analysis for C13H18O2
==============================
Expected carbons: 13
Observed signals: 10
Missing carbons: 3
Has symmetry: Yes

Hydrogen Budget:
  Expected H: 18
  Accounted H: 15
  Missing H: 3

Potential equivalents (high intensity):
  127.5 ppm (CH) - relative intensity: 1.8
  129.3 ppm (CH) - relative intensity: 1.9
```

---

### Dereplication

```bash
lucy dereplicate c13 SPECTRUM_PATH FORMULA [OPTIONS]

Arguments:
  SPECTRUM_PATH  Path to 13C experiment
  FORMULA        Molecular formula

Options:
  --database PATH       Path to SD file (auto-discovers if not set)
  --top-n INT          Number of matches to show (default: 5)
  --threshold FLOAT     Match threshold (default: 0.7)
  --format [text|json]  Output format
```

**Examples:**
```bash
# Auto-discover database (prefers COCONUT)
lucy dereplicate c13 data/Ibuprofen/2 C13H18O2

# Use specific database
lucy dereplicate c13 data/Ibuprofen/2 C13H18O2 --database data/reference/nmrshiftdb2withsignals.sd

# More results
lucy dereplicate c13 data/Ibuprofen/2 C13H18O2 --top-n 10
```

---

### LSD Integration

#### Check LSD Availability

```bash
lucy lsd check
```

#### Generate LSD Input

```bash
lucy lsd generate DATA_DIR FORMULA [OPTIONS]

Arguments:
  DATA_DIR  Directory with Bruker experiments
  FORMULA   Molecular formula

Options:
  -o, --output PATH     Output file path
  --format [text|json]  Output format
```

**Example:**
```bash
lucy lsd generate data/Ibuprofen C13H18O2 -o ibuprofen.lsd
```

#### Run LSD Solver

```bash
lucy lsd run INPUT_FILE [OPTIONS]

Arguments:
  INPUT_FILE  Path to .lsd file

Options:
  --timeout INT         Timeout in seconds (default: 60)
  --output-dir PATH     Directory for output files
  --format [text|json]  Output format
```

#### Rank LSD Solutions

```bash
lucy lsd rank SOLUTIONS_PATH [OPTIONS]

Arguments:
  SOLUTIONS_PATH  Directory containing LSD solution files (.sol)

Options:
  -s, --spectrum PATH   Path to Bruker 13C spectrum for experimental shifts
  --shifts TEXT         Comma-separated 13C shifts in ppm (alternative to --spectrum)
  -n, --top INTEGER     Number of top results to show (default: 10)
  -t, --tolerance FLOAT Tolerance in ppm for matching (default: 3.0)
  --table PATH          Path to HOSE lookup table (auto-detected if not set)
  --format [text|json]  Output format
```

**Examples:**
```bash
# Rank using curated shift list (RECOMMENDED)
# Use the peak list that was refined during the CASE workflow
lucy lsd rank output/ --shifts "180.5,140.8,137.0,129.4,127.1,45.1,40.4,30.2,22.4,18.2"

# Rank using experimental 13C spectrum (re-picks peaks from scratch)
lucy lsd rank output/ --spectrum data/Ibuprofen/2 --top 5

# With custom tolerance
lucy lsd rank output/ --shifts "180.5,140.8,137.0,129.4,127.1" --tolerance 2.0
```

> **Best Practice**: Use `--shifts` with your curated peak list rather than `--spectrum`.
> During the CASE workflow, peaks may have been validated against DEPT, adjusted for
> overlapping signals, or manually curated. Using `--spectrum` would discard this
> curation and re-pick peaks from scratch, potentially reintroducing noise or
> missing validated peaks.

**Output:**
```
Ranking 50 LSD solutions
  Successfully ranked: 48
  Skipped (no SMILES): 2
  Experimental peaks: 10
  Tolerance: 3.0 ppm

Top 5 solutions:
----------------------------------------------------------------------
  1. Solution 3: MAE=1.85 ppm, matched=10/13
     CC(C)Cc1ccc(cc1)C(C)C(=O)O
  2. Solution 7: MAE=2.34 ppm, matched=10/13
     CC(C)Cc1ccc(C(C)C(=O)O)cc1
  ...
```

---

### 13C Shift Prediction

#### Predict Shifts from SMILES

```bash
lucy predict c13 SMILES [OPTIONS]

Arguments:
  SMILES  SMILES string of the molecule

Options:
  --table PATH          Path to HOSE lookup table
  --format [text|json]  Output format
```

**Example:**
```bash
lucy predict c13 "CC(C)Cc1ccc(cc1)C(C)C(=O)O"
```

#### Build Lookup Table

```bash
lucy predict build-table SD_FILE [OPTIONS]

Arguments:
  SD_FILE  Path to SD file with 13C data (nmrshiftdb or COCONUT)

Options:
  -o, --output PATH     Output file path
  --source [nmrshiftdb|coconut]  Database type (auto-detected)
```

**Example:**
```bash
lucy predict build-table data/reference/nmrshiftdb2withsignals.sd
```

---

## Python API

### Reading Spectra

```python
from lucy_ng import BrukerReader

# Read 1D spectrum
spectrum_1d = BrukerReader.read_1d("data/Ibuprofen/2")
print(f"Nucleus: {spectrum_1d.nucleus}")
print(f"Frequency: {spectrum_1d.frequency} MHz")
print(f"Points: {len(spectrum_1d.data)}")
print(f"PPM range: {spectrum_1d.ppm_scale.min():.1f} - {spectrum_1d.ppm_scale.max():.1f}")

# Read 2D spectrum
spectrum_2d = BrukerReader.read_2d("data/Ibuprofen/6")
print(f"Experiment: {spectrum_2d.experiment_type}")
print(f"Shape: {spectrum_2d.data.shape}")
```

### Peak Picking

```python
from lucy_ng import BrukerReader, AdaptivePeakPicker

# Basic 1D peak picking
spectrum = BrukerReader.read_1d("data/Ibuprofen/2")
peaks = AdaptivePeakPicker.pick_peaks(spectrum, threshold=0.05)

print(f"Found {len(peaks.peaks)} peaks")
for peak in peaks.peaks[:5]:
    print(f"  {peak.position:.2f} ppm: {peak.intensity:.2e}")

# With negative peak detection (for DEPT)
dept_peaks = AdaptivePeakPicker.pick_peaks(
    spectrum,
    threshold=0.05,
    detect_negative=True
)
```

### DEPT-Guided HSQC Picking

```python
from lucy_ng import BrukerReader
from lucy_ng.processing import DEPTGuidedPicker

# Load spectra
hsqc = BrukerReader.read_2d("data/Ibuprofen/6")
dept135 = BrukerReader.read_1d("data/Ibuprofen/3")
dept90 = BrukerReader.read_1d("data/Ibuprofen/4")  # Optional

# Pick with DEPT-135 only
result = DEPTGuidedPicker.pick_hsqc_peaks(hsqc, dept135)

# Or with DEPT-90 for better disambiguation
result = DEPTGuidedPicker.pick_hsqc_peaks_with_dept90(hsqc, dept135, dept90)

# Access results
print(result.summary())
print(f"DEPT peaks: {len(result.dept_peaks.peaks)}")
print(f"HSQC peaks: {len(result.peaks.peaks)}")
print(f"All carbons found: {result.all_carbons_found}")

# Carbon multiplicities
for ppm, mult in result.carbon_multiplicities.items():
    print(f"  {ppm:.1f} ppm: {mult}")
```

### HMBC-Guided Picking

```python
from lucy_ng import BrukerReader
from lucy_ng.processing import HMBCGuidedPicker

hmbc = BrukerReader.read_2d("data/Ibuprofen/7")
c13 = BrukerReader.read_1d("data/Ibuprofen/2")
hsqc = BrukerReader.read_2d("data/Ibuprofen/6")
dept135 = BrukerReader.read_1d("data/Ibuprofen/3")

result = HMBCGuidedPicker.pick_hmbc_peaks_from_spectra(
    hmbc=hmbc,
    carbon_spectrum=c13,
    hsqc=hsqc,
    dept135=dept135,
)

print(result.summary())
print(f"Raw peaks: {result.raw_peak_count}")
print(f"Validated: {result.validated_count}")
print(f"Rejected: {result.rejected_count}")
```

### Symmetry Analysis

```python
from lucy_ng import BrukerReader
from lucy_ng.processing import DEPTGuidedPicker
from lucy_ng.analysis import SymmetryAnalyzer

# Load spectra and pick peaks
hsqc = BrukerReader.read_2d("data/Ibuprofen/6")
dept135 = BrukerReader.read_1d("data/Ibuprofen/3")
dept_result = DEPTGuidedPicker.pick_hsqc_peaks(hsqc, dept135)

# Analyze symmetry
result = SymmetryAnalyzer.analyze("C13H18O2", dept_result, hsqc)

print(f"Expected carbons: {result.expected_carbons}")
print(f"Observed signals: {result.signal_count}")
print(f"Has symmetry: {result.has_symmetry}")
print(f"\nHydrogen budget:")
print(f"  Expected: {result.hydrogen_budget.expected_h}")
print(f"  Accounted: {result.hydrogen_budget.total_accounted}")
print(f"  Missing: {result.hydrogen_budget.missing_h}")
```

### Dereplication

```python
from lucy_ng import BrukerReader
from lucy_ng.dereplication import DereplicationService, CoconutLoader, NMRShiftDBLoader

# Load spectrum
spectrum = BrukerReader.read_1d("data/Ibuprofen/2")

# Option 1: Using COCONUT (streaming, recommended for large DB)
loader = CoconutLoader("data/reference/coconut_predicted.sd")
service = DereplicationService(loader)
result = service.dereplicate_from_spectrum(
    spectrum=spectrum,
    molecular_formula="C13H18O2",
    top_n=5,
)

# Option 2: Using NMRShiftDB (loads into memory)
loader = NMRShiftDBLoader("data/reference/nmrshiftdb2withsignals.sd")
loader.load()  # Required for NMRShiftDB
service = DereplicationService(loader)
result = service.dereplicate_from_spectrum(spectrum, "C13H18O2")

# Process results
print(f"Candidates found: {result.candidates_found}")
print(f"Best score: {result.best_score:.2f}")
print(f"Is match: {result.is_match}")

for match in result.top_matches:
    print(f"\n{match.entry.name}")
    print(f"  Formula: {match.entry.molecular_formula}")
    print(f"  Score: {match.score:.2f}")
    print(f"  Matched peaks: {match.matched_peaks}")
```

### LSD Integration

```python
from lucy_ng import BrukerReader
from lucy_ng.processing import DEPTGuidedPicker, HMBCGuidedPicker
from lucy_ng.lsd import LSDInputGenerator, LSDRunner

# Load all spectra
hsqc = BrukerReader.read_2d("data/Ibuprofen/6")
dept135 = BrukerReader.read_1d("data/Ibuprofen/3")
hmbc = BrukerReader.read_2d("data/Ibuprofen/7")
c13 = BrukerReader.read_1d("data/Ibuprofen/2")

# Pick peaks
dept_result = DEPTGuidedPicker.pick_hsqc_peaks(hsqc, dept135)
hmbc_result = HMBCGuidedPicker.pick_hmbc_peaks_from_spectra(
    hmbc=hmbc, carbon_spectrum=c13, hsqc=hsqc, dept135=dept135
)

# Generate LSD problem
problem = LSDInputGenerator.from_dept_result(
    dept_result=dept_result,
    hmbc_peaks=hmbc_result.peaks,
    molecular_formula="C13H18O2",
    name="ibuprofen",
)

# Generate input file content
lsd_content = LSDInputGenerator.generate(problem)
print(lsd_content)

# Write to file
LSDInputGenerator.write_file(problem, "ibuprofen.lsd")

# Run LSD (if installed)
if LSDRunner.is_available():
    runner = LSDRunner()
    result = runner.run(problem, timeout=60)
    print(f"Solutions found: {result.solution_count}")
    for sol in result.solutions:
        print(sol)
```

### Solution Ranking

```python
from lucy_ng import SolutionRanker, BrukerReader, AdaptivePeakPicker
from lucy_ng.lsd.parser import LSDOutputParser
from pathlib import Path

# Load experimental 13C shifts
spectrum = BrukerReader.read_1d("data/Ibuprofen/2")
peaks = AdaptivePeakPicker.pick_peaks(spectrum)
experimental_shifts = [p.position for p in peaks.peaks]

# Or provide shifts directly
experimental_shifts = [180.5, 140.8, 137.0, 129.4, 127.1, 45.1, 40.4, 30.2, 22.4, 18.2]

# Load LSD solutions
solutions = LSDOutputParser.parse_solutions(Path("output/"))

# Create ranker from HOSE lookup table
ranker = SolutionRanker.from_table_file(
    table_path="data/reference/hose_nmrshiftdb.json.gz",
    tolerance=3.0,  # ppm tolerance for matching
)

# Rank solutions
result = ranker.rank(solutions, experimental_shifts, top_n=10)

# Access results
print(result.summary())
print(f"Total solutions: {result.total_solutions}")
print(f"Successfully ranked: {result.ranked_count}")
print(f"Skipped (no SMILES): {result.skipped_count}")

# Iterate through ranked solutions (best first)
for i, sol in enumerate(result.solutions):
    print(f"\n{i+1}. Solution {sol.solution_index}")
    print(f"   SMILES: {sol.smiles}")
    print(f"   MAE: {sol.mae:.2f} ppm")
    print(f"   Matched: {sol.matched_count}/{sol.total_carbons} carbons")
    print(f"   Prediction rate: {sol.prediction_rate:.1%}")
```

### 13C Shift Prediction

```python
from lucy_ng import C13Predictor, HOSELookupTable
from pathlib import Path

# Load predictor from lookup table
predictor = C13Predictor.from_table_file(
    Path("data/reference/hose_nmrshiftdb.json.gz"),
    max_radius=6,  # Use up to 6-sphere HOSE codes
)

# Predict shifts from SMILES
result = predictor.predict_from_smiles("CC(C)Cc1ccc(cc1)C(C)C(=O)O")

print(f"Carbons: {result.carbon_count}")
print(f"Success rate: {result.success_rate:.1%}")

for pred in result.predictions:
    print(f"  Atom {pred.atom_index}: {pred.shift:.1f} ppm "
          f"(confidence: {pred.confidence:.2f}, radius: {pred.radius_used})")

# Build a lookup table from SD file (one-time setup)
from lucy_ng.prediction import HOSELookupTable, HOSECodeGenerator
from lucy_ng.dereplication import NMRShiftDBLoader

loader = NMRShiftDBLoader("data/reference/nmrshiftdb2withsignals.sd")
loader.load()

table = HOSELookupTable()
generator = HOSECodeGenerator()

for entry in loader.entries:
    if entry.smiles:
        mol = generator.prepare_mol(entry.smiles)
        if mol:
            # Add HOSE codes and shifts to table
            # (simplified - see HOSELookupTable.build_from_loader for full implementation)
            pass

# Save table for future use
table.save("my_hose_table.json.gz")
```

---

## Workflow Examples

### Complete Structure Elucidation Workflow

```python
from pathlib import Path
from lucy_ng import BrukerReader, SolutionRanker, AdaptivePeakPicker
from lucy_ng.processing import DEPTGuidedPicker, HMBCGuidedPicker
from lucy_ng.analysis import SymmetryAnalyzer
from lucy_ng.dereplication import DereplicationService, NMRShiftDBLoader
from lucy_ng.lsd import LSDInputGenerator, LSDRunner

def elucidation_workflow(data_dir: str, formula: str):
    """Complete structure elucidation workflow."""
    data_path = Path(data_dir)

    # Step 1: Load all spectra
    print("Loading spectra...")
    c13 = BrukerReader.read_1d(str(data_path / "2"))
    dept135 = BrukerReader.read_1d(str(data_path / "3"))
    hsqc = BrukerReader.read_2d(str(data_path / "6"))
    hmbc = BrukerReader.read_2d(str(data_path / "7"))

    # Step 2: DEPT-guided HSQC picking
    print("Picking HSQC peaks...")
    dept_result = DEPTGuidedPicker.pick_hsqc_peaks(hsqc, dept135)
    print(f"  Found {len(dept_result.peaks.peaks)} HSQC peaks")

    # Step 3: Guided HMBC picking
    print("Picking HMBC peaks...")
    hmbc_result = HMBCGuidedPicker.pick_hmbc_peaks_from_spectra(
        hmbc=hmbc, carbon_spectrum=c13, hsqc=hsqc, dept135=dept135
    )
    print(f"  Validated {hmbc_result.validated_count} HMBC peaks")

    # Step 4: Symmetry analysis
    print("Analyzing symmetry...")
    symmetry = SymmetryAnalyzer.analyze(formula, dept_result, hsqc)
    print(f"  Has symmetry: {symmetry.has_symmetry}")
    if symmetry.has_symmetry:
        print(f"  Missing carbons: {symmetry.missing_carbons}")

    # Step 5: Try dereplication first
    print("Checking database...")
    try:
        loader = NMRShiftDBLoader("data/reference/nmrshiftdb2withsignals.sd")
        loader.load()
        service = DereplicationService(loader)
        derep = service.dereplicate_from_spectrum(c13, formula)

        if derep.is_match:
            print(f"  MATCH FOUND: {derep.top_matches[0].entry.name}")
            print(f"  Score: {derep.top_matches[0].score:.2f}")
            return {"match": derep.top_matches[0]}
    except FileNotFoundError:
        print("  No database available, proceeding to LSD...")

    # Step 6: Generate LSD input
    print("Generating LSD input...")
    problem = LSDInputGenerator.from_dept_result(
        dept_result=dept_result,
        hmbc_peaks=hmbc_result.peaks,
        molecular_formula=formula,
    )
    print(f"  Atoms: {len(problem.atoms)}")
    print(f"  Correlations: {len(problem.correlations)}")

    # Step 7: Run LSD
    if not LSDRunner.is_available():
        print("  LSD not installed, returning input file")
        return {"lsd_input": LSDInputGenerator.generate(problem)}

    print("Running LSD solver...")
    runner = LSDRunner()
    lsd_result = runner.run(problem, timeout=120)
    print(f"  Solutions: {lsd_result.solution_count}")

    if lsd_result.solution_count == 0:
        return {"solutions": [], "count": 0}

    if lsd_result.solution_count == 1:
        print("  Single solution found - no ranking needed")
        return {"solutions": lsd_result.solutions, "count": 1}

    # Step 8: Rank solutions by 13C spectrum prediction
    print("Ranking solutions...")
    try:
        # Get experimental 13C shifts
        peaks = AdaptivePeakPicker.pick_peaks(c13)
        experimental_shifts = [p.position for p in peaks.peaks]

        # Create ranker and rank solutions
        ranker = SolutionRanker.from_table_file(
            "data/reference/hose_nmrshiftdb.json.gz",
            tolerance=3.0,
        )
        ranking = ranker.rank(lsd_result.solutions, experimental_shifts, top_n=10)

        print(f"  Ranked {ranking.ranked_count} solutions")
        if ranking.solutions:
            best = ranking.solutions[0]
            print(f"  Best match: Solution {best.solution_index}")
            print(f"  MAE: {best.mae:.2f} ppm")
            print(f"  SMILES: {best.smiles}")

        return {
            "solutions": lsd_result.solutions,
            "count": lsd_result.solution_count,
            "ranking": ranking,
        }
    except FileNotFoundError:
        print("  HOSE table not found, skipping ranking")
        return {"solutions": lsd_result.solutions, "count": lsd_result.solution_count}

# Run workflow
result = elucidation_workflow("data/Ibuprofen", "C13H18O2")
```

### Batch Processing

```python
from pathlib import Path
from lucy_ng import BrukerReader, AdaptivePeakPicker
import json

def batch_peak_picking(base_dir: str, output_file: str):
    """Process multiple spectra and save results."""
    results = []

    for compound_dir in Path(base_dir).iterdir():
        if not compound_dir.is_dir():
            continue

        compound_name = compound_dir.name
        print(f"Processing {compound_name}...")

        # Find 13C experiment
        for exp_dir in compound_dir.iterdir():
            if not exp_dir.is_dir():
                continue
            try:
                spectrum = BrukerReader.read_1d(str(exp_dir))
                if spectrum.nucleus == "13C":
                    peaks = AdaptivePeakPicker.pick_peaks(spectrum)
                    results.append({
                        "compound": compound_name,
                        "experiment": exp_dir.name,
                        "peaks": [
                            {"ppm": p.position, "intensity": p.intensity}
                            for p in peaks.peaks
                        ]
                    })
                    break
            except Exception:
                continue

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Processed {len(results)} compounds")

batch_peak_picking("data/", "peak_results.json")
```

---

## Best Practices

### 1. Use Guided Peak Picking

Always prefer guided peak picking over raw 2D peak picking:

```python
# Good: Use DEPT-guided HSQC
result = DEPTGuidedPicker.pick_hsqc_peaks(hsqc, dept135)

# Avoid: Raw 2D picking produces noise
peaks = PeakPicker2D.pick_peaks(hsqc)  # Many false peaks
```

### 2. Check Results

Always check if operations succeeded:

```python
# For dereplication
if result.is_match:
    # High confidence match
    structure = result.top_matches[0]
else:
    # Need structure generation
    ...

# For LSD
if result.success and result.solution_count > 0:
    # Valid solutions found
    ...
elif result.solution_count == 0:
    # No solutions - check constraints
    ...
```

### 3. Handle Symmetry

For symmetric molecules, check symmetry analysis:

```python
symmetry = SymmetryAnalyzer.analyze(formula, dept_result, hsqc)
if symmetry.has_symmetry:
    print(f"Warning: {symmetry.missing_carbons} equivalent carbons detected")
    # May need to adjust LSD input
```

### 4. Use Appropriate Thresholds

Default thresholds work for most spectra, but adjust if needed:

```python
# Default (good for most cases)
peaks = AdaptivePeakPicker.pick_peaks(spectrum, threshold=0.05)

# Lower threshold for weak signals
peaks = AdaptivePeakPicker.pick_peaks(spectrum, threshold=0.02)

# Higher threshold for noisy spectra
peaks = AdaptivePeakPicker.pick_peaks(spectrum, threshold=0.10)
```

### 5. Save Intermediate Results

For reproducibility, save intermediate results:

```python
import json

# Save peak lists
with open("peaks.json", "w") as f:
    json.dump({
        "hsqc": [{"c": p.f1_position, "h": p.f2_position}
                 for p in result.peaks.peaks],
        "multiplicities": result.carbon_multiplicities,
    }, f)

# Save LSD input
LSDInputGenerator.write_file(problem, "problem.lsd")
```
