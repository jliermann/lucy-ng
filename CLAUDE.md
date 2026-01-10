# lucy-ng

AI-agent powered Computer-Assisted Structure Elucidation for organic natural products.

## Quick Reference

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

## Project Structure

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

## Technology Stack

- **Python 3.10+** - minimum version
- **Pydantic v2** - data models with validation
- **nmrglue** - Bruker NMR file parsing
- **NumPy/SciPy** - numerical processing
- **RDKit** - SD file parsing for reference databases
- **hatch** - build system
- **pytest** - testing
- **ruff** - linting
- **mypy** - type checking (strict mode)

## Code Conventions

- Type hints on all functions
- Docstrings with Args/Returns/Raises sections
- Static methods for readers (e.g., `BrukerReader.read_1d()`)
- Helper functions prefixed with `_` for private use
- Line length: 100 characters
- Imports: standard library, third-party, local (isort order)

## NMR Data

Test data is Bruker format in `data/` directory:
- `data/Ibuprofen/` - 1D (1H, 13C) and 2D (COSY, HSQC, HMBC)
- `data/4-Hydroxy-3-Iodo-biphenyl/` - includes NOESY
- Processed data read from `pdata/1/` subdirectory

## Key Patterns

### Reading NMR data
```python
from lucy_ng import BrukerReader, Spectrum1D

spectrum: Spectrum1D = BrukerReader.read_1d("data/Ibuprofen/10")
```

### Models are Pydantic
```python
from lucy_ng.models import Peak1D

peak = Peak1D(ppm=45.2, intensity=1.0e6, assignment="C-1")
```

## Planning

This project uses GSD (Get Shit Done) workflow. Planning files in `.planning/`:
- `STATE.md` - current position and session context
- `ROADMAP.md` - milestone and phase overview
- `PROJECT.md` - vision, requirements, constraints
- `phases/` - detailed phase plans and summaries

Use `/gsd:resume-work` to restore context at session start.
