---
phase: "75"
plan: "04"
slug: python-schema-followups
type: execute
wave: 2
depends_on: ["75-01"]
files_modified:
  - src/lucy_ng/cli/fragment.py
  - tests/test_lsd_formatter.py
  - ~/.claude/agents/lucy-lsd-engineer.md
autonomous: true
requirements: [SKILL-01]

must_haves:
  truths:
    - "lucy fragment to-lsd accepts --filter-index N option (default 3)"
    - "lucy fragment to-lsd --filter-index 3 emits DEFF F3 and FEXP \"F3\" (not F1)"
    - "lucy fragment to-lsd --filter-index 1 emits DEFF F1 and FEXP \"F1\" (backward compat)"
    - "schema constraint_inventory_v2.json uses additionalProperties: true (no change needed — confirmed)"
    - "pytest -x -q green after changes"
    - "lsd-engineer.md fragment zero-solution fallback line 172 removes DEFF Fn (not DEFF F1 hard-coded)"
    - "lsd-engineer.md fragment CLI example uses --filter-index 3"
  artifacts:
    - path: src/lucy_ng/cli/fragment.py
      provides: "Updated to-lsd CLI with configurable filter index"
      exports: ["to_lsd command with --filter-index option"]
    - path: tests/test_lsd_formatter.py
      provides: "Tests for filter-index 3 output"
      contains: "filter_index.*3\|F3.*fragment"
  key_links:
    - from: "lucy fragment to-lsd --filter-index 3"
      to: "lsd-engineer.md F-number reservation rule"
      via: "CASE agent must pass --filter-index 3 when ring exclusion active"
      pattern: "DEFF F3"
---

<objective>
Close the DEFF F numbering conflict identified in research open question 1. The `lucy fragment to-lsd` CLI currently hardcodes F1 for the goodlist fragment. Ring exclusion (added in Phase 74) uses F1 and F2. When both are active in the same LSD file, the F1 collision makes LSD try to use the ring3 filter as a fragment (or vice versa) — wrong behavior.

Fix: add a `--filter-index N` option to `to-lsd` (default 3, reserved for fragment goodlist when ring exclusion is active). Also confirm the JSON schema already uses `additionalProperties: true` (confirmed — no schema change needed).

Purpose: The skill instruction in lsd-engineer.md (plan 75-01) now tells the agent "F1/F2 = ring exclusion, F3+ = fragment goodlist." The CLI must produce F3 by default to match that instruction.

Output: Updated CLI, updated tests, pytest green.
</objective>

<execution_context>
@/Users/steinbeck/.claude/get-shit-done/workflows/execute-plan.md
@/Users/steinbeck/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/PROJECT.md
@/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/phases/75-skill-consolidation/75-RESEARCH.md
@/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/phases/75-skill-consolidation/75-01-SUMMARY.md
</context>

<interfaces>
From src/lucy_ng/cli/fragment.py (current to-lsd command):

```python
@fragment.command("to-lsd")
@click.argument("smiles", type=str)
@click.option("--output-dir", type=click.Path(path_type=Path), default=None)
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="json")
def to_lsd(smiles: str, output_dir: Path | None, output_format: str) -> None:
    ...
    deff_cmd = DEFFFormatter.deff_command(1, written_path.name)   # hardcoded 1 → must become configurable
    fexp_cmd = DEFFFormatter.fexp_command([1])                     # hardcoded [1] → must become configurable
```

From src/lucy_ng/fragments/lsd_formatter.py:

```python
@staticmethod
def deff_command(fragment_number: int, filepath: str) -> str:
    return f'DEFF F{fragment_number} "{filepath}"'

@staticmethod
def fexp_command(fragment_numbers: list[int], logic: str = "OR") -> str:
    ...
```

The `DEFFFormatter.deff_command` and `fexp_command` already accept arbitrary fragment numbers — the fix is purely in the CLI (pass 3 instead of 1 as default).

Schema at schemas/constraint_inventory_v2.json line 21:
```json
"additionalProperties": true,
```
No schema change needed — the new `ring_exclusion_enabled` field is accepted automatically.
</interfaces>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Add --filter-index option to lucy fragment to-lsd, update tests</name>
  <files>src/lucy_ng/cli/fragment.py
tests/test_lsd_formatter.py</files>
  <behavior>
    - Test 1: `lucy fragment to-lsd "CCO"` → JSON output contains `deff_command: 'DEFF F3 "fragment_..."'` and `fexp_command: 'FEXP "F3"'` (default is 3)
    - Test 2: `lucy fragment to-lsd "CCO" --filter-index 1` → `deff_command: 'DEFF F1 "fragment_..."'` (explicit override for backward compat)
    - Test 3: `lucy fragment to-lsd "CCO" --filter-index 5` → `deff_command: 'DEFF F5 "fragment_..."'` and `fexp_command: 'FEXP "F5"'`
    - Test 4: existing tests that assert F1 output by default must be updated to expect F3 (or pass --filter-index 1 explicitly)
  </behavior>
  <action>
Read src/lucy_ng/cli/fragment.py fully. Then make these changes:

**Change 1: Add --filter-index option to the to_lsd command**

In the `to_lsd` function, add a new click option after `--format`:

```python
@click.option(
    "--filter-index",
    "filter_index",
    type=int,
    default=3,
    show_default=True,
    help=(
        "DEFF filter index for the goodlist fragment (default 3). "
        "F1 and F2 are reserved for ring exclusion (DEFF F1 ring3, DEFF F2 ring4). "
        "Use 3 or higher when ring exclusion is active (Phase 75 convention). "
        "Use --filter-index 1 only when ring exclusion is not active (backward compat)."
    ),
)
```

Also add `filter_index: int` to the function signature.

**Change 2: Use filter_index in deff_cmd and fexp_cmd generation**

Replace the two hardcoded lines:
```python
deff_cmd = DEFFFormatter.deff_command(1, written_path.name)
fexp_cmd = DEFFFormatter.fexp_command([1])
```

With:
```python
deff_cmd = DEFFFormatter.deff_command(filter_index, written_path.name)
fexp_cmd = DEFFFormatter.fexp_command([filter_index])
```

**Change 3: Also update the fragment search multi-result output (line 186)**

The `fragment search` command builds DEFF commands for multiple matches:
```python
deff_commands = [
    f'DEFF F{i + 1} "fragment_{i + 1}.lsd"' for i in range(len(matches))
```

This generates F1, F2, ... for multiple fragment results. Since the CASE agent always uses `--top 1`, only the single-fragment path matters for correctness. However, for consistency, if the lsd-engineer wants a non-conflicting search result it should also start at F3. But this would be a breaking change to multi-fragment output (a deferred/future feature). For Phase 75: leave the `fragment search` output unchanged — it is not used by CASE (only `to-lsd` is). Add a comment:
```python
# NOTE: Multi-fragment output uses F1..Fn. For CASE workflow, use lucy fragment to-lsd
# with --filter-index 3 (reserves F1/F2 for ring exclusion per Phase 75 convention).
```

**Change 4: Update existing tests in test_lsd_formatter.py**

Read tests/test_lsd_formatter.py. Find any test that calls `lucy fragment to-lsd` or tests the CLI output of `to-lsd` and asserts `DEFF F1`. There are likely integration test calls using `CliRunner`. Update those tests to either:
  (a) Pass `--filter-index 1` explicitly to preserve old F1 assertion (backward compat test), OR
  (b) Update the assertion to expect F3 (correct new default)

Use approach (a) for tests that say "backward compat" and approach (b) for any test labelled as "default output."

Add two new tests to test_lsd_formatter.py (or a new test function in that file):

```python
def test_to_lsd_default_filter_index_is_3(runner):
    """Default --filter-index is 3 (reserves F1/F2 for ring exclusion)."""
    result = runner.invoke(fragment, ["to-lsd", "CCO"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "DEFF F3" in data["deff_command"]
    assert data["fexp_command"] == 'FEXP "F3"'

def test_to_lsd_explicit_filter_index_1(runner):
    """Explicit --filter-index 1 allows backward compat."""
    result = runner.invoke(fragment, ["to-lsd", "CCO", "--filter-index", "1"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "DEFF F1" in data["deff_command"]
    assert data["fexp_command"] == 'FEXP "F1"'
```

Also verify and update existing test at line 258 and 303 (which call `DEFFFormatter.deff_command(1, ...)` directly — those test the formatter, not the CLI, so they are fine unchanged). Only CLI invocation tests via CliRunner need updating.

**Also: add a note to lsd-engineer.md Fragment Goodlist section** (in src/ not ~/.claude/ — but actually lsd-engineer.md is in ~/.claude/, not src/). The skill instruction was already updated in plan 75-01's Edit G to say "DEFF NOT which goes after correlations" → "ring-exclusion DEFF F / FEXP which also goes after correlations." Now additionally ensure the Fragment Goodlist section in lsd-engineer.md mentions `--filter-index 3`. Edit ~/.claude/agents/lucy-lsd-engineer.md: find the `lucy fragment to-lsd` CLI example and add `--filter-index 3`:

Old text (exact):
```
lucy fragment to-lsd "<smiles>" --output-dir analysis/iteration_NN/ --format json
```

New text:
```
lucy fragment to-lsd "<smiles>" --output-dir analysis/iteration_NN/ --filter-index 3 --format json
```

Also update the `deff_command` output field description below it if it says `DEFF F1`:

Find in Fragment Goodlist section:
```
- `deff_command`: the DEFF F1 command string to insert in compound.lsd
```

New text:
```
- `deff_command`: the DEFF F3 command string to insert in compound.lsd (F3 because F1/F2 are reserved for ring exclusion)
```

**BLOCKER 2 + WARNING 5 fixes: Update ALL remaining fragment F1 references in lsd-engineer.md**

The following edits fix the 7 remaining `DEFF F1` (fragment goodlist context) references in ~/.claude/agents/lucy-lsd-engineer.md. Ring-exclusion F1/F2 references are LEFT UNCHANGED — those are correct. Fragment goodlist references change from F1 → F3.

Read the current lsd-engineer.md, then apply these edits in order:

**lsd-engineer Edit 1 — Line 169: Fragment persistence rule (WARNING 5 — "same as DEFF NOT" stale)**

Old text (exact):
```
**Fragment persistence rule:** Carry DEFF F1/FEXP forward across iterations, same as DEFF NOT. Read from previous LSD file, never reconstruct.
```

New text:
```
**Fragment persistence rule:** Carry the fragment DEFF F3/FEXP forward across iterations (read from previous LSD file, never reconstruct), same as the ring-exclusion DEFF F1/F2/FEXP.
```

**lsd-engineer Edit 2 — Line 172: Zero-solution fallback (OPERATIONAL BUG — removes wrong line)**

Old text (exact):
```
1. Remove DEFF F1 and FEXP lines from the LSD file
```

New text:
```
1. Remove the fragment DEFF Fn and FEXP lines from the LSD file (Fn = the fragment goodlist filter, F3 by default — check the `deff_command` field in the inventory for the actual filter index; do NOT remove the ring-exclusion DEFF F1/F2 lines)
```

**lsd-engineer Edit 3 — Line 194: Manual checklist item 10**

Old text (exact):
```
10. If fragment applied: DEFF F1/FEXP present after inventory block but before first MULT, fragment .lsd file exists in iteration dir
```

New text:
```
10. If fragment applied: DEFF F3/FEXP present after inventory block but before first MULT, fragment .lsd file exists in iteration dir (F3 = fragment goodlist; F1/F2 = ring exclusion — distinct namespaces)
```

**lsd-engineer Edit 4 — Line 418 area: inventory JSON example deff_command field**

Old text (exact):
```
;     "deff_command": "DEFF F1 "fragment_abc123def456.lsd"",
```

New text:
```
;     "deff_command": "DEFF F3 "fragment_abc123def456.lsd"",
```

**lsd-engineer Edit 5 — Line 433 area: raw LSD example line after inventory block**

Old text (exact):
```
DEFF F1 "fragment_abc123def456.lsd"
FEXP "F1"
```

New text:
```
DEFF F3 "fragment_abc123def456.lsd"
FEXP "F3"
```

**lsd-engineer Edit 6 — Line 453: Initialization Procedure DEFF F1/FEXP placement note**

Old text (exact):
```
      - DEFF F1/FEXP lines go after inventory block, before first MULT
```

New text:
```
      - DEFF F3/FEXP lines go after inventory block, before first MULT (F3 = fragment goodlist, reserved above ring-exclusion F1/F2)
```

**lsd-engineer Edit 7 — Line 474: Update Procedure DEFF F1/FEXP carry-forward**

Old text (exact):
```
   - Copy deff_fexp from previous inventory. If previous status was "applied", carry forward DEFF F1/FEXP lines. Re-run fragment search for logging. If previous was "discarded", keep "discarded" status.
```

New text:
```
   - Copy deff_fexp from previous inventory. If previous status was "applied", carry forward DEFF F3/FEXP lines (check `deff_command` in the inventory for the actual Fn index). Re-run fragment search for logging. If previous was "discarded", keep "discarded" status.
```

**lsd-engineer Edit 8 — Line 519: Workflow step 6 DEFF F1/FEXP fragment placement**

Old text (exact):
```
6. Build/update LSD file: inventory block first (initialized or updated per Section 5C/5D), then DEFF F1/FEXP (if fragment applied), then MULT defs, HSQC, HMBC batch, BOND/LIST/PROP, DEFF F1+F2/FEXP ring exclusion
```

New text:
```
6. Build/update LSD file: inventory block first (initialized or updated per Section 5C/5D), then DEFF F3/FEXP (if fragment applied), then MULT defs, HSQC, HMBC batch, BOND/LIST/PROP, DEFF F1+F2/FEXP ring exclusion
```

Note: Edit 8 is applied AFTER Plan 75-01 Task 2 Edit N has already changed "DEFF NOT" → "DEFF F1+F2/FEXP ring exclusion" on that line. Verify the current text before applying — if Plan 75-01 ran first, use the post-75-01 version as the old text.

**Also update must_haves artifacts entry for lsd-engineer.md** (this plan already declares it as files_modified via 75-01 SUMMARY dependency — no frontmatter change needed since lsd-engineer.md is already listed in 75-01's files_modified and 75-04 adds skill edits to the same file).
  </action>
  <verify>
    <automated>
pytest tests/test_lsd_formatter.py -x -q -k "filter_index or to_lsd" 2>&1 | tail -20
# New tests must pass

cd /Users/steinbeck/Dropbox/develop/lucy-ng && pytest -x -q 2>&1 | tail -10
# Full suite must pass (regression check)

# CLI smoke test
cd /Users/steinbeck/Dropbox/develop/lucy-ng && python -m lucy_ng.cli.main fragment to-lsd "CCO" 2>/dev/null | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(d['deff_command'])"
# Must print: DEFF F3 "fragment_..."

# lsd-engineer.md skill edits: Blocker 2 + Warning 5
# Operational fallback no longer hard-codes F1 (line 172 fix)
grep -n "Remove the fragment DEFF Fn" ~/.claude/agents/lucy-lsd-engineer.md
# Must return >= 1 line

# Fragment persistence rule updated (Warning 5 / line 169 fix)
grep -n "same as the ring-exclusion DEFF F1/F2" ~/.claude/agents/lucy-lsd-engineer.md
# Must return >= 1 line

# No hard-coded "carry forward DEFF F1/FEXP" in fragment context
grep -n "carry forward DEFF F1/FEXP" ~/.claude/agents/lucy-lsd-engineer.md || echo "0 - good"
# Must return 0
    </automated>
  </verify>
  <done>
lucy fragment to-lsd emits DEFF F3 / FEXP "F3" by default. --filter-index 1 override works for backward compat. pytest suite green. lsd-engineer.md Fragment Goodlist CLI example uses --filter-index 3. Operational fallback (line 172) removes DEFF Fn not hard-coded F1. Fragment persistence rule (line 169) references ring-exclusion F1/F2 correctly. Schema check confirms no action needed (additionalProperties: true).
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| CLI --filter-index default change | Default changes from 1 to 3 — any existing script calling to-lsd without --filter-index will get F3 (behavior change) |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-75-04-01 | Tampering | Default index change breaks existing to-lsd callers outside CASE agent | accept | Phase 74 introduced the feature; no production use established yet; F3 default matches new convention |
| T-75-04-02 | Elevation of Privilege | Wrong filter index causes LSD to apply wrong fragment as ring exclusion | mitigate | Convention documented in --help text: "F1 and F2 reserved for ring exclusion"; lsd-engineer.md skill enforces it |
| T-75-SC | Tampering | npm/pip/cargo installs | accept | No new packages installed in this plan |
</threat_model>

<verification>
```bash
cd /Users/steinbeck/Dropbox/develop/lucy-ng

# New CLI behavior
python -m lucy_ng.cli.main fragment to-lsd "CCO" --format json 2>/dev/null | \
  python3 -c "import sys,json; d=json.loads(sys.stdin.read()); assert 'F3' in d['deff_command'], d['deff_command']; print('PASS: default F3')"

python -m lucy_ng.cli.main fragment to-lsd "CCO" --filter-index 1 --format json 2>/dev/null | \
  python3 -c "import sys,json; d=json.loads(sys.stdin.read()); assert 'F1' in d['deff_command'], d['deff_command']; print('PASS: explicit F1')"

# Full test suite
pytest -x -q 2>&1 | tail -5

# Schema: no action needed — verify additionalProperties: true
python3 -c "import json; s=json.load(open('schemas/constraint_inventory_v2.json')); assert s['additionalProperties'] == True; print('PASS: schema accepts new fields')"
```
</verification>

<success_criteria>
1. `lucy fragment to-lsd "CCO"` JSON output contains `DEFF F3` and `FEXP "F3"` (default changed from 1 to 3)
2. `lucy fragment to-lsd "CCO" --filter-index 1` JSON output contains `DEFF F1` (backward compat preserved)
3. Two new tests in test_lsd_formatter.py pass (test_to_lsd_default_filter_index_is_3, test_to_lsd_explicit_filter_index_1)
4. Full pytest suite green (no regression)
5. schemas/constraint_inventory_v2.json confirmed additionalProperties: true (no change needed)
6. lsd-engineer.md Fragment Goodlist CLI example uses `--filter-index 3`
</success_criteria>

<output>
Create /Users/steinbeck/Dropbox/develop/lucy-ng/.planning/phases/75-skill-consolidation/75-04-SUMMARY.md when done.
NOTE: src/ changes ARE committed to the lucy-ng git repo. Commit: `feat(75): add --filter-index option to fragment to-lsd (default 3, reserves F1/F2 for ring exclusion)`
Skill file edits (~/.claude/) are NOT committed.
</output>
