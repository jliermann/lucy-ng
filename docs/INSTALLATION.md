# Installation Guide

This guide covers all installation options for lucy-ng.

## Table of Contents

- [Requirements](#requirements)
- [Quick Installation](#quick-installation)
- [Installation Options](#installation-options)
- [External Dependencies](#external-dependencies)
- [Reference Databases](#reference-databases)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Claude Code Skill Installation](#claude-code-skill-installation)

## Requirements

### Python Version

Lucy-ng requires **Python 3.10 or higher**.

Check your Python version:
```bash
python3 --version
```

### System Dependencies

Lucy-ng's Python dependencies will be installed automatically. The core dependencies are:

| Package | Version | Purpose |
|---------|---------|---------|
| nmrglue | >=0.9 | Bruker NMR file parsing |
| numpy | >=1.24 | Numerical operations |
| scipy | >=1.10 | Peak picking algorithms |
| pydantic | >=2.0 | Data model validation |
| rdkit | >=2023.0 | SD file parsing for databases |
| click | >=8.0 | CLI framework |
| tqdm | >=4.0 | Progress bars |

**Optional dependencies:**

| Package | Purpose | Notes |
|---------|---------|-------|
| hose-code-generator | 13C shift prediction | See [Python 3.12 note](#13c-prediction-python-312) |
| mcp[cli] | MCP server for AI agents | Installed with `[mcp]` extra |

## Quick Installation

### From GitHub (Recommended)

Lucy-ng is currently installed directly from GitHub:

```bash
# Basic installation
pip install "lucy-ng @ git+https://github.com/steinbeck/lucy-ng.git"

# With MCP server support (recommended for AI integration)
pip install "lucy-ng[mcp] @ git+https://github.com/steinbeck/lucy-ng.git"
```

This adds the `mcp[cli]>=1.2.0` dependency for AI agent integration.

> **Note for macOS/zsh users**: The quotes are required because zsh interprets square brackets as glob patterns. Without quotes, you'll get "no matches found" error.

### Full Installation (All Features)

```bash
pip install "lucy-ng[mcp,dev] @ git+https://github.com/steinbeck/lucy-ng.git"
```

## Installation Options

### Option 1: User Installation

Install for the current user only (no root required):

```bash
pip install --user "lucy-ng[mcp] @ git+https://github.com/steinbeck/lucy-ng.git"
```

### Option 2: Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv lucy-env
source lucy-env/bin/activate  # Linux/macOS
# or: lucy-env\Scripts\activate  # Windows

# Install lucy-ng
pip install "lucy-ng[mcp] @ git+https://github.com/steinbeck/lucy-ng.git"
```

### Option 3: Development Installation (For Contributors)

For contributing or modifying lucy-ng:

```bash
# Clone repository
git clone https://github.com/steinbeck/lucy-ng.git
cd lucy-ng

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev,mcp]"

# Verify installation
pytest
```

### Option 4: System-Wide Installation

```bash
sudo pip install "lucy-ng[mcp] @ git+https://github.com/steinbeck/lucy-ng.git"
```

## 13C Prediction (Python 3.12)

The 13C shift prediction feature (`lucy predict c13`, `predict_c13_shifts` MCP tool, solution ranking) requires the `hose-code-generator` package for HOSE code generation.

### Python 3.10/3.11

On Python 3.10 or 3.11, hosegen installs automatically with all its dependencies.

### Python 3.12+

On Python 3.12, the `hose-code-generator` package has a broken test dependency (`xmlrunner`) that fails to install. Install it manually without dependencies:

```bash
# After installing lucy-ng
pip install git+https://github.com/Ratsemaat/HOSE_code_generator.git --no-deps
```

The `--no-deps` flag skips the broken `xmlrunner` dependency, which is only needed for running hosegen's own tests, not for HOSE code generation. The prediction features work correctly without it.

### Checking Availability

You can check if HOSE code prediction is available:

```python
from lucy_ng.prediction import HOSEGEN_AVAILABLE
print(f"HOSE prediction available: {HOSEGEN_AVAILABLE}")
```

Or via CLI:
```bash
lucy predict c13 "CCO"  # Will show error if hosegen not installed
```

## External Dependencies

### LSD Solver (Optional)

LSD (Logic for Structure Determination) is required for structure generation. It's optional for dereplication and analysis.

#### Download and Install

1. Download LSD from: http://eos.univ-reims.fr/LSD/
2. Extract the archive:
   ```bash
   tar -xzf LSD-3.5.3.tar.gz
   cd LSD-3.5.3
   ```
3. Compile (if needed):
   ```bash
   make
   ```
4. Add to PATH or copy to standard location:
   ```bash
   # Option A: Add to PATH
   export PATH="$PATH:$HOME/LSD-3.5.3"

   # Option B: Copy to ~/bin
   mkdir -p ~/bin
   cp lsd ~/bin/
   export PATH="$PATH:$HOME/bin"

   # Option C: Copy to system location
   sudo cp lsd /usr/local/bin/
   ```

#### Install outlsd (Recommended)

The `outlsd` program converts LSD solutions to SMILES format, which is required for solution ranking. It is distributed with LSD.

```bash
# Copy outlsd alongside lsd
cp outlsd ~/bin/
# or
sudo cp outlsd /usr/local/bin/
```

Without `outlsd`:
- LSD will still generate solutions
- But `lucy lsd rank` cannot rank them (no SMILES available)
- The `rank_lsd_solutions` MCP tool will skip all solutions

#### Verify LSD Installation

```bash
# Using CLI - shows both lsd and outlsd status
lucy lsd check

# Or directly
which lsd
which outlsd
```

Expected output:
```
LSD: available
outlsd: available (SMILES conversion enabled)
```

### pyLSD (Alternative Solver)

pyLSD is a Python wrapper around LSD with additional features. Install separately if needed:

```bash
pip install pylsd
```

## Reference Database

Lucy-ng uses **one pre-built SQLite database** for BOTH dereplication and 13C
prediction (formula-indexed compound lookup + HOSE-based shift prediction). It is
required for the `dereplicate`, `predict c13`, and CASE-ranking paths. You do **not**
build it from raw SD files for a normal install — download the pre-built one:

```bash
mkdir -p data/reference
lucy database download -o data/reference/lucy-ng-derep.db   # ~830 MB → ~2.8 GB
lucy database info data/reference/lucy-ng-derep.db          # verify row counts
```

| Property | Value |
|----------|-------|
| Source | Figshare, DOI [10.6084/m9.figshare.31073554](https://doi.org/10.6084/m9.figshare.31073554) |
| Default path | `data/reference/lucy-ng-derep.db` |
| Contents | 928,443 compounds (COCONUT + NMRShiftDB), 7.9M HOSE statistics |

### Auto-Discovery

`DatabaseFinder` discovers `data/reference/lucy-ng-derep.db` automatically (including
from a CASE data directory outside the repo). Override explicitly with `--database`:

```bash
lucy dereplicate c13 spectrum_path formula --database /path/to/lucy-ng-derep.db
```

> The raw COCONUT/NMRShiftDB SD files are only needed to **rebuild** the SQLite DB from
> source (a maintenance task) — not for running lucy-ng.

## Verification

After installation, verify everything works:

### Check CLI Installation

```bash
# Should show help message
lucy --help

# Check version
lucy --version
```

### Check MCP Server

```bash
# Should show help for MCP server
lucy-mcp --help

# Or run directly
python -m lucy_ng.mcp --help
```

### Run Tests

```bash
# Quick test (if dev dependencies installed)
pytest tests/test_mcp_server.py -v

# Full test suite
pytest
```

### Test with Sample Data

```bash
# Read a spectrum (if test data available)
lucy read 1d data/Ibuprofen/2

# Pick peaks
lucy pick 1d data/Ibuprofen/2
```

## Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'lucy_ng'`

**Solution**:
```bash
# Ensure you're in the right environment
which python3
pip list | grep lucy

# Reinstall if needed
pip install --force-reinstall lucy-ng
```

### RDKit Installation Issues

**Problem**: RDKit fails to install

**Solution**:
```bash
# Try conda instead
conda install -c conda-forge rdkit

# Or use mamba
mamba install rdkit
```

### MCP Server Not Found

**Problem**: `lucy-mcp: command not found`

**Solution**:
```bash
# Ensure MCP extras were installed
pip install lucy-ng[mcp]

# Check if entry point exists
pip show lucy-ng | grep -A 10 "Entry-points"

# Run directly as module
python -m lucy_ng.mcp
```

### LSD Not Found

**Problem**: `lucy lsd check` says LSD is not available

**Solution**:
```bash
# Find LSD binary
find ~ -name "lsd" -type f 2>/dev/null

# Add to PATH
export PATH="$PATH:/path/to/lsd/directory"

# Verify
which lsd
```

### Database Loading Slow

**Problem**: Dereplication takes very long with COCONUT

**Solution**: This is normal for the first query. Lucy-ng uses streaming mode so it doesn't load the entire 4.8 GB file into memory. Typical query time is 1-2 minutes for formula-based filtering.

### Memory Issues

**Problem**: Out of memory errors with large databases

**Solution**: Lucy-ng's COCONUT loader uses streaming mode by default. If you're still seeing issues:
```bash
# Increase available memory
ulimit -v unlimited

# Or use NMRShiftDB instead
lucy dereplicate c13 spectrum formula --database data/reference/nmrshiftdb2withsignals.sd
```

### HOSE Code Generator Issues (Python 3.12)

**Problem**: Installation fails with `xmlrunner` or `_TextTestResult` errors

```
ImportError: cannot import name '_TextTestResult' from 'unittest'
```

**Solution**: This is a known issue with Python 3.12. Install hosegen without its broken test dependency:

```bash
pip install git+https://github.com/Ratsemaat/HOSE_code_generator.git --no-deps
```

**Problem**: `hosegen package not installed` error when using prediction

**Solution**: Install hosegen as shown above. The prediction features require this package for HOSE code generation.

## Claude Code Skill Installation

Lucy-ng's Claude Code integration is the `/lucy-ng:*` **commands** plus the **CASE team
agents** that `/lucy-ng:case` spawns. Both must be present, and an environment flag must
be set, or CASE fails at its prerequisite gate.

> For a fresh headless server (e.g. provisioning the `sheldon` compute host), follow the
> end-to-end **[SERVER_BOOTSTRAP.md](SERVER_BOOTSTRAP.md)** guide (or run
> `scripts/bootstrap_case_host.sh`) — it does the steps below plus Python/LSD/DB.

### Install the commands and agents

Symlink the repo's `.claude/` content into `~/.claude` (edits stay in sync; use `cp -r`
for a frozen snapshot):

```bash
git clone https://github.com/steinbeck/lucy-ng.git
cd lucy-ng
mkdir -p ~/.claude/agents ~/.claude/commands

# Commands (case, dereplicate, predict, sanitise, status + references/)
ln -sfn "$PWD/.claude/commands/lucy-ng" ~/.claude/commands/lucy-ng

# CASE team agents — REQUIRED for /lucy-ng:case to spawn its team
for a in "$PWD"/.claude/agents/lucy-*.md; do
  ln -sfn "$a" ~/.claude/agents/"$(basename "$a")"
done
```

### Enable agent teams

`/lucy-ng:case` runs a multi-agent team — Claude Code needs this experimental flag:

```bash
echo 'export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1' >> ~/.bashrc   # or ~/.zshrc
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

### Verify

After restarting Claude Code, the commands are available:

```
/lucy-ng:case        /lucy-ng:dereplicate        /lucy-ng:predict
/lucy-ng:sanitise    /lucy-ng:status
```

### Available commands

| Command | Purpose |
|---------|---------|
| `/lucy-ng:case` | Full de novo structure elucidation (spawns the 4-agent team) |
| `/lucy-ng:dereplicate` | Database matching only |
| `/lucy-ng:predict` | Predict 13C shifts for a SMILES |
| `/lucy-ng:sanitise` | Remove compound identity from datasets for blind CASE |
| `/lucy-ng:status` | Check environment readiness (lucy/LSD/DB) |

### CASE team agents (in `~/.claude/agents/`)

| Agent | Role |
|-------|------|
| `lucy-nmr-chemist` | Peak picking, statistical detection, spectral QA |
| `lucy-lsd-engineer` | LSD constraint building + solver runs |
| `lucy-solution-analyst` | Solution ranking + identity reporting |
| `lucy-devils-advocate` | Pre-run validation + post-solution G-IDENT/G-MULT gates |
| `lucy-diagnostic` | Deep LSD-failure diagnosis (escalation only) |

## Next Steps

After installation:

1. **Read the User Guide**: See [USER_GUIDE.md](USER_GUIDE.md) for detailed usage
2. **AI Agent Guide**: See [../CLAUDE.md](../CLAUDE.md) for comprehensive structure elucidation workflow and pitfalls
3. **Explore the CLI**: Run `lucy --help` to see all commands
4. **Try the examples**: See the Quick Start section in the main README
