# Phase 77: Fix lucy lsd run + Emergent-Aromatic Tooling + Skill Hygiene — Pattern Map

**Mapped:** 2026-06-01
**Files analyzed:** 9 (5 source files modified, 2 test files modified/created, 1 fixture file added, 1 skill file retired)
**Analogs found:** 8 / 9 (1 skill-file retirement has no code analog)

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/lucy_ng/lsd/runner.py` — `_execute_lsd` + `_invoke_outlsd` | service | request-response (subprocess) | `src/lucy_ng/lsd/runner.py` itself (existing methods) | self — targeted edit |
| `src/lucy_ng/lsd/generator.py` — new `detect_aromatic_cosy_pairs()` | utility | transform | `src/lucy_ng/detection/grouping.py::group_signals()` | role-match (pure-function transform) |
| `src/lucy_ng/cli/detect.py` — new `aromatic-cosy` subcommand | controller | request-response | `src/lucy_ng/cli/detect.py::hybridisation_command` | exact (same file, same pattern) |
| `tests/test_lsd_runner.py` — new `TestInvokeOutlsd` class + `test_ring_exclusion_lsd_produces_smiles` | test | request-response | `tests/test_lsd_runner.py::TestLSDRunnerFixed` | exact (same class, same skipif pattern) |
| `tests/test_lsd_generator.py` — new `TestDetectAromaticCosyPairs` class | test | transform | `tests/test_signal_grouping.py::TestGroupSignals` | role-match (unit test for pure function) |
| `tests/fixtures/regression/arm_a_ring_excl.lsd` | fixture (data) | — | `.planning/phases/72-design-re-validation/experiment/arm_a.lsd` | exact copy, one path edit |
| `~/.claude/agents/lucy-lsd-engineer.md` | skill (config) | — | existing file (targeted edit) | self — targeted edit |
| `~/.claude/agents/lucy-case-agent.md` | skill (config) | — | no code analog | retirement only |
| `~/.claude/commands/lucy-ng/case.md` + related skill files | skill (config) | — | existing files (targeted edit) | self — targeted edit |

---

## Pattern Assignments

### `src/lucy_ng/lsd/runner.py` — `_execute_lsd` (FIX-01A: filter file copy)

**Analog:** `src/lucy_ng/lsd/generator.py::LSDInputGenerator.write_file()` (lines 204–225) and `_write_filter_files()` (lines 227–242)

**The gap:** `_execute_lsd` copies the `.lsd` input file to `output_dir` (line 244–246) but never calls `_write_filter_files`. `write_file()` always calls it. The fix is one line added after the existing `shutil.copy2` block.

**Existing file-copy block to modify** (`src/lucy_ng/lsd/runner.py` lines 244–249):
```python
if input_file.parent.resolve() != output_dir.resolve():
    dest = output_dir / input_file.name
    shutil.copy2(str(input_file), str(dest))
    lsd_input_name = input_file.name
else:
    lsd_input_name = input_file.name
```

**Pattern to insert after the block** (mirrors `generator.py::write_file` lines 222–224):
```python
# Copy bundled ring3/ring4 filter files so DEFF F1 "ring3" / DEFF F2 "ring4" resolve.
# Unconditional — matches write_file() behavior; idempotent if already present.
LSDInputGenerator._write_filter_files(output_dir)
```

**`_write_filter_files` implementation** (`src/lucy_ng/lsd/generator.py` lines 227–242) — copy pattern verbatim:
```python
@staticmethod
def _write_filter_files(output_dir: Path) -> None:
    package = importlib.resources.files("lucy_ng.lsd.filters")
    for name in ("ring3", "ring4"):
        content = (package / name).read_text()
        (output_dir / name).write_text(content)
```

**Import already present** in `runner.py` line 9:
```python
from lucy_ng.lsd.generator import LSDInputGenerator
```
No new imports needed for FIX-01A.

---

### `src/lucy_ng/lsd/runner.py` — `_invoke_outlsd` (FIX-01B: fail-loud validation)

**Analog:** `src/lucy_ng/lsd/runner.py::_invoke_outlsd` (lines 13–47) — targeted edit of the existing function.

**Current false-positive check** (line 42–43):
```python
if proc.stdout.strip():
    smiles_file.write_text(proc.stdout)
    return smiles_file
```

**Replacement pattern** — raise `RuntimeError` for known-bad output, return `None` for unknown failures. This matches the exception-to-`LSDResult(success=False)` chain that already exists in `_execute_lsd` lines 295–309:
```python
stdout = proc.stdout.strip()
# Fail-loud: detect known error patterns before writing to disk
if not stdout:
    raise RuntimeError(
        "outlsd produced no output — .sol file may be incomplete "
        "(likely cause: ring3/ring4 filter files missing from output_dir)"
    )
if "This is not a file for OUTLSD" in stdout:
    raise RuntimeError(
        f"outlsd rejected .sol file: {stdout[:200]!r}. "
        "Likely cause: ring3/ring4 filter files missing from output_dir, "
        "causing LSD to produce a partial .sol (input echo only). "
        "Fix: ensure _execute_lsd copies filter files (FIX-01A)."
    )
if stdout.startswith("outlsd:"):
    raise RuntimeError(f"outlsd error: {stdout[:200]!r}")
# Output passes string checks — write to disk
smiles_file.write_text(proc.stdout)
return smiles_file
```

**Exception re-raise pattern** — the existing `except Exception: pass; return None` must be split so `RuntimeError` propagates:
```python
except RuntimeError:
    raise  # Propagate fail-loud errors to _execute_lsd exception handler
except Exception:
    pass
return None
```

**How `RuntimeError` is converted to `LSDResult(success=False)`** — already handled by `_execute_lsd` lines 303–309:
```python
except Exception as e:
    return LSDResult(
        success=False,
        solution_count=0,
        stderr=str(e),
        return_code=-1,
    )
```
No changes needed in `_execute_lsd`'s outer exception handler; raising `RuntimeError` from `_invoke_outlsd` propagates through `_run_outlsd` (line 397) into `_execute_lsd`'s `except Exception` block.

---

### `src/lucy_ng/lsd/generator.py` — new `detect_aromatic_cosy_pairs()` (FIX-02)

**Analog:** `src/lucy_ng/detection/grouping.py::group_signals()` (lines 58–200) — same role (pure transform function) and same input type (`SignalGroup` / list of groups from grouping).

**Import pattern** to add at top of `generator.py` (extend existing imports):
```python
# Add to existing imports in src/lucy_ng/lsd/generator.py lines 1-9:
from lucy_ng.detection.models import SignalGroup
```

**`SignalGroup.atom_ids` property** (`src/lucy_ng/detection/models.py` lines 386–391) returns 1-based atom IDs — this is what `detect_aromatic_cosy_pairs()` consumes:
```python
@property
def atom_ids(self) -> list[int]:
    """Return 1-based atom IDs for LSD."""
    return [idx + 1 for idx in self.indices]
```

**Function signature and algorithm** — place as a module-level function in `generator.py`, after `LSDInputGenerator` class (analogous to how `parse_molecular_formula` sits at module level lines 12–29):
```python
def detect_aromatic_cosy_pairs(
    groups: list[SignalGroup],
    aromatic_range: tuple[float, float] = (100.0, 165.0),
) -> list[tuple[int, int]]:
    """Derive cross-ring COSY equivalence pairs for aromatic CH groups.

    For two groups of aromatic sp2 CH atoms detected by lucy analyze grouping,
    pairs them cross-ring using the reversed-sort algorithm. Verified reference:
    arm_a.lsd (.planning/phases/72-design-re-validation/experiment/arm_a.lsd)
    → COSY 4 7 + COSY 5 6 → 2/2 aromatic solutions (ibuprofen present).

    Algorithm: zip(sorted(groupA.atom_ids), reversed(sorted(groupB.atom_ids)))
    This produces cross-group pairing (NEVER within-group), preventing LSD
    error 283 when ring BONDs are also present.

    Args:
        groups: SignalGroup list from group_signals() (lucy analyze grouping output)
        aromatic_range: ppm range for aromatic sp2 CH carbon shifts

    Returns:
        List of (atom1_id, atom2_id) tuples — 1-based, for add_aromatic_equivalence_pair()
    """
    aromatic_groups = [
        g for g in groups
        if all(aromatic_range[0] <= s <= aromatic_range[1] for s in g.shifts)
    ]

    pairs: list[tuple[int, int]] = []
    used: set[int] = set()

    for i, ga in enumerate(aromatic_groups):
        if i in used:
            continue
        for j, gb in enumerate(aromatic_groups):
            if j <= i or j in used:
                continue
            if len(ga.atom_ids) == len(gb.atom_ids) and len(ga.atom_ids) >= 2:
                a_ids = sorted(ga.atom_ids)
                b_ids = list(reversed(sorted(gb.atom_ids)))
                pairs.extend(zip(a_ids, b_ids))
                used.add(i)
                used.add(j)
                break

    return pairs
```

**Integration with `LSDProblem`** — caller loops over `detect_aromatic_cosy_pairs()` output and calls `add_aromatic_equivalence_pair()` (`src/lucy_ng/lsd/models.py` lines 229–253):
```python
# Usage pattern (in LSDInputGenerator or agent code):
from lucy_ng.lsd.generator import detect_aromatic_cosy_pairs

pairs = detect_aromatic_cosy_pairs(grouping_result.groups)
for atom1, atom2 in pairs:
    problem.add_aromatic_equivalence_pair(atom1, atom2)
```

`add_aromatic_equivalence_pair` already deduplicates by sorted key — no extra dedup needed in `detect_aromatic_cosy_pairs`.

---

### `src/lucy_ng/cli/detect.py` — new `aromatic-cosy` subcommand (FIX-02 CLI)

**Analog:** `src/lucy_ng/cli/detect.py::hybridisation_command` (lines 16–94) — exact same file, same `@detect.command` / `@click.argument` / `@click.option` pattern.

**Imports pattern** (lines 1–8 of detect.py — no new imports needed; `click` already imported):
```python
import click
from pathlib import Path
from lucy_ng.database import DatabaseFinder
```

**Subcommand registration pattern** (lines 16–17):
```python
@detect.command("aromatic-cosy")
@click.argument("shifts", type=str)
@click.option(
    "--multiplicities", "-m", type=str, default=None,
    help="Comma-separated multiplicities (e.g. 'CH,CH,CH,CH'). Optional.",
)
@click.option(
    "--tolerance", "-t", type=float, default=0.25,
    help="Grouping tolerance in ppm (default: 0.25).",
)
@click.option(
    "--format", "output_format",
    type=click.Choice(["text", "json"]), default="text",
    help="Output format.",
)
def aromatic_cosy_command(
    shifts: str,
    multiplicities: str | None,
    tolerance: float,
    output_format: str,
) -> None:
    """Derive cross-ring COSY pairs for aromatic CH equivalence groups.

    Given comma-separated 13C shifts (aromatic region), detects groups
    of equivalent aromatic CH carbons and emits cross-ring COSY pairs
    for use in LSD problem construction.

    Algorithm verified by arm_a.lsd reference: produces COSY 4 7 + COSY 5 6
    for ibuprofen para-disubstituted benzene (2/2 aromatic solutions).

    Examples:

        lucy detect aromatic-cosy "129.38,129.38,127.26,127.26"

        lucy detect aromatic-cosy "129.38,127.26" --format json
    """
```

**Error-output pattern** (verbatim from `hybridisation_command` lines 71–73):
```python
    # No database needed for this command (pure grouping algorithm)
    # Run detection
    try:
        from lucy_ng.detection.grouping import group_signals
        from lucy_ng.lsd.generator import detect_aromatic_cosy_pairs

        shift_list = [float(s.strip()) for s in shifts.split(",")]
        mult_list = [m.strip() for m in multiplicities.split(",")] if multiplicities else None
        grouping = group_signals(shift_list, multiplicities=mult_list, tolerance=tolerance)
        pairs = detect_aromatic_cosy_pairs(grouping.groups)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1) from e

    # Output
    if output_format == "json":
        import json
        click.echo(json.dumps({"cosy_pairs": [list(p) for p in pairs]}))
    else:
        if pairs:
            for a, b in pairs:
                click.echo(f"COSY {a} {b}")
        else:
            click.echo("No aromatic equivalence pairs detected.")
```

**The `detect` group is already registered** in `src/lucy_ng/cli/main.py` line 52 — no changes to `main.py` needed.

---

### `tests/test_lsd_runner.py` — new `TestInvokeOutlsd` + `test_ring_exclusion_lsd_produces_smiles`

**Analog:** `tests/test_lsd_runner.py::TestLSDRunnerFixed` (lines 257–492) — exact same file, same class structure, same `@pytest.mark.skipif` / `tmp_path` / `monkeypatch` patterns.

**File-level imports** (lines 1–12 — already present, no new imports needed):
```python
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
from rdkit import Chem

from lucy_ng.lsd.models import Hybridization, LSDAtom, LSDCorrelation, LSDProblem
from lucy_ng.lsd.runner import LSDRunner, LSDResult
```

**Fixture constant** (line 254 — existing pattern):
```python
FIXTURE_DIR = Path(__file__).parent / "fixtures" / "regression"
```

**`@pytest.mark.skipif` pattern** for integration tests (lines 265–268 — copy verbatim):
```python
@pytest.mark.skipif(
    shutil.which("LSD") is None,
    reason="LSD binary not installed",
)
```

**New `TestInvokeOutlsd` class — unit tests, no LSD needed** (modeled on `test_invoke_outlsd_unit` at line 424):
```python
class TestInvokeOutlsd:
    """Unit tests for _invoke_outlsd fail-loud behavior (FIX-01B).

    These tests use monkeypatch and do NOT require LSD/outlsd to be installed.
    """

    def test_fail_loud_on_error_string(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """_invoke_outlsd raises RuntimeError when outlsd outputs the known error string."""
        from lucy_ng.lsd.runner import _invoke_outlsd

        sol_file = tmp_path / "compound.sol"
        sol_file.write_text("# header\n")

        def mock_run(*args, **kwargs):
            class MockResult:
                stdout = "outlsd: This is not a file for OUTLSD.\n"
                returncode = 0
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        with pytest.raises(RuntimeError, match="This is not a file for OUTLSD"):
            _invoke_outlsd(Path("/fake/outlsd"), sol_file, tmp_path)

    def test_fail_loud_on_empty_output(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """_invoke_outlsd raises RuntimeError when outlsd produces no output."""
        from lucy_ng.lsd.runner import _invoke_outlsd

        sol_file = tmp_path / "compound.sol"
        sol_file.write_text("# header\n")

        def mock_run(*args, **kwargs):
            class MockResult:
                stdout = ""
                returncode = 0
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        with pytest.raises(RuntimeError, match="no output"):
            _invoke_outlsd(Path("/fake/outlsd"), sol_file, tmp_path)
```

**New integration test `test_ring_exclusion_lsd_produces_smiles`** (modeled on `test_runner_produces_smiles` at lines 287–315):
```python
@pytest.mark.skipif(
    shutil.which("LSD") is None,
    reason="LSD binary not installed",
)
def test_ring_exclusion_lsd_produces_smiles(self, tmp_path: Path) -> None:
    """run_file() with a ring-exclusion LSD file (DEFF F1/F2) produces valid SMILES.

    Regression for FIX-01A: _execute_lsd must copy ring3/ring4 filter files.
    Fixture: arm_a_ring_excl.lsd (has DEFF F1 "ring3" + DEFF F2 "ring4").
    Expected: 2 solutions, both aromatic (ibuprofen present).
    """
    outlsd_bin = shutil.which("outlsd")
    assert outlsd_bin is not None, "outlsd binary not found on PATH"

    lsd_fixture = FIXTURE_DIR / "arm_a_ring_excl.lsd"
    runner = LSDRunner()
    runner.run_file(lsd_fixture, output_dir=tmp_path, timeout=120)

    smiles_file = tmp_path / "solutions.smi"
    assert smiles_file.exists(), (
        "solutions.smi not written — ring3/ring4 filter files likely not copied"
    )
    lines = [ln for ln in smiles_file.read_text().splitlines() if ln.strip()]
    assert len(lines) == 2, (
        f"arm_a_ring_excl.lsd should produce exactly 2 solutions, got {len(lines)}. "
        "If 0: LSD failed (filter files missing). If 392: wrong fixture used."
    )
    # Both solutions must be valid SMILES with aromatic atoms
    for line in lines:
        smiles = line.split()[0]
        mol = Chem.MolFromSmiles(smiles)
        assert mol is not None, f"Not valid SMILES: {smiles!r}"
        aromatic_atoms = sum(1 for a in mol.GetAtoms() if a.GetIsAromatic())
        assert aromatic_atoms >= 6, (
            f"Expected aromatic ring in solution, got {aromatic_atoms} aromatic atoms: {smiles!r}"
        )
```

---

### `tests/test_lsd_generator.py` — new `TestDetectAromaticCosyPairs` class

**Analog:** `tests/test_signal_grouping.py::TestGroupSignals` (lines 39–200) — same pattern: parametrized unit tests for a pure transform function, using literal input lists, asserting on output structure.

**Existing file imports** (lines 1–9 — add `SignalGroup`):
```python
# Existing imports in test_lsd_generator.py:
from lucy_ng.lsd.generator import LSDInputGenerator
# Add:
from lucy_ng.detection.models import SignalGroup
from lucy_ng.detection.grouping import group_signals
from lucy_ng.lsd.generator import detect_aromatic_cosy_pairs
```

**Test class pattern** (modeled on `TestGroupSignals` structure):
```python
class TestDetectAromaticCosyPairs:
    """Unit tests for detect_aromatic_cosy_pairs() — FIX-02."""

    def test_ibuprofen_aromatic_groups_produces_cross_ring_pairs(self) -> None:
        """Two groups at 129.38 and 127.26 ppm → [(4,7),(5,6)] (Arm A reference)."""
        # Ibuprofen aromatic CH: group A at 129.38 (indices 3,4 → atom_ids 4,5)
        #                        group B at 127.26 (indices 5,6 → atom_ids 6,7)
        grouping = group_signals(
            [129.38, 129.38, 127.26, 127.26],
            multiplicities=["CH", "CH", "CH", "CH"],
            tolerance=0.25,
        )
        pairs = detect_aromatic_cosy_pairs(grouping.groups)

        assert len(pairs) == 2
        # Cross-ring: atoms from group A paired with atoms from group B
        pair_set = {tuple(sorted(p)) for p in pairs}
        # In Arm A: (4,7) and (5,6)
        # With 0-based input indices [0,1,2,3], atom_ids are [1,2,3,4]
        # sorted groupA = [1,2], reversed(sorted(groupB)) = [4,3]
        # → pairs = [(1,4),(2,3)]
        assert all(a != b for a, b in pairs), "No self-COSY pairs"
        # Cross-group: no pair should have both atoms from same shift
        group_a_ids = set(grouping.groups[0].atom_ids)
        group_b_ids = set(grouping.groups[1].atom_ids)
        for a, b in pairs:
            assert not (a in group_a_ids and b in group_a_ids), "Within-group pair detected"
            assert not (a in group_b_ids and b in group_b_ids), "Within-group pair detected"

    def test_single_group_no_pairs(self) -> None:
        """Single aromatic group → no pairs (no partner to cross-pair with)."""
        grouping = group_signals(
            [129.38, 129.40],
            multiplicities=["CH", "CH"],
            tolerance=0.25,
        )
        pairs = detect_aromatic_cosy_pairs(grouping.groups)
        assert pairs == []

    def test_non_aromatic_shifts_excluded(self) -> None:
        """Aliphatic shifts outside aromatic_range are ignored."""
        grouping = group_signals(
            [44.90, 45.03, 129.38, 129.38],
            multiplicities=["CH2", "CH2", "CH", "CH"],
            tolerance=0.25,
        )
        # groups: [44.90,45.03] (aliphatic) and [129.38,129.38] (aromatic)
        pairs = detect_aromatic_cosy_pairs(grouping.groups)
        # Only 1 aromatic group → no pairs
        assert pairs == []
```

---

### `tests/fixtures/regression/arm_a_ring_excl.lsd`

**Source:** `.planning/phases/72-design-re-validation/experiment/arm_a.lsd`

**Required edit:** The original `arm_a.lsd` uses absolute paths for DEFF (lines 54–55):
```
DEFF F1 "/Users/steinbeck/Dropbox/develop/LSD/Filters/ring3"
DEFF F2 "/Users/steinbeck/Dropbox/develop/LSD/Filters/ring4"
```

The test fixture must use **relative paths** (bundled filter files copied by `_write_filter_files`):
```
DEFF F1 "ring3"
DEFF F2 "ring4"
```

All other content is identical. The executor creates the fixture by copying `arm_a.lsd` and replacing the two `DEFF` lines with the relative-path versions.

---

### `~/.claude/agents/lucy-lsd-engineer.md` — targeted edit (FIX-03)

**Analog:** No code analog — skill text file. Pattern: targeted line-range edits only, no full rewrite.

**Lines 124–130 (false Phase-73 claim):** Replace the claim that `lucy lsd run` works with:
- "Phase 73 fix was incomplete — `_invoke_outlsd` unified, but `_execute_lsd` did not copy ring3/ring4 filter files when invoked via `run_file()`. FIX-01 (Phase 77) corrects this."

**COSY helper reference:** Add `lucy detect aromatic-cosy` CLI command reference near the existing COSY/D-04 aromatic equivalence section. Command syntax: `lucy detect aromatic-cosy "<shifts>" [--multiplicities "<mults>"] [--format json]`.

**D-04 escalation wording:** Update the existing escalation section (near line 583) to match D-77-01/D-77-06:
- Threshold N for ring-BOND escalation: after **3** non-aromatic iterations, ring-BOND escalation is the documented-legitimate path.
- Requirement: log escalation decision in CASE-PROGRESS.md with iteration number.
- SKEL benzene (`SKEL "c1ccccc1"`) remains forbidden in all cases.

---

### `~/.claude/agents/lucy-case-agent.md` — retirement (FIX-03)

**No code analog.** Single change: neutralize frontmatter to prevent accidental spawning.

**Current frontmatter:**
```yaml
name: lucy-case-agent
```

**Replacement:**
```yaml
name: DEPRECATED-lucy-case-agent
```

This name change prevents Claude Code from matching it as a spawnable agent while preserving the historical record and the `> DEPRECATED -- DO NOT USE` blockquote already present in the body.

---

### `~/.claude/commands/lucy-ng/case.md` and `lucy-devils-advocate.md` — targeted audit (FIX-03)

**Analog:** No code analog — documentation verification only, not code changes.

**`case.md`:** Verify emergent-ring guidance (COSY 4 7 + COSY 5 6, cross-ring) is not buried. Add D-77-06 UAT criterion note for Phase 78 handoff: "emergent ring = clean pass; ring-BONDs as CASE-PROGRESS-documented escalation after 3 non-aromatic iterations = conditional pass; silent ring-BONDs or SKEL = fail."

**`lucy-devils-advocate.md`:** Verify G5-G8 gates cover the FIX-01/02 failure modes. Update the COSY equivalence-pair check (G-gate that detects `COSY 4 5` within-group pairs) to reference `lucy detect aromatic-cosy` output as the authoritative source.

---

## Shared Patterns

### Subprocess invocation with stdin (outlsd pattern)
**Source:** `src/lucy_ng/lsd/runner.py::_invoke_outlsd` lines 33–41
**Apply to:** FIX-01B edit of `_invoke_outlsd`
```python
with sol_file.open("r") as fh:
    proc = subprocess.run(
        [str(outlsd_path), "5"],
        stdin=fh,               # file handle, NOT input= kwarg
        capture_output=True,
        text=True,
        timeout=30,
        cwd=output_dir,
    )
```
Key: always `stdin=fh` (file handle), never `input=...`. This is enforced by the existing `test_invoke_outlsd_unit` test (line 474–479).

### importlib.resources bundled file access
**Source:** `src/lucy_ng/lsd/generator.py::_write_filter_files` lines 239–242
**Apply to:** FIX-01A (called from `_execute_lsd`)
```python
package = importlib.resources.files("lucy_ng.lsd.filters")
for name in ("ring3", "ring4"):
    content = (package / name).read_text()
    (output_dir / name).write_text(content)
```
Import: `import importlib.resources` — already present in `generator.py` line 3, not in `runner.py`. Since `_write_filter_files` is a static method called as `LSDInputGenerator._write_filter_files(output_dir)`, no new import is needed in `runner.py`.

### LSD integration test skipif gate
**Source:** `tests/test_lsd_runner.py::TestLSDRunnerFixed` lines 265–268
**Apply to:** All new integration tests in `TestLSDRunnerFixed` and `TestInvokeOutlsd`
```python
@pytest.mark.skipif(
    shutil.which("LSD") is None,
    reason="LSD binary not installed",
)
```

### Click `@detect.command` subcommand structure
**Source:** `src/lucy_ng/cli/detect.py::hybridisation_command` lines 16–94
**Apply to:** New `aromatic-cosy` subcommand
Pattern: `@detect.command("name")` → `@click.argument` → `@click.option(--format)` → function body with `try/except` → `if output_format == "json": click.echo(...)`.

### `pytest.raises` error-path testing
**Source:** `tests/test_lsd_runner.py::TestLSDRunnerExecution::test_run_without_lsd_raises` lines 107–113
**Apply to:** `TestInvokeOutlsd` fail-loud tests
```python
with pytest.raises(RuntimeError, match="<substring>"):
    _invoke_outlsd(...)
```

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `~/.claude/agents/lucy-case-agent.md` frontmatter neutralization | skill retirement | — | No code analog; pattern is YAML frontmatter key rename (`name:` field); executor follows FIX-03 prose instructions directly |

---

## Metadata

**Analog search scope:** `src/lucy_ng/lsd/`, `src/lucy_ng/cli/`, `src/lucy_ng/detection/`, `tests/`
**Files scanned:** 12 source files + 6 test files
**Pattern extraction date:** 2026-06-01
