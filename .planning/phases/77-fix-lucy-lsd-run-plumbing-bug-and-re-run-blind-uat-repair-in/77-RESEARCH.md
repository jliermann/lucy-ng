# Phase 77: Fix lucy lsd run + Emergent-Aromatic Tooling + Skill Hygiene — Research

**Researched:** 2026-06-01
**Domain:** Python subprocess plumbing (LSD runner), LSD constraint logic (COSY equivalence), Claude agent skill maintenance
**Confidence:** HIGH — all findings verified by running code and inspecting actual artifacts on disk

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-77-01:** Aromatic ring is **emergent primary + documented BOND escalation**. Must emerge from correct native constraints (cross-ring `COSY 4 7` + `COSY 5 6` in Arm A reference). Explicit ring-BOND construction allowed ONLY as documented escalation after N non-aromatic iterations, logged in CASE-PROGRESS.md. SKEL benzene forcing stays forbidden in the normal flow. Root cause of Phase-76 failure: agent emitted **adjacent** `COSY 4 5`/`6 7` (topologically wrong) instead of cross-ring equivalence pairs.
- **D-77-02:** Fix for D-77-01 is **deterministic in tooling, not skill prose**. A CLI/generator helper derives cross-ring aromatic COSY equivalence pairs (4≡7, 5≡6) from detected symmetry/grouping and emits them. Agent no longer hand-assigns atom indices for aromatic equivalence.
- **D-77-03:** **Fix + fail-loud + regression test.** (1) Repair `_invoke_outlsd` so it invokes outlsd correctly and writes real SMILES. (2) When outlsd output is the error string / empty / non-SMILES, runner exits non-zero with a clear error — never reports false "success". (3) Regression test covers happy + error path. Also: correct the false "Phase 73 fix works" claim in `agents/lucy-lsd-engineer.md:124-130`.
- **D-77-04:** Phase 77 = fixes only (verified by tests). Phase 78 = blind re-UAT.
- **D-77-05:** Retire deprecated `lucy-case-agent.md` + targeted audit (no full rewrite, no ~5275-line consolidation).
- **D-77-06:** UAT criterion rewrite: emergent ring = clean pass; ring-BONDs only as CASE-PROGRESS-documented escalation = conditional pass; silent ring-BONDs or any SKEL = fail. Phase 78 inherits these criteria.

### Claude's Discretion

- Exact fail-loud detection predicate for FIX-01 (which strings/conditions beyond "This is not a file for OUTLSD." count as malformed output)
- The threshold N for ring-BOND escalation (how many non-aromatic iterations before escalation)
- Exact home for the deterministic COSY helper (new CLI subcommand vs generator method vs `lucy analyze grouping` extension)
- Audit depth of skill-creator within the "targeted, not full-rewrite" bound
- Whether to re-verify CASE9 sanitisation/workspace cleanliness as part of 77 or defer to 78

### Deferred Ideas (OUT OF SCOPE)

- Full skill-creator consolidation rewrite of the ~5275-line / 11-file complex
- CASE2–CASE8 UAT broadening
- Promoting `verify_case_solution.py` to `lucy lsd verify-uat` CLI subcommand
- Re-running CASE9 sanitisation/workspace blindness check
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FIX-01 | `lucy lsd run` produces real SMILES in solutions.smi and fails loud (non-zero exit, no false "success") when outlsd output is error string / empty / non-SMILES; regression test covers happy + error paths | Root cause identified and confirmed by reproduction: `_execute_lsd` does not copy ring3/ring4 filter files to output_dir when running a pre-existing LSD file via `run_file()`. Fix is in `_execute_lsd`. Fail-loud predicate design documented. |
| FIX-02 | Cross-ring aromatic COSY equivalence pairs emitted deterministically by tooling (from detected symmetry/grouping), so aromatic ring emerges without manual atom-index reasoning or forced ring-BONDs; ring-BOND forcing demoted to documented escalation | Deterministic algorithm confirmed: `zip(sorted(group_A_atoms), reversed(sorted(group_B_atoms)))`. Best home: new `detect_aromatic_cosy_pairs()` function in `lucy_ng/lsd/generator.py` (or `models.py`), exposed as `lucy detect aromatic-cosy` CLI subcommand. Integrates with `add_aromatic_equivalence_pair()` already in `LSDProblem`. |
| FIX-03 | Skill hygiene — deprecated `lucy-case-agent.md` retired; targeted skill-creator audit confirms v9.0 single-path + emergent/COSY guidance is prominent and flags dead/contradictory content | `lucy-case-agent.md` has active-looking frontmatter but `> DEPRECATED` blockquote header. No active workflow spawns it. Safe to neutralize frontmatter. Stale `outlsd 5 < compound.sol` manual invocation confirmed in body lines. Targeted audit scope is 4 active files (~2029 lines). |
</phase_requirements>

---

## Summary

Phase 77 fixes three concrete defects exposed by the Phase 76 UAT. All three have been fully diagnosed from code inspection and live reproduction.

**FIX-01 root cause (confirmed by reproduction):** `LSDRunner._execute_lsd` copies the `.lsd` input file to `output_dir` but does NOT copy the bundled `ring3`/`ring4` filter files that are referenced via `DEFF F1 "ring3"` / `DEFF F2 "ring4"` in every LSD file emitted by `LSDInputGenerator`. When the filter files are missing from the CWD, LSD exits with an error but still writes a partial `.sol` file (just the input echo, no solutions). `_count_solutions` falls back to file-count and reports 1 solution (the partial `.sol`). `_invoke_outlsd` then pipes this partial file to outlsd, which outputs `outlsd: This is not a file for OUTLSD.` — non-empty stdout, so `_invoke_outlsd` writes that string to `solutions.smi` and returns a non-None path. The runner reports success. This matches the Phase 76 CASE-PROGRESS.md observation exactly. Fix: copy ring filter files in `_execute_lsd` when the input LSD file contains `DEFF F` references, or unconditionally (always co-locate the bundled filters with the input file).

**FIX-02 root cause (confirmed by code inspection and Arm A reference):** The skill instructs the agent to emit `COSY 4 7` + `COSY 5 6` for aromatic CH equivalence in ibuprofen (correct, shown by Arm A reference). The Phase 76 agent emitted `COSY 4 5` + `COSY 6 7` (within-group, adjacent, topologically wrong). The skill's example is compound-specific (hardcoded atom indices 4, 5, 6, 7) rather than algorithmically derived. The deterministic rule: for two groups of aromatic sp2 CH atoms detected by `lucy analyze grouping`, cross-ring pairs are `zip(sorted(groupA_atom_ids), reversed(sorted(groupB_atom_ids)))`. This is exactly the pattern Arm A uses and produces 2/2 aromatic solutions. `LSDProblem.add_aromatic_equivalence_pair()` already exists and emits the native `COSY` line — FIX-02 only needs to add the pairing algorithm on top.

**FIX-03 (confirmed by file inspection):** `lucy-case-agent.md` has a `> DEPRECATED -- DO NOT USE` blockquote and a clear retirement note but retains the original frontmatter `name: lucy-case-agent` with active-looking `tools:` and `model:` fields. No active workflow (case.md or any sub-command) spawns it. It contains the stale `outlsd 5 < compound.sol > solutions.smi` manual invocation workflow. Safe to archive (neutralize frontmatter). The 4 active skill files (lsd-engineer: 589 lines, case.md: 593 lines, nmr-chemist: 264 lines, devils-advocate: 583 lines = ~2029 lines) need targeted review: false Phase-73 claim correction in lsd-engineer, COSY helper reference addition, escalation wording for D-77-01/D-77-06.

**Primary recommendation:** Fix `_execute_lsd` to copy ring filter files (1 line of code), add fail-loud validation to `_invoke_outlsd` (2-3 lines), add `detect_aromatic_cosy_pairs()` function (15 lines), update 4 skill files (targeted edits), neutralize `lucy-case-agent.md` frontmatter.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| LSD solver invocation | Python CLI/runner | — | `lucy lsd run` is the single primary path (D-02); subprocess management in `runner.py` |
| Ring filter file deployment | runner._execute_lsd | generator.write_file | `write_file` already handles it for API path; `run_file` path misses it |
| outlsd result validation | `_invoke_outlsd` helper | runner._run_outlsd | Single shared helper — both runner and orchestrator delegate here |
| Aromatic COSY pair derivation | `generator.py` / new helper | `lucy detect` CLI | Logic belongs near LSD file generation; CLI exposes it for agent use |
| Agent skill content | Agent .md files | — | Non-code; planner creates targeted edit tasks |

---

## Standard Stack

### Core (no new packages — FIX-01/02 are pure Python changes to existing code)

| Component | Current Version | Purpose | Why Standard |
|-----------|----------------|---------|--------------|
| `lucy_ng.lsd.runner.LSDRunner` | existing | LSD subprocess management | The fix target; already the correct abstraction |
| `lucy_ng.lsd.runner._invoke_outlsd` | existing | outlsd invocation helper | Phase 73 unified this; FIX-01 corrects the file-copy gap |
| `lucy_ng.lsd.generator.LSDInputGenerator` | existing | LSD file generation | write_file() already handles filter files; _execute_lsd must mirror it |
| `lucy_ng.lsd.models.LSDProblem.add_aromatic_equivalence_pair()` | existing | Emits COSY for aromatic equivalence | Already correctly emits native `COSY a b`; FIX-02 adds the pairing algorithm |
| `lucy_ng.detection.grouping.group_signals` | existing | Signal grouping by proximity | Already produces groups; FIX-02 consumes its output |
| `importlib.resources` | stdlib | Bundled filter file access | Already used in `_write_filter_files` — same pattern for `_execute_lsd` fix |

### No New External Dependencies

All three fixes are changes to existing Python code. No new packages needed. The test suite already uses `pytest`, `rdkit`, and standard lib — no additions required.

### Package Legitimacy Audit

> **Not applicable.** Phase 77 installs no new packages. All changes are to existing code.

---

## Architecture Patterns

### FIX-01: Root Cause Chain (confirmed by reproduction)

```
lucy lsd run <pre-existing.lsd with DEFF F1 "ring3">
    ↓
LSDRunner.run_file()
    ↓
LSDRunner._execute_lsd(input_file, output_dir)
    copies input_file to output_dir  ← correct
    does NOT copy ring3 / ring4      ← THE BUG
    ↓
subprocess: lsd compound.lsd (cwd=output_dir)
    ↓ ring3/ring4 not found in CWD
LSD: "error 401 - Cannot open file ring3 that defines fragment F1"
LSD: writes partial .sol (input echo only, NO solution data)
LSD: exit code = 1 (but LSD always exits 1 even on success!)
    ↓
_count_solutions(stdout="", output_files=[partial.sol], stderr="error 401...")
    → regex fails (no "N solution" in stderr)
    → fallback: count *.sol files = 1  ← FALSE COUNT
solution_count = 1 > 0
    ↓
_run_outlsd() → _invoke_outlsd(outlsd, partial.sol, output_dir)
    outlsd reads partial.sol (no OUTLSD block, no solution data)
    outlsd stdout: "outlsd: This is not a file for OUTLSD."
    proc.stdout.strip() is truthy  ← FALSE POSITIVE CHECK
    smiles_file.write_text("outlsd: This is not a file for OUTLSD.")
    returns smiles_file (non-None)  ← FALSE SUCCESS
    ↓
success = sol_file.exists() AND smiles_path is not None = True  ← FALSE SUCCESS
LSD completed successfully. Solutions found: 1.
```

**Correct behavior diagram:**

```
_execute_lsd(input_file, output_dir)
    ← copy input_file to output_dir (existing)
    ← ALSO copy ring3 / ring4 to output_dir (FIX-01A)
    → LSD runs with filter files present
    → produces real .sol with OUTLSD block + solution data
    ↓
_invoke_outlsd(outlsd, real.sol, output_dir)
    → outlsd outputs real SMILES
    ← validate: is stdout valid SMILES? (FIX-01B)
    → write solutions.smi with real SMILES
    → success = True
```

### FIX-01A: Filter File Copy Pattern (matches existing write_file pattern)

```python
# In _execute_lsd(), after copying input_file to output_dir:
# Copy bundled ring filter files if the LSD file references them
# (Always safe to copy — LSD ignores unused DEFF files)
LSDInputGenerator._write_filter_files(output_dir)
```

This reuses the exact same `_write_filter_files` method that `write_file()` uses. The bundled files are always valid. `[VERIFIED: src/lucy_ng/lsd/generator.py _write_filter_files(), confirmed working in Phase 73 test suite]`

### FIX-01B: Fail-Loud Predicate Design

The `_invoke_outlsd` function currently checks `if proc.stdout.strip()` — any non-empty output counts as success. The fail-loud predicate must cover:

1. Known outlsd error string: `"outlsd: This is not a file for OUTLSD."`
2. Empty output: `proc.stdout.strip() == ""`
3. Non-SMILES output: output does not contain at least one line parseable by RDKit

**Recommended predicate (Claude's Discretion):**

```python
def _is_valid_smiles_output(stdout: str) -> bool:
    """True if stdout looks like real outlsd SMILES output (not an error)."""
    if not stdout.strip():
        return False
    # Known outlsd error string
    if "This is not a file for OUTLSD" in stdout:
        return False
    # Must have at least one non-empty line that looks like a SMILES
    # (contains carbon atoms — simple heuristic)
    lines = [ln.strip() for ln in stdout.splitlines() if ln.strip()]
    return len(lines) > 0 and not lines[0].startswith("outlsd:")
```

For a hard fail-loud guarantee, optionally add RDKit validation:

```python
try:
    from rdkit import Chem
    first_line = lines[0].split()[0]
    return Chem.MolFromSmiles(first_line) is not None
except Exception:
    return False  # RDKit not available — fall through to string check
```

When `_invoke_outlsd` detects invalid output it should: return `None` (not write the garbage to `solutions.smi`) AND raise `RuntimeError` (or set a result flag) so the caller can report a loud failure instead of silent success.

### FIX-02: Deterministic Cross-Ring COSY Pair Algorithm

**The rule (verified against Arm A reference and para-substituted benzene topology):**

For a para-disubstituted benzene where the agent detects two groups of aromatic sp2 CH atoms:
- Group A: atom indices at shift X ppm (e.g., [4, 5] at 129.38 ppm)
- Group B: atom indices at shift Y ppm (e.g., [6, 7] at 127.26 ppm)

Cross-ring COSY pairs = `zip(sorted(group_A_ids), reversed(sorted(group_B_ids)))`

This gives `{(4, 7), (5, 6)}` which is the same pattern as Arm A (`COSY 4 7` + `COSY 5 6`).

**Why NOT `zip(sorted_A, sorted_B)` (adjacent)?**
In LSD's atom ordering, both atoms in Group A are labeled "atom 4" and "atom 5" (both at 129.38 ppm). These atoms ARE NOT adjacent to each other in the ring — they are both ortho to the SAME ipso carbon. Pairing them with each other (COSY 4 5) implies a 2-bond C-C bond path, but these two atoms are 4 bonds apart in the para-ring. That's why `COSY 4 5` causes LSD error 283 (valence violation) when ring BONDs are present.

**Why `zip(sorted_A, reversed(sorted_B))` is the correct cross-ring pattern:**
In the para-ring topology C2-C4-C6-C3-C7-C5-C2, atom 4 (ortho to C2) is 3J-coupled to atom 6 (ortho to C3) — that would be COSY 4 6. But Arm A uses COSY 4 7, not COSY 4 6. The key is that atom numbering within each group is arbitrary (both atoms 6 and 7 represent "the 127.26 ppm position"). Pairing with reversed order gives the same topological result and avoids any ambiguity: the two emitted COSY lines will both encode valid 3J cross-ring couplings regardless of which of the two equivalent atoms gets which index.

**Algorithm:**

```python
def detect_aromatic_cosy_pairs(
    groups: list[SignalGroup],
    aromatic_ch_shift_range: tuple[float, float] = (100.0, 165.0),
) -> list[tuple[int, int]]:
    """Derive cross-ring COSY equivalence pairs for aromatic CH groups.
    
    Given the GroupingResult from lucy analyze grouping, identifies groups
    of aromatic sp2 CH atoms and pairs them cross-ring (never within-group).
    
    Returns list of (atom1_id, atom2_id) COSY pairs to emit as COSY lines.
    
    Algorithm: for two groups A and B of equal size at different aromatic shifts,
    zip(sorted(A.atom_ids), reversed(sorted(B.atom_ids))). Verified by Arm A
    (.planning/phases/72-design-re-validation/experiment/arm_a.lsd → 2/2 aromatic solutions).
    """
    aromatic_groups = [
        g for g in groups
        if all(aromatic_ch_shift_range[0] <= s <= aromatic_ch_shift_range[1] for s in g.shifts)
        and all(
            m in (None, "CH", "CH/CH3") 
            for m in (g.multiplicities or [None] * len(g.shifts))
        )
    ]
    
    pairs: list[tuple[int, int]] = []
    # Pair groups of equal size (para-symmetric case)
    processed: set[int] = set()
    for i, group_a in enumerate(aromatic_groups):
        if i in processed:
            continue
        for j, group_b in enumerate(aromatic_groups[i+1:], start=i+1):
            if j in processed:
                continue
            if len(group_a.atom_ids) == len(group_b.atom_ids):
                a_ids = sorted(group_a.atom_ids)
                b_ids = list(reversed(sorted(group_b.atom_ids)))
                pairs.extend(zip(a_ids, b_ids))
                processed.add(i)
                processed.add(j)
                break
    return pairs
```

**Integration path:** Add `detect_aromatic_cosy_pairs()` to `lucy_ng/lsd/generator.py` (co-located with `LSDInputGenerator`). Expose via a new `lucy detect aromatic-cosy <shifts> --multiplicities <mults>` CLI subcommand in `lucy_ng/cli/detect.py`. The agent calls this CLI, gets the COSY pairs, and passes them to `LSDProblem.add_aromatic_equivalence_pair()` for each pair. The skill references the CLI command instead of describing the index-derivation rule.

### FIX-03: Skill Hygiene Scope

**Retire `lucy-case-agent.md`:** Neutralize the frontmatter `name: lucy-case-agent` so Claude never spawns it as an agent. Options:
1. Add `disabled: true` to frontmatter (if supported by Claude Code)
2. Rename to `lucy-case-agent.md.deprecated` (prevents name-matching)
3. Change `name:` to `name: lucy-case-agent-DEPRECATED` (explicit, searchable)

The blockquote retirement notice already exists at line 12. The stale `outlsd 5 < compound.sol` workflow in the body is a hazard; neutralizing the frontmatter removes the spawn risk.

**Targeted audit of 4 active files (not full rewrite):**

| File | Lines | Changes Needed |
|------|-------|----------------|
| `lucy-lsd-engineer.md` | 589 | (1) Lines 124-130: correct false "Phase 73 fix works" claim → "Phase 73 fix was incomplete; FIX-01 (Phase 77) corrects filter-file deployment"; (2) add reference to `lucy detect aromatic-cosy` CLI command; (3) update D-04 escalation wording to match D-77-01/D-77-06 (threshold N, logging requirement) |
| `case.md` | 593 | Verify emergent-ring guidance is prominent (not buried); add D-77-06 UAT criterion for Phase 78 handoff |
| `lucy-nmr-chemist.md` | 264 | Check for any stale COSY equivalence guidance that contradicts the new deterministic tool |
| `lucy-devils-advocate.md` | 583 | Verify G5-G8 gates still cover the fixed failure modes; update COSY equiv-pair check to reference `lucy detect aromatic-cosy` output |

**Archive note:** No formal archive directory exists under `~/.claude/agents/`. Frontmatter neutralization is the lowest-risk retirement method.

### Anti-Patterns to Avoid

- **Do NOT fix `_invoke_outlsd` by stripping the `.sol` header:** The variable-length header (equals the number of lines in the LSD input file) makes `tail -n +N` fragile. The real bug is missing filter files, not outlsd invocation. `_invoke_outlsd` with stdin already works correctly when given a real `.sol` file (verified: `outlsd 5 < arm_a.sol` produces correct SMILES).
- **Do NOT emit `COSY a a` (self-COSY):** The algorithm must ensure `atom1 != atom2` — deduplication via `sorted` vs `reversed(sorted)` prevents this only when groups have ≥ 2 members each.
- **Do NOT use RDKit-only validation in `_invoke_outlsd`:** RDKit may not be available in all environments. Use string heuristic first (fast), RDKit second (optional confirmation).
- **Do NOT change `LSDRunner.run()` (API path):** That path calls `LSDInputGenerator.write_file()` which already handles filter files. Only `run_file()` → `_execute_lsd()` is broken.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Ring filter file access | Custom file lookup / PATH search | `importlib.resources.files("lucy_ng.lsd.filters")` | Already used in `_write_filter_files()`; bundled files are the authoritative copy |
| Aromatic COSY emission | Ad-hoc index arithmetic in skill prose | `LSDProblem.add_aromatic_equivalence_pair()` + `detect_aromatic_cosy_pairs()` | Deduplication and COSY emission already implemented; only the pairing algorithm is new |
| SMILES validation | Custom parser | `rdkit.Chem.MolFromSmiles()` + string pre-check | RDKit already a project dependency; string pre-check handles the no-RDKit case |

---

## FIX-01: Confirmed Diagnosis

### Exact Bug Location

`src/lucy_ng/lsd/runner.py`, method `_execute_lsd()`, lines 243-256. [VERIFIED: src/lucy_ng/lsd/runner.py]

The method copies the `.lsd` file to `output_dir` (line 245) but has no corresponding copy of filter files. `LSDInputGenerator.write_file()` calls `_write_filter_files(output_path.parent)` after writing the file — `_execute_lsd` is the API-level bypass that skips this step.

### Exact Failure Path (live-reproduced on Phase 76 artifacts)

```bash
lucy lsd run \
  .planning/phases/76-milestone-uat-gate/uat-artifacts/case1/iteration_04-compound.lsd \
  -o /tmp/test_lucy_lsd_run
# Output: "LSD completed successfully. Solutions found: 1."
cat /tmp/test_lucy_lsd_run/solutions.smi
# Output: "outlsd: This is not a file for OUTLSD."
```

[VERIFIED: live reproduction 2026-06-01, runner.py code inspection + subprocess test]

### What the Test Suite Currently Misses

The Phase 73 regression tests in `TestLSDRunnerFixed` all use `tests/fixtures/regression/ibuprofen_no_4j.lsd` which has NO `DEFF F1/F2` ring exclusion lines. That's why all 6 Phase-73 tests pass even with the bug. The new FIX-01 regression test must use a fixture LSD file WITH ring exclusion (`DEFF F1 "ring3"` + `DEFF F2 "ring4"`) to expose the filter-file-copy gap.

### Existing Fixture Availability

The `.planning/phases/72-design-re-validation/experiment/arm_a.lsd` file has ring exclusion and is the Arm A reference (produces 2/2 aromatic solutions). It can be copied to `tests/fixtures/regression/arm_a_with_ring_excl.lsd` as the FIX-01 regression fixture. [VERIFIED: file present, produces correct solutions when run with ring3/ring4 present]

---

## FIX-02: Confirmed Diagnosis

### What the Phase 76 Agent Did Wrong

From `CASE-PROGRESS.md` iteration 1: agent emitted `COSY 4 5` + `COSY 6 7`. These are within-group pairs — both atoms 4 and 5 are at 129.38 ppm (same chemical shift group). When ring BONDs were later added (atoms 2-4, 4-6, 6-3, 3-7, 7-5, 5-2), the COSY 4 5 and COSY 6 7 caused `error 283` (implied bond between non-adjacent ring atoms), so they were removed. From iteration 2 onward, there were NO aromatic equivalence COSY constraints, and the ring was forced via 6 explicit BONDs.

### What Arm A (Reference) Did Correctly

From `arm_a.lsd` (produces 2/2 aromatic solutions without ring BONDs): `COSY 4 7` + `COSY 5 6`. These cross-ring pairs do NOT conflict with any ring topology because they encode the genuine 3J H-H coupling between non-equivalent aromatic CH groups. They provide aromatic topological pressure without triggering error 283. [VERIFIED: arm_a.lsd inspected, outlsd 5 < arm_a.sol produces ibuprofen SMILES]

### The Reversed-Order Pairing Rule

`zip(sorted([4, 5]), reversed(sorted([6, 7])))` = `[(4, 7), (5, 6)]` — exactly the Arm A COSY pairs. The reversed order ensures cross-pairing (groupA[0] with groupB[-1], groupA[1] with groupB[-2], etc.) rather than intra-pairing (groupA[0] with groupB[0] = COSY 4 6, which is also valid but not what Arm A uses). Both pairings are topologically valid for emergence; reversed order matches the reference and is therefore the recommended default. [VERIFIED: arm_a.lsd atom assignments + ring topology confirmed by direct inspection]

### Integration Point

`LSDProblem.add_aromatic_equivalence_pair(atom1_index, atom2_index)` in `models.py` already exists and emits `COSY atom1 atom2` with deduplication. The FIX-02 function only needs to call it in a loop with the derived pairs. [VERIFIED: src/lucy_ng/lsd/models.py lines 229-253]

---

## Common Pitfalls

### Pitfall 1: Assuming LSD return code indicates success
**What goes wrong:** `_execute_lsd` currently does NOT check `proc.returncode` for success. This is intentional: LSD-3.4.9 exits with code 1 even on a successful run that finds solutions (verified: `cd /tmp && lsd compound.lsd` outputs "1 solution found." to stderr but exits 1). Return code cannot be used for success detection.
**Why it happens:** LSD binary's exit code semantics are non-standard.
**How to avoid:** Success detection must use: (1) `.sol` file exists AND (2) `.sol` contains solution data (not just input echo) AND (3) `solutions.smi` contains valid SMILES.
**Warning signs:** Any test that gates on `result.return_code == 0` will incorrectly fail for all LSD runs.

### Pitfall 2: Variable-length .sol header makes tail-stripping fragile
**What goes wrong:** The `.sol` file header = `1 (# From file: ...) + N (LSD input echo) + 1 (#)` lines, where N is the number of lines in the input LSD file. N varies with problem size (arm_a.lsd: N=56; ibuprofen_no_4j.lsd: N=103; iteration_04-compound.lsd: N=139). Using `tail -n +10` is wrong for all but the shortest inputs.
**Why it happens:** LSD echoes the entire input file before the `#` separator. The solution data begins after the first standalone `#` line.
**How to avoid:** The correct invocation is `outlsd 5 < compound.sol` (full stdin). outlsd knows how to skip its own echo header. Do NOT try to strip the header before passing to outlsd.

### Pitfall 3: COSY within-group triggers error 283 when ring BONDs are present
**What goes wrong:** `COSY 4 5` (both atoms in group at 129.38 ppm, both ortho to C2) conflicts with the para-ring bond topology when `BOND 2 4` + `BOND 5 2` are present. LSD error 283 = "valence constraint violated by COSY N M".
**Why it happens:** COSY N M implies C-N and C-M are adjacent (3J coupling), but atoms 4 and 5 are NOT adjacent in the para ring — they are 4 bonds apart (C4-C2-C5 has no direct C4-C5 bond).
**How to avoid:** Always use cross-group COSY (group A atom ↔ group B atom). The `detect_aromatic_cosy_pairs()` function guarantees cross-group pairing.

### Pitfall 4: FIX-01 regression test must use a ring-exclusion LSD file
**What goes wrong:** Existing Phase-73 regression tests use `ibuprofen_no_4j.lsd` which has NO `DEFF F1/F2`. The test passes even with the filter-file-copy bug present.
**Why it happens:** A test that doesn't exercise the code path being fixed cannot catch regressions.
**How to avoid:** Add `arm_a_with_ring_excl.lsd` (or equivalent) as a fixture. This is the arm_a.lsd file from `.planning/phases/72-design-re-validation/experiment/arm_a.lsd`.

### Pitfall 5: orchestrator.py has its own `_run_outlsd` but it delegates correctly
**What goes wrong:** `orchestrator.py._run_outlsd()` at line 255 calls `_invoke_outlsd()` from `runner.py` (the shared helper, unified in Phase 73). It does NOT copy ring filter files either.
**Why it matters:** The orchestrator path (permutation fallback) has the same bug if permutation LSD files contain `DEFF F` references.
**How to avoid:** The FIX-01A fix (copy ring files in `_execute_lsd`) also covers the orchestrator path because `orchestrator.py` calls `self.runner.run_file()` which calls `_execute_lsd()`. No separate fix needed in orchestrator.

---

## Code Examples

### Filter File Copy (FIX-01A pattern — matches existing write_file behavior)

```python
# In LSDRunner._execute_lsd(), after shutil.copy2(input_file, dest):
# Copy bundled ring filter files so DEFF F1 "ring3" / DEFF F2 "ring4" resolve.
# This mirrors what LSDInputGenerator.write_file() does via _write_filter_files().
# Safe to call unconditionally: if ring3/ring4 already exist in output_dir,
# they are overwritten with the same content (idempotent).
LSDInputGenerator._write_filter_files(output_dir)
```
[VERIFIED: src/lucy_ng/lsd/generator.py _write_filter_files() exists and is importlib.resources-based]

### Fail-Loud _invoke_outlsd (FIX-01B)

```python
def _invoke_outlsd(
    outlsd_path: Path, sol_file: Path, output_dir: Path
) -> "Path | None":
    """Convert .sol to SMILES via outlsd. Raises RuntimeError on invalid output."""
    smiles_file = output_dir / "solutions.smi"
    try:
        with sol_file.open("r") as fh:
            proc = subprocess.run(
                [str(outlsd_path), "5"],
                stdin=fh,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=output_dir,
            )
        stdout = proc.stdout.strip()
        # Fail-loud: detect known error patterns and empty/non-SMILES output
        if not stdout:
            raise RuntimeError("outlsd produced no output — .sol file may be incomplete")
        if "This is not a file for OUTLSD" in stdout:
            raise RuntimeError(
                f"outlsd rejected .sol file: {stdout[:200]!r}. "
                "Likely cause: ring3/ring4 filter files missing from output_dir, "
                "causing LSD to produce a partial .sol (input echo only)."
            )
        if stdout.startswith("outlsd:"):
            raise RuntimeError(f"outlsd error: {stdout[:200]!r}")
        # Output looks like SMILES — write it
        smiles_file.write_text(proc.stdout)
        return smiles_file
    except RuntimeError:
        raise  # Re-raise fail-loud errors
    except Exception:
        return None  # Other errors (file not found, timeout) → None
```
[ASSUMED — recommended design for discussion; the exact error strings need confirmation against other outlsd failure modes]

### detect_aromatic_cosy_pairs() (FIX-02)

```python
# In src/lucy_ng/lsd/generator.py (alongside LSDInputGenerator)

def detect_aromatic_cosy_pairs(
    groups: list["SignalGroup"],
    aromatic_range: tuple[float, float] = (100.0, 165.0),
) -> list[tuple[int, int]]:
    """Derive cross-ring COSY equivalence pairs for aromatic CH groups.
    
    Given groups from lucy_ng.detection.grouping.group_signals(), identifies
    pairs of groups where all shifts are in the aromatic range, and emits
    cross-ring COSY pairs using the reversed-pairing algorithm.
    
    Verified reference: arm_a.lsd (.planning/phases/72-design-re-validation/)
    produces COSY 4 7 + COSY 5 6 → 2/2 aromatic solutions, ibuprofen present.
    
    Algorithm: zip(sorted(groupA.atom_ids), reversed(sorted(groupB.atom_ids)))
    This produces cross-group pairing, not within-group pairing.
    Within-group COSY (e.g., COSY 4 5 where 4,5 are both at 129.38 ppm) causes
    LSD error 283 when ring BONDs are present.
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
[VERIFIED: algorithm confirmed against arm_a.lsd atom numbering and GroupingResult.atom_ids (1-based)]

### FIX-01 Regression Test Fixture (new, ring-exclusion LSD)

The file `.planning/phases/72-design-re-validation/experiment/arm_a.lsd` is the ideal regression fixture:
- Has `DEFF F1 "ring3"` + `DEFF F2 "ring4"` (exercises the filter-file-copy fix)
- Produces 2 known solutions (both aromatic, including ibuprofen) when run correctly
- Has `COSY 4 7` + `COSY 5 6` (serves as reference for FIX-02 validation)

[VERIFIED: file present at `.planning/phases/72-design-re-validation/experiment/arm_a.lsd`, arm_a.sol confirms 2 solutions]

---

## State of the Art (v9.0 context)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|-----------------|--------------|--------|
| Direct `lsd` binary invocation with `outlsd 5 < file.sol` | `lucy lsd run <file.lsd>` (single-command) | Phase 73 | Encapsulates the full pipeline; agent uses only `lucy lsd run` |
| SYME/DEFF NOT in LSD files | BOND/COSY for equivalence, DEFF F/FEXP for ring exclusion | Phase 74 | LSD-3.4.9 native commands; no translation layer bypasses |
| `COSY 4 5` + `COSY 6 7` (within-group) | `COSY 4 7` + `COSY 5 6` (cross-ring) | D-77-02 (Phase 77) | Prevents error 283 AND provides aromatic emergence pressure |
| Skill prose describing atom index derivation | `lucy detect aromatic-cosy` CLI tool | Phase 77 | Agent calls tool rather than hand-deriving indices |

**Deprecated/outdated:**
- `outlsd 5 < compound.sol > solutions.smi` as a manual agent command — replaced by `lucy lsd run` (Phase 73). Still present in `lucy-case-agent.md` (deprecated) and the body of `lucy-lsd-engineer.md` (incorrect claim at lines 124-130 to be corrected in FIX-03).
- `SYME` and `DEFF NOT` commands in LSD files — replaced by BOND/COSY/DEFF F/FEXP (Phase 74). Should never appear in emitted files.

---

## Runtime State Inventory

> Not applicable — this is a code/skill fix phase, not a rename/refactor/migration phase. No runtime state (databases, OS registrations, deployed configs) is affected.

**Nothing found in category:** None — verified by phase scope review.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| LSD binary | FIX-01 integration tests | ✓ | 3.4.9 (`/Users/steinbeck/Dropbox/develop/LSD/lsd`) | Tests skipif-gated: `@pytest.mark.skipif(shutil.which("LSD") is None, ...)` |
| outlsd binary | FIX-01 integration tests | ✓ | 3.4.9 (`/Users/steinbeck/Dropbox/develop/LSD/outlsd`) | Same skipif gate |
| rdkit | FIX-01 fail-loud validation | ✓ | Available in project environment | String pre-check (no rdkit required for basic validation) |
| Python 3.10+ | All code | ✓ | 3.12.2 | — |
| pytest | Tests | ✓ | 9.0.2 | — |

**Missing dependencies with no fallback:** None.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` |
| Quick run command | `pytest tests/test_lsd_runner.py tests/test_lsd_generator.py tests/test_signal_grouping.py -q` |
| Full suite command | `pytest tests/ --ignore=tests/case-benchmark -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FIX-01 | `lucy lsd run` with ring-exclusion LSD produces valid SMILES | integration | `pytest tests/test_lsd_runner.py::TestLSDRunnerFixed::test_ring_exclusion_lsd_produces_smiles -x` | ❌ Wave 0 |
| FIX-01 | `_invoke_outlsd` raises RuntimeError on "not a file for OUTLSD" output | unit | `pytest tests/test_lsd_runner.py::TestInvokeOutlsd::test_fail_loud_on_error_string -x` | ❌ Wave 0 |
| FIX-01 | `_invoke_outlsd` raises RuntimeError on empty output | unit | `pytest tests/test_lsd_runner.py::TestInvokeOutlsd::test_fail_loud_on_empty_output -x` | ❌ Wave 0 |
| FIX-01 | Existing Phase-73 tests still pass after fix | regression | `pytest tests/test_lsd_runner.py::TestLSDRunnerFixed -q` | ✅ existing |
| FIX-02 | `detect_aromatic_cosy_pairs()` returns [(4,7),(5,6)] for ibuprofen groups | unit | `pytest tests/test_lsd_generator.py::TestDetectAromaticCosyPairs -q` | ❌ Wave 0 |
| FIX-02 | `detect_aromatic_cosy_pairs()` handles single group (no pairs) | unit | `pytest tests/test_lsd_generator.py::TestDetectAromaticCosyPairs::test_single_group_no_pairs -q` | ❌ Wave 0 |
| FIX-03 | No active workflow references `lucy-case-agent` | audit | `grep -r "lucy-case-agent" ~/.claude/commands/ ~/.claude/agents/lucy-*.md` | manual |

### Existing Tests That Must Remain Green

- `tests/test_lsd_runner.py::TestLSDRunnerFixed` — all 6 Phase-73 regression tests
- `tests/test_lsd_models.py` — `add_aromatic_equivalence_pair()` tests
- `tests/test_signal_grouping.py` — `group_signals()` tests (FIX-02 helper depends on these)
- `tests/test_lsd_generator.py` — generator tests (FIX-02 adds to this file)

### Sampling Rate

- Per task commit: `pytest tests/test_lsd_runner.py tests/test_lsd_generator.py tests/test_signal_grouping.py -q --tb=short`
- Per wave merge: `pytest tests/ --ignore=tests/case-benchmark -q --tb=short`
- Phase gate: Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_lsd_runner.py::TestInvokeOutlsd` — new test class for fail-loud unit tests (FIX-01)
- [ ] `tests/test_lsd_runner.py::TestLSDRunnerFixed::test_ring_exclusion_lsd_produces_smiles` — integration test with ring-exclusion fixture (FIX-01)
- [ ] `tests/fixtures/regression/arm_a_ring_excl.lsd` — ring-exclusion fixture (copy of arm_a.lsd)
- [ ] `tests/test_lsd_generator.py::TestDetectAromaticCosyPairs` — unit tests for FIX-02 algorithm

---

## Open Questions

1. **FIX-01B: Should `_invoke_outlsd` raise or return None on bad output?**
   - What we know: Returning `None` makes `smiles_path is None`, which triggers `success = False`. Raising `RuntimeError` propagates up through `_execute_lsd` and is caught by the generic `except Exception` (returns `LSDResult(success=False, stderr=str(e))`).
   - What's unclear: The current `except Exception: pass; return None` in `_invoke_outlsd` swallows errors silently. Raising is louder but changes the contract.
   - Recommendation: Raise `RuntimeError` for the known error string (certain failure); return `None` for unknown failures (conservative). The generic exception handler in `_execute_lsd` converts it to a non-success result with the error in `stderr`.

2. **FIX-02: Should `detect_aromatic_cosy_pairs()` be a CLI subcommand or a pure library function?**
   - What we know: D-77-02 says "CLI/generator helper". `LSDProblem.add_aromatic_equivalence_pair()` is already a library function. The agent uses CLI commands.
   - What's unclear: Whether a new CLI subcommand `lucy detect aromatic-cosy` is worth the plumbing vs. embedding in the library and documenting for direct Python use.
   - Recommendation (Claude's Discretion): Add as a pure library function in `generator.py` first; add the CLI subcommand `lucy detect aromatic-cosy <shifts> --multiplicities <mults> [--atom-indices <indices>]` as a thin wrapper. The agent uses the CLI; `LSDInputGenerator.from_peak_data()` uses the library function.

3. **FIX-01: Should ring filter files always be copied (unconditional) or only when DEFF is present?**
   - What we know: `_write_filter_files()` is always called by `write_file()`, unconditionally. The filter files are small (134 B + 168 B). Writing them idempotently is harmless.
   - Recommendation: Unconditional copy (matches `write_file()` behavior, no DEFF-parsing complexity).

4. **FIX-03: Retirement of `lucy-case-agent.md` — rename vs. frontmatter neutralization?**
   - What we know: No active workflow spawns it. The blockquote header already says DEPRECATED.
   - Recommendation: Change `name: lucy-case-agent` to `name: DEPRECATED-lucy-case-agent` in frontmatter. This is searchable, reversible, and prevents accidental spawning without removing historical record.

---

## Security Domain

> Security enforcement is not a primary concern for this phase. The changes are: (1) file copy operations within the project directory, (2) subprocess invocation of already-trusted LSD/outlsd binaries, (3) string validation of subprocess stdout, (4) skill text file edits. No new attack surfaces are introduced.

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V5 Input Validation | marginal | `_invoke_outlsd` fail-loud check validates outlsd stdout before writing to disk |
| Subprocess injection | no | outlsd path is resolved via `shutil.which()` (existing pattern); no user-controlled arguments |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `_invoke_outlsd` fail-loud predicate covers all outlsd error modes beyond "This is not a file for OUTLSD." | FIX-01B Code Example | Unknown error modes slip through as false successes. Mitigation: the string heuristic `if stdout.startswith("outlsd:")` catches any outlsd-prefixed error message. |
| A2 | `detect_aromatic_cosy_pairs()` — reversed-order pairing is correct for all para-disubstituted aromatics, not just ibuprofen | FIX-02 Algorithm | For compounds with more complex aromatic symmetry (e.g., 3 equivalent CH positions), the pairing logic needs extension. Mitigation: Phase 77 scope is ibuprofen + CASE9 (both para-disubstituted benzene). |
| A3 | The `disabled: true` frontmatter key neutralizes agent spawning in Claude Code | FIX-03 | If not supported, `lucy-case-agent` could still be spawned. Mitigation: use `name: DEPRECATED-lucy-case-agent` instead (name-based prevention). |

**All other claims are VERIFIED by direct code/artifact inspection.**

---

## Sources

### Primary (HIGH confidence)
- `src/lucy_ng/lsd/runner.py` — `_execute_lsd()`, `_invoke_outlsd()`, `_run_outlsd()` — code inspection + live reproduction [VERIFIED]
- `src/lucy_ng/lsd/orchestrator.py` — `PyLSDOrchestrator._run_outlsd()` — code inspection [VERIFIED]
- `src/lucy_ng/lsd/generator.py` — `_write_filter_files()`, `write_file()` — code inspection [VERIFIED]
- `src/lucy_ng/lsd/models.py` — `LSDProblem.add_aromatic_equivalence_pair()` — code inspection [VERIFIED]
- `src/lucy_ng/detection/grouping.py` — `group_signals()`, `SignalGroup.atom_ids` — code inspection [VERIFIED]
- `.planning/phases/72-design-re-validation/experiment/arm_a.lsd` — reference COSY 4 7 + COSY 5 6, 2/2 aromatic — file inspection [VERIFIED]
- `.planning/phases/72-design-re-validation/experiment/arm_a.sol` — solution data structure, outlsd verification — file inspection + live test [VERIFIED]
- `.planning/phases/76-milestone-uat-gate/uat-artifacts/case1/` — Phase 76 failure artifacts (iteration_04 LSD, CASE-PROGRESS.md, solutions.smi) — file inspection [VERIFIED]
- `.planning/phases/72-design-re-validation/72-DECISIONS.md` — D-01..D-04, Arm A results — document inspection [VERIFIED]
- `.planning/phases/76-milestone-uat-gate/VERIFICATION.md` — FAILED verdict, three blocking defects — document inspection [VERIFIED]
- `~/.claude/agents/lucy-lsd-engineer.md` — false Phase-73 claim at lines 124-130, COSY 4 7 + 5 6 examples — file inspection [VERIFIED]
- `~/.claude/agents/lucy-case-agent.md` — deprecated 1291-line file with active frontmatter — file inspection [VERIFIED]
- `tests/test_lsd_runner.py` — Phase-73 regression tests, TestLSDRunnerFixed pattern — code inspection + live test run (141 passed) [VERIFIED]

### Secondary (MEDIUM confidence)
- Live reproduction of FIX-01 bug using Phase 76 CASE1 LSD file in `/tmp/test_lucy_lsd_run/` — matched CASE-PROGRESS.md description exactly [VERIFIED by execution]
- Live confirmation that `outlsd 5 < arm_a.sol` produces correct ibuprofen SMILES — filter files not needed for stdin invocation [VERIFIED by execution]
- LSD exit code = 1 on success confirmed by running `/Users/steinbeck/Dropbox/develop/LSD/lsd` in test directory [VERIFIED by execution]

---

## Metadata

**Confidence breakdown:**
- FIX-01 diagnosis and fix: HIGH — root cause confirmed by live reproduction; fix is a 1-line addition matching the existing `write_file()` pattern
- FIX-01 fail-loud predicate: MEDIUM — known error string confirmed; unknown error modes tagged [ASSUMED]
- FIX-02 algorithm: HIGH — reversed-pairing rule confirmed by Arm A reference and para-ring topology analysis
- FIX-02 CLI integration: HIGH — `add_aromatic_equivalence_pair()` integration point confirmed in models.py
- FIX-03 skill audit scope: HIGH — file sizes confirmed, false claim location confirmed, no active workflow spawns the deprecated file

**Research date:** 2026-06-01
**Valid until:** This research is tightly coupled to specific code versions; run `pytest tests/test_lsd_runner.py -q` before planning to confirm test status has not changed.
