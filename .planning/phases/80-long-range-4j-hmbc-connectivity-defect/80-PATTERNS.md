# Phase 80: Long-Range (4J) HMBC Connectivity Defect - Pattern Map

**Mapped:** 2026-06-09
**Files analyzed:** 10 (6 source files modified, 3 test classes added, 1 skill-layer change)
**Analogs found:** 10 / 10

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/lucy_ng/lsd/models.py` | model | CRUD | `src/lucy_ng/lsd/models.py` (existing `LSDProblem`) | exact (field addition) |
| `src/lucy_ng/lsd/generator.py` | utility | transform | `src/lucy_ng/lsd/generator.py` (existing `pylsd_mode` gate) | exact (gate relocation) |
| `src/lucy_ng/ranking/ranker.py` | service | transform | `src/lucy_ng/ranking/ranker.py` (existing aromatic sanity check) | exact (promote warning → filter) |
| `src/lucy_ng/ranking/models.py` | model | CRUD | `src/lucy_ng/ranking/models.py` (existing `RankedSolution`) | exact (field addition) |
| `src/lucy_ng/data/schemas/constraint_inventory_v2.json` | config | CRUD | `src/lucy_ng/data/schemas/constraint_inventory_v2.json` | exact (schema surgery) |
| `src/lucy_ng/cli/pylsd.py` | middleware | request-response | `src/lucy_ng/cli/pylsd.py` (existing `pylsd_run`) | exact (deprecation wrapper) |
| `tests/test_lsd_generator.py::TestElimBudget` (new class) | test | CRUD | `tests/test_lsd_generator.py::TestLSDInputGeneratorEmit` | role-match |
| `tests/test_ranking.py::TestPlausibilityFilter` (new class) | test | transform | `tests/test_ranking.py::TestSolutionRankerRank` | role-match |
| `tests/test_ranking.py::TestPlausibilityFilterOrdering` (new class) | test | transform | `tests/test_ranking.py::TestTwoTierRanking` | role-match |
| `tests/test_lsd_schema.py::TestSchemaV2Phase80` (new class in `test_inventory_schema.py`) | test | CRUD | `tests/test_inventory_schema.py::TestSchemaValidation` | exact |

---

## Pattern Assignments

### `src/lucy_ng/lsd/models.py` — add `elim_budget: int = 0`

**Analog:** `src/lucy_ng/lsd/models.py` — existing `LSDProblem` dataclass

**Existing field pattern** (lines 178–185):
```python
@dataclass
class LSDProblem:
    atoms: list[LSDAtom] = field(default_factory=list)
    correlations: list[LSDCorrelation] = field(default_factory=list)
    constraints: list[LSDConstraint] = field(default_factory=list)
    molecular_formula: str | None = None
    name: str = "problem"
    comments: list[str] = field(default_factory=list)
    pylsd_mode: bool = False
    elim_commands: list[tuple[int, int]] = field(default_factory=list)
    ring_exclusion_enabled: bool = False
```

**What to add:** Insert `elim_budget: int = 0` after `elim_commands` (or after `pylsd_mode`). Simple scalar field with default 0 — same pattern as `ring_exclusion_enabled: bool = False`. No `field()` wrapper needed; primitive with default.

**Where to insert** — after line 185 (`elim_commands`):
```python
    elim_budget: int = 0  # Global ELIM N: solver may drop up to N HMBC/COSY (D-01/D-02)
```

No `__post_init__` validation is needed (0 is the safe default; the skill enforces the ceiling at N=3).

---

### `src/lucy_ng/lsd/generator.py` — decouple ELIM emission from `pylsd_mode`

**Analog:** `src/lucy_ng/lsd/generator.py` lines 111–118 (the existing `pylsd_mode` gate)

**Current gated ELIM pattern** (lines 111–118):
```python
# pyLSD header commands (FORM, ELIM) — only when pylsd_mode enabled
if problem.pylsd_mode:
    if problem.molecular_formula:
        lines.append(LSDInputGenerator.emit_form(problem.molecular_formula))
    for n, m in problem.elim_commands:
        lines.append(LSDInputGenerator.emit_elim(n, m))
    if problem.molecular_formula or problem.elim_commands:
        lines.append("")
```

**Existing `emit_elim` static method** (lines 61–75):
```python
@staticmethod
def emit_elim(n: int, m: int) -> str:
    """Emit a pyLSD ELIM command line."""
    return f"ELIM {n} {m}"
```

**What to change:** After the existing `pylsd_mode` block (line 118), add a second, independent block that emits `ELIM {elim_budget} 0` when `elim_budget > 0`. This does NOT touch or remove the existing `pylsd_mode` block (backward compatible). The new emission pattern mirrors the same "if condition, append line, append blank separator" shape:

```python
# Global ELIM budget (Phase 80: primary 4J mechanism, independent of pylsd_mode)
if problem.elim_budget > 0:
    lines.append(LSDInputGenerator.emit_elim(problem.elim_budget, 0))
    lines.append("")
```

The separator blank line follows the same pattern used throughout `generate()` (lines 119, 126, etc.).

---

### `src/lucy_ng/ranking/ranker.py` — add `_is_chemically_plausible()` + pre-filter

**Analog:** `src/lucy_ng/ranking/ranker.py` lines 85–126 (aromatic ring detection block + sanity check)

**Existing aromatic ring detection** (lines 85–100):
```python
# Check for aromatic ring
has_aromatic = False
mol = Chem.MolFromSmiles(solution.smiles)
if mol is not None:
    has_aromatic = any(atom.GetIsAromatic() for atom in mol.GetAtoms())

ranked_solution = RankedSolution(
    solution_index=solution.index,
    smiles=solution.smiles,
    mae=mae,
    matched_count=matched_count,
    total_carbons=prediction.carbon_count,
    prediction_rate=prediction.success_rate,
    assignments=assignments,
    has_aromatic_ring=has_aromatic,
)
ranked.append(ranked_solution)
```

**Existing aromatic warning block** (lines 110–126) — this becomes the template for the pre-filter:
```python
# Aromatic ring sanity check
aromatic_shift_count = sum(
    1 for s in experimental_shifts if 110.0 <= s <= 160.0
)
any_aromatic = any(r.has_aromatic_ring for r in ranked)
if aromatic_shift_count >= 4 and ranked and not any_aromatic:
    warnings.append(
        f"Aromatic ring expected ({aromatic_shift_count} shifts in "
        f"110-160 ppm) but no solutions contain aromatic rings. "
        f"Possible 4J HMBC artifact — consider removing HMBC "
        f"correlations between aromatic ring positions and "
        f"benzylic/alpha substituents."
    )
```

**Existing sort** (line 104):
```python
ranked.sort(key=lambda r: (-r.matched_count, r.mae))
```

**New helper function** — module-level private function, placed just before `class SolutionRanker`:
```python
def _is_chemically_plausible(
    solution: "RankedSolution",
    experimental_shifts: list[float],
    formula: str | None = None,
) -> bool:
    """Return False if the solution is chemically implausible.

    Check 1: Aromatic ring required when >= 4 shifts in 110-160 ppm.
    Check 2: DBE consistency when formula is provided (tolerance ±1).
    """
    # Check 1: aromatic ring when shifts suggest aromaticity
    aromatic_shift_count = sum(1 for s in experimental_shifts if 110.0 <= s <= 160.0)
    if aromatic_shift_count >= 4 and not solution.has_aromatic_ring:
        return False
    # Check 2: DBE consistency (optional — requires formula)
    if formula:
        expected_dbe = _calc_dbe_from_formula(formula)
        mol = Chem.MolFromSmiles(solution.smiles)
        if mol is not None:
            actual_dbe = _calc_dbe_from_mol(mol)
            if abs(actual_dbe - expected_dbe) > 1:
                return False
    return True
```

**Pre-filter insertion in `rank()`** — replace line 104 sort with:
```python
# Chemical plausibility pre-filter (D-09): partition before MAE sort
plausible = [r for r in ranked if _is_chemically_plausible(r, experimental_shifts, formula)]
implausible = [r for r in ranked if not _is_chemically_plausible(r, experimental_shifts, formula)]
plausible.sort(key=lambda r: (-r.matched_count, r.mae))
ranked = plausible + implausible  # implausible appended after, preserves full set for audit
```

**`rank()` signature change** — add optional `formula` parameter:
```python
def rank(
    self,
    solutions: list[LSDSolution],
    experimental_shifts: list[float],
    top_n: int | None = None,
    formula: str | None = None,   # NEW — for DBE consistency check (D-09)
) -> RankingResult:
```

This mirrors the existing `top_n: int | None = None` optional parameter pattern — backward compatible, keyword-only by convention.

**DBE helper functions** (module-level, near `_is_chemically_plausible`):
```python
def _calc_dbe_from_formula(formula: str) -> float:
    """Compute Degree of Unsaturation from a molecular formula string.

    DBE = (2C + 2 + N - H - X) / 2  where X = halogens.
    Uses parse_molecular_formula() from generator.py.
    """
    from lucy_ng.lsd.generator import parse_molecular_formula
    counts = parse_molecular_formula(formula)
    c = counts.get("C", 0)
    h = counts.get("H", 0)
    n = counts.get("N", 0)
    x = counts.get("F", 0) + counts.get("Cl", 0) + counts.get("Br", 0) + counts.get("I", 0)
    return (2 * c + 2 + n - h - x) / 2


def _calc_dbe_from_mol(mol: "Chem.Mol") -> float:
    """Compute DBE from an RDKit mol object via CalcMolFormula."""
    from rdkit.Chem import rdMolDescriptors
    formula = rdMolDescriptors.CalcMolFormula(mol)
    return _calc_dbe_from_formula(formula)
```

**Update `RankingResult` warnings block** — replace the old advisory text with a neutral observation (the pre-filter now acts; the warning is informational):
```python
# Update warning text to reflect that pre-filter acted, not just warned
if aromatic_shift_count >= 4 and ranked and not any_aromatic:
    warnings.append(
        f"Aromatic ring expected ({aromatic_shift_count} shifts in 110-160 ppm) "
        f"but no plausible solutions contain aromatic rings. "
        f"Implausible solutions (no aromatic ring) are appended after plausible ones."
    )
```

---

### `src/lucy_ng/ranking/models.py` — add `is_plausible: bool = True` to `RankedSolution`

**Analog:** `src/lucy_ng/ranking/models.py` lines 59–61 (`has_aromatic_ring` field)

**Existing optional bool field pattern** (lines 59–61):
```python
has_aromatic_ring: bool = Field(
    default=False, description="Whether the structure contains an aromatic ring"
)
```

**What to add** — immediately after `has_aromatic_ring`:
```python
is_plausible: bool = Field(
    default=True,
    description="False when chemical plausibility pre-filter (D-09) rejected this solution. "
                "Implausible solutions are appended after plausible ones in the ranked list.",
)
```

**Usage in ranker.py** — set `is_plausible=False` on implausible solutions before appending them to the ranked list:
```python
for r in implausible:
    r = r.model_copy(update={"is_plausible": False})
```
(Pydantic v2 `model_copy(update={...})` is the canonical immutable-update pattern; `RankedSolution` inherits from `BaseModel`.)

---

### `src/lucy_ng/data/schemas/constraint_inventory_v2.json` — retire pyLSD required fields

**Analog:** `src/lucy_ng/data/schemas/constraint_inventory_v2.json` lines 7–19 (`"required"` array)

**Current `"required"` array** (lines 7–19):
```json
"required": [
  "version", "iteration", "formula", "timestamp",
  "mult_count", "hsqc_count", "hmbc_batches", "hmbc_total",
  "pylsd_mode", "elim_annotated", "deferred_4j"
]
```

**Phase 80 change:** Remove `"pylsd_mode"`, `"elim_annotated"`, `"deferred_4j"` from `"required"`. The three fields remain as optional properties in the `"properties"` block for backward compatibility (existing CASE1/CASE9 LSD files with `deferred_4j: []` stay valid).

Add `"elim_budget"` as a new optional property after `"elim_value"`:
```json
"elim_budget": {
  "type": "integer",
  "minimum": 0,
  "default": 0,
  "description": "Global ELIM N value (Phase 80 D-02). 0 = no ELIM. Replaces deferred_4j as the 4J mechanism tracker. Ceiling: 3."
}
```

**`allOf` blocks** — the G2 and G3 invariants (`pylsd_mode=true` forbids non-null `elim_value`; `elim_annotated=true` requires `pylsd_mode=true`) become vacuously true since `pylsd_mode` is never `true` in new files. They are harmless to keep; remove only if they cause test failures in `TestSchemaV2Phase80`.

---

### `src/lucy_ng/cli/pylsd.py` — deprecation warning

**Analog:** `src/lucy_ng/cli/pylsd.py` line 144+ (`pylsd_run` command entry point)

**Existing Click command pattern** — the `pylsd_run` function is decorated with `@pylsd.command("run")`. The deprecation warning should be the first statement of that function body, before any other logic, using `click.echo(..., err=True)`:

```python
@pylsd.command("run")
# ... existing decorators ...
def pylsd_run(...):
    """Run PyLSD orchestration (DEPRECATED — use lucy lsd run with ELIM escalation)."""
    click.echo(
        "Warning: lucy pylsd run is deprecated (Phase 80 D-05). "
        "Use lucy lsd run with ELIM escalation instead. "
        "See .planning/phases/80-long-range-4j-hmbc-connectivity-defect/80-CONTEXT.md",
        err=True,
    )
    # ... existing function body continues unchanged ...
```

The `err=True` pattern is already used at line 71 (`click.echo(..., err=True)`). The docstring is updated to mark the command deprecated — this appears in `lucy pylsd run --help`.

---

## New Test Classes

### `tests/test_lsd_generator.py::TestElimBudget` (new class)

**Analog:** `tests/test_lsd_generator.py` lines 415–477 (`TestLSDInputGeneratorEmit` static method tests + `test_generate_pylsd_elim_commands`)

**Import block** (copy from file top, lines 1–13):
```python
"""Tests for LSD input file generator."""

import pytest
from pathlib import Path
import tempfile

from lucy_ng import BrukerReader, DEPTGuidedPicker, Peak1D, Peak2D, PeakList1D, PeakList2D
from lucy_ng.lsd.models import Hybridization, LSDAtom, LSDConstraint, LSDCorrelation, LSDProblem
from lucy_ng.lsd.generator import LSDInputGenerator
from lucy_ng.detection.models import SignalGroup
from lucy_ng.detection.grouping import group_signals
from lucy_ng.lsd.generator import detect_aromatic_cosy_pairs
```

**Class structure to mirror** (from `test_generate_pylsd_elim_commands`, lines 463–477):
```python
class TestElimBudget:
    """Tests for elim_budget field and ELIM emission (Phase 80 D-01/D-02)."""

    def test_elim_budget_zero_emits_no_elim(self):
        """LSDProblem(elim_budget=0) must produce NO ELIM line in generated file."""
        problem = LSDProblem(name="test", elim_budget=0)
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0))
        content = LSDInputGenerator.generate(problem)
        # No ELIM line — exact match to ensure no spurious emission
        assert "ELIM" not in content

    def test_elim_budget_one_emits_elim_1_0(self):
        """LSDProblem(elim_budget=1) must emit 'ELIM 1 0' in generated file."""
        problem = LSDProblem(name="test", elim_budget=1)
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0))
        content = LSDInputGenerator.generate(problem)
        assert "ELIM 1 0" in content

    def test_elim_budget_three_emits_elim_3_0(self):
        """LSDProblem(elim_budget=3) must emit 'ELIM 3 0'."""
        problem = LSDProblem(name="test", elim_budget=3)
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0))
        content = LSDInputGenerator.generate(problem)
        assert "ELIM 3 0" in content

    def test_elim_budget_appears_before_mult(self):
        """ELIM line must appear before first MULT line in the file."""
        problem = LSDProblem(name="test", elim_budget=1)
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0))
        content = LSDInputGenerator.generate(problem)
        elim_pos = content.index("ELIM 1 0")
        mult_pos = content.index("MULT")
        assert elim_pos < mult_pos

    def test_elim_budget_independent_of_pylsd_mode(self):
        """ELIM budget emission must NOT require pylsd_mode=True."""
        problem = LSDProblem(name="test", elim_budget=2, pylsd_mode=False)
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0))
        content = LSDInputGenerator.generate(problem)
        assert "ELIM 2 0" in content

    def test_elim_budget_default_is_zero(self):
        """LSDProblem default elim_budget must be 0 (no ELIM by default)."""
        problem = LSDProblem()
        assert problem.elim_budget == 0
```

Key patterns used: `LSDProblem(name=..., elim_budget=N)`, `LSDInputGenerator.generate(problem)`, string `in content` / `not in content`, `content.index()` for position checks. All from the existing `test_generate_pylsd_elim_commands` shape.

---

### `tests/test_ranking.py::TestPlausibilityFilter` (new class)

**Analog:** `tests/test_ranking.py` lines 346–430 (`TestSolutionRankerRank`) for mock-predictor fixture and `rank()` call structure; lines 475–509 (`TestTwoTierRanking`) for the multi-solution ordering assertions.

**Import block** (copy from file top, lines 1–13 — unchanged):
```python
"""Tests for LSD solution ranking."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile

from lucy_ng.ranking.models import ShiftAssignment, RankedSolution, RankingResult
from lucy_ng.ranking.ranker import SolutionRanker
from lucy_ng.lsd.parser import LSDSolution
from lucy_ng.prediction import C13Predictor
from lucy_ng.prediction.models import PredictionResult, PredictedShift
```

**Helper functions already in the file** (lines 14–38, `make_predicted_shift` and `make_prediction_result`) — reuse directly, do not redefine.

**Class structure to add** (append after last existing class):
```python
class TestPlausibilityFilter:
    """Tests for _is_chemically_plausible() pre-filter (Phase 80 D-09)."""

    @pytest.fixture
    def mock_predictor(self):
        """Create a mock predictor."""
        predictor = MagicMock(spec=C13Predictor)
        return predictor

    def test_non_aromatic_rejected_when_aromatic_expected(self, mock_predictor):
        """Non-aromatic solution is IMPLAUSIBLE when >= 4 shifts are in 110-160 ppm."""
        # Ibuprofen-like aromatic shifts (5 shifts in 110-160 ppm)
        experimental = [180.0, 141.0, 137.0, 129.4, 127.1, 45.0, 30.0]

        def predict(smiles: str):
            return make_prediction_result(smiles, [180.0, 141.0, 137.0, 129.4, 127.1, 45.0, 30.0])

        mock_predictor.predict_from_smiles.side_effect = predict
        ranker = SolutionRanker(mock_predictor, tolerance=3.0)

        solutions = [
            LSDSolution(index=1, smiles="C1CCCCC1C(=O)O"),  # cyclohexane acid, no aromatic ring
        ]
        result = ranker.rank(solutions, experimental)

        # The non-aromatic solution should appear but be marked implausible
        assert len(result.solutions) == 1
        assert result.solutions[0].is_plausible is False

    def test_aromatic_retained_when_aromatic_expected(self, mock_predictor):
        """Aromatic solution is PLAUSIBLE when shifts suggest aromaticity."""
        experimental = [180.0, 141.0, 137.0, 129.4, 127.1, 45.0, 30.0]

        def predict(smiles: str):
            return make_prediction_result(smiles, [180.0, 141.0, 137.0, 129.4, 127.1, 45.0, 30.0])

        mock_predictor.predict_from_smiles.side_effect = predict
        ranker = SolutionRanker(mock_predictor, tolerance=3.0)

        solutions = [
            LSDSolution(index=1, smiles="CC(C)Cc1ccc(cc1)C(C)C(=O)O"),  # ibuprofen, has aromatic ring
        ]
        result = ranker.rank(solutions, experimental)

        assert result.solutions[0].is_plausible is True

    def test_non_aromatic_ok_when_no_aromatic_shifts(self, mock_predictor):
        """Non-aromatic solution is PLAUSIBLE when < 4 shifts in 110-160 ppm."""
        experimental = [45.0, 30.0, 22.0]  # Only aliphatic shifts

        def predict(smiles: str):
            return make_prediction_result(smiles, [45.0, 30.0, 22.0])

        mock_predictor.predict_from_smiles.side_effect = predict
        ranker = SolutionRanker(mock_predictor, tolerance=3.0)

        solutions = [
            LSDSolution(index=1, smiles="CCC"),  # no aromatic ring
        ]
        result = ranker.rank(solutions, experimental)

        assert result.solutions[0].is_plausible is True
```

Pattern notes: `LSDSolution(index=N, smiles="...")` (from lines 371–374), `ranker.rank(solutions, experimental)`, assertion on `result.solutions[0].is_plausible`.

---

### `tests/test_ranking.py::TestPlausibilityFilterOrdering` (new class)

**Analog:** `tests/test_ranking.py::TestTwoTierRanking` lines 475–509 — multi-solution ordering via `predict_side_effect`.

```python
class TestPlausibilityFilterOrdering:
    """Tests that plausible solutions rank ABOVE implausible ones (Phase 80 D-09)."""

    @pytest.fixture
    def mock_predictor(self):
        predictor = MagicMock(spec=C13Predictor)
        return predictor

    def test_plausible_ranks_above_implausible(self, mock_predictor):
        """Plausible solution (aromatic) must appear before implausible (non-aromatic)
        even when the implausible solution has a lower MAE."""

        def predict(smiles: str):
            if smiles == "AROMATIC":
                # Slightly higher MAE than the non-aromatic
                return make_prediction_result(smiles, [180.0, 141.0, 137.0, 129.4, 127.1, 48.0, 30.0])
            else:  # NON_AROMATIC
                # Perfect MAE but no aromatic ring
                return make_prediction_result(smiles, [180.0, 141.0, 137.0, 129.4, 127.1, 45.0, 30.0])

        mock_predictor.predict_from_smiles.side_effect = predict
        ranker = SolutionRanker(mock_predictor, tolerance=3.0)

        # Experimental shifts: 5 in 110-160 ppm range → aromatic required
        experimental = [180.0, 141.0, 137.0, 129.4, 127.1, 45.0, 30.0]
        solutions = [
            LSDSolution(index=1, smiles="NON_AROMATIC"),   # non-aromatic, low MAE
            LSDSolution(index=2, smiles="AROMATIC"),        # aromatic, higher MAE
        ]

        result = ranker.rank(solutions, experimental)

        assert len(result.solutions) == 2
        # Aromatic solution must be first (plausible before implausible)
        assert result.solutions[0].smiles == "AROMATIC"
        assert result.solutions[0].is_plausible is True
        assert result.solutions[1].smiles == "NON_AROMATIC"
        assert result.solutions[1].is_plausible is False

    def test_survivor_ordering_preserved(self, mock_predictor):
        """Among plausible solutions, original matched_count-desc / MAE-asc order is preserved."""

        def predict(smiles: str):
            if smiles == "HIGH_MATCH_AROMATIC":
                return make_prediction_result(smiles, [141.0, 137.0, 129.4, 127.1, 45.0, 30.0, 22.0])
            else:  # LOW_MATCH_AROMATIC
                return make_prediction_result(smiles, [141.0, 137.0, 999.0, 888.0, 45.0, 30.0, 22.0])

        mock_predictor.predict_from_smiles.side_effect = predict
        ranker = SolutionRanker(mock_predictor, tolerance=3.0)

        # 4 shifts in 110-160 range: both solutions need aromatic ring to be plausible
        experimental = [141.0, 137.0, 129.4, 127.1, 45.0, 30.0, 22.0]
        solutions = [
            LSDSolution(index=1, smiles="LOW_MATCH_AROMATIC"),
            LSDSolution(index=2, smiles="HIGH_MATCH_AROMATIC"),
        ]

        result = ranker.rank(solutions, experimental)

        assert result.solutions[0].smiles == "HIGH_MATCH_AROMATIC"
        assert result.solutions[1].smiles == "LOW_MATCH_AROMATIC"
```

---

### `tests/test_inventory_schema.py::TestSchemaV2Phase80` (new class, appended to existing file)

**Analog:** `tests/test_inventory_schema.py::TestSchemaValidation` lines 123–199 — same validator + `_load_schema()` + `_minimal_valid_v2()` helpers, same `Draft202012Validator` approach.

**Import and helpers already in file** (lines 1–52) — reuse `_load_schema()`, `_minimal_valid_v2()`, `Draft202012Validator`. No new imports needed.

**Class to append:**
```python
class TestSchemaV2Phase80:
    """Tests for Phase 80 schema changes: retire required pyLSD fields, add elim_budget.

    These tests FAIL before the schema is updated (Wave 0 prerequisite).
    """

    def test_accepts_inventory_without_pylsd_mode(self):
        """Phase 80: inventory without 'pylsd_mode' field must be accepted."""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        instance = _minimal_valid_v2()
        del instance["pylsd_mode"]  # Remove the now-optional field
        errors = list(validator.iter_errors(instance))
        assert errors == [], f"Expected no errors but got: {[e.message for e in errors]}"

    def test_accepts_inventory_without_elim_annotated(self):
        """Phase 80: inventory without 'elim_annotated' field must be accepted."""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        instance = _minimal_valid_v2()
        del instance["elim_annotated"]
        errors = list(validator.iter_errors(instance))
        assert errors == [], f"Expected no errors but got: {[e.message for e in errors]}"

    def test_accepts_inventory_without_deferred_4j(self):
        """Phase 80: inventory without 'deferred_4j' field must be accepted."""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        instance = _minimal_valid_v2()
        del instance["deferred_4j"]
        errors = list(validator.iter_errors(instance))
        assert errors == [], f"Expected no errors but got: {[e.message for e in errors]}"

    def test_accepts_inventory_with_elim_budget(self):
        """Phase 80: inventory with 'elim_budget' integer field must be accepted."""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        instance = _minimal_valid_v2()
        del instance["pylsd_mode"]
        del instance["elim_annotated"]
        del instance["deferred_4j"]
        instance["elim_budget"] = 1  # New Phase 80 field
        errors = list(validator.iter_errors(instance))
        assert errors == [], f"Expected no errors but got: {[e.message for e in errors]}"

    def test_rejects_negative_elim_budget(self):
        """Phase 80: elim_budget must be >= 0 (minimum: 0)."""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        instance = _minimal_valid_v2()
        del instance["pylsd_mode"]
        del instance["elim_annotated"]
        del instance["deferred_4j"]
        instance["elim_budget"] = -1
        errors = list(validator.iter_errors(instance))
        assert len(errors) >= 1, "Expected error for negative elim_budget"

    def test_schema_required_excludes_retired_pyLSD_fields(self):
        """Phase 80: 'pylsd_mode', 'elim_annotated', 'deferred_4j' must NOT be in required."""
        schema = _load_schema()
        required = schema.get("required", [])
        for retired_field in ("pylsd_mode", "elim_annotated", "deferred_4j"):
            assert retired_field not in required, (
                f"Retired field '{retired_field}' must not be in schema.required after Phase 80"
            )
```

Key patterns from the analog: `_load_schema()`, `Draft202012Validator(schema)`, `_minimal_valid_v2()`, `del instance["field"]`, `list(validator.iter_errors(instance))`, `assert errors == []`, `assert len(errors) >= 1`.

Note: The RESEARCH.md mentions `test_lsd_schema.py` does not exist yet — the correct file is `test_inventory_schema.py` (confirmed by `find` output). The new class `TestSchemaV2Phase80` is appended to that file.

---

## Shared Patterns

### Dataclass field addition (models.py files)

**Source:** `src/lucy_ng/lsd/models.py` lines 178–186 (`LSDProblem` dataclass)
**Apply to:** `src/lucy_ng/lsd/models.py` (new `elim_budget` field), `src/lucy_ng/ranking/models.py` (new `is_plausible` field)

For `@dataclass` classes: use primitive default directly (`elim_budget: int = 0`). For `BaseModel` (Pydantic v2) classes: use `Field(default=..., description="...")`.

```python
# dataclass pattern (lsd/models.py):
elim_budget: int = 0

# Pydantic v2 pattern (ranking/models.py):
is_plausible: bool = Field(
    default=True,
    description="...",
)
```

### Conditional `generate()` block with blank-line separator

**Source:** `src/lucy_ng/lsd/generator.py` lines 100–118
**Apply to:** `src/lucy_ng/lsd/generator.py` (new `elim_budget` emission block)

Every logical section in `generate()` ends with `lines.append("")`. The condition gate is always `if problem.<field>:` or `if problem.<field> > 0:`. New blocks follow the same shape:

```python
if problem.<condition>:
    lines.append(<emit_something>)
    lines.append("")  # blank separator
```

### Test class: assertion on generated LSD content

**Source:** `tests/test_lsd_generator.py` lines 463–477
**Apply to:** `tests/test_lsd_generator.py::TestElimBudget`

Pattern: construct `LSDProblem(...)`, add one atom, call `LSDInputGenerator.generate(problem)`, assert string membership and/or position. Never read files; use in-memory `content` string.

### Test class: mock predictor fixture + rank() call

**Source:** `tests/test_ranking.py` lines 346–430 (`TestSolutionRankerRank`)
**Apply to:** `tests/test_ranking.py::TestPlausibilityFilter`, `TestPlausibilityFilterOrdering`

Standard fixture:
```python
@pytest.fixture
def mock_predictor(self):
    predictor = MagicMock(spec=C13Predictor)
    return predictor
```

Standard SMILES-dispatch side-effect:
```python
def predict_side_effect(smiles: str):
    if smiles == "KNOWN_SMILES":
        return make_prediction_result(smiles, [...shifts...])
    ...
mock_predictor.predict_from_smiles.side_effect = predict_side_effect
```

Use `LSDSolution(index=N, smiles="...")` directly — no additional construction needed.

### Test class: JSON Schema validation

**Source:** `tests/test_inventory_schema.py` lines 123–199 (`TestSchemaValidation`)
**Apply to:** `tests/test_inventory_schema.py::TestSchemaV2Phase80`

Standard pattern:
```python
schema = _load_schema()
validator = Draft202012Validator(schema)
instance = _minimal_valid_v2()
# mutate instance...
errors = list(validator.iter_errors(instance))
assert errors == []  # or assert len(errors) >= 1
```

---

## No Analog Found

All files in Phase 80 have direct analogs. The agent skill files (`~/.claude/agents/lucy-lsd-engineer.md`, `~/.claude/agents/lucy-devils-advocate.md`, `~/.claude/agents/lucy-solution-analyst.md`, `~/.claude/agents/lucy-diagnostic.md`, `~/.claude/commands/lucy-ng/case.md`) are markdown prose edits — no code pattern applies; surgical section replacement is the pattern, guided by the line numbers in RESEARCH.md Q3.

---

## Metadata

**Analog search scope:** `src/lucy_ng/lsd/`, `src/lucy_ng/ranking/`, `src/lucy_ng/data/schemas/`, `src/lucy_ng/cli/`, `tests/`
**Files read:** 10 source/test files
**Pattern extraction date:** 2026-06-09
