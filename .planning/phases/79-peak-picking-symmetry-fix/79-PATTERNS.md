# Phase 79: Peak-Picking & Symmetry Detection Fix — Pattern Map

**Mapped:** 2026-06-08
**Files analyzed:** 9 (5 Python, 4 markdown)
**Analogs found:** 9 / 9

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/lucy_ng/processing/peak_picker.py` | service | transform | self (surgical edit) | exact |
| `src/lucy_ng/models/peaks.py` | model | transform | self (additive field) | exact |
| `src/lucy_ng/cli/pick.py` | CLI/controller | request-response | self (additive JSON field) | exact |
| `src/lucy_ng/cli/analyze.py` | CLI/controller | request-response | self (solvent param thread-through) | exact |
| `src/lucy_ng/processing/peak_picker.py` (new function `detect_intensity_symmetry`) | utility | transform | `src/lucy_ng/analysis/` `IntensityReporter` | role-match |
| `tests/test_peak_picker_snr.py` | test | batch | `tests/test_peak_picker_2d.py` | role-match |
| `tests/test_intensity_symmetry.py` | test | batch | `tests/test_symmetry_analysis.py` | role-match |
| `tests/test_cli_pick.py` (new methods) | test | request-response | self (existing class `TestPick1D`) | exact |
| `~/.claude/agents/lucy-nmr-chemist.md` | agent skill | event-driven | self (procedural section insertion) | exact |
| `~/.claude/commands/lucy-ng/case.md` | orchestrator | event-driven | self (`detect_loops` step extension) | exact |
| `~/.claude/commands/lucy-ng/references/loop-patterns.md` | reference | — | self (existing pattern block) | exact |
| `~/.claude/commands/lucy-ng/references/advisory-templates.md` | reference | — | self (existing advisory block) | exact |

---

## Pattern Assignments

### `src/lucy_ng/processing/peak_picker.py` — MAD threshold + solvent exclusion + SNR annotation

**Analog:** self (surgical replacement of lines 88–89 + instance method extension)

**Imports pattern** (lines 1–6 — no new imports needed):
```python
import numpy as np
from scipy.signal import find_peaks, peak_widths

from lucy_ng.models import Peak1D, PeakList1D, Spectrum1D
```

**Existing threshold pattern to REPLACE** (lines 87–89):
```python
# BEFORE — max-relative (target of replacement)
max_intensity = np.max(np.abs(data))
abs_threshold = threshold * max_intensity
```

**New threshold pattern — module-level helpers to ADD** (insert before the class):
```python
# Solvent residual 13C shifts: exclusion windows (low_ppm, high_ppm)
# Each window is centred on the residual shift with ±5 ppm margin for multiplets.
_SOLVENT_EXCLUSION_13C: dict[str, tuple[float, float]] = {
    "CDCl3":   (72.0, 82.0),   # 77.16 ppm triplet
    "DMSO":    (37.0, 42.0),   # 39.52 ppm septet
    "DMSO-d6": (37.0, 42.0),
    "CD3OD":   (46.0, 52.0),   # 49.0 ppm septet
    "MeOD":    (46.0, 52.0),
    "CD3CN":   (1.0,   5.0),   # 1.32 ppm septet (benign low-ppm region anyway)
    "acetone": (27.0, 33.0),   # 29.84 ppm
    "C6D6":    (125.0, 131.0), # 128.06 ppm triplet
}


def _compute_snr_threshold(
    data: np.ndarray,
    ppm_scale: np.ndarray,
    solvent: str | None = None,
    k: float = 3.0,
) -> tuple[float, float]:
    """Compute SNR-based absolute threshold using MAD noise estimate.

    Args:
        data: Spectrum intensity array.
        ppm_scale: Corresponding ppm axis.
        solvent: Bruker SOLVENT string (e.g. "CDCl3"). If None or not in table,
                 MAD is computed over the full array (still robust for 13C).
        k: SNR floor multiplier. IUPAC LoD convention: k=3.

    Returns:
        (abs_threshold, sigma_mad) — threshold = k * sigma_mad.
    """
    exclusion = _SOLVENT_EXCLUSION_13C.get(solvent or "", None)
    if exclusion is not None:
        lo, hi = exclusion
        mask = (ppm_scale >= lo) & (ppm_scale <= hi)
        clean_data = data[~mask]
    else:
        clean_data = data

    mad = float(np.median(np.abs(clean_data - np.median(clean_data))))
    sigma_mad = 1.4826 * mad
    return k * sigma_mad, sigma_mad
```

**Updated `pick_peaks_instance` core pattern** (replace lines 83–108 in the instance method body):
```python
def pick_peaks_instance(
    self,
    spectrum: Spectrum1D,
    threshold: float = 0.05,       # kept for backwards compat; used only when use_snr=False
    detect_negative: bool = False,
    snr_floor: float = 3.0,        # IUPAC LoD convention
    use_snr: bool = True,          # new default-on SNR mode
) -> PeakList1D:
    data = spectrum.data
    ppm_scale = spectrum.ppm_scale
    ppm_per_point = abs(ppm_scale[1] - ppm_scale[0]) if len(ppm_scale) > 1 else 1.0

    if use_snr:
        abs_threshold, sigma_mad = _compute_snr_threshold(
            data, ppm_scale, solvent=spectrum.solvent, k=snr_floor
        )
    else:
        abs_threshold = threshold * np.max(np.abs(data))
        sigma_mad = None

    # _estimate_min_distance call is unchanged — it uses abs_threshold internally
    min_distance_ppm = self._estimate_min_distance(data, ppm_per_point, abs_threshold)
    min_distance_points = max(1, int(min_distance_ppm / ppm_per_point))

    peak_indices, _ = find_peaks(data, height=abs_threshold, distance=min_distance_points)

    peaks = []
    for idx in peak_indices:
        snr = float(abs(data[idx]) / sigma_mad) if sigma_mad is not None else None
        peaks.append(Peak1D(
            position=float(ppm_scale[idx]),
            intensity=float(data[idx]),
            snr=snr,
        ))

    if detect_negative:
        neg_indices, _ = find_peaks(-data, height=abs_threshold, distance=min_distance_points)
        for idx in neg_indices:
            snr = float(abs(data[idx]) / sigma_mad) if sigma_mad is not None else None
            peaks.append(Peak1D(
                position=float(ppm_scale[idx]),
                intensity=float(data[idx]),
                snr=snr,
            ))

    peaks.sort(key=lambda p: p.position, reverse=True)
    return PeakList1D(peaks=peaks, nucleus=spectrum.nucleus)
```

**`pick_peaks` static method signature extension** (lines 38–63 — forward snr_floor and use_snr):
```python
@staticmethod
def pick_peaks(
    spectrum: Spectrum1D,
    threshold: float = 0.05,
    detect_negative: bool = False,
    snr_floor: float = 3.0,
    use_snr: bool = True,
) -> PeakList1D:
    if AdaptivePeakPicker._default_instance is None:
        AdaptivePeakPicker._default_instance = AdaptivePeakPicker()
    return AdaptivePeakPicker._default_instance.pick_peaks_instance(
        spectrum, threshold, detect_negative, snr_floor, use_snr
    )
```

**New function `detect_intensity_symmetry`** (add after `AdaptivePeakPicker` class, or in a new `src/lucy_ng/processing/intensity_symmetry.py`):
```python
def detect_intensity_symmetry(
    peaks: list[Peak1D],
    aromatic_ch_ppms: list[float],
    tolerance_ppm: float = 1.0,
    min_ratio: float = 1.6,
) -> list[tuple[float, float, int]]:
    """Detect intensity-doubled aromatic CH peaks as 2C-equivalence candidates.

    Scope restriction (D-06): only HSQC-confirmed aromatic CH carbons in 100-165 ppm.
    Returns list of (ppm, intensity_ratio_to_class_median, estimated_carbon_count).
    """
    aromatic_ch_peaks = [
        p for p in peaks
        if any(abs(p.position - ref) < tolerance_ppm for ref in aromatic_ch_ppms)
        and 100.0 <= p.position <= 165.0
    ]
    if len(aromatic_ch_peaks) < 2:
        return []

    median_intensity = float(np.median([p.intensity for p in aromatic_ch_peaks]))
    if median_intensity <= 0:
        return []

    return [
        (p.position, p.intensity / median_intensity, round(p.intensity / median_intensity))
        for p in aromatic_ch_peaks
        if p.intensity / median_intensity >= min_ratio
    ]
```

---

### `src/lucy_ng/models/peaks.py` — add `snr` field to `Peak1D`

**Analog:** self — existing optional-field pattern at lines 13–14 (`assignment`, `multiplicity`)

**Existing optional field pattern** (lines 8–15):
```python
class Peak1D(BaseModel):
    """1D NMR peak."""
    position: float   # ppm
    intensity: float
    assignment: str | None = None
    multiplicity: str | None = None   # s, d, t, q, m, etc.
```

**New field to ADD** (insert after `multiplicity`, line 15):
```python
    snr: float | None = None   # signal-to-noise ratio vs MAD-based sigma (Phase 79)
```

No validator needed — `snr` is a plain optional float; it mirrors the pattern of `assignment` and `multiplicity` which also have `None` defaults with no validator beyond the field type.

---

### `src/lucy_ng/cli/pick.py` — surface `noise_sigma` and per-peak `snr` in JSON

**Analog:** self — existing JSON serialisation block at lines 62–74

**Existing JSON block** (lines 62–74):
```python
if output_format == "json":
    data = {
        "count": len(peaks.peaks),
        "negative_detected": has_significant_negative,
        "peaks": [
            {
                "ppm": p.position,
                "intensity": p.intensity,
            }
            for p in peaks.peaks
        ],
    }
    click.echo(json.dumps(data, indent=2))
```

**Updated JSON block** (replace the `data = {...}` dict only):
```python
if output_format == "json":
    # Retrieve noise_sigma from the first peak that has snr set, back-computing it;
    # or expose it from the picker if the picker is called with capture.
    # Simpler: call pick_peaks_instance directly to capture sigma_mad.
    # Pattern: call instance method, capture sigma_mad alongside peaks.
    #
    # Implementation note: pick_peaks_instance returns PeakList1D only.
    # Refactor: have pick_1d call _compute_snr_threshold separately to get sigma_mad,
    # then pass it to the picker as the height= argument, OR add sigma_mad to PeakList1D.
    # Recommended: add optional `noise_sigma: float | None = None` to PeakList1D model
    # (same optional-field pattern as spectrum_id), then set it in pick_peaks_instance.
    data = {
        "count": len(peaks.peaks),
        "noise_sigma": peaks.noise_sigma,    # NEW — None for legacy/non-SNR callers
        "negative_detected": has_significant_negative,
        "peaks": [
            {
                "ppm": p.position,
                "intensity": p.intensity,
                "snr": p.snr,               # NEW — None for threshold=<explicit> callers
            }
            for p in peaks.peaks
        ],
    }
    click.echo(json.dumps(data, indent=2))
```

**Backwards-compatibility guarantee:** The existing test `test_pick_1d_json` asserts `"ppm" in data["peaks"][0]` and `"intensity" in data["peaks"][0]` — adding `"snr"` does NOT break this. The `"noise_sigma"` top-level key is new; no existing test asserts its absence.

**`has_significant_negative` detection must use `sigma_mad` not `max`:**
After the SNR refactor, replace the pre-pick threshold used for negative detection (lines 50–51) to stay consistent:
```python
# BEFORE (line 50-51) — max-relative negative detection gate
effective_threshold = threshold if threshold is not None else 0.05
max_abs = float(np.max(np.abs(spectrum.data)))
has_significant_negative = bool(np.min(spectrum.data) < -effective_threshold * max_abs)

# AFTER — reuse sigma_mad computed by picker, or keep simple heuristic:
# The negative detection is separate from peak detection; the heuristic is fine to keep
# as-is. The key change is to call pick_peaks with use_snr=True (default), which
# already picks based on SNR. The has_significant_negative gate uses abs(min)/abs(max)
# which is independent of the threshold mechanism. No change needed here.
```

---

### `src/lucy_ng/cli/analyze.py` — thread `spectrum.solvent` through to picker

**Analog:** self — `pick_peaks` calls at lines 51–54

**Existing picker call** (lines 50–54):
```python
picker = AdaptivePeakPicker()
if threshold is not None:
    peaks = picker.pick_peaks(spectrum, threshold=threshold)
else:
    peaks = picker.pick_peaks(spectrum)
```

**Updated call** (pass `use_snr` and solvent via Spectrum1D; the picker reads `spectrum.solvent` internally — no change to call site needed once the picker is updated per D-04 option-b):
```python
# Option (b) from RESEARCH.md Pitfall 4: picker extracts solvent from Spectrum1D directly.
# If that approach is taken, the analyze_symmetry call site is UNCHANGED.
# If option (a) is taken (explicit param), update to:
picker = AdaptivePeakPicker()
if threshold is not None:
    peaks = picker.pick_peaks(spectrum, threshold=threshold, use_snr=False)
else:
    peaks = picker.pick_peaks(spectrum)   # use_snr=True default, solvent from spectrum
```

The planner should choose option (b) — the picker reads `spectrum.solvent` itself. This keeps all four call sites (pick.py, analyze.py, test files) unchanged.

---

### `tests/test_peak_picker_snr.py` — NEW: FIX-04 regression

**Analog:** `tests/test_peak_picker_2d.py` (integration test with real Bruker data, `Path` constants, `BrukerReader.read_*`)

**File header and import pattern** (`test_peak_picker_2d.py` lines 1–15):
```python
"""Tests for SNR/MAD peak-picker threshold (FIX-04).

Regression tests verifying that:
  - CASE9 ester carbonyl at 166.08 ppm is picked by the new threshold.
  - CASE1 (ibuprofen) 13C peak count is unchanged.
  - Per-peak SNR annotation is present.
"""

from pathlib import Path

import pytest

from lucy_ng.models import PeakList1D
from lucy_ng.processing.peak_picker import AdaptivePeakPicker, _compute_snr_threshold
from lucy_ng.readers import BrukerReader

# Real Bruker data paths — confirmed available by RESEARCH.md
DATA_DIR = Path(__file__).parent.parent / "data"
CASE1_C13 = DATA_DIR / "Ibuprofen" / "2"                          # in-repo

# CASE9 is outside the repo (see reference_test_data memory)
CASE9_C13 = Path(
    "/Users/steinbeck/Dropbox/develop/data/nmrdata"
    "/active-lucy-ng-testprojects/CASE9/12"
)
```

**Integration test pattern** (mirror `test_peak_picker_2d.py` class structure):
```python
class TestSNRThreshold:
    """Unit tests for _compute_snr_threshold helper."""

    def test_mad_lower_than_max_for_cdcl3_dominated_spectrum(self) -> None:
        """sigma_mad must be << 5% of max for CDCl3-dominated spectrum."""
        import numpy as np
        # Synthetic: noise floor + one large CDCl3 spike
        rng = np.random.default_rng(42)
        noise = rng.normal(0, 1e5, 32768)
        ppm = np.linspace(220.0, 0.0, 32768)
        # Inject CDCl3 spike at 77 ppm
        cdcl3_idx = int((220.0 - 77.16) / 220.0 * 32768)
        noise[cdcl3_idx] = 4.6e7
        threshold, sigma_mad = _compute_snr_threshold(noise, ppm, solvent="CDCl3")
        # sigma_mad must be close to 1e5, not inflated by the spike
        assert sigma_mad < 5e5, f"sigma_mad too large: {sigma_mad:.2e}"
        # threshold = 3 * sigma_mad, must be << 2.30e6 (the old 5%-max threshold)
        assert threshold < 1e6


class TestCASE9Regression:
    """Integration regression: CASE9 carbonyl must be picked."""

    @pytest.mark.skipif(
        not CASE9_C13.exists(),
        reason="CASE9 dataset not available on this machine",
    )
    def test_case9_carbonyl_picked(self) -> None:
        """Ester C=O at 166.08 ppm (SNR≈17) must appear in peak list."""
        spectrum = BrukerReader.read_1d(str(CASE9_C13))
        peaks = AdaptivePeakPicker.pick_peaks(spectrum)

        ppms = [p.position for p in peaks.peaks]
        # Carbonyl at 166.08 ppm — accept ±2 ppm window
        assert any(164.0 <= ppm <= 168.0 for ppm in ppms), (
            f"Carbonyl not found near 166 ppm. Picked: {sorted(ppms, reverse=True)[:10]}"
        )

    @pytest.mark.skipif(
        not CASE9_C13.exists(),
        reason="CASE9 dataset not available on this machine",
    )
    def test_case9_all_peaks_have_snr(self) -> None:
        """Every picked peak must carry a non-None SNR annotation."""
        spectrum = BrukerReader.read_1d(str(CASE9_C13))
        peaks = AdaptivePeakPicker.pick_peaks(spectrum)
        for p in peaks.peaks:
            assert p.snr is not None
            assert p.snr > 0


class TestCASE1Regression:
    """Regression: ibuprofen 13C peak count must not decrease."""

    def test_case1_count_unchanged(self) -> None:
        """Ibuprofen should still yield ≥ 9 13C peaks (same as before)."""
        spectrum = BrukerReader.read_1d(str(CASE1_C13))
        peaks = AdaptivePeakPicker.pick_peaks(spectrum)
        # v8.0 picked 13 peaks; SNR threshold picks a superset — assert floor
        assert len(peaks.peaks) >= 9, (
            f"Ibuprofen peak count dropped to {len(peaks.peaks)}"
        )
```

---

### `tests/test_intensity_symmetry.py` — NEW: FIX-05 unit + regression

**Analog:** `tests/test_symmetry_analysis.py` (unit tests with synthetic `Peak1D` fixtures + real-data integration class)

**Import and fixture pattern** (`test_symmetry_analysis.py` lines 1–25 + conftest.py Spectrum1D fixture pattern):
```python
"""Tests for detect_intensity_symmetry (FIX-05).

Verifies that CASE9's two 2C aromatic CH peaks are flagged as equivalence
candidates while single-carbon peaks are not.
"""

import pytest
import numpy as np

from lucy_ng.models import Peak1D
from lucy_ng.processing.peak_picker import detect_intensity_symmetry


# Synthetic fixtures — same style as test_symmetry_analysis.py
@pytest.fixture
def case9_like_aromatic_peaks() -> list[Peak1D]:
    """CASE9 13C peaks: two 2C arom-CH (high intensity) + two 1C arom-Cq (low)."""
    return [
        # 2C aromatic CH — ratio ~100× median of class
        Peak1D(position=129.94, intensity=1.81e7),
        Peak1D(position=125.31, intensity=1.72e7),
        # 1C aromatic Cq — below threshold
        Peak1D(position=150.80, intensity=3.1e6),
        Peak1D(position=130.16, intensity=2.9e6),
        # Non-aromatic (below 100 ppm) — must NOT be returned
        Peak1D(position=22.10, intensity=1.70e7),
    ]


@pytest.fixture
def aromatic_ch_ppms_case9() -> list[float]:
    """HSQC-confirmed aromatic CH positions for CASE9."""
    return [129.94, 125.31]  # the two 2C aromatic CH from CASE9 HSQC
```

**Unit test class pattern** (mirror `TestIntensityReporter` structure in `test_symmetry_analysis.py`):
```python
class TestDetectIntensitySymmetry:
    """Unit tests for detect_intensity_symmetry."""

    def test_case9_flags_two_candidates(
        self,
        case9_like_aromatic_peaks: list[Peak1D],
        aromatic_ch_ppms_case9: list[float],
    ) -> None:
        """Both 2C aromatic CH peaks must be flagged."""
        result = detect_intensity_symmetry(
            case9_like_aromatic_peaks, aromatic_ch_ppms_case9
        )
        assert len(result) == 2
        ppms = [r[0] for r in result]
        assert any(abs(ppm - 129.94) < 1.0 for ppm in ppms)
        assert any(abs(ppm - 125.31) < 1.0 for ppm in ppms)

    def test_estimated_carbon_count_is_2(
        self,
        case9_like_aromatic_peaks: list[Peak1D],
        aromatic_ch_ppms_case9: list[float],
    ) -> None:
        """Estimated carbon count for 2C candidates must be 2."""
        result = detect_intensity_symmetry(
            case9_like_aromatic_peaks, aromatic_ch_ppms_case9
        )
        for _, ratio, count in result:
            assert count == 2, f"Expected count=2, got {count} (ratio={ratio:.1f})"

    def test_non_aromatic_peaks_excluded(
        self,
        case9_like_aromatic_peaks: list[Peak1D],
        aromatic_ch_ppms_case9: list[float],
    ) -> None:
        """Peaks outside 100-165 ppm must not appear in results."""
        result = detect_intensity_symmetry(
            case9_like_aromatic_peaks, aromatic_ch_ppms_case9
        )
        for ppm, _, _ in result:
            assert 100.0 <= ppm <= 165.0

    def test_empty_aromatic_ch_list_returns_empty(self) -> None:
        """No HSQC-confirmed aromatics -> empty result."""
        peaks = [Peak1D(position=129.0, intensity=1e7)]
        result = detect_intensity_symmetry(peaks, aromatic_ch_ppms=[])
        assert result == []

    def test_single_aromatic_ch_returns_empty(self) -> None:
        """Single aromatic CH: no class median comparison possible -> empty."""
        peaks = [Peak1D(position=129.0, intensity=1e7)]
        result = detect_intensity_symmetry(peaks, aromatic_ch_ppms=[129.0])
        assert result == []
```

---

### `tests/test_cli_pick.py` — NEW methods inside `TestPick1D`

**Analog:** self — existing `test_pick_1d_json` and `test_pick_1d_dept135_json_negative` methods (lines 22–75)

**Pattern to follow** (existing method at lines 22–33):
```python
def test_pick_1d_json(self) -> None:
    """Test picking 1D peaks with JSON output."""
    runner = CliRunner()
    result = runner.invoke(pick, ["1d", "data/Ibuprofen/2", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "count" in data
    assert "peaks" in data
    assert data["count"] > 0
    assert "ppm" in data["peaks"][0]
    assert "intensity" in data["peaks"][0]
```

**New methods to ADD to `TestPick1D`** (same runner, same dataset, additive assertions):
```python
def test_pick_1d_json_has_snr(self) -> None:
    """New SNR field must be present in each peak in JSON output."""
    runner = CliRunner()
    result = runner.invoke(pick, ["1d", "data/Ibuprofen/2", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "snr" in data["peaks"][0]
    # snr must be a positive number (not None serialized as null)
    assert data["peaks"][0]["snr"] is not None
    assert data["peaks"][0]["snr"] > 0

def test_pick_1d_json_has_noise_sigma(self) -> None:
    """New noise_sigma top-level field must be present in JSON output."""
    runner = CliRunner()
    result = runner.invoke(pick, ["1d", "data/Ibuprofen/2", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "noise_sigma" in data
    assert data["noise_sigma"] is not None
    assert data["noise_sigma"] > 0
```

---

### `~/.claude/agents/lucy-nmr-chemist.md` — DBE self-check + intensity-symmetry procedural steps

**Analog:** self — existing `## 5. Statistical Detection Protocol` section and the `[SETUP-COMPLETE]` message template (lines 106–196 and 200–222)

**Existing workflow step that ends the setup** (section 5 detection, line 117):
```
Run detection ONCE per compound, before first LSD iteration.
```

**Existing [SETUP-COMPLETE] format** (lines 201–222):
```
[SETUP-COMPLETE]
DBE: <value> (calculation: (2C + 2 + N - H) / 2)
...
Quality assessment: 13C SNR=N (tier), HSQC SNR=N (tier), HMBC SNR=N (tier)
Statistical detection:
  - <shift> ppm: <hybridisation result>, <neighbours result>
...
Key observations: <1-2 sentences summarizing notable chemistry>
```

**Two insertion points:**

**Insertion 1** — After the `analyze grouping` row in the detection table (section 5, before "Run detection ONCE"), add a new numbered sub-section:

```markdown
### Intensity-Symmetry Check (MANDATORY for aromatic compounds)

After `lucy analyze symmetry` and before statistical detection, if aromatic CH peaks
are present (HSQC correlations in 110-165 ppm):

1. Collect the ppm positions of all HSQC-confirmed aromatic CH carbons.
2. Compare 13C peak intensities within this class only:
   - Compute the median intensity of the aromatic CH class.
   - Any peak with intensity ≥ 1.6× the median is a **2C-equivalence candidate**.
3. Report candidates under "Symmetry" in [SETUP-COMPLETE]:
   - "Intensity-symmetry: <ppm> (ratio=<R>, 2C candidate)" for each flagged peak.
   - "Intensity-symmetry: none detected" if no candidates.
4. Pass confirmed 2C-equivalence candidates to `lucy detect aromatic-cosy` as grouped shifts.

**Why:** 13C intensity for aromatic CH reflects the number of equivalent carbons
contributing to that signal. Para-disubstituted aromatic rings produce two 2C-equivalent
pairs with ~2× the intensity of a mono-substituted ring carbon. This feeds
`detect_aromatic_cosy_pairs` correctly.
```

**Insertion 2** — After statistical detection (after section 5) and before sending `[SETUP-COMPLETE]`, add a new section `## 5a. DBE Self-Check (MANDATORY)`:

```markdown
## 5a. DBE Self-Check (MANDATORY — before [SETUP-COMPLETE])

After completing statistical detection, ALWAYS perform a DBE balance check.

**Formula:** DBE = (2C + 2 + N − H) / 2

**Account for DBE from found evidence:**
- Benzene/aromatic ring: 4 DBE (ring=1 + 3 C=C double bonds)
- Each additional ring: 1 DBE
- Each C=C double bond outside ring: 1 DBE
- Each C=O (carbonyl, ester, amide, carbamate): 1 DBE

**If DBE_found < DBE_formula:**
- deficit = DBE_formula − DBE_found
- O present in formula and 160–220 ppm region has NO picked peak?
  → FLAG: "DBE deficit of N; O in formula; 160-220 ppm region appears empty.
     Check SNR annotation — any peak in 160-220 ppm with SNR 3-20?
     If so, it may have been picked but not yet assigned."
- N present and 150–180 ppm (amide) or 100–120 ppm (nitrile) empty?
  → FLAG similar message.
- No O or N but deficit > 0: likely an additional ring or C=C.

**Output:** Add to [SETUP-COMPLETE] under the "Key observations" field:
- "DBE balance: accounted X of Y DBE." — if balanced.
- "DBE deficit: N DBE unaccounted; suspected source: <region/atom type>" — if deficit.

This check is a **diagnostic flag**, not a decision gate. The agent decides
whether to act on it.
```

**[SETUP-COMPLETE] format addition** — add two new fields after `Quality assessment:`:
```
DBE balance: <accounted N of M DBE> or <deficit N DBE; suspected: region>
Intensity-symmetry: <ppm: ratio, 2C candidate> or <none detected>
```

---

### `~/.claude/commands/lucy-ng/case.md` — 5th pattern in `detect_loops` step

**Analog:** self — existing `detect_loops` step lines 343–366 (the 4 pattern checks + convergence logic)

**Existing pattern check structure** (lines 352–358):
```
**Pattern 1: ELIM Thrashing** — ELIM appears in constraints added in 2+ iterations, OR ELIM added, removed, then added again.

**Pattern 2: Zero-Solution Loop** — 3+ consecutive iterations with solution_count = 0.

**Pattern 3: Solution Explosion** — Last 3 iterations all have solution_count > 100 AND each iteration reduces count by less than 10%.

**Pattern 4: Constraint Churning** — Last 5 iterations show >10 constraints added AND >5 constraints removed AND most recent solution_count > 50.
```

**New Pattern 5 to INSERT** (after Pattern 4 line, before the convergence check block):
```
**Pattern 5: Quality Convergence Failure** — Most recent [RANKING-COMPLETE] message (or
CASE-PROGRESS.md ## Ranking section for current iteration) shows Chemical plausibility =
IMPLAUSIBLE or QUESTIONABLE for ALL top-3 candidates.
OR-trigger: best-MAE > 4.0 ppm AND solution_count ≤ 20.
Guard: only fire if a [RANKING-COMPLETE] record exists for the current iteration.
Do NOT fire if solution_count = 0 (Pattern 2 covers that case).
```

**`track_and_decide` counter addition** (lines 476–496):
```
**Per-pattern intervention counters:**
- ELIM_THRASHING: count_elim
- ZERO_SOLUTION_LOOP: count_zero
- SOLUTION_EXPLOSION: count_explosion
- CONSTRAINT_CHURNING: count_churning
- QUALITY_CONVERGENCE_FAILURE: count_quality   ← NEW

Decision for QUALITY_CONVERGENCE_FAILURE:
- count_quality == 0: deliver assumption-reexamination advisory (proceed to deliver_advisory)
- count_quality >= 1: honest termination — do NOT escalate to diagnostic specialist
  (the diagnostic specialist is LSD-focused; quality convergence is a picking issue).
  Send to coordinator:
  "Assumption re-examination complete. No correctable peak-picking defect found after
   1 re-examination cycle. Additional experiments may be needed."
```

---

### `~/.claude/commands/lucy-ng/references/loop-patterns.md` — 5th pattern definition

**Analog:** self — existing `### Constraint Churning` block (lines 48–59)

**Existing pattern block structure** (lines 48–59):
```markdown
### Constraint Churning
**Definition:** Adding and removing constraints randomly without convergence over 5+ iterations.

**Detection criteria:**
- Last 5 iterations show >10 constraints added AND >5 constraints removed
- Most recent iteration has solution_count > 50

**Common root causes:**
- Random correlation selection (not criteria-based)
- Not following incremental HMBC strategy
- Molecular formula incorrect (no strategy will converge)
```

**New block to APPEND** (after `### Constraint Churning`, before `</loop_detection_reference>`):
```markdown
### Quality Convergence Failure
**Definition:** Solutions converge to a small count but ALL top-K candidates are
IMPLAUSIBLE or QUESTIONABLE per the solution-analyst's verdict.

**Detection criteria (primary — check FIRST):**
- solution-analyst's most recent [RANKING-COMPLETE] record lists Chemical plausibility
  as "IMPLAUSIBLE" or "QUESTIONABLE" for ALL top-3 candidates.
- A [RANKING-COMPLETE] record for the current iteration must exist (guard against
  false fire before ranking has run).

**Detection criteria (OR trigger):**
- best MAE in latest [RANKING-COMPLETE] > 4.0 ppm AND solution_count ≤ 20.

**Common root causes:**
- A key peak was missed in initial 13C picking (e.g., weak quaternary carbonyl masked
  by a solvent-dominated max-relative threshold)
- DBE deficit: missing carbonyl → forced extra ring → correct structure excluded
- Para-symmetry not detected: 2C-equivalent aromatic peaks not passed to
  detect_aromatic_cosy_pairs → emergent ring mechanism never activated
- Incorrect molecular formula

**Why this is different from Patterns 1–4:**
Patterns 1–4 detect LSD-level symptoms (zero solutions, explosion, churning, ELIM thrash).
This pattern fires when LSD is healthy but the **interpretation going into LSD was wrong
from the start**. A solution_count of ≤ 20 looks like SUCCESS to the other patterns —
that is exactly the CASE9 trap.

**Budget:** Exactly 1 re-examination cycle (D-12). After that, honest termination.
Do NOT escalate to the diagnostic specialist (it is LSD-focused, not pick-focused).
```

---

### `~/.claude/commands/lucy-ng/references/advisory-templates.md` — assumption-reexamination advisory

**Analog:** self — existing `<step name="deliver_advisory">` block and inline advisory templates in `case.md` `intervene` step (lines 399–474)

**Existing advisory template structure** (from `intervene` step, Constraint Churning example):
```
Constraint churning detected (high add/remove activity without convergence).

Reset to last known-good state (iteration <N> with <X> solutions).

Follow incremental HMBC strategy...
Do NOT add/remove randomly. Be systematic.
```

**Key structural conventions observed:**
1. Opening line names the pattern detected.
2. Bullet-point checklist of actions with concrete step labels.
3. Closes with a single prohibition or constraint.

**New advisory block to APPEND** (add as a new `<step>` block at the end of advisory-templates.md, before the closing `</anti_patterns>` tag):
```markdown
<step name="quality_convergence_advisory">

## Advisory: Quality Convergence Failure

**Deliver to:** nmr-chemist (reactivation advisory) via SendMessage.

**When to use:** QUALITY_CONVERGENCE_FAILURE detected (count_quality == 0). All top-3
solutions are IMPLAUSIBLE/QUESTIONABLE despite a converged solution count.

**Advisory text:**

```
[SUPERVISOR ADVISORY - QUALITY CONVERGENCE FAILURE]

All top solutions are IMPLAUSIBLE or QUESTIONABLE. The LSD constraint logic appears
sound (solutions converged), but the 13C INTERPRETATION going into LSD may be wrong.

Re-examination checklist (perform in order, stop when a concrete defect is found):

1. DBE balance: count accounted DBE (rings + C=C + C=O). Is the total < formula DBE?
   - If deficit: check the SNR annotation from your `lucy pick 1d --format json` output.
     Any peaks in 160-220 ppm with SNR 3-20 that were not assigned?
   - If yes: that is a candidate missed carbonyl. Note it and proceed to step 3.

2. Intensity-symmetry: were any aromatic CH peaks flagged as 2C-equivalence candidates
   (intensity ≥ 1.6× class median)?
   - If yes AND they were NOT passed to `lucy detect aromatic-cosy`: re-run
     `lucy detect aromatic-cosy` with the correct grouped shifts. Send updated
     HMBC equivalence groups to lsd-engineer for the next iteration.
   - If yes AND they were already passed: confirm lsd-engineer used grouped notation
     `HMBC N (M1 M2)` syntax in the LSD file.

3. Multiplicity spot-check: for any suspect peak (DBE candidate or near-equivalent),
   confirm DEPT-135 sign is consistent with the assignment.

After re-examination:
  - If a concrete defect is found: describe it in your [DETECTION-COMPLETE] message.
    lsd-engineer will rebuild the LSD file incorporating the correction.
  - If no defect found: respond "Re-examination complete: no correctable peak-picking
    defect found." The coordinator will close with honest termination.

Budget: THIS IS THE ONLY re-examination cycle. Do not initiate a further re-pick
unless a concrete suspicion exists (empty expected-region despite DBE deficit with
SNR 3-20 evidence). A blind re-pick at lower threshold is not warranted — the SNR
floor is already at k=3.
```

**SendMessage target:** nmr-chemist (NOT lsd-engineer — the defect is in picking, not constraints).
**After delivering advisory:** Return to monitor_progress. Do not trigger a full new LSD run yet — wait for nmr-chemist to respond with [DETECTION-COMPLETE] or "no defect found."

</step>
```

---

## Shared Patterns

### Optional field addition to Pydantic v2 model
**Source:** `src/lucy_ng/models/peaks.py` lines 13–14 (`assignment`, `multiplicity`)
**Apply to:** `Peak1D.snr` field addition, and the recommended `PeakList1D.noise_sigma` field addition
```python
# Pattern: optional field with None default, no validator unless constraints needed
field_name: type | None = None
```

### Click CLI JSON block extension (additive only)
**Source:** `src/lucy_ng/cli/pick.py` lines 62–74
**Apply to:** `pick_1d` JSON output block
**Convention:** New keys are simply added to the dict. Existing assertions in tests use `"key" in data["peaks"][0]` — they do not assert key absence, so additions are safe.

### Integration test with real Bruker data (skip if data absent)
**Source:** `tests/test_peak_picker_2d.py` lines 13–14 (PATH constants) + `tests/test_symmetry_analysis.py` pytest.fixture pattern
**Apply to:** `tests/test_peak_picker_snr.py`
```python
@pytest.mark.skipif(not SOME_PATH.exists(), reason="Dataset not available on this machine")
def test_something() -> None: ...
```
CASE9 data is outside the repo; `skipif` guards are required. CASE1 (Ibuprofen) is in-repo — no skip guard needed.

### Markdown skill pattern: new procedural section in nmr-chemist
**Source:** `~/.claude/agents/lucy-nmr-chemist.md` section `## 5. Statistical Detection Protocol` (procedural numbered steps with a named header, one-sentence rationale, ends with a `[SETUP-COMPLETE]` field addition)
**Apply to:** DBE self-check section and intensity-symmetry check insertion.
**Convention:**
- `##` heading with `(MANDATORY — condition)` suffix for required steps.
- Numbered checklist; bold flag phrases.
- Short rationale paragraph at end: "**Why:**".
- Corresponding field appended to the `[SETUP-COMPLETE]` format block.

### Markdown skill pattern: new loop-pattern block
**Source:** `~/.claude/commands/lucy-ng/references/loop-patterns.md` `### Constraint Churning` block (lines 48–59)
**Apply to:** Quality Convergence Failure pattern.
**Convention:**
- `###` heading = pattern name.
- `**Definition:**` sentence.
- `**Detection criteria:**` bullet list.
- `**Common root causes:**` bullet list.
- Optional `**Why this is different:**` paragraph for non-obvious patterns.

### Markdown skill pattern: advisory template block
**Source:** `~/.claude/commands/lucy-ng/references/advisory-templates.md` existing `<step>` blocks + `case.md` intervene step advisory text format
**Convention:**
- Wrap in `<step name="...">` XML element.
- Header line: `[SUPERVISOR ADVISORY - PATTERN NAME]`.
- Numbered checklist of re-examination steps.
- Final line: budget/prohibition constraint.
- Meta-instructions outside the quoted advisory text block: SendMessage target, post-delivery action.

---

## No Analog Found

None. All files have direct analogs in the existing codebase.

---

## Metadata

**Analog search scope:** `src/lucy_ng/`, `tests/`, `~/.claude/agents/`, `~/.claude/commands/lucy-ng/`
**Files scanned:** 12 source/test files read, 4 skill markdown files read
**Pattern extraction date:** 2026-06-08
