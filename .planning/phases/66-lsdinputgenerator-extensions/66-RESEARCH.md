# Phase 66: LSDInputGenerator Extensions — Research

**Researched:** 2026-03-16
**Domain:** Python code extension — LSD input file format, `LSDInputGenerator`, `LSDCorrelation`, `LSDProblem`
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INPUT-01 | LSDInputGenerator supports FORM command for molecular formula declaration in pyLSD-format files | FORM is a plain-text header command: `FORM C13H18O2`. Emitted once, near top of file, after comments. LSD binary tolerance of unknown commands must be confirmed in Phase 69 (deferred). |
| INPUT-02 | LSDInputGenerator supports ELIM header command (`ELIM N M` for correlation elimination) | ELIM is a pyLSD-specific command that drops correlations entirely (not a bond-range extension). It belongs in the header section, before MULT. `emit_elim(n, m)` emits `ELIM N M`. CRITICAL: ELIM is NOT the same as extended bond range. |
| INPUT-03 | LSDInputGenerator supports SHIX/SHIH commands for chemical shift assignment to atoms | SHIX already emitted in `generate()` (lines 70–78 of generator.py). SHIH is not currently emitted. Need `emit_shih(atom_idx, shift)` and ensure SHIX emission is callable as a method, not only inline in `generate()`. |
| INPUT-04 | LSDInputGenerator supports extended HMBC bond range syntax (`HMBC X Y 2 4` for 2-4 bond correlations) | `LSDCorrelation.to_lsd_line()` currently ignores `min_bonds`/`max_bonds` and always emits `HMBC X Y`. When `max_bonds != 3` (the default), the generator MUST emit the extended form `HMBC X Y min_bonds max_bonds`. |
</phase_requirements>

---

## Summary

Phase 66 is a **pure Python extension** to existing code. No new dependencies are required. The work falls into four discrete, well-scoped changes to two files (`src/lucy_ng/lsd/models.py` and `src/lucy_ng/lsd/generator.py`) plus a new validator function and corresponding tests.

The codebase is already partially ready: `LSDCorrelation` has `min_bonds` and `max_bonds` fields, and `LSDAtom.carbon_shift` is already emitted as `SHIX` lines in `generate()`. The gap is that `to_lsd_line()` on `LSDCorrelation` ignores those bond-range fields, and the generator has no method for FORM, ELIM, or SHIH emission. A `validate_pylsd_input()` function is needed to catch the most dangerous mistake: writing a FORM line whose atom count disagrees with the MULT atom count.

The existing test suite (62 tests, all passing) must remain green. Eight to twelve new tests are needed.

**Primary recommendation:** Extend `LSDCorrelation.to_lsd_line()` to emit `HMBC X Y 2 4` when `max_bonds != 3`. Add `emit_form`, `emit_elim`, `emit_shih` as static methods on `LSDInputGenerator`. Add `validate_pylsd_input(problem)` that raises `ValueError` on FORM/MULT mismatch. No new classes needed.

---

## Standard Stack

### Core (already in use — no new installs)
| Module | Location | Purpose |
|--------|----------|---------|
| `lucy_ng.lsd.models` | `src/lucy_ng/lsd/models.py` | `LSDAtom`, `LSDCorrelation`, `LSDConstraint`, `LSDProblem` |
| `lucy_ng.lsd.generator` | `src/lucy_ng/lsd/generator.py` | `LSDInputGenerator` + `parse_molecular_formula()` |
| `re` (stdlib) | already imported in generator.py | Formula parsing — `parse_molecular_formula()` already exists |
| `pytest` | tests/ | All new tests use same fixture pattern as existing tests |

**Installation:** None required.

---

## Architecture Patterns

### Recommended Change Surface

```
src/lucy_ng/lsd/
├── models.py       # Change: LSDCorrelation.to_lsd_line() — emit HMBC X Y 2 4 when max_bonds != 3
├── generator.py    # Add: emit_form(), emit_elim(), emit_shih(), validate_pylsd_input()
└── (no new files needed)

tests/
└── test_lsd_generator.py   # Add: TestPyLSDExtensions class (new FORM/ELIM/SHIH/bond-range tests)
                            # Add: TestPyLSDValidator class (FORM/MULT mismatch tests)
```

### Pattern 1: Conditional Bond Range in `LSDCorrelation.to_lsd_line()`

**What:** `to_lsd_line()` currently emits `HMBC X Y` regardless of `min_bonds`/`max_bonds`. The fix is a single conditional: when `max_bonds != 3` (the default), emit `HMBC X Y {min_bonds} {max_bonds}`.

**Why `max_bonds != 3` as the trigger:** The default HMBC bond range in LSD is 2-3. Only emit the extended form when the range differs from the default. This means existing LSD files with no explicit range are not broken.

**Change in `models.py`:**
```python
# In LSDCorrelation.to_lsd_line(), HMBC branch:
elif self.correlation_type == "HMBC":
    # Emit extended bond range only when it differs from the LSD default (2-3)
    if self.min_bonds != 2 or self.max_bonds != 3:
        return f"HMBC {self.atom1_index} {self.atom2_index} {self.min_bonds} {self.max_bonds}"
    return f"HMBC {self.atom1_index} {self.atom2_index}"
```

**Backward compatibility:** All existing tests assert `HMBC 1 3` for `min_bonds=2, max_bonds=3`. This change preserves that — only non-default ranges trigger the extended form.

### Pattern 2: Static Emitter Methods on `LSDInputGenerator`

**What:** Three new `@staticmethod` methods that return a formatted string (not write to file). The `generate()` method calls them internally where appropriate.

```python
@staticmethod
def emit_form(formula: str) -> str:
    """Return 'FORM C13H18O2' line for pyLSD-format files."""
    return f"FORM {formula}"

@staticmethod
def emit_elim(n: int, m: int) -> str:
    """Return 'ELIM N M' line for correlation elimination."""
    return f"ELIM {n} {m}"

@staticmethod
def emit_shih(atom_idx: int, shift: float) -> str:
    """Return 'SHIH atom_idx shift' line for 1H chemical shift assignment."""
    return f"SHIH {atom_idx} {shift:.2f}"
```

**FORM placement in `generate()`:** FORM belongs in the file header section (after comment lines, before MULT). `LSDProblem` already has `molecular_formula`. The generator currently emits it only as a comment (`; Molecular formula: C13H18O2`). Add a `pylsd_mode: bool = False` field to `LSDProblem`, or accept a separate parameter. The simplest approach: add `emit_form_command: bool = False` as a field on `LSDProblem` that controls whether the FORM line is emitted.

**Alternative (simpler):** Add `pylsd_mode: bool = False` to `LSDProblem`. When `pylsd_mode=True`, `generate()` emits `FORM {molecular_formula}` in the header. The planner should decide; research recommends this approach as it bundles pyLSD behavior in one flag.

**ELIM placement in `generate()`:** ELIM goes in the header, after FORM but before MULT. The generator will need a list of ELIM commands attached to the problem. Simplest: `LSDProblem.elim_commands: list[tuple[int, int]]` field (default empty list).

**SHIX vs SHIH:** `SHIX` = 13C shift for atom. `SHIH` = 1H shift for atom. The generator already emits SHIX from `atom.carbon_shift`. SHIH should be emitted from `atom.proton_shift` (the field exists on `LSDAtom` but is never used in `generate()`). Add SHIH emission alongside SHIX in the existing "Chemical shifts" section.

### Pattern 3: `validate_pylsd_input()` as a standalone function in `generator.py`

**What:** A function that takes an `LSDProblem` and raises `ValueError` if the FORM atom count does not match the MULT atom count.

```python
def validate_pylsd_input(problem: LSDProblem) -> None:
    """Validate pyLSD-format problem for consistency.

    Raises:
        ValueError: If FORM atom count does not match MULT atom count.
    """
    if problem.molecular_formula is None:
        return  # No FORM to validate
    formula_counts = parse_molecular_formula(problem.molecular_formula)
    # Count atoms from MULT definitions
    mult_counts: dict[str, int] = {}
    for atom in problem.atoms:
        mult_counts[atom.element] = mult_counts.get(atom.element, 0) + 1
    # Check carbon count (primary check)
    form_c = formula_counts.get("C", 0)
    mult_c = mult_counts.get("C", 0)
    if form_c != mult_c:
        raise ValueError(
            f"FORM/MULT mismatch: FORM declares {form_c} carbons "
            f"but MULT defines {mult_c} carbons in '{problem.molecular_formula}'"
        )
```

**Why only carbon?** Carbon count is the most reliably set count (all carbons are MULT). Heteroatom counts in MULT often require flexibility (oxygen ambiguity, etc.). A carbon-only check catches the primary failure mode while avoiding false positives.

### Anti-Patterns to Avoid

- **Don't add FORM/ELIM/SHIH emission to existing tests that assert old output format.** The existing `test_generate_with_molecular_formula` asserts the formula only appears as a comment. Do not change `generate()` behavior for the default case — only when `pylsd_mode=True` is set.
- **Don't make FORM emission the default.** The Phase 69 regression test must confirm that a FORM line does not break the existing `lucy lsd run` path. Until that confirmation exists, FORM should be opt-in.
- **Don't change the HMBC default.** `min_bonds=2, max_bonds=3` must continue to produce `HMBC X Y` (no trailing bond numbers). Breaking this would invalidate all existing LSD files.
- **Don't emit SHIH for atoms with `proton_shift=None`.** Most LSDAtom instances have no proton_shift set; guard with `if atom.proton_shift is not None`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Molecular formula parsing | Custom regex | `parse_molecular_formula()` in generator.py | Already exists and tested |
| FORM atom count extraction | Separate parser | `parse_molecular_formula()` | Same function, already handles C/H/N/O/etc |
| File writing | New writer | `LSDInputGenerator.write_file()` | Existing method, no change needed |

---

## Common Pitfalls

### Pitfall 1: HMBC Default Range Breakage

**What goes wrong:** Changing the HMBC output logic breaks the `test_to_lsd_line_hmbc` test that asserts `HMBC 1 3` for `min_bonds=2, max_bonds=3`.

**Why it happens:** `LSDCorrelation` defaults are `min_bonds=2, max_bonds=3`. If the condition uses `min_bonds != 2 and max_bonds != 3` (AND instead of OR), it will never trigger.

**How to avoid:** Use `if self.min_bonds != 2 or self.max_bonds != 3:` — emit extended form whenever EITHER field differs from default.

**Warning signs:** Existing test `test_to_lsd_line_hmbc` fails.

### Pitfall 2: FORM Emitted Without pylsd_mode Guard

**What goes wrong:** If `generate()` unconditionally emits a FORM line when `molecular_formula` is set, every existing LSD file gains an unknown FORM command. The LSD binary may or may not tolerate this — Phase 69 is supposed to confirm tolerance.

**Why it happens:** It's tempting to just emit FORM whenever formula exists, since it's just a header comment upgrade.

**How to avoid:** Gate FORM emission behind `problem.pylsd_mode` (a boolean field on `LSDProblem`, default `False`). Existing code never sets this, so existing behavior is unchanged.

### Pitfall 3: FORM/MULT Mismatch Validator Too Strict

**What goes wrong:** Validating all heteroatom counts causes false positives — oxygen count in MULT is unreliable when hydroxyl vs ether ambiguity exists (deliberate design choice in `from_peak_data()`).

**Why it happens:** The validator naively compares all formula elements against all MULT elements.

**How to avoid:** Validate carbon only. Carbon is the primary molecular scaffold; all carbons MUST be in MULT with no ambiguity.

### Pitfall 4: SHIH Emitted for Wrong Atom Type

**What goes wrong:** SHIH should be emitted for proton-bearing atoms. If emitted for quaternary carbons or heteroatoms without proton_shift, the LSD file gains nonsense lines.

**Why it happens:** Iterating all atoms without checking `atom.proton_shift is not None`.

**How to avoid:** Guard: `if atom.proton_shift is not None: lines.append(emit_shih(atom.index, atom.proton_shift))`.

### Pitfall 5: ELIM Semantic Confusion

**What goes wrong:** ELIM is confused with the extended HMBC bond range mechanism. ELIM drops correlations entirely; `HMBC X Y 2 4` expands the bond range. These are NOT interchangeable.

**Why it happens:** The phase description mentions both. State.md decision log says: "ELIM does NOT extend bond ranges — it drops correlations entirely."

**How to avoid:** Document clearly in code comments. `emit_elim` docstring must state: "ELIM drops the correlation entirely. For 4J handling, use HMBC X Y 2 4 (set max_bonds=4 on LSDCorrelation)."

---

## Code Examples

### Extended HMBC line (INPUT-04 target output)

```
HMBC 6 8 2 4    ; 4J suspect — extended bond range 2-4
HMBC 6 11       ; Standard 2-3J HMBC (no trailing numbers)
```

### FORM line (INPUT-01 target output)

```
; LSD input file: ibuprofen
; Generated by lucy-ng
FORM C13H18O2

; Atom definitions
MULT 1 C 2 0    ; ...
```

### ELIM line (INPUT-02 target output)

```
FORM C13H18O2
ELIM 4 4

; Atom definitions
MULT 1 C 2 0    ; ...
```

### SHIX + SHIH lines (INPUT-03 target output)

```
; Chemical shifts
SHIX 1 180.56    ; 13C shift
SHIX 6 129.38
SHIH 10 3.71     ; 1H shift for CH at 45.03
```

### validate_pylsd_input usage

```python
problem = LSDProblem(molecular_formula="C13H18O2", pylsd_mode=True)
# Add only 12 carbons by mistake
for i in range(12):
    problem.add_atom(LSDAtom(i+1, "C", Hybridization.SP2, 0))
validate_pylsd_input(problem)  # raises ValueError: FORM declares 13 carbons but MULT defines 12
```

---

## State of the Art

| Old Approach | Current Approach | Impact for Phase 66 |
|--------------|------------------|---------------------|
| `HMBC X Y` always (2-3J default) | `HMBC X Y 2 4` for 4J suspects | Need to change `to_lsd_line()` in `LSDCorrelation` |
| Formula only as comment | `FORM C13H18O2` as pyLSD header command | Need `emit_form()` gated by `pylsd_mode` |
| No ELIM support | `ELIM N M` for artifact removal (pyLSD) | Need `emit_elim()` and ELIM list on `LSDProblem` |
| SHIH field on `LSDAtom` unused | `SHIH` line emitted when `proton_shift` set | Need SHIH emission in `generate()` |

---

## Open Questions

1. **`pylsd_mode` flag: on `LSDProblem` or as a `generate()` parameter?**
   - What we know: `LSDProblem` is a dataclass; adding a field is clean but changes the model.
   - What's unclear: Whether downstream Phase 67 orchestrator needs to inspect `pylsd_mode` from the problem object, or just sets it before calling `generate()`.
   - Recommendation: Add `pylsd_mode: bool = False` to `LSDProblem` dataclass. The orchestrator (Phase 67) needs to set this on problems it creates.

2. **ELIM list representation: `list[tuple[int,int]]` or `list[LSDConstraint]`?**
   - What we know: ELIM takes two integers (N M). Not a bond constraint between atoms.
   - What's unclear: Whether ELIM ever needs metadata/reason tracking like constraints do.
   - Recommendation: `elim_commands: list[tuple[int, int]] = field(default_factory=list)` on `LSDProblem`. Keep it simple — Phase 68 schema work can refine later.

3. **LSD binary tolerance of FORM command**
   - What we know: Phase 69 explicitly tests this. STATE.md: "FORM/LSD binary tolerance confirmed empirically in Phase 69."
   - What's unclear: Whether FORM causes LSD to error, warn, or silently ignore.
   - Recommendation: Gate FORM emission behind `pylsd_mode=True` for now. Phase 69 confirms tolerance and may remove the gate.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` (rootdir: `/Users/steinbeck/Dropbox/develop/lucy-ng`) |
| Quick run command | `pytest tests/test_lsd_generator.py tests/test_lsd_models.py -q` |
| Full suite command | `pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INPUT-01 | `emit_form("C13H18O2")` returns `"FORM C13H18O2"` | unit | `pytest tests/test_lsd_generator.py -k "form" -x` | Wave 0 (new) |
| INPUT-01 | `generate()` emits FORM line when `pylsd_mode=True` | unit | `pytest tests/test_lsd_generator.py -k "pylsd_form" -x` | Wave 0 (new) |
| INPUT-02 | `emit_elim(4, 4)` returns `"ELIM 4 4"` | unit | `pytest tests/test_lsd_generator.py -k "elim" -x` | Wave 0 (new) |
| INPUT-02 | `generate()` emits ELIM lines when `elim_commands` set | unit | `pytest tests/test_lsd_generator.py -k "elim_commands" -x` | Wave 0 (new) |
| INPUT-03 | `emit_shih(atom_idx, shift)` returns `"SHIH 1 3.71"` | unit | `pytest tests/test_lsd_generator.py -k "shih" -x` | Wave 0 (new) |
| INPUT-03 | `generate()` emits SHIH when `atom.proton_shift` set; no SHIH for None | unit | `pytest tests/test_lsd_generator.py -k "proton_shift" -x` | Wave 0 (new) |
| INPUT-03 | Existing SHIX output unchanged | regression | `pytest tests/test_lsd_generator.py::TestLSDInputGeneratorBasic::test_generate_with_chemical_shifts -x` | ✅ existing |
| INPUT-04 | `LSDCorrelation(1, 2, "HMBC", min_bonds=2, max_bonds=4).to_lsd_line() == "HMBC 1 2 2 4"` | unit | `pytest tests/test_lsd_models.py -k "hmbc_extended" -x` | Wave 0 (new) |
| INPUT-04 | Default `min_bonds=2, max_bonds=3` still produces `"HMBC 1 3"` (no trailing numbers) | regression | `pytest tests/test_lsd_models.py::TestLSDCorrelation::test_to_lsd_line_hmbc -x` | ✅ existing |
| INPUT-04 | `generate()` emits `HMBC 6 8 2 4` for correlation with max_bonds=4 | unit | `pytest tests/test_lsd_generator.py -k "hmbc_bond_range" -x` | Wave 0 (new) |
| INPUT-05 (validation) | `validate_pylsd_input()` raises `ValueError` on FORM/MULT carbon count mismatch | unit | `pytest tests/test_lsd_generator.py -k "validate_pylsd" -x` | Wave 0 (new) |
| INPUT-05 (validation) | `validate_pylsd_input()` passes when counts match; passes when no formula | unit | `pytest tests/test_lsd_generator.py -k "validate_pylsd" -x` | Wave 0 (new) |

### Sampling Rate
- **Per task commit:** `pytest tests/test_lsd_generator.py tests/test_lsd_models.py -q`
- **Per wave merge:** `pytest -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] New test class `TestPyLSDExtensions` in `tests/test_lsd_generator.py` — covers INPUT-01, INPUT-02, INPUT-03, INPUT-04 emitter methods
- [ ] New test class `TestPyLSDValidator` in `tests/test_lsd_generator.py` — covers `validate_pylsd_input()` error and pass cases
- [ ] New test method `TestLSDCorrelation::test_to_lsd_line_hmbc_extended` in `tests/test_lsd_models.py` — covers INPUT-04 `to_lsd_line()` change

No new test files needed — extend existing files.

---

## Key Findings Summary

1. **LSDCorrelation already has `min_bonds`/`max_bonds` fields** — they just need to be wired into `to_lsd_line()`. This is the smallest change with the highest impact (INPUT-04).

2. **SHIX emission already works** — `generate()` emits SHIX from `atom.carbon_shift`. SHIH just needs the same treatment for `atom.proton_shift` (INPUT-03 is largely already implemented for the 13C side).

3. **`parse_molecular_formula()` already exists in generator.py** — reuse it in `validate_pylsd_input()` for the FORM/MULT consistency check.

4. **`pylsd_mode` boolean needed on `LSDProblem`** — gates FORM and ELIM emission, preserving backward compatibility with all existing LSD files and tests.

5. **ELIM is NOT a bond range extension** — the decision in STATE.md is authoritative. `emit_elim` emits `ELIM N M` (drop correlation), while `HMBC X Y 2 4` expands range. Both are needed, they serve different purposes.

6. **62 existing tests pass** — the change surface is small and all regressions are immediately detectable via the quick test run.

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `src/lucy_ng/lsd/generator.py` — current SHIX emission, `generate()` structure
- Direct code inspection: `src/lucy_ng/lsd/models.py` — `LSDCorrelation.to_lsd_line()`, existing `min_bonds`/`max_bonds` fields
- Direct code inspection: `tests/test_lsd_generator.py`, `tests/test_lsd_models.py` — 62 existing tests, baseline confirmed green
- `.planning/REQUIREMENTS.md` — INPUT-01 through INPUT-04 requirements
- `.planning/phases/65-hypothesis-gate/validation_result.md` — GO decision, confirmed ibuprofen hypothesis

### Secondary (MEDIUM confidence)
- `.planning/STATE.md` decisions: "ELIM does NOT extend bond ranges", "Use `HMBC X Y 2 4` for 4J handling" — authoritative project decision
- `ibuprofen.lsd` (project root) + `ibuprofen_no4j.lsd` — reference for LSD file syntax, HMBC line format observed in practice

### Tertiary (LOW confidence)
- LSD command reference (FORM, ELIM, SHIX, SHIH syntax): inferred from STATE.md project decisions and pyLSD integration context; FORM/LSD binary tolerance is explicitly deferred to Phase 69 empirical confirmation

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all changes to existing code, no new dependencies
- Architecture: HIGH — concrete code paths identified, exact line numbers known
- Pitfalls: HIGH — derived from existing test baseline and explicit STATE.md decisions
- LSD binary FORM tolerance: LOW — explicitly deferred to Phase 69

**Research date:** 2026-03-16
**Valid until:** 2026-04-16 (codebase is internal — valid until Phase 66 code changes)
