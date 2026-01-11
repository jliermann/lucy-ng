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

---

## Workflow Examples

### Complete Structure Elucidation Workflow

```python
from pathlib import Path
from lucy_ng import BrukerReader
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
    if LSDRunner.is_available():
        print("Running LSD solver...")
        runner = LSDRunner()
        result = runner.run(problem, timeout=120)
        print(f"  Solutions: {result.solution_count}")
        return {"solutions": result.solutions, "count": result.solution_count}
    else:
        print("  LSD not installed, returning input file")
        return {"lsd_input": LSDInputGenerator.generate(problem)}

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
