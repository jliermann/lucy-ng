# Architecture

This document describes the technical architecture and design decisions behind lucy-ng.

## Table of Contents

- [Overview](#overview)
- [Module Structure](#module-structure)
- [Data Flow](#data-flow)
- [Design Decisions](#design-decisions)
- [Key Classes](#key-classes)
- [Extension Points](#extension-points)

## Overview

Lucy-ng is architected as a layered Python library with three main interfaces:

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interfaces                        │
├─────────────────┬─────────────────┬─────────────────────────┤
│   CLI (click)   │  Python API     │   MCP Server (FastMCP)  │
├─────────────────┴─────────────────┴─────────────────────────┤
│                      Core Library                           │
├──────────┬──────────┬───────────┬───────────┬──────────────┤
│ Readers  │Processing│ Analysis  │Dereplicat.│     LSD      │
├──────────┴──────────┴───────────┴───────────┴──────────────┤
│                      Data Models (Pydantic)                 │
└─────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Separation of Concerns**: Each module has a single responsibility
2. **Static Methods for Convenience**: Core operations are static for easy use
3. **Immutable Data Models**: All models are Pydantic dataclasses
4. **Explicit Error Handling**: Operations return result objects, not exceptions
5. **AI-First API**: All operations return structured data suitable for LLM consumption

## Module Structure

```
src/lucy_ng/
├── __init__.py           # Public API exports
├── models/               # Pydantic data models
│   ├── __init__.py
│   ├── spectrum.py       # Spectrum1D, Spectrum2D
│   └── peaks.py          # Peak1D, Peak2D, PeakList1D, PeakList2D
├── readers/              # NMR file readers
│   ├── __init__.py
│   └── bruker.py         # BrukerReader
├── processing/           # Signal processing and peak picking
│   ├── __init__.py
│   ├── peak_picker.py    # AdaptivePeakPicker
│   ├── peak_picker_2d.py # PeakPicker2D
│   ├── peak_validator.py # PeakValidator
│   ├── dept_guided_picker.py    # DEPTGuidedPicker
│   └── hmbc_guided_picker.py    # HMBCGuidedPicker
├── analysis/             # Spectroscopic analysis
│   ├── __init__.py
│   ├── hydrogen_budget.py    # HydrogenBudgetAnalyzer
│   ├── intensity_report.py   # IntensityReporter
│   └── symmetry.py           # SymmetryAnalyzer
├── dereplication/        # Database matching
│   ├── __init__.py
│   ├── coconut.py        # CoconutLoader (streaming)
│   ├── nmrshiftdb.py     # NMRShiftDBLoader
│   ├── matcher.py        # SpectrumMatcher
│   └── service.py        # DereplicationService
├── lsd/                  # LSD solver integration
│   ├── __init__.py
│   ├── models.py         # LSDProblem, LSDAtom, etc.
│   ├── generator.py      # LSDInputGenerator
│   ├── runner.py         # LSDRunner
│   └── parser.py         # LSDOutputParser
├── cli/                  # Command-line interface
│   ├── __init__.py
│   ├── read.py
│   ├── pick.py
│   ├── analyze.py
│   ├── dereplicate.py
│   └── lsd.py
└── mcp/                  # MCP server
    ├── __init__.py
    └── server.py         # FastMCP tool definitions
```

## Data Flow

### Reading → Peak Picking → Analysis

```
Bruker Files          BrukerReader         Processing          Analysis
    │                      │                   │                   │
    ▼                      ▼                   ▼                   ▼
┌────────┐  read_1d   ┌──────────┐  pick   ┌──────────┐  analyze ┌────────┐
│ pdata/ │ ─────────▶ │Spectrum1D│ ──────▶ │PeakList1D│ ───────▶ │Results │
└────────┘            └──────────┘         └──────────┘          └────────┘
    │                      │                   │
    │                      │                   │
    ▼                      ▼                   ▼
┌────────┐  read_2d   ┌──────────┐  pick   ┌──────────┐
│ pdata/ │ ─────────▶ │Spectrum2D│ ──────▶ │PeakList2D│
└────────┘            └──────────┘         └──────────┘
```

### Structure Elucidation Pipeline

```
HSQC + DEPT-135                    HMBC + 13C + HSQC
      │                                   │
      ▼                                   ▼
┌─────────────────┐              ┌─────────────────┐
│DEPTGuidedPicker │              │HMBCGuidedPicker │
└────────┬────────┘              └────────┬────────┘
         │                                │
         ▼                                ▼
    DEPTGuidedResult                HMBCGuidedResult
         │                                │
         └──────────┬─────────────────────┘
                    │
                    ▼
           ┌─────────────────┐
           │LSDInputGenerator│
           └────────┬────────┘
                    │
                    ▼
              ┌──────────┐
              │LSDProblem│
              └────┬─────┘
                   │
                   ▼
             ┌──────────┐
             │LSDRunner │
             └────┬─────┘
                  │
                  ▼
             ┌──────────┐
             │LSDResult │
             └──────────┘
```

## Design Decisions

### 1. Static Methods for Core Operations

**Decision**: Use static methods for primary operations like peak picking.

**Rationale**:
- Simpler API for users
- No need to instantiate objects for common tasks
- Consistent with library patterns (like `json.loads()`)

**Implementation**:
```python
class AdaptivePeakPicker:
    @staticmethod
    def pick_peaks(spectrum, threshold=0.05) -> PeakList1D:
        # Creates internal instance with defaults
        if AdaptivePeakPicker._default_instance is None:
            AdaptivePeakPicker._default_instance = AdaptivePeakPicker()
        return AdaptivePeakPicker._default_instance.pick_peaks_instance(...)
```

### 2. Pydantic v2 for Data Models

**Decision**: Use Pydantic dataclasses for all data structures.

**Rationale**:
- Automatic validation
- JSON serialization built-in
- Type hints enforced at runtime
- IDE support for autocomplete

**Example**:
```python
from pydantic import BaseModel

class Peak1D(BaseModel):
    position: float
    intensity: float
    assignment: str | None = None
```

### 3. Result Objects Instead of Exceptions

**Decision**: Return structured result objects from operations.

**Rationale**:
- AI agents can handle structured errors
- No try/catch needed for expected failures
- Consistent interface across all operations

**Example**:
```python
# MCP tool returns structured result
@mcp.tool()
def read_spectrum_1d(path: str) -> dict:
    try:
        spectrum = BrukerReader.read_1d(path)
        return {"success": True, "nucleus": spectrum.nucleus, ...}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### 4. Guided Peak Picking Strategy

**Decision**: Use 1D spectra as ground truth to filter 2D peaks.

**Rationale**:
- Raw 2D peak picking produces many noise peaks
- DEPT-135 definitively shows all protonated carbons
- Cross-validation removes artifacts
- Improves LSD constraint quality dramatically

**Implementation**:
```python
class DEPTGuidedPicker:
    @staticmethod
    def pick_hsqc_peaks(hsqc, dept135):
        # 1. Pick DEPT peaks (ground truth)
        dept_peaks = AdaptivePeakPicker.pick_peaks(dept135)

        # 2. Iteratively lower HSQC threshold
        for threshold in [0.05, 0.025, 0.0125, ...]:
            hsqc_peaks = PeakPicker2D.pick_peaks(hsqc, threshold)

            # 3. Validate HSQC against DEPT
            if all_dept_carbons_matched(hsqc_peaks, dept_peaks):
                break

        # 4. Return filtered peaks
        return DEPTGuidedResult(peaks=validated_hsqc, ...)
```

### 5. Streaming for Large Databases

**Decision**: Use streaming mode for COCONUT database.

**Rationale**:
- COCONUT is ~4.8 GB with ~895K entries
- Loading into memory is impractical
- Formula filtering allows streaming

**Implementation**:
```python
class CoconutLoader:
    def get_by_formula(self, formula: str):
        # Stream through file, only parse matching entries
        for entry in self._stream_by_formula(formula):
            yield entry

    def _stream_by_formula(self, formula):
        with open(self.path) as f:
            while block := self._read_next_block(f):
                if formula in block:
                    yield self._parse_block(block)
```

### 6. MCP Tool Design

**Decision**: Each MCP tool is self-contained and returns complete results.

**Rationale**:
- AI agents work best with complete responses
- Reduces back-and-forth for simple queries
- Error information included in response

**Example**:
```python
@mcp.tool()
def pick_hsqc_peaks(hsqc_path: str, dept135_path: str) -> dict:
    """Pick HSQC peaks using DEPT-guided algorithm."""
    try:
        hsqc = BrukerReader.read_2d(hsqc_path)
        dept135 = BrukerReader.read_1d(dept135_path)
        result = DEPTGuidedPicker.pick_hsqc_peaks(hsqc, dept135)
        return {
            "success": True,
            "dept_peaks_count": len(result.dept_peaks.peaks),
            "hsqc_peaks_count": len(result.peaks.peaks),
            "carbon_multiplicities": result.carbon_multiplicities,
            "peaks": [...],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
```

## Key Classes

### Data Models

| Class | Description |
|-------|-------------|
| `Spectrum1D` | 1D NMR spectrum with data, ppm scale, metadata |
| `Spectrum2D` | 2D NMR spectrum with F1/F2 axes |
| `Peak1D` | Single 1D peak (position, intensity) |
| `Peak2D` | Single 2D peak (f1_position, f2_position, intensity) |
| `PeakList1D` | Collection of 1D peaks with nucleus |
| `PeakList2D` | Collection of 2D peaks |

### Readers

| Class | Description |
|-------|-------------|
| `BrukerReader` | Read Bruker TopSpin format (1D and 2D) |

### Processing

| Class | Description |
|-------|-------------|
| `AdaptivePeakPicker` | FWHM-adaptive 1D peak picker |
| `PeakPicker2D` | Connected-region 2D peak picker |
| `DEPTGuidedPicker` | DEPT-guided HSQC peak picking |
| `HMBCGuidedPicker` | Reference-guided HMBC picking |
| `PeakValidator` | Cross-validate 2D vs 1D peaks |

### Analysis

| Class | Description |
|-------|-------------|
| `HydrogenBudgetAnalyzer` | Compare MF H count with observed |
| `IntensityReporter` | Report relative peak intensities |
| `SymmetryAnalyzer` | Detect molecular symmetry |

### Dereplication

| Class | Description |
|-------|-------------|
| `CoconutLoader` | Stream COCONUT SD file |
| `NMRShiftDBLoader` | Load NMRShiftDB SD file |
| `SpectrumMatcher` | Match observed vs reference |
| `DereplicationService` | High-level dereplication API |

### LSD Integration

| Class | Description |
|-------|-------------|
| `LSDProblem` | Complete LSD problem definition |
| `LSDAtom` | Atom definition for LSD |
| `LSDInputGenerator` | Generate LSD input files |
| `LSDRunner` | Execute LSD as subprocess |
| `LSDResult` | LSD execution results |

## Extension Points

### Adding New Readers

1. Create new class in `readers/`
2. Implement `read_1d()` and/or `read_2d()` methods
3. Return `Spectrum1D` or `Spectrum2D`
4. Export from `readers/__init__.py`

```python
# readers/varian.py
class VarianReader:
    @staticmethod
    def read_1d(path: str) -> Spectrum1D:
        # Implementation
        return Spectrum1D(...)
```

### Adding New Databases

1. Create loader class in `dereplication/`
2. Implement `get_by_formula()` method
3. Return `DatabaseEntry` objects
4. Use with `DereplicationService`

```python
# dereplication/custom_db.py
class CustomDBLoader:
    def get_by_formula(self, formula: str) -> Generator[DatabaseEntry]:
        # Implementation
        yield DatabaseEntry(...)
```

### Adding New MCP Tools

1. Add function in `mcp/server.py`
2. Decorate with `@mcp.tool()`
3. Return structured dict with `success` key
4. Document parameters in docstring

```python
@mcp.tool()
def my_new_tool(param: str) -> dict:
    """Description for AI agents.

    Args:
        param: Description of parameter

    Returns:
        Dictionary with results
    """
    try:
        result = do_something(param)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### Adding CLI Commands

1. Create command in appropriate `cli/*.py` module
2. Use Click decorators
3. Support `--format json` output
4. Register in `cli/__init__.py`

```python
# cli/my_command.py
@click.command()
@click.argument("path")
@click.option("--format", type=click.Choice(["text", "json"]))
def my_command(path, format):
    """Description."""
    result = process(path)
    if format == "json":
        click.echo(json.dumps(result))
    else:
        click.echo(format_text(result))
```
