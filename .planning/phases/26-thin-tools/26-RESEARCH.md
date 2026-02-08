# Phase 26: Thin Tools - Research

**Researched:** 2026-02-08
**Domain:** Python refactoring, MCP removal, CLI simplification, code consolidation
**Confidence:** HIGH

## Summary

Phase 26 implements a fundamental architecture simplification: remove MCP entirely, make all CLI commands thin data-access wrappers, and shift ALL intelligence to the AI agent operating from skill documents. This is not merely "refactoring" but an architectural pivot from dual-mode (smart Python + AI) to single-mode (thin Python, intelligent AI).

**Key architectural shift:** From "Python does smart things, AI orchestrates" to "Python returns raw data, AI does all reasoning."

The research reveals that this is a well-understood refactoring pattern (extract business logic from infrastructure), but lucy-ng's scale (~2,139 lines of domain logic across 8 modules) and tight integration between CLI/MCP/shared-core make this a substantial effort. The three-layer architecture (CLI + MCP → shared implementation) means refactoring only needs to happen in the shared modules, but tests must be carefully managed to avoid losing regression coverage of the underlying algorithms.

**Primary recommendation:** Execute this as a two-wave plan: Wave 1 removes MCP + consolidates duplication + makes Tier 3 CLI thin; Wave 2 reviews Tier 2 CLI for intelligence removal. Validate continuously using Ibuprofen de novo CASE.

## Standard Stack

The phase uses existing lucy-ng stack with no new dependencies.

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.10+ | Implementation language | lucy-ng minimum version |
| click | >=8.0 | CLI framework | Already in use for lucy CLI |
| pytest | >=7.0 | Testing | Already in use for tests |
| ruff | >=0.1 | Linting | Already configured in pyproject.toml |
| mypy | >=1.0 | Type checking | Already configured (strict mode) |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest-cov | >=4.0 | Coverage reporting | Optional: verify test coverage before/after |
| git | any | Version control | Required: track incremental refactoring |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Incremental refactoring | Big-bang rewrite | Incremental preserves working state; big-bang is faster but riskier |
| Keep tests | Delete tests | Keep = regression safety; delete = cleaner but lose coverage |
| Two-wave plan | Single wave | Two-wave = safer (validate MCP removal first); single = faster |

**Installation:**

No new dependencies. All tools already in lucy-ng dev environment.

```bash
# Already installed via:
pip install -e ".[dev]"
```

## Architecture Patterns

### Current Three-Layer Architecture

lucy-ng has a three-layer stack where CLI and MCP are thin wrappers over shared implementation:

```
MCP Server (server.py, 1282 lines)     CLI Modules (9 files, 2695 lines)
          \                                /
           \                              /
            +------- Shared Core --------+
            |                            |
            |  readers/bruker.py    (278)|
            |  processing/*.py      (752)|
            |  analysis/*.py        (576)|
            |  dereplication/*.py   (526)|
            |  lsd/*.py            (991)|
            |  prediction/*.py     (277)|
            |  ranking/*.py        (205)|
            |  database/*.py       (729)|
            |  nmrxiv/*.py         (454)|
            |  visualization/*.py (1151)|
            |  Total: ~5,939 lines      |
            +----------------------------+
```

**Implication for Phase 26:**
- Refactoring only needs to happen in shared modules (middle layer)
- MCP removal is straightforward deletion (top-left layer)
- CLI simplification means changing how CLI calls into shared modules (top-right layer)

**Source:** AUDIT-REPORT.md Section 5.2

### Pattern 1: Thin Wrapper Over Shared Logic

**What:** CLI command is a thin adapter that parses args, calls shared module, formats output.

**When to use:** All CLI commands after Phase 26.

**Example (current smart wrapper):**

```python
# cli/lsd.py - BEFORE (smart wrapper with auto-discovery)
@lsd.command("generate")
def lsd_generate(data_dir: str, formula: str, output: str | None):
    """Generate LSD input from NMR data directory."""
    data_path = Path(data_dir)

    # INTELLIGENCE: Auto-discover experiments by pulse program
    experiments = {}
    for subdir in sorted(data_path.iterdir()):
        try:
            spec2d = BrukerReader.read_2d(str(subdir))
            experiments[spec2d.experiment_type.upper()] = subdir
        except Exception:
            spec1d = BrukerReader.read_1d(str(subdir))
            pulse_prog = spec1d.metadata.get("pulse_program", "").lower()
            if "dept135" in pulse_prog:
                experiments["DEPT135"] = subdir
            # ... more auto-detection ...

    # INTELLIGENCE: DEPT-guided HSQC picking
    dept_result = DEPTGuidedPicker.pick_hsqc_peaks(hsqc, dept135)

    # INTELLIGENCE: HMBC filtering
    hmbc_result = HMBCGuidedPicker.pick_hmbc_peaks_from_spectra(...)

    # INTELLIGENCE: LSD constraint generation
    problem = LSDInputGenerator.from_dept_result(...)

    lsd_content = LSDInputGenerator.generate(problem)
    click.echo(lsd_content)
```

**Example (thin wrapper after Phase 26):**

```python
# cli/lsd.py - AFTER (thin wrapper, no intelligence)
# NOTE: lucy lsd generate is REMOVED ENTIRELY per user decision
# AI writes LSD files directly using skill knowledge

# Other commands become thin...
@pick.command("hsqc")
def pick_hsqc(path: str, threshold: float = 0.05):
    """Pick raw HSQC peaks above threshold (no DEPT filtering)."""
    hsqc = BrukerReader.read_2d(path)

    # Call thin picker (no DEPT guidance)
    from lucy_ng.processing.peak_picker_2d import PeakPicker2D
    peaks = PeakPicker2D.pick_peaks(hsqc, threshold=threshold)

    # Format and output
    for peak in peaks.peaks:
        click.echo(f"{peak.f1_position:.2f}\t{peak.f2_position:.2f}\t{peak.intensity:.1f}")
```

**Key differences:**
- No auto-discovery (AI specifies exact paths)
- No guided picking (raw threshold-based picking only)
- No constraint generation (AI builds constraints using skill knowledge)
- Simple data formatting (JSON or TSV, no interpretation)

**Source:** CONTEXT.md decisions + existing cli/lsd.py

### Pattern 2: Code Consolidation into Shared Utilities

**What:** Move duplicated wrapper-layer logic into shared utilities accessible to both CLI and (previously) MCP.

**When to use:** When the same logic appears in multiple wrapper layers.

**Example (database auto-detection consolidation):**

```python
# BEFORE: Duplicated in cli/dereplicate.py and mcp/server.py

# cli/dereplicate.py lines 23-82
def _find_database_path() -> Path | None:
    """Find SQLite database in default locations."""
    # 60 lines of search logic...
    return None

# mcp/server.py imports from CLI module (cross-layer dependency)
from lucy_ng.cli.dereplicate import _find_database_path
```

```python
# AFTER: Consolidated in database/finder.py

# src/lucy_ng/database/finder.py (NEW)
class DatabaseFinder:
    """Locate lucy-ng database files in standard locations."""

    @staticmethod
    def find_derep_database() -> Path | None:
        """Find lucy-ng-derep.db in standard locations.

        Search order:
        1. LUCY_DATABASE environment variable
        2. data/reference/lucy-ng-derep.db (project location)
        3. Common locations (~/.lucy/, ~/lucy-ng/)
        4. macOS Spotlight (mdfind)
        5. Dropbox/develop (common dev location)

        Returns:
            Path to database file if found, None otherwise
        """
        # Moved from cli/dereplicate.py
        # ... search logic ...

# cli/dereplicate.py - AFTER
from lucy_ng.database.finder import DatabaseFinder

@dereplicate.command("c13")
def dereplicate_c13(c13_path: str, formula: str, database: str | None):
    if database is None:
        database = DatabaseFinder.find_derep_database()
    # ... rest of command ...
```

**Benefits:**
- Single implementation to maintain
- No cross-layer imports (CLI importing from MCP or vice versa)
- Testable in isolation
- CLI can continue using smart defaults (finder) while MCP removal doesn't affect it

**Source:** AUDIT-REPORT.md Section 3, lines 129-133

### Pattern 3: Extract Intelligence to Skill, Keep Algorithm in Python

**What:** For Tier 2 tools with domain-tuned defaults, document the reasoning strategy in SKILL.md but keep the algorithmic implementation in Python.

**When to use:** When the "intelligence" is actually a well-defined algorithm (like adaptive peak picking) but the defaults or interpretation require domain knowledge.

**Example (pick_peaks_1d - Tier 2):**

```python
# processing/peak_picker.py - ALGORITHM STAYS
class AdaptivePeakPicker:
    """Two-pass adaptive peak picking algorithm."""

    @staticmethod
    def pick_peaks(
        spectrum: Spectrum1D,
        threshold: float = 0.05,  # Domain-tuned default
        fwhm_factor: float = 1.5,  # Domain-tuned default
    ) -> PeakList1D:
        """Pick peaks using two-pass adaptive algorithm.

        This is a standard algorithm (SciPy find_peaks + local baseline).
        The defaults are tuned for NMR but can be overridden.
        """
        # ... SciPy-based peak picking ...
```

```markdown
# skill/SKILL.md Section 3 - STRATEGY DOCUMENTED

### Peak Picking Strategy (PEAK-01)

**1D Peak Picking (13C, DEPT):**

Use `lucy pick 1d <path>` with default threshold 0.05 (5% of maximum intensity).

**When to override defaults:**
- **Low S/N (< 30):** Increase threshold to 0.08-0.10 to reduce noise peaks
- **High S/N (> 100):** Can lower to 0.03 to catch weak peaks
- **Crowded aliphatic region:** Use --fwhm-factor 2.0 for better peak separation

**The algorithm:** Two-pass adaptive with local baseline correction (SciPy find_peaks).
This is a standard signal processing approach, not NMR-specific intelligence.
```

**Key principle:** Algorithm is generic (SciPy find_peaks), defaults are domain-tuned (0.05 threshold for NMR), interpretation is skill (when to override).

**Source:** AUDIT-REPORT.md Section 2 Tier 2 classifications

### Anti-Patterns to Avoid

- **Deleting tests without verification:** Tests for smart behavior may also test underlying algorithms. Review before deleting.
- **Big-bang refactoring:** Changing all 8 intelligence hotspots at once creates debugging nightmare. Go module-by-module.
- **Removing too much from Tier 2:** Some Tier 2 tools (dereplicate_c13, rank_lsd_solutions) have algorithmic intelligence that should stay. Review carefully.
- **Breaking CLI for users:** Even though this is v2.0 alpha, document breaking changes clearly.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Move duplicated code | Copy-paste with adjustments | Extract to shared module | Eliminates drift, single maintenance point |
| Database path search | Custom logic in each command | Shared DatabaseFinder class | Platform-specific edge cases (Spotlight, Dropbox sync) already handled |
| Test refactoring | Delete all smart-behavior tests | Keep as regression tests, mark as "algorithm tests" | Underlying algorithms (DEPT sign interpretation, HMBC filtering logic) are still valuable |
| LSD file parsing | Parse in CLI and separately in library | Consolidate to lsd/parser.py | Already has LSDOutputParser, input parsing should live alongside |

**Key insight:** The refactoring is "move intelligence from Python to AI", not "delete intelligence entirely." The algorithms stay; only the decision-making moves.

## Common Pitfalls

### Pitfall 1: Removing Algorithms When You Mean to Remove Heuristics

**What goes wrong:**
Confusing "domain heuristics" (carbonyl detection by shift range) with "algorithmic implementation" (DEPT sign interpretation). The former is intelligence (should move to skill); the latter is calculation (should stay in Python).

**Why it happens:**
Both are "smart behavior" but different kinds. Heuristics = "if shift > 165, probably carbonyl" (domain rule). Algorithm = "if DEPT sign is negative, multiplicity is CH2" (NMR physics fact).

**How to avoid:**

| Ask | Intelligence (move to skill) | Algorithm (keep in Python) |
|-----|----------------------------|---------------------------|
| Is this a decision rule? | "If aromatic, assume sp2" ✓ | "Negative DEPT = CH2" ✗ |
| Does it vary by context? | "Use 5-10 HMBC if high quality" ✓ | "Find peaks > threshold" ✗ |
| Is it a fact of physics? | "Carbonyl often 165-185" ✓ | "DEPT-135: CH3/CH up, CH2 down" ✗ |
| Would an expert override it? | "Sometimes quaternary is sp3" ✓ | "Peak position is max of window" ✗ |

**Warning signs:**
- Removing `DEPTGuidedPicker.pick_hsqc_peaks` algorithm → Too much. Keep the algorithm, make CLI thin by not calling it.
- Removing shift-based carbonyl detection → Correct. This is a heuristic the AI should apply.
- Removing HOSE radius fallback → Too much. This is a defined algorithm (6→5→4→3→2→1 with confidence weighting).

**Example:**

```python
# HEURISTIC - Move to skill
if 165 <= carbon_shift <= 185:
    hybridization = Hybridization.SP2  # Probably ester/amide carbonyl
elif 190 <= carbon_shift <= 220:
    hybridization = Hybridization.SP2  # Probably ketone/aldehyde carbonyl

# ALGORITHM - Keep in Python
if dept_sign > 0:
    multiplicity = "CH/CH3"  # DEPT-135 physics: positive = CH or CH3
elif dept_sign < 0:
    multiplicity = "CH2"     # DEPT-135 physics: negative = CH2
```

### Pitfall 2: Losing Test Coverage During Refactoring

**What goes wrong:**
Deleting tests for "smart behavior" inadvertently deletes tests for underlying algorithms. Example: Deleting all `test_dept_guided_picker.py` loses regression tests for the DEPT sign interpretation algorithm.

**Why it happens:**
Tests named after the high-level feature (DEPT-guided picking) actually test both the high-level orchestration (should be removed) and the low-level algorithm (should be kept).

**How to avoid:**

**Test classification strategy:**

1. **Identify what the test validates:**
   - Orchestration logic (auto-discovery, multi-step workflow)? → Delete or rewrite as integration test
   - Algorithmic correctness (DEPT sign → multiplicity, peak threshold detection)? → Keep as regression test
   - Edge case handling (negative DEPT, zero peaks)? → Review; likely keep

2. **For tests to keep, rename to reflect what they test:**

```python
# BEFORE (ambiguous what's being tested)
def test_pick_hsqc_peaks():
    """Test DEPT-guided HSQC peak picking."""
    # Tests both orchestration AND algorithm

# AFTER (split into two tests)
def test_dept_sign_to_multiplicity():
    """Test DEPT sign interpretation algorithm (regression test)."""
    # Keeps algorithmic test: positive → CH/CH3, negative → CH2

def test_hsqc_raw_peak_picking():
    """Test raw HSQC peak picking above threshold."""
    # New thin wrapper test: just threshold-based picking
```

3. **Mark algorithm tests explicitly:**

```python
# tests/test_processing_algorithms.py (NEW file for algorithm regression tests)
"""Regression tests for peak picking and filtering algorithms.

These tests validate the underlying algorithms (DEPT physics, cross-validation logic,
etc.) independent of the CLI/MCP thin wrapper layer. They should be preserved even
as the wrapper layer becomes thinner.
"""

class TestDEPTSignInterpretation:
    """DEPT-135 sign interpretation is NMR physics, not heuristic."""
    # ... tests ...

class TestHMBCCrossValidation:
    """HMBC filtering against known C/H positions is algorithmic."""
    # ... tests ...
```

**Warning signs:**
- Test coverage drops from 85% to 40% → Probably deleted algorithm tests, not just orchestration tests
- No tests remain for DEPT sign interpretation → Algorithmic coverage lost
- Only CLI tests, no library tests → Regression coverage gone

### Pitfall 3: Inconsistent Thin-ness Across Commands

**What goes wrong:**
Some commands become fully thin (raw data only) while others retain smart defaults, creating inconsistent AI agent experience. Example: `lucy pick hsqc` becomes thin but `lucy dereplicate c13` still auto-detects database.

**Why it happens:**
The CONTEXT.md user decision says "all CLI commands become thin" but Tier 1 tools (read, fetch, check) are explicitly marked "stay as-is." The boundary between "operational convenience" (database auto-detection) and "domain intelligence" (DEPT-guided picking) is unclear.

**How to avoid:**

**Thin-ness classification:**

| Behavior | Thin or Smart? | Rationale |
|----------|---------------|-----------|
| Database auto-detection (env var → project → Spotlight) | **Operational convenience** → Keep | Not domain intelligence; path finding is OS-level concern |
| Experiment type auto-detection (pulse program → HSQC/DEPT) | **Domain intelligence** → Remove | Requires NMR knowledge; AI should specify experiment types explicitly |
| DEPT-guided threshold adjustment | **Domain intelligence** → Remove | Requires spectroscopy reasoning; AI should set thresholds |
| Format auto-detection (SD vs SQLite) | **Operational convenience** → Keep | File format detection is standard practice |
| HMBC cross-validation filtering | **Domain intelligence** → Remove | Requires NMR validation logic; AI should filter |

**Consistency rules:**

1. **Tier 1 tools keep operational convenience:**
   - Database path finding (not domain knowledge)
   - File format detection (standard practice)
   - Binary availability checking (`check_lsd_availability`)
   - File I/O operations (`read_spectrum_1d`)

2. **All domain inference removed:**
   - Spectral quality assessment (move to AI via SKILL.md)
   - Peak filtering based on NMR knowledge (DEPT, HMBC validation)
   - Constraint generation from spectra (LSD input generation)
   - Experiment type inference (pulse program patterns)

3. **When in doubt, ask:** "Would an NMR expert override this decision in specific cases?"
   - Yes → Domain intelligence, remove
   - No → Operational convenience, keep

**Source:** CONTEXT.md user decision "All CLI commands become thin" + Tier classifications from AUDIT-REPORT.md

### Pitfall 4: MCP Removal Breaks Agent Workflows

**What goes wrong:**
Existing AI agent workflows depend on MCP tool calls. Removing MCP without updating agent instructions causes failures.

**Why it happens:**
The supervisor, CASE, and diagnostic specialist agents were designed for MCP tools. They have specific tool names (e.g., `pick_hsqc_peaks`, `generate_lsd_input`) hardcoded in their skill documents and agent definitions.

**How to avoid:**

**Agent update checklist:**

1. **.claude/agents/supervisor.md** (383 lines):
   - Remove MCP tool references
   - Add Bash tool usage patterns for `lucy ...` CLI
   - Update routing logic to use CLI commands

2. **.claude/agents/diagnostic-specialist.md** (455 lines):
   - Already uses Bash tool for `lucy lsd` commands
   - Remove any lingering MCP tool references
   - Update to expect AI-written LSD files (not `generate_lsd_input` output)

3. **skill/SKILL.md frontmatter**:
   - Remove `tools:` list (MCP tools)
   - Update to reference CLI commands via Bash

4. **skill/CASE/SKILL.md workflow**:
   - Update Step 2 (peak picking) from MCP tools to CLI commands
   - Update Step 4 (LSD generation) to direct file writing, not `lucy lsd generate`
   - Update Step 5 (ranking) from MCP to CLI

**Migration pattern:**

```markdown
# BEFORE (MCP tools)
## Step 2: Pick Peaks

Use `pick_hsqc_peaks` tool with DEPT-135 spectrum for ground truth...

# AFTER (CLI via Bash)
## Step 2: Pick Peaks

Use Bash tool to run `lucy pick hsqc <path> --threshold 0.05` for raw HSQC peaks.
Apply DEPT-guided filtering logic yourself using SKILL.md Section 3.2...
```

**Warning signs:**
- Agent tries to call `pick_hsqc_peaks()` → MCP tool reference not updated
- Agent doesn't know how to run CLI commands → Bash usage pattern missing from skill
- Agent expects `generate_lsd_input` → Not updated for direct LSD file writing

**Source:** CONTEXT.md MCP removal decision + existing agent definitions at .claude/agents/

## Code Examples

Verified patterns from existing lucy-ng codebase:

### Thin CLI Command Pattern

```python
# Example: Read spectrum (already thin, Tier 1)
# src/lucy_ng/cli/read.py

@read.command("1d")
@click.argument("path", type=click.Path(exists=True))
@click.option("--format", type=click.Choice(["text", "json"]), default="text")
def read_1d(path: str, format: str) -> None:
    """Read a Bruker 1D NMR spectrum."""
    spectrum = BrukerReader.read_1d(path)

    if format == "json":
        click.echo(json.dumps({
            "nucleus": spectrum.nucleus,
            "frequency": spectrum.frequency,
            "points": len(spectrum.data),
            "ppm_min": float(spectrum.ppm_scale.min()),
            "ppm_max": float(spectrum.ppm_scale.max()),
        }))
    else:
        click.echo(f"Nucleus: {spectrum.nucleus}")
        click.echo(f"Frequency: {spectrum.frequency} MHz")
        # ... more text output ...
```

**Pattern elements:**
- Single shared module call: `BrukerReader.read_1d(path)`
- Argument parsing: `click.argument`, `click.option`
- Format handling: JSON vs text output
- Zero domain logic: no NMR reasoning, just I/O

**Source:** src/lucy_ng/cli/read.py (existing Tier 1 command)

### Database Finder Consolidation

```python
# Target location: src/lucy_ng/database/finder.py (NEW)

"""Database file location utilities."""

import os
import subprocess
from pathlib import Path


class DatabaseFinder:
    """Locate lucy-ng database files in standard locations."""

    @staticmethod
    def find_derep_database() -> Path | None:
        """Find lucy-ng-derep.db in standard locations.

        Search order:
        1. LUCY_DATABASE environment variable
        2. data/reference/lucy-ng-derep.db (project location)
        3. Common locations (~/.lucy/, ~/lucy-ng/)
        4. macOS Spotlight (mdfind)
        5. Dropbox/develop (common dev location)

        Returns:
            Path to database file if found, None otherwise
        """
        db_name = "lucy-ng-derep.db"

        # 1. Environment variable
        env_db = os.environ.get("LUCY_DATABASE")
        if env_db:
            env_path = Path(env_db)
            if env_path.exists() and env_path.suffix == ".db":
                return env_path

        # 2. Project location
        default_db = Path("data/reference") / db_name
        if default_db.exists():
            return default_db

        # 3. Common locations
        common_paths = [
            Path.home() / ".lucy" / db_name,
            Path.home() / "lucy-ng" / "data" / "reference" / db_name,
            Path.home() / ".local" / "share" / "lucy-ng" / db_name,
        ]
        for p in common_paths:
            if p.exists():
                return p

        # 4. macOS Spotlight
        try:
            result = subprocess.run(
                ["mdfind", "-name", db_name],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                found_path = Path(result.stdout.strip().split("\n")[0])
                if found_path.exists():
                    return found_path
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # 5. Dropbox/develop
        dropbox_dev = Path.home() / "Dropbox" / "develop" / "lucy-ng" / "data" / "reference" / db_name
        if dropbox_dev.exists():
            return dropbox_dev

        return None
```

**Usage after consolidation:**

```python
# cli/dereplicate.py
from lucy_ng.database.finder import DatabaseFinder

@dereplicate.command("c13")
def dereplicate_c13(c13_path: str, formula: str, database: str | None):
    if database is None:
        database = DatabaseFinder.find_derep_database()
        if database is None:
            click.echo("Error: Database not found. Use --database or set LUCY_DATABASE.", err=True)
            raise SystemExit(1)
    # ... rest of command ...
```

**Source:** Extracted from src/lucy_ng/cli/dereplicate.py lines 23-82

### LSD File Writing (AI Direct, No CLI)

```python
# AI agent code (conceptual - happens in Claude Code, not Python)

# BEFORE Phase 26: Agent calls lucy lsd generate
result = bash("lucy lsd generate data/Ibuprofen C13H18O2")
lsd_content = result.stdout
write("ibuprofen.lsd", lsd_content)

# AFTER Phase 26: Agent writes LSD file directly using skill knowledge
from skill/SKILL.md Section 6 (LSD Reference):
- Read DEPT peaks: bash("lucy pick 1d data/Ibuprofen/3")
- Read HSQC peaks: bash("lucy pick hsqc data/Ibuprofen/6 --threshold 0.05")
- Read HMBC peaks: bash("lucy pick hmbc data/Ibuprofen/7 --threshold 0.05")

Apply DEPT-guided filtering logic (skill/SKILL.md Section 3.2):
- Match HSQC carbons to DEPT carbons (tolerance ±1.0 ppm)
- Extract multiplicity from DEPT sign (positive = CH/CH3, negative = CH2)

Apply HMBC cross-validation (skill/SKILL.md Section 3.3):
- Filter HMBC peaks against known C positions (±1.5 ppm)
- Filter HMBC peaks against HSQC H positions (±0.1 ppm)

Build LSD problem structure (skill/SKILL.md Section 6.2):
- MULT lines from HSQC + formula (sp2/sp3 from shift, H from multiplicity)
- HSQC lines from filtered HSQC peaks
- HMBC lines from validated HMBC peaks
- sp2 count parity check (must be even)

Write LSD file:
write("ibuprofen.lsd", """
; LSD input file: Ibuprofen
; Generated by AI agent using skill knowledge
; Molecular formula: C13H18O2

; Atom definitions
MULT 1 C 2 0
MULT 2 C 2 1
...

; Direct C-H correlations (HSQC)
HSQC 2 2
HSQC 3 3
...

; Long-range C-H correlations (HMBC)
HMBC 1 2
HMBC 1 3
...

EXIT
""")
```

**Key differences:**
- No `lucy lsd generate` command exists
- AI reads raw peak data from thin CLI commands
- AI applies filtering/validation logic from SKILL.md
- AI constructs LSD syntax directly (knows MULT, HSQC, HMBC format)
- AI validates constraints (sp2 even, H budget) before writing

**Source:** CONTEXT.md user decision "lucy lsd generate removed entirely" + skill/diagnostic/SKILL.md Section 1

## State of the Art

| Old Approach (pre-Phase 26) | Current Approach (Phase 26) | When Changed | Impact |
|------------------------------|----------------------------|--------------|--------|
| MCP + CLI dual mode | CLI only | Phase 26 | Simplifies architecture, single interface |
| Smart CLI with embedded heuristics | Thin CLI returning raw data | Phase 26 | All intelligence moves to AI agent |
| `lucy lsd generate` auto-generates LSD | AI writes LSD files directly | Phase 26 | AI has full control over constraints |
| DEPT-guided HSQC picking in Python | Raw HSQC picking + AI filtering | Phase 26 | AI can override filtering logic |
| HMBC cross-validation in Python | Raw HMBC picking + AI validation | Phase 26 | AI can adjust tolerances per spectrum |
| Symmetry heuristics in Python | Raw intensity data + AI reasoning | Phase 26 | AI reasons from first principles |

**Deprecated/outdated:**

- **MCP server (`src/lucy_ng/mcp/server.py`)**: Entire file deleted. AI uses CLI via Bash tool instead.
- **`lucy lsd generate` command**: Removed entirely. AI writes LSD files directly using skill knowledge.
- **DEPTGuidedPicker in CLI**: Algorithm stays in library, CLI no longer calls it (calls raw picker instead).
- **HMBCGuidedPicker in CLI**: Algorithm stays in library, CLI no longer calls it (calls raw picker instead).
- **LSDInputGenerator.from_dept_result()**: High-level helper removed. Low-level `LSDInputGenerator.generate(problem)` kept for testing/library use.

## Open Questions

Things that couldn't be fully resolved:

1. **Tier 2 CLI Intelligence Scope**
   - What we know: Tier 2 tools have "domain-tuned defaults or scoring strategies" (AUDIT-REPORT.md)
   - What's unclear: Which Tier 2 intelligence is "algorithm" (keep) vs "heuristic" (remove)?
   - Recommendation: Review each Tier 2 tool individually during Wave 2. Examples:
     - `pick_peaks_1d`: Adaptive algorithm with tuned defaults → **Keep algorithm, document defaults in SKILL.md**
     - `dereplicate_c13`: Region-specific tolerances, geometric mean scoring → **Review scoring logic; may be algorithmic**
     - `rank_lsd_solutions`: N:1 symmetry matching, MAE calculation → **Keep algorithm, document interpretation in SKILL.md**
     - `predict_c13_shifts`: HOSE radius fallback with confidence → **Keep algorithm, document confidence formula in SKILL.md**

2. **Test Strategy Boundary**
   - What we know: Smart-behavior tests exist for DEPT/HMBC/symmetry (20+ test files touch these)
   - What's unclear: Which tests are "orchestration" (delete) vs "algorithm" (keep)?
   - Recommendation:
     - Keep all tests initially
     - Mark tests as "orchestration" vs "algorithm" during refactoring
     - Move algorithm tests to `tests/test_processing_algorithms.py` (new file)
     - Delete orchestration tests only after verifying algorithm coverage

3. **Agent Skill Document Size**
   - What we know: skill/ documents total 5,089 lines (across 6 files)
   - What's unclear: Does adding LSD file writing guidance to CASE/SKILL.md make it too large?
   - Recommendation:
     - skill/diagnostic/SKILL.md Section 1 already has LSD command reference (1,874 lines total)
     - skill/SKILL.md Section 6 has basic LSD reference (610 lines total)
     - CASE agent references both; no new content needed for LSD writing
     - IF validation reveals gaps, add subsection to skill/CASE/SKILL.md (estimated +50 lines)

4. **Validation Success Criteria**
   - What we know: "Correct Ibuprofen structure appears as top-ranked LSD solution (top 3)" (CONTEXT.md)
   - What's unclear: What constitutes "correct" ranking? Exact SMILES match or structural equivalence?
   - Recommendation:
     - Use `rdkit.Chem.MolToSmiles(mol, canonical=True)` for canonical SMILES comparison
     - Accept any stereoisomer as valid (Ibuprofen has 1 chiral center; 13C NMR doesn't resolve it)
     - Accept any tautomer as valid (if applicable)
     - Log all top-3 SMILES for manual verification

## Sources

### Primary (HIGH confidence)

- **AUDIT-REPORT.md** (.planning/phases/20-system-audit/) - Tier classifications, intelligence hotspots, duplication areas
- **26-CONTEXT.md** (.planning/phases/26-thin-tools/) - User decisions from /gsd:discuss-phase
- **STATE.md** (.planning/) - Phase 25 completion status, accumulated decisions
- **Existing codebase inspection**:
  - src/lucy_ng/mcp/server.py (lines 1-100, structure analysis)
  - src/lucy_ng/lsd/generator.py (lines 1-100, intelligence patterns)
  - src/lucy_ng/processing/dept_guided_picker.py (lines 1-100, algorithm structure)
  - src/lucy_ng/processing/hmbc_guided_picker.py (lines 1-100, filtering logic)
  - src/lucy_ng/analysis/symmetry_analysis.py (lines 1-100, heuristics)
  - src/lucy_ng/cli/lsd.py (lines 1-150, auto-discovery pattern)
  - src/lucy_ng/cli/dereplicate.py (lines 1-150, database finder pattern)
  - tests/test_dept_guided_picker.py (lines 1-100, test patterns)
  - tests/test_lsd_generator.py (lines 1-100, test coverage)
- **skill/ documents analysis**:
  - skill/SKILL.md (lines 1-150, existing content scope)
  - skill/diagnostic/SKILL.md (lines 1-100, LSD reference depth)
  - Total line count: 5,089 lines across 6 skill files
- **pyproject.toml** - Test framework configuration (pytest, mypy, ruff)

### Secondary (MEDIUM confidence)

- **Python refactoring best practices** - From training data (extract business logic from infrastructure)
- **Thin wrapper pattern** - Standard software architecture pattern
- **Test pyramid strategy** - Integration tests at top, unit tests at base (keep algorithm tests)

### Tertiary (LOW confidence)

None. All findings verified against primary sources.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All tools already in use, verified from pyproject.toml
- Architecture patterns: HIGH - Verified from existing codebase inspection
- Pitfalls: HIGH - Derived from AUDIT-REPORT.md intelligence classifications + CONTEXT.md user decisions
- Code consolidation targets: HIGH - Line references from AUDIT-REPORT.md Section 3

**Research date:** 2026-02-08
**Valid until:** Indefinite (refactoring patterns stable; lucy-ng codebase is the ground truth)

**Research notes:**

- CONTEXT.md contains critical user decision: "ALL CLI commands become thin" (not just Tier 3)
- This OVERRIDES AUDIT-REPORT.md recommendation for "dual-mode architecture" (MCP thin, CLI smart)
- `lucy lsd generate` complete removal is a major breaking change; document in migration guide
- Validation criterion (Ibuprofen top-3 ranking) is achievable based on existing test data at data/Ibuprofen/
- No external dependencies needed; all refactoring uses existing lucy-ng stack
