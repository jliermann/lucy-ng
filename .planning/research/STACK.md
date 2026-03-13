# Technology Stack: pyLSD Integration and 4J HMBC Exploration

**Project:** lucy-ng
**Milestone:** v8.0 pyLSD Integration
**Researched:** 2026-03-13
**Confidence:** HIGH for pyLSD mechanics (thesis + official docs + manual). MEDIUM for version currency (latest release is a8, no 2024/2025 updates found).

---

## Context: What Already Exists

The existing stack is locked. Do not re-evaluate these components:

| Component | Version | Status |
|-----------|---------|--------|
| Python | 3.10+ | Locked |
| RDKit | 2025.9.4 | In use |
| NumPy | 2.2.1 | In use |
| SciPy | 1.17.0 | In use |
| Pydantic v2 | 2.12.5 | In use |
| Click | 8.1.8 | In use |
| SQLite | stdlib | In use (schema v6) |
| tqdm | 4.67.3 | In use |
| LSD binary | 3.5.3 | Installed (via PATH) |
| outlsd binary | 3.5.3 | Installed (via PATH) |

The v8.0 milestone adds pyLSD on top of this stack. **No existing dependencies are removed.**

---

## New Capabilities Required

The pyLSD integration milestone needs to:

1. **Install pyLSD** — download and configure the pyLSD-a8 distribution so `python lsd.py` can be called
2. **Call pyLSD from lucy-ng** — invoke pyLSD via subprocess, same pattern as existing LSD runner
3. **Generate pyLSD input files** — extend `LSDInputGenerator` to emit `FORM`, `PIEC`, `ELIM`, and multi-state `MULT` syntax
4. **Collect multi-run solutions** — pyLSD runs LSD multiple times internally; collect merged SMILES output
5. **4J exploration** — write HMBC commands with explicit bond range `HMBC C H 2 4` plus `ELIM N 4` to enable solver-level 4J handling

---

## pyLSD: Obtaining and Installing

### Source

**Repository:** https://github.com/nuzillard/PyLSD

pyLSD is **not on PyPI**. The PyPI packages named `pylsd` and `pylsd-nova` are unrelated (Python bindings for an image line-segment detector — completely different project, same name collision).

**Download:** Pre-built archive from GitHub releases:
- Linux: `pylsd-linux-a8.tar.gz`
- Windows: `pylsd-windows-a8.zip`

**Current version:** PyLSD-a8 (alpha 8). No releases found from 2024/2025 — this appears to be the latest stable version. Confidence: MEDIUM (checked GitHub; no newer release visible).

### Installation Procedure

```bash
# 1. Download and extract (Linux)
wget https://github.com/nuzillard/PyLSD/raw/master/pylsd-linux-a8.tar.gz
tar -xzf pylsd-linux-a8.tar.gz
# Creates three directories: Variant/, Predict/, LSD/

# 2. Configure defaults.py in Variant/ — must edit these paths:
#   lsdbin     = "../LSD"          (path to LSD/outlsd executables)
#   datafolder = "../LSD/Data"     (where pyLSD writes temp files)
#   java       = "java"            (Java executable path, for built-in ranking)
#   predictorspath = "../Predict"  (only needed for built-in ranking — NOT used in lucy-ng)

# 3. Test installation
cd Variant
python lsd.py breg57.lsd   # should produce solutions for built-in example
```

### Python Version Requirement

Python 3 required from pyLSD-a8 onward. Compatible with lucy-ng's Python 3.10+ constraint. No version conflict.

### Dependencies

| Dependency | Required For | Status |
|------------|-------------|--------|
| Python 3 | Running `lsd.py` | Already satisfied |
| Java Runtime ≥ 6 | pyLSD's built-in ranking (nmrshiftdb2-based) | **NOT needed** — lucy-ng uses HOSE-based ranking instead |
| LSD binary (lsd) | pyLSD calls lsd internally | Already installed |
| outlsd binary | SMILES conversion (already used by lucy-ng) | Already installed |

**Key finding:** Java is only needed for pyLSD's built-in ranking, which Sherlock (and lucy-ng) explicitly disable in favour of HOSE-based ranking. No Java dependency required for lucy-ng integration.

---

## How pyLSD Differs from Direct LSD Execution

### What pyLSD Is

pyLSD is a Python script (`Variant/lsd.py`) that acts as an orchestrator over the LSD binary. It:

1. Reads an enhanced `.lsd` input file containing pyLSD-specific commands (FORM, PIEC, ELIM, multi-state MULT)
2. Enumerates all combinations of variable atom states (hybridisation, multiplicity, valency)
3. Generates one plain LSD input file per combination
4. Runs the LSD binary on each generated file (potentially many runs)
5. Merges all solution files into a single output
6. Optionally ranks merged solutions using nmrshiftdb2 (disabled in lucy-ng)

**Invocation:** `python lsd.py myfile.lsd` from the `Variant/` directory.

**Current lucy-ng invocation:** `subprocess.run([lsd_path], input=file_content, ...)` — pipes the file to the lsd binary directly.

**pyLSD invocation:** `subprocess.run(["python", "lsd.py", str(input_file)], cwd=variant_dir, ...)` — passes filename as argument, must run from Variant/.

This is the primary integration change: the runner calls `python lsd.py FILE` rather than `lsd < FILE`.

### File Format Differences

The pyLSD input format is a **superset** of the LSD input format. Every valid LSD file is a valid pyLSD file. pyLSD adds these commands that do not exist in native LSD:

| Command | pyLSD | Native LSD | Notes |
|---------|-------|------------|-------|
| `FORM` | YES | NO | Molecular formula as text string |
| `PIEC` | YES | NO | Connected piece count (always 1) |
| `ELIM` | Both | YES (native) | ELIM exists in native LSD too — pyLSD passes it through |
| `MULT` multi-state | YES | NO | Multiple hybridisation/multiplicity options as tuples |
| `SHIX` | Both | YES (native) | 13C shift assignment — exists in LSD 3.5.x |
| `SHIH` | Both | YES (native) | 1H shift assignment — exists in LSD 3.5.x |
| `MOMA` | pyLSD only | NO | Molecular mass constraint (not needed for CASE) |
| `DEMU` | pyLSD only | NO | Default parameters for supplementary atoms |

**Critical note:** The existing lucy-ng `LSDInputGenerator` already generates `SHIX` and `SHIH` commands — these work identically in both LSD and pyLSD. No format migration needed for existing output.

---

## Command Reference for New File Format

### FORM — Molecular Formula (pyLSD only)

```
FORM C 13 H 18 O 2
```

Defines the molecular formula. Serves as upper boundary on solution space. pyLSD uses this to determine what supplementary atoms to add when MULT states are ambiguous.

**Usage in lucy-ng:** Always add FORM as first command in pyLSD input files. The formula is already available in the workflow (required for LSD constraint generation in existing code).

### PIEC — Connected Pieces (pyLSD only)

```
PIEC 1
```

Restricts output to fully connected molecules. Always set to 1. No variation needed.

### ELIM — Eliminate Long-Range Correlations

```
ELIM N_correlations N_bonds
```

ELIM exists in **native LSD** and passes through to pyLSD unchanged. Semantics:

- `ELIM 1 4` — allow up to 1 HMBC correlation to be interpreted as a 4J (up to 4 bonds). The solver will try eliminating that correlation if it prevents solution assembly.
- `ELIM 3 4` — allow up to 3 correlations to be 4J.
- ELIM is **disabled by default** (Sherlock disables it too). Only enable when suspect 4J correlations are present.

**For 4J exploration in lucy-ng:** When nmr-chemist flags suspect 4J HMBC correlations, enable ELIM with count = number of suspect correlations. This lets the solver decide which correlations are 4J rather than forcing the agent to manually exclude them.

**Interaction with HMBC bond range:** When a HMBC line specifies explicit bond range `HMBC C H 2 4`, the correlation is treated as possibly 4J. ELIM must be active (with `N_bonds >= 4`) for such extended-range HMBC commands to take effect. Without ELIM, extended bond ranges have no effect.

Example for ibuprofen 4J case (3 suspect correlations through aromatic ring):
```
ELIM 3 4
HMBC 4 8 2 4   ; suspect 4J: C4a -> H6 through para-substituted benzene
HMBC 6 9 2 4   ; suspect 4J: C5a -> H7
HMBC 8 4 2 4   ; suspect 4J: same pair reversed
```

### MULT — Multi-State Atom Definition (extended in pyLSD)

**Native LSD (single state only):**
```
MULT atom_num element hybridisation multiplicity
MULT 1 C 2 0    ; atom 1 is sp2 carbon with 0 attached H (quaternary sp2)
```

**pyLSD (multiple states as tuples):**
```
MULT atom_num element[(valencies)] (hybridisations) (multiplicities)
MULT 14 O (2 3) (0 1)     ; oxygen, sp2 or sp3, 0 or 1 attached H
MULT 19 N35 (1 2 3) (0 1 2 3)  ; nitrogen, valence 3 or 5, sp1/sp2/sp3, 0-3 H
```

**Impact:** pyLSD enumerates all state combinations and runs LSD once per combination. For ibuprofen's 2 oxygens with ambiguous states, this produces `2*2 = 4` LSD runs. For typical natural products with 2-4 ambiguous heteroatoms, expect 4-16 LSD runs — manageable.

**For lucy-ng:** Unambiguous carbons (known from DEPT) continue using single-state MULT. Only heteroatoms with unknown hybridisation use tuple notation. The lsd-engineer agent writes tuple MULT for heteroatoms when hybridisation is not directly observable (O, N without direct spectral evidence).

### SHIX / SHIH — Chemical Shift Assignment

Already supported in existing LSDInputGenerator. No changes needed. Included here for completeness:

```
SHIX atom_index shift_ppm    ; 13C shift for heavy atom
SHIH H_index shift_ppm       ; 1H shift for hydrogen
```

---

## Integration Architecture

### Option A: pyLSD as Subprocess (Recommended)

The existing `LSDRunner` calls `lsd < file`. The new `PyLSDRunner` calls `python lsd.py file`:

```python
class PyLSDRunner:
    def __init__(self, pylsd_dir: Path):
        # pylsd_dir = path to Variant/ directory
        self.variant_dir = pylsd_dir
        self.lsd_py = pylsd_dir / "lsd.py"

    def run_file(self, input_file: Path, timeout: int = 300) -> LSDResult:
        proc = subprocess.run(
            ["python", str(self.lsd_py), str(input_file)],
            cwd=self.variant_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        # pyLSD writes solutions in input_file directory as *.smi or *.sol
        # Parse solutions, collect SMILES, return LSDResult
        ...
```

**Why subprocess over importing `lsd.py`:** pyLSD's `lsd.py` is a standalone script, not a Python package. It uses `sys.exit()` calls and global state that make direct import unsafe. Subprocess is cleaner and consistent with the existing LSD runner architecture.

**Working directory:** pyLSD must be invoked from `Variant/` (it uses relative paths in `defaults.py` to locate LSD binaries and data folders). Pass the absolute input file path as argument; pyLSD writes output to the input file's directory.

### Option B: Direct LSD Calls with Manual ELIM (Fallback)

For 4J exploration specifically, the existing `LSDRunner` can use ELIM directly — ELIM is a native LSD command, not pyLSD-only. If the only goal is 4J handling (not ambiguous atom states), the agent can write an LSD file with ELIM enabled and call `lsd` directly.

**When to use Option B:** If pyLSD installation proves problematic (path configuration, cross-platform issues). All 4J exploration functionality works without pyLSD — pyLSD's value is specifically for ambiguous heteroatom states (the MULT multi-state feature).

**Recommendation:** Implement pyLSD integration (Option A) for full capability, but design the 4J exploration workflow to work via Option B (direct LSD + ELIM) as a fallback. The CLI command `lucy lsd run-pylsd` wraps pyLSD; `lucy lsd run` continues to call LSD directly.

---

## LSDInputGenerator Extension

The existing `LSDInputGenerator` needs a new mode to emit pyLSD syntax. **Do not change existing LSD output** — maintain backward compatibility.

New method: `LSDInputGenerator.generate_pylsd(problem, elim_count=0, elim_max_bonds=4)`:

```python
# Additions to generate_pylsd() output vs generate():

# 1. FORM command at top (before PIEC)
lines.append(f"FORM {format_formula(problem.molecular_formula)}")
lines.append("PIEC 1")

# 2. ELIM (conditional — only when agent requests it)
if elim_count > 0:
    lines.append(f"ELIM {elim_count} {elim_max_bonds}")

# 3. MULT with tuple notation for ambiguous atoms
# Single-state carbon: "MULT 1 C 2 0"  (unchanged)
# Multi-state oxygen: "MULT 14 O (2 3) (0 1)"
for atom in problem.atoms:
    if atom.has_multiple_states:
        lines.append(atom.to_pylsd_mult_line())  # tuple notation
    else:
        lines.append(atom.to_mult_line())  # existing LSD notation (unchanged)

# 4. HMBC with optional bond range
# Default: "HMBC 1 3"  (unchanged, 2-3 bonds implied)
# Explicit range: "HMBC 1 3 2 4"  (for flagged 4J suspects)
```

The `LSDCorrelation` model gets an optional `bond_range: tuple[int, int] | None` field. When set to `(2, 4)`, the correlation is written with explicit range. The agent sets this field when flagging suspect 4J correlations.

---

## Configuration Management

pyLSD requires `defaults.py` to be configured for the local system. This is a one-time setup analogous to configuring the LSD binary path. Options:

1. **Environment variable** `PYLSD_DIR` pointing to the Variant/ directory — simplest, consistent with existing PATH-based LSD discovery.
2. **lucy status** check — extend `lucy lsd check` to also verify pyLSD is found and configured.

**Recommended:** Add `PYLSD_DIR` environment variable support to `PyLSDRunner`. The `lucy status` skill already checks for LSD; add pyLSD check to the same command.

---

## New CLI Command

```bash
lucy lsd run-pylsd compound.lsd      # Run pyLSD on a file
lucy lsd run-pylsd compound.lsd --elim 3 4  # With ELIM enabled
```

This parallels the existing `lucy lsd run` command. The agent chooses which command to use based on whether pyLSD features are needed.

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Java runtime as lucy-ng dependency | Only needed for pyLSD's built-in ranking, which is disabled in favour of HOSE-based ranking | No change — existing HOSE ranking is sufficient |
| pylsd-nova or ocrd-fork-pylsd from PyPI | Completely different project — Python bindings for an image processing library, not NMR CASE | Download nuzillard/PyLSD from GitHub |
| casekit (Java) | Sherlock uses this Java library for pyLSD file generation. Lucy-ng is Python and already has LSDInputGenerator. | Extend existing Python LSDInputGenerator |
| Sherlock web services | Full Java/Spring microservice stack. Lucy-ng is a CLI tool. | Direct subprocess invocation of pyLSD |
| WebCocon 4J-Flag approach | WebCocon's 4J-Flag parameter varies the count of allowed 4J correlations iteratively. LSD's ELIM achieves the same result directly. Different tool, not applicable. | LSD ELIM command |
| Parallel LSD runs (manual orchestration) | pyLSD already handles parallelism internally for variable atom states. Lucy-ng does not need to re-implement this. | Let pyLSD orchestrate its own LSD runs |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| pyLSD invocation | Subprocess `python lsd.py FILE` | Import `lsd.py` as module | lsd.py uses `sys.exit()` and global mutable state; not designed for import. Subprocess is safe and consistent with existing LSD runner. |
| 4J handling | LSD ELIM (works in both LSD and pyLSD) | Remove 4J suspect correlations entirely | Removal was v4.0 approach — caused empty solution set. ELIM lets solver decide which correlations are 4J, preserving all correlations in the constraint set. |
| 4J handling | LSD ELIM | WebCocon 4J-Flag iterative approach | WebCocon is a different CASE tool (COCON-based). Lucy-ng uses LSD/pyLSD. ELIM is the LSD-native mechanism for exactly this problem. |
| File format extension | Extend LSDInputGenerator with `generate_pylsd()` | New PyLSDInputGenerator class | Minor functional addition; same model types. Adding a method maintains DRY and avoids duplicating all the existing MULT/HSQC/HMBC/BOND generation logic. |

---

## Version Compatibility

| Component | Required | Notes |
|-----------|----------|-------|
| PyLSD | a8 (latest) | Python 3 required from a8. No newer version found. |
| LSD binary | 3.5.2 or 3.5.3 | pyLSD-a8 is based on LSD 3.5.2. LSD 3.5.3 is identical to 3.5.2. Both work. |
| Python | 3.10+ | pyLSD a8 requires Python 3; no upper bound issue seen. |
| Java | NOT required | Only for built-in ranking — disable in defaults.py |

---

## Installation

No new Python packages required. pyLSD is a standalone Python script, not a pip-installable package.

```bash
# Download and install pyLSD (one-time setup)
wget https://github.com/nuzillard/PyLSD/raw/master/pylsd-linux-a8.tar.gz
tar -xzf pylsd-linux-a8.tar.gz -C ~/PyLSD/
# Edit ~/PyLSD/Variant/defaults.py:
#   lsdbin = os.path.expanduser("~/PyLSD/LSD")  (or wherever LSD binaries are)
#   datafolder = os.path.expanduser("~/PyLSD/LSD/Data")

# Verify pyLSD works
cd ~/PyLSD/Variant && python lsd.py breg57.lsd

# Set environment variable for lucy-ng
export PYLSD_DIR=~/PyLSD/Variant

# Verify lucy-ng can find pyLSD (after v8.0 ships)
lucy lsd check
```

---

## Sources

**PRIMARY SOURCES (HIGH confidence):**
- [PyLSD official site](https://nuzillard.github.io/PyLSD/) — confirmed download method (GitHub archive), Python 3 requirement from a8, invocation as `python lsd.py FILE`
- [PyLSD Installation](https://nuzillard.github.io/PyLSD/INSTALL.html) — confirmed: Java optional (ranking only), defaults.py configuration, three-directory structure (Variant/, LSD/, Predict/)
- [LSD Manual (nuzillard.github.io)](https://nuzillard.github.io/LSD/MANUAL_ENG.html) — ELIM command confirmed: `ELIM P1 P2` where P1=max correlations eliminated, P2=max bond count; SHIX/SHIH confirmed as native LSD commands
- [GitHub: nuzillard/PyLSD](https://github.com/nuzillard/PyLSD) — confirmed available distributions: pylsd-linux-a8.tar.gz, pylsd-windows-a8.zip, pylsd-nmrbox-a7.tar.gz
- `background/wenk-thesis.txt` lines 2069–2247, 5491–5600 — FORM/PIEC/ELIM/MULT/SHIX/SHIH command semantics, complete ibuprofen pyLSD example, pyLSD execution description, Sherlock's Java ranking explicitly disabled

**SECONDARY SOURCES (MEDIUM confidence):**
- [Sherlock PMC paper (PMC9920390)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9920390/) — pyLSD used for structure generation, built-in ranking disabled in Sherlock
- [WebCocon 4J paper (PMC8398166)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8398166/) — alternative 4J approach (WebCocon 4J-Flag); reviewed and not adopted
- `src/lucy_ng/lsd/runner.py` — existing runner architecture; subprocess pattern confirmed for pyLSD adaptation

---

*Stack research for: pyLSD integration enabling ambiguous atom states and ELIM-based 4J exploration*
*Researched: 2026-03-13*
*Confidence: HIGH for command semantics, integration architecture, and ELIM usage. MEDIUM for pyLSD version currency (a8 appears to be latest, no updates since ~2022 visible).*
