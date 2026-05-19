---
phase: 68-constraint-inventory-v2-schema
reviewed: 2026-05-19T12:00:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - schemas/constraint_inventory_v2.json
  - src/lucy_ng/cli/lsd.py
  - tests/test_inventory_schema.py
  - /Users/steinbeck/.claude/agents/lucy-lsd-engineer.md
  - /Users/steinbeck/.claude/agents/lucy-devils-advocate.md
findings:
  critical: 3
  warning: 5
  info: 3
  total: 11
status: issues_found
---

# Phase 68: Code Review Report

**Reviewed:** 2026-05-19T12:00:00Z
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Phase 68 delivers a JSON Schema Draft 2020-12 file, a new `lucy lsd validate-inventory` CLI subcommand, 34 tests, and updates to two agent skill files. The schema structure and CLI flow are sound for the development-install case and the test suite exercises the primary paths correctly. However, three blockers were found: the schema file is not bundled in the package wheel (breaking the CLI for pip-installed users), the `validate-inventory --format json` success response omits the parsed inventory object (breaking the agent's G2/G3 gate logic in `lucy-devils-advocate`), and the G3 grep pattern in `lucy-devils-advocate` is unanchored and will produce false positives from any comment line containing the literal text `; ELIM`.

---

## Critical Issues

### CR-01: `_get_schema_path()` fails silently for non-editable pip installs

**File:** `src/lucy_ng/cli/lsd.py:142-159`

**Issue:** `_get_schema_path()` derives `project_root` as `package_dir.parent.parent` — which resolves correctly under an editable install (`src/lucy_ng` → `src` → `repo_root`) but resolves to the Python standard library prefix under a regular `pip install` (e.g. `/opt/miniconda3/lib/python3.12/site-packages/lucy_ng` → `/opt/miniconda3/lib/python3.12`). The constructed path `/opt/miniconda3/lib/python3.12/schemas/constraint_inventory_v2.json` does not exist, so `_get_schema_path()` raises `FileNotFoundError`. Every call to `lucy lsd validate-inventory` from a non-editable install exits 1 with "Schema not found" before any validation occurs.

The root cause is that `schemas/constraint_inventory_v2.json` is stored at repo root, not under `src/lucy_ng/`. `pyproject.toml` declares `packages = ["src/lucy_ng"]`, so the `schemas/` directory is never included in the built wheel and there is no package-data fallback path.

**Fix:** Move or copy the schema into the package tree (e.g. `src/lucy_ng/data/schemas/constraint_inventory_v2.json`) and use `importlib.resources` or `importlib.metadata` to locate it. Alternatively, keep the repo-root location but add a package-data include and a second resolution path:

```python
def _get_schema_path() -> Path:
    import lucy_ng
    package_dir = Path(lucy_ng.__file__).parent

    # 1. Bundled within the installed package (pip install)
    bundled = package_dir / "data" / "schemas" / "constraint_inventory_v2.json"
    if bundled.exists():
        return bundled

    # 2. Repo root (editable install / development)
    project_root = package_dir.parent.parent
    repo_schema = project_root / "schemas" / "constraint_inventory_v2.json"
    if repo_schema.exists():
        return repo_schema

    raise FileNotFoundError(
        "Schema not found. Re-install the package or check the schemas/ directory."
    )
```

And in `pyproject.toml`:
```toml
[tool.hatch.build.targets.wheel]
packages = ["src/lucy_ng"]
artifacts = ["src/lucy_ng/data/schemas/*"]
```

---

### CR-02: `validate-inventory --format json` omits parsed inventory fields, breaking G2/G3 gate logic

**File:** `src/lucy_ng/cli/lsd.py:270-273` and `/Users/steinbeck/.claude/agents/lucy-devils-advocate.md:225-253`

**Issue:** On success, `validate-inventory --format json` emits only `{"valid": true, "file": "...", "version": 2}`. It does not include the parsed inventory object (`pylsd_mode`, `elim_annotated`, `deferred_4j`, etc.).

The `lucy-devils-advocate` skill Section 5A assigns this output to `INVENTORY`:
```bash
INVENTORY=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d))")
```
Section 5B Check 4 then says "Extract `pylsd_mode` from the INVENTORY JSON." But `INVENTORY` has `{valid, file, version}` — no `pylsd_mode`, `elim_annotated`, or `deferred_4j` fields. The agent would have to re-parse the LSD file manually to run G2 and G3, contradicting the protocol's stated purpose of using the CLI validator as the single extraction step.

In practice the agent will either hallucinate these values, fail silently, or skip the G2/G3 checks — defeating the primary purpose of phase 68.

**Fix:** Add an `inventory` key to the success response containing the parsed and schema-validated inventory object:

```python
# Line 270-273 — replace the success echo:
if output_format == "json":
    click.echo(json.dumps({
        "valid": True,
        "file": lsd_file,
        "version": 2,
        "inventory": instance,   # the parsed inventory object
    }, indent=2))
```

This gives the agent `data["inventory"]["pylsd_mode"]`, `data["inventory"]["deferred_4j"]` etc. in one step, consistent with Section 5A's intent.

---

### CR-03: G3 grep `"; ELIM"` is unanchored — false positives from comment lines and inventory JSON

**File:** `/Users/steinbeck/.claude/agents/lucy-devils-advocate.md:320-328`

**Issue:** G3 uses `grep -c "; ELIM" compound.lsd` (unanchored). This matches any line containing the substring `; ELIM`, including:

1. **Inventory comment lines** — every deferred_4j entry in the JSON block contains `"annotation": "; ELIM"`, which is embedded as `;     "annotation": "; ELIM"` in the LSD file. This line matches the grep and inflates the count.
2. **Arbitrary comment lines** — any comment explaining that "; ELIM" is not used (e.g., `; Note: this file was run without ; ELIM annotations`) triggers the G3 check.

The net effect: an LSD file with `pylsd_mode=true` but `elim_annotated=false` (i.e., no actual HMBC annotation lines) would incorrectly trigger G3 and be BLOCKED if its inventory JSON contains deferred_4j entries (because those entries contain `"; ELIM"` as a value in the JSON text).

Note the contrast with G2, which correctly uses `^ELIM` and is even annotated in the skill: "This grep MUST be anchored to line start." G3 received no equivalent protection.

**Fix:** Anchor the G3 grep to match only HMBC command lines with a trailing `; ELIM` annotation:

```bash
# G3: count only actual HMBC annotation lines, not comments or inventory JSON
grep -c "^HMBC.*; ELIM" analysis/iteration_NN/compound.lsd
```

Also add the same explanatory note that G2 has, explaining why anchoring is required.

---

## Warnings

### WR-01: Schema cross-field invariants for G2 and G3 are not enforced

**File:** `schemas/constraint_inventory_v2.json:79-124`

**Issue:** The schema `description` fields document the G2 and G3 invariants:
- G2: `pylsd_mode=true` implies `elim_value` must be `null`
- G3: `elim_annotated=true` implies `deferred_4j` must be non-empty AND `pylsd_mode=true`

Neither invariant is enforced by the schema. An inventory with `pylsd_mode=true, elim_value=4` or `elim_annotated=true, deferred_4j=[]` passes validation without errors. The gate logic exists only in the `devils-advocate` agent, not in the schema that is supposed to be the source of truth.

**Fix:** Add `if/then` constraints (JSON Schema Draft 2020-12 supports them):

```json
"if": {"properties": {"elim_annotated": {"const": true}}, "required": ["elim_annotated"]},
"then": {
  "properties": {"pylsd_mode": {"const": true}, "deferred_4j": {"minItems": 1}},
  "required": ["pylsd_mode", "deferred_4j"]
}
```

For G2:
```json
"if": {"properties": {"pylsd_mode": {"const": true}}, "required": ["pylsd_mode"]},
"then": {
  "properties": {"elim_value": {"type": "null"}}
}
```

---

### WR-02: `hmbc_batches[].batch` field has no `minimum` constraint — zero-indexed batch accepted

**File:** `schemas/constraint_inventory_v2.json:58-72`

**Issue:** The `batch` field in `hmbc_batches` items has `type: integer` and description "Batch number (1-based, one per CASE iteration)" but no `"minimum": 1` constraint. A batch with `"batch": 0` passes validation. This is inconsistent with the `iteration` field (which has `"minimum": 1`) and the `atom1`/`atom2` fields in `deferred_4j` (which also have `"minimum": 1`). An off-by-one in the agent writing batch numbers would go undetected.

**Fix:**
```json
"batch": {
  "type": "integer",
  "minimum": 1,
  "description": "Batch number (1-based, one per CASE iteration)."
}
```

---

### WR-03: `lsd-engineer` update procedure does not list `elim_annotated` as a field to update

**File:** `/Users/steinbeck/.claude/agents/lucy-lsd-engineer.md:419-432`

**Issue:** Section 5D "Update Procedure (Iteration N > 1)" instructs the agent to update `iteration`, `hmbc_batches`, `hmbc_total`, and `timestamp` — but `elim_annotated` is not listed. The initialization procedure (5C step 5c) correctly sets it based on `len(deferred_4j) > 0`. However if a future iteration removes a deferred_4j entry (e.g., after confirming it as a genuine 4J), `elim_annotated` would remain `true` in the stale-copied inventory, putting the file in an inconsistent state that G3 would then BLOCK on (even if no `; ELIM` annotations remain).

The current design says deferred_4j entries are never removed, so this is a latent risk. But the protocol is incomplete as written.

**Fix:** Add to the "Update only these fields" list in Section 5D:
> - Recompute `elim_annotated`: set to `true` if `len(deferred_4j) > 0` (after any additions or removals), `false` otherwise.

---

### WR-04: `_extract_inventory_block` silently succeeds when `END` delimiter is missing

**File:** `src/lucy_ng/cli/lsd.py:162-182`

**Issue:** If an LSD file has the `START` delimiter (`=== CONSTRAINT INVENTORY v2 ===`) but no `END` delimiter (`=== END CONSTRAINT INVENTORY ===`), `_extract_inventory_block` continues scanning the entire file. Lines that do not start with `; ` (i.e., all LSD commands like `MULT`, `HSQC`, `HMBC`) are silently dropped, and the function returns the partial JSON it accumulated from the `;`-prefixed lines.

In the typical case where the JSON block is complete but someone accidentally deleted or mistyped the END delimiter, this means:
1. The JSON still parses successfully (the LSD commands after the block are non-`; ` lines and get discarded).
2. `validate-inventory` reports "Valid" — masking the structural corruption of the LSD file.

**Fix:** After the loop, if `in_block` is still `True` (loop ended without finding the END delimiter), treat the block as malformed:

```python
if json_lines and not in_block:   # normal: END was found
    return "\n".join(json_lines)
elif in_block:                     # END delimiter never found
    return None   # or raise a distinct error
```

Alternatively, track a `found_end` boolean and return `None` / signal an error when it is `False` after the loop.

---

### WR-05: `validate-inventory` does not handle `PermissionError` on file read

**File:** `src/lucy_ng/cli/lsd.py:200`

**Issue:** `content = Path(lsd_file).read_text()` is not wrapped in a try/except. `click.Path(exists=True)` only validates that the path exists; it does not verify readability. If the file exists but is not readable (mode 0o000, owned by another user, etc.), a `PermissionError` propagates as an unhandled exception, producing a Python traceback instead of a clean `{"valid": false, "errors": [...]}` JSON response.

The agent's bash pipeline (`VALID=$(echo "$RESULT" | python3 -c "...")`) would then receive the traceback in `$RESULT`, `json.load()` would throw, and the pipeline would silently fail rather than reporting the problem.

**Fix:**
```python
try:
    content = Path(lsd_file).read_text(encoding="utf-8")
except PermissionError as e:
    if output_format == "json":
        click.echo(json.dumps({
            "valid": False, "file": lsd_file,
            "errors": [{"message": f"Cannot read file: {e}", "validator": "file_access"}],
        }, indent=2))
    else:
        click.echo(f"Error: Cannot read file: {e}", err=True)
    raise SystemExit(1)
```

(Adding `encoding="utf-8"` explicitly also avoids locale-dependent failures for LSD files with non-ASCII comments.)

---

## Info

### IN-01: `pytest` import in test file is unused

**File:** `tests/test_inventory_schema.py:5`

**Issue:** `import pytest` is present but never used. No `pytest.mark.*`, `pytest.raises`, or `pytest.param` calls appear anywhere in the file. The `tmp_path` fixture is a built-in pytest fixture that does not require an explicit import. Ruff (`F401`) will flag this.

**Fix:** Remove `import pytest`.

---

### IN-02: Schema accepts empty strings for `formula` and `timestamp`

**File:** `schemas/constraint_inventory_v2.json:33-39`

**Issue:** `formula` and `timestamp` are `type: string` with no `minLength` or `pattern` constraint. An inventory with `"formula": ""` or `"timestamp": ""` passes validation. For `formula` a simple pattern like `"pattern": "^[A-Z][A-Za-z0-9]+$"` would enforce non-empty molecular formula. For `timestamp`, `"format": "date-time"` could be used (requires the `jsonschema` `format` checker to be enabled, which is not the default, so a `minLength` check may be more reliable).

**Fix (schema):**
```json
"formula": {
  "type": "string",
  "minLength": 2,
  "pattern": "^[A-Z]",
  "description": "Molecular formula, e.g. 'C13H18O2'."
},
"timestamp": {
  "type": "string",
  "minLength": 10,
  "description": "ISO 8601 timestamp when this inventory was written."
}
```

---

### IN-03: Schema does not enforce `hmbc_total` consistency with `hmbc_batches[].count` sum

**File:** `schemas/constraint_inventory_v2.json:74-76`

**Issue:** `hmbc_total` is declared as `type: integer, minimum: 0` but there is no constraint tying it to the sum of `hmbc_batches[].count` values. An inventory with `hmbc_total: 999` and one batch containing 2 correlations passes validation. The `devils-advocate` Check 1 catches this discrepancy against the actual file grep count, but the schema itself provides no protection.

JSON Schema Draft 2020-12 cannot express sum-equality constraints natively (it requires custom keywords or a `$defs` approach). This is a known limitation of the schema language. Document the constraint explicitly in the `hmbc_total` description and rely on the CLI's Check 1 grep validation.

**Fix (documentation only):**
```json
"hmbc_total": {
  "type": "integer",
  "minimum": 0,
  "description": "Total HMBC correlations across all batches. MUST equal sum(hmbc_batches[i].count). Enforced by devils-advocate Check 1, not by this schema."
}
```

---

_Reviewed: 2026-05-19T12:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
