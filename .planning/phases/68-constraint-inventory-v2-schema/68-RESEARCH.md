# Phase 68: Constraint Inventory v2 Schema - Research

**Researched:** 2026-05-19
**Domain:** JSON Schema, Click CLI extension, agent skill documentation, LSD file format
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Clean v2 break — new delimiters `; === CONSTRAINT INVENTORY v2 ===` and `; === END CONSTRAINT INVENTORY ===`. The lsd-engineer agent writes v2 exclusively.
- **D-02:** Reader (devils-advocate) detects v1 blocks and emits WARNING ("Legacy v1 inventory — using fallback validation"), but does NOT block the run. No explicit v1→v2 migration reader needed — every CASE run starts fresh at iteration_01.
- **D-03:** Field `"version": 2` is mandatory in every v2 block (belt-and-suspenders on top of delimiter detection).
- **D-04:** `deferred_4j` is an array of structured objects (NOT string array as in v1). Per-entry schema:
  ```json
  {
    "atom1": <int, LSD-index>,
    "atom2": <int, LSD-index>,
    "shift1": <float, ppm>,
    "shift2": <float, ppm>,
    "correlation_type": "HMBC",
    "annotation": "; ELIM"
  }
  ```
- **D-05:** Identity via `(atom1, atom2, correlation_type)` tuple — aligned with PyLSDOrchestrator.
- **D-06:** Strict separation: Inventory = pre-run constraint state. Run results stay in `run_report.json` (SolutionMerger).
- **D-07:** All three new gates are CRITICAL (blocking):
  - G1: FORM/MULT consistency — when `pylsd_mode=true` and FORM present, MULT carbon sum must match.
  - G2: ELIM-vs-bond-range semantics — when `pylsd_mode=true`, a bare `ELIM N M` LSD command (not a comment) = BLOCK. v8.0 convention is `HMBC X Y 2 4 ; ELIM`.
  - G3: Annotation-vs-mode consistency — when `; ELIM` comment-annotations exist in HMBC lines, `pylsd_mode=true` AND `elim_annotated=true` AND `deferred_4j` must be non-empty.
- **D-08:** No new override mechanism — existing APPROVED/BLOCKED/WARNING semantics unchanged. User can intervene via orchestrator advisory.
- **D-09:** Source of Truth = `schemas/constraint_inventory_v2.json` (repo-root-relative, NOT under `src/`), JSON Schema Draft 2020-12.
- **D-10:** New CLI command `lucy lsd validate-inventory <file.lsd>` with `--format json`. Exit 0 = valid, 1 = invalid.
- **D-11:** Skill markdown files reference schema file by path; v1 inline JSON example replaced with v2 example. Example = illustration; schema file = truth.
- **D-12:** Devil's-Advocate calls `lucy lsd validate-inventory --format json` via Bash — replaces today's grep/sed/awk pipeline in Section 5A.

### Claude's Discretion

- Exact JSON Schema structure (which fields are `required`, `additionalProperties` strategy).
- Precise `--format json` output format for the CLI validator (standard jsonschema error output is acceptable starting point).
- Wording of the WARNING message for v1 legacy blocks in the Devil's Advocate skill.

### Deferred Ideas (OUT OF SCOPE)

- `lucy pylsd run` CLI command (Phase 69).
- Agent routing to pyLSD (Phase 70).
- Live UAT with ibuprofen (Phase 71).
- `LSDProblem.pylsd_mode` Python model (already done in Phase 66, `src/lucy_ng/lsd/models.py:184`).
- Override CLI for devils-advocate blocks (`lucy lsd run --override-inventory-check`).
- Inventory diff tool (`lucy lsd diff-inventory`).
- Pydantic model `ConstraintInventoryV2` (defer until Python-side generation is needed).
- v1→v2 migration tool (WARNING + fallback only).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INPUT-05 | Constraint inventory schema v2 tracks 4J suspect correlations with `pylsd_mode`, `deferred_4j` metadata | JSON Schema Draft 2020-12 fully supported by installed `jsonschema>=4.18.0`; `deferred_4j` object array design verified; CLI validator pattern confirmed from existing `lsd.py` commands |
</phase_requirements>

---

## Summary

Phase 68 extends the constraint inventory system — the JSON block embedded as LSD-comment header lines — from v1 (string-array `deferred_4j`, no `pylsd_mode` flag) to v2 (structured object array, three new fields, machine-readable JSON Schema file, CLI validator). The changes touch four artifacts: (1) `schemas/constraint_inventory_v2.json` (new file), (2) `src/lucy_ng/cli/lsd.py` (new `validate-inventory` subcommand), (3) `~/.claude/agents/lucy-lsd-engineer.md` Section 5 (schema table + file format + init/update procedures), and (4) `~/.claude/agents/lucy-devils-advocate.md` Section 5 (extraction pipeline replaced by CLI call, three new CRITICAL gates added).

No existing Python logic changes. The `jsonschema` library (4.25.1 installed, 4.26.0 latest on PyPI) already supports Draft 2020-12 via `Draft202012Validator` [VERIFIED: pip index]. The CLI pattern is a direct copy of the existing `lsd run` / `lsd rank` subcommand style in `src/lucy_ng/cli/lsd.py`. The test pattern follows `TestPyLSDExtensions` and `TestPyLSDValidator` in `tests/test_lsd_generator.py`.

The most dangerous semantic confusion this phase must encode explicitly is G2: `ELIM N M` as a bare LSD command *drops* a correlation entirely (the v7.0 trap that produced 100% false-positive 4J detection). The v8.0 convention is `HMBC X Y 2 4` (extended bond range) with a trailing `; ELIM` *comment* that the PyLSDOrchestrator parses to identify suspect correlations for permutation. G2 in the Devil's Advocate skill is the primary runtime defense against this confusion.

**Primary recommendation:** Implement in a single plan. The schema file, CLI command, and two skill rewrites are tightly coupled (devils-advocate references the CLI; the CLI references the schema; the skill documents the schema); splitting them across two plans adds synchronization risk with no parallelism benefit.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Schema definition (v2 JSON Schema) | Repository / Schema file | — | Single source of truth; consumed by both CLI validator and skill docs |
| Inventory writing | Agent (lsd-engineer) | — | Agent writes LSD files including inventory block; no Python generator involvement in Phase 68 |
| Inventory validation | CLI (`lucy lsd validate-inventory`) | Agent (devils-advocate calls CLI) | CLI owns validation logic; devils-advocate orchestrates via Bash call |
| Gate enforcement (G1/G2/G3) | Agent (devils-advocate) skill | — | Gates are decision logic, not Python; encoded in skill markdown |
| v1 legacy detection | Agent (devils-advocate) | — | WARNING-only; no code path needed |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `jsonschema` | 4.26.0 (latest), 4.25.1 (installed) | JSON Schema Draft 2020-12 validation in CLI validator | [VERIFIED: pip index versions jsonschema] — `Draft202012Validator` confirmed available; project already has Python 3.10+ and all transitive deps satisfied |

### Supporting

No new supporting packages. The CLI validator is a Click subcommand using the existing `click>=8.0` dependency already in `pyproject.toml`.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `jsonschema` | `fastjsonschema` | `fastjsonschema` compiles schemas to Python functions (faster) but does not return structured error objects with `path`/`validator` fields — harder to serialize for `--format json` output |
| `jsonschema` | `pydantic` validation only | Pydantic is already a project dependency, but its error format diverges from JSON Schema vocabulary — `jsonschema` error output is cleaner for machine consumption by the devils-advocate Bash pipeline |

**Installation:** `jsonschema` is already installed (4.25.1). Needs to be added to `pyproject.toml` dependencies:
```bash
# Add to [project] dependencies in pyproject.toml:
# "jsonschema>=4.18.0",
```

Version `>=4.18.0` is the minimum that includes `Draft202012Validator` [ASSUMED — based on jsonschema changelog patterns; 4.18.0 was released in 2023 and added Draft 2020-12 as a stable feature].

---

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| `jsonschema` | PyPI | ~14 years | Very high (core Python ecosystem) | github.com/python-jsonschema/jsonschema | [OK] | Approved |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

---

## Architecture Patterns

### System Architecture Diagram

```
LSD File (with "; === CONSTRAINT INVENTORY v2 ===" header block)
        |
        v
[lucy lsd validate-inventory <file.lsd>]
        |
        +-- Extract block (lines starting with "; " between v2 delimiters)
        |        |
        |        v
        |   Strip "; " prefix from each line
        |        |
        |        v
        |   json.loads() -> dict
        |        |
        |        v
        |   Draft202012Validator(schema).iter_errors(instance)
        |        |
        |   +----+----+
        |   |         |
        |  Valid    Errors
        |   |         |
        |  exit 0   Collect all errors
        |            |
        |         --format json?
        |           /    \
        |        YES      NO
        |        |         |
        |  JSON to stdout  Human text to stdout
        |  exit 1          exit 1
        v
[Devil's Advocate skill]
        |
        +-- Bash: lucy lsd validate-inventory --format json path/to/compound.lsd
        |
        +-- Parse JSON response
        |        |
        |   valid=true -> proceed
        |   valid=false -> BLOCK with error details
        v
[G1/G2/G3 gate checks] (additional checks beyond schema validation)
        |
        G1: FORM vs MULT carbon count (when pylsd_mode=true)
        G2: bare ELIM command detection (grep "^ELIM" in file body, not comment)
        G3: ; ELIM annotations vs pylsd_mode/elim_annotated consistency
```

### Recommended Project Structure

```
schemas/                          # NEW directory (repo-root level)
  constraint_inventory_v2.json    # JSON Schema Draft 2020-12 source of truth
src/lucy_ng/cli/
  lsd.py                          # ADD validate-inventory subcommand here
tests/
  test_lsd_cli.py                 # ADD CLI tests here (or new test_inventory_schema.py)
~/.claude/agents/
  lucy-lsd-engineer.md            # UPDATE Section 5 (schema table, file format, procedures)
  lucy-devils-advocate.md         # UPDATE Section 5A (extraction) + 5B (new gates)
```

The `schemas/` directory lives at repo root (not under `src/lucy_ng/`) so that agent skill docs and CLI code reference the same canonical path without package-relative lookups.

### Pattern 1: Click Subcommand Registration

**What:** New `validate-inventory` added to the existing `lsd` Click group in `src/lucy_ng/cli/lsd.py`.
**When to use:** Any new `lucy lsd <subcommand>` follows this pattern.

```python
# Source: src/lucy_ng/cli/lsd.py (existing pattern from lsd_run, lsd_rank)
@lsd.command("validate-inventory")
@click.argument("lsd_file", type=click.Path(exists=True))
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format (json for machine-readable, used by devils-advocate).",
)
def lsd_validate_inventory(lsd_file: str, output_format: str) -> None:
    """Validate the constraint inventory block in an LSD file.

    LSD_FILE is the path to the LSD input file containing a v2 inventory block.
    Exits 0 if valid, 1 if invalid or no inventory found.
    """
    ...
```

Registration: `lsd.py` already uses the `@lsd.command(...)` decorator pattern. No change to `main.py` is needed because `lsd` group is already registered via `cli.add_command(lsd)` at line 52 of `src/lucy_ng/cli/main.py`.

### Pattern 2: Inventory Block Extraction

**What:** Python implementation of the extraction pipeline currently done via bash grep/sed in the devils-advocate skill. This becomes the CLI validator's core.

```python
# Proposed implementation sketch for validate-inventory command body
from pathlib import Path
import json
import jsonschema

def _extract_inventory_block(content: str) -> str | None:
    """Extract JSON from between v2 inventory delimiters, stripping '; ' prefix."""
    lines = content.splitlines()
    in_block = False
    json_lines: list[str] = []
    for line in lines:
        if "=== CONSTRAINT INVENTORY v2 ===" in line:
            in_block = True
            continue
        if "=== END CONSTRAINT INVENTORY ===" in line and in_block:
            break
        if in_block and line.startswith("; "):
            json_lines.append(line[2:])  # strip "; " prefix (exactly 2 chars)
        elif in_block and line == ";":
            json_lines.append("")
    return "\n".join(json_lines) if json_lines else None

# In the Click command:
content = Path(lsd_file).read_text()
raw_json = _extract_inventory_block(content)
if raw_json is None:
    # Check for v1 block — fallback
    if "=== CONSTRAINT INVENTORY v1 ===" in content:
        # emit warning + exit 1 with legacy message
    else:
        # no inventory block at all
    ...
instance = json.loads(raw_json)
schema = json.loads(Path("schemas/constraint_inventory_v2.json").read_text())
validator = jsonschema.Draft202012Validator(schema)
errors = list(validator.iter_errors(instance))
```

### Pattern 3: `--format json` Output Structure

**What:** Machine-readable output the devils-advocate skill parses via Bash.
**When to use:** All CLI commands in lucy-ng support `--format json`. The validator follows the same convention.

```python
# Output structure for --format json (valid case):
{"valid": true, "file": "<path>", "version": 2}

# Output structure for --format json (invalid case):
{
  "valid": false,
  "file": "<path>",
  "errors": [
    {
      "message": "2 was expected",
      "path": ["version"],
      "validator": "const"
    }
  ]
}

# Exit code: 0 = valid, 1 = invalid or no inventory found
```

This structure mirrors the `jsonschema.ValidationError` attributes (`message`, `absolute_path`, `validator`) — verified via `iter_errors()` output. The existing `lsd_run` JSON output pattern (dict → `json.dumps(data, indent=2)` → `click.echo`) applies unchanged.

### Pattern 4: JSON Schema Draft 2020-12 Structure

**What:** The `schemas/constraint_inventory_v2.json` file. Claude's discretion on exact structure; research provides a concrete proposal.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://lucy-ng/schemas/constraint_inventory_v2.json",
  "title": "Constraint Inventory v2",
  "description": "Machine-readable constraint state embedded in LSD file headers",
  "type": "object",
  "required": ["version", "iteration", "formula", "timestamp",
               "mult_count", "hsqc_count", "hmbc_batches", "hmbc_total",
               "pylsd_mode", "elim_annotated", "deferred_4j"],
  "additionalProperties": true,
  "properties": {
    "version":          {"type": "integer", "const": 2},
    "iteration":        {"type": "integer", "minimum": 1},
    "formula":          {"type": "string"},
    "timestamp":        {"type": "string"},
    "mult_count":       {"type": "integer", "minimum": 0},
    "hsqc_count":       {"type": "integer", "minimum": 0},
    "hmbc_total":       {"type": "integer", "minimum": 0},
    "pylsd_mode":       {"type": "boolean"},
    "elim_annotated":   {"type": "boolean"},
    "hmbc_batches": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["batch", "count", "correlations"],
        "properties": {
          "batch":        {"type": "integer"},
          "count":        {"type": "integer"},
          "correlations": {"type": "array", "items": {"type": "string"}}
        },
        "additionalProperties": false
      }
    },
    "deferred_4j": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["atom1", "atom2", "shift1", "shift2", "correlation_type", "annotation"],
        "properties": {
          "atom1":            {"type": "integer", "minimum": 1},
          "atom2":            {"type": "integer", "minimum": 1},
          "shift1":           {"type": "number"},
          "shift2":           {"type": "number"},
          "correlation_type": {"type": "string", "const": "HMBC"},
          "annotation":       {"type": "string", "const": "; ELIM"}
        },
        "additionalProperties": false
      }
    },
    "grouped_hmbc":             {"type": "array", "items": {"type": "string"}},
    "bond_constraints":         {"type": "array", "items": {"type": "string"}},
    "syme_pairs":               {"type": "array", "items": {"type": "string"}},
    "list_prop_constraints":    {"type": "array", "items": {"type": "string"}},
    "elim_value":               {"type": ["integer", "null"]},
    "deff_not_patterns":        {"type": "array", "items": {"type": "string"}},
    "deff_fexp":                {"type": ["object", "null"]},
    "detection_results":        {"type": "object"},
    "applied_from_detection":   {"type": "array", "items": {"type": "string"}},
    "pending_from_detection":   {"type": "array", "items": {"type": "string"}}
  }
}
```

Note: `additionalProperties: true` at the top level is intentional — v2 schema does not break agents that write extra fields (forward compatibility). The `deferred_4j` items use `additionalProperties: false` for strict object validation.

### Anti-Patterns to Avoid

- **Bare ELIM command in pylsd_mode:** `ELIM N M` as a standalone LSD command (not a comment) drops the correlation entirely. Use `HMBC X Y 2 4 ; ELIM` instead. This is G2. [CITED: STATE.md "ELIM does NOT extend bond ranges — it drops correlations entirely."]
- **Reconstructing inventory from memory:** Always read the previous iteration's LSD file and copy inventory forward. Never rebuild from scratch. [CITED: lsd-engineer.md Section 5D "NEVER rebuild the inventory from scratch"]
- **Mid-line `;` in command lines affecting extraction:** The extraction pipeline (`grep "^; "`) only captures lines *starting* with `; `. An LSD command like `HMBC 4 8 2 4 ; ELIM` does NOT start with `; ` and is therefore NOT captured — this is the correct behavior. The `; ELIM` annotation inside a JSON string value (`"annotation": "; ELIM"`) survives the `sed 's/^; //'` stripping correctly because it appears after the 2-char prefix, not at position 0.
- **`jsonschema.validate()` vs `iter_errors()`:** `validate()` raises on first error only. Use `iter_errors()` to collect all errors for a complete JSON report in `--format json` output.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON Schema validation | Custom field-by-field checks | `jsonschema.Draft202012Validator` | Handles `const`, `minimum`, `additionalProperties`, nested object schemas, and produces structured error objects for free |
| JSON extraction from comment lines | Complex regex or state machine | Simple `startswith("; ")` + `[2:]` strip + `json.loads()` | LSD comment format is fixed; the extraction is 10 lines; see Pattern 2 above |
| Inventory v1 detection | Full parser | Single `"=== CONSTRAINT INVENTORY v1 ===" in content` string search | v1 only triggers a WARNING path, not schema validation |

**Key insight:** The entire validator is ~35 lines of Python. The complexity budget goes into the schema definition and skill documentation, not the implementation.

---

## Runtime State Inventory

This is a schema/documentation phase with no rename or data migration. No runtime state audit required.

---

## Common Pitfalls

### Pitfall 1: G2 Detector Matching Comments Instead of Commands

**What goes wrong:** A grep like `grep "ELIM"` in the LSD file body catches both `ELIM 4 4` (the dangerous LSD command) and lines like `HMBC 4 8 2 4 ; ELIM` (the correct v8.0 annotation). G2 fires a false positive.

**Why it happens:** ELIM appears in two syntactically different contexts: as a standalone command and as a trailing comment on an HMBC line.

**How to avoid:** G2's grep must be anchored to line start: `grep "^ELIM"` (or equivalent: lines where the first non-whitespace token is `ELIM`). This matches only bare LSD commands, not trailing comments.

**Warning signs:** G2 blocking an LSD file that correctly uses `HMBC X Y 2 4 ; ELIM` format.

---

### Pitfall 2: Schema Path Relative to CWD vs. Package

**What goes wrong:** `Path("schemas/constraint_inventory_v2.json")` in the CLI code assumes CWD is the repo root. If `lucy lsd validate-inventory` is invoked from a `analysis/iteration_NN/` subdirectory, the schema file is not found.

**Why it happens:** Python's `Path("relative/path")` is relative to the process CWD, not the source file location.

**How to avoid:** Load the schema using an absolute path derived from the package location, similar to how `_get_default_table_path()` in `lsd.py` (line 112) finds the HOSE lookup table:

```python
import lucy_ng
_SCHEMA_PATH = Path(lucy_ng.__file__).parent.parent.parent / "schemas" / "constraint_inventory_v2.json"
# Or: Path(__file__).parent.parent.parent.parent / "schemas" / "constraint_inventory_v2.json"
# src/lucy_ng/cli/lsd.py -> src/lucy_ng/cli -> src/lucy_ng -> src -> repo_root
```

**Warning signs:** `FileNotFoundError: schemas/constraint_inventory_v2.json` when running `lucy lsd validate-inventory` from any directory other than the project root.

---

### Pitfall 3: v1 Block Silently Passing Extraction

**What goes wrong:** If the extraction function searches for `"CONSTRAINT INVENTORY"` without the version suffix, a v1 block is extracted and run through the v2 schema — fails with confusing errors about missing `pylsd_mode` field rather than the helpful "Legacy v1 inventory" warning.

**Why it happens:** Extraction logic not version-discriminating.

**How to avoid:** The extraction function must check for `"=== CONSTRAINT INVENTORY v2 ==="` (with `v2`). A separate check for `"=== CONSTRAINT INVENTORY v1 ==="` triggers the WARNING path with `exit 1` and an appropriate message.

---

### Pitfall 4: `deferred_4j` Type Regression in Agent Writing

**What goes wrong:** The lsd-engineer agent writes the v2 inventory with `deferred_4j` as a string array (v1 format: `["C4(129.4) H8(45.0)"]`) instead of an object array. Schema validation rejects it with a confusing type error.

**Why it happens:** Agent's training pulls from the v1 inline example in `lucy-lsd-engineer.md` Section 5B if the skill file is not updated. The agent may also fall back to string format under time pressure.

**How to avoid:** The skill update must (a) replace the v1 inline example with a complete v2 example, (b) include an explicit `UPGRADE NOTE: deferred_4j changed from string array to object array in v2` callout in the skill, and (c) document the full object structure in the Section 5A schema table.

---

### Pitfall 5: `elim_value` Field Confusion with `elim_annotated`

**What goes wrong:** `elim_value` (v1 field: the argument to the `ELIM N M` LSD command, or null) and `elim_annotated` (v2 new field: bool indicating HMBC lines carry `; ELIM` comments) serve different purposes. Conflating them causes G3 to malfunction.

**Why it happens:** Both relate to ELIM; both can be null/false in a standard run.

**How to avoid:** Skill documentation must explicitly contrast them:
- `elim_value`: non-null only when a bare `ELIM N M` command was written to the LSD file (last-resort zero-solution recovery). **If `pylsd_mode=true`, G2 blocks runs with non-null `elim_value`.**
- `elim_annotated`: true when any HMBC line carries a `; ELIM` trailing comment for PyLSDOrchestrator parsing. **If `pylsd_mode=true` and `elim_annotated=true`, `deferred_4j` must be non-empty (G3).**

---

## Code Examples

### Existing v1 Inventory Block (from lucy-lsd-engineer.md Section 5B — verbatim)

This is the format that will be replaced by v2. Key differences to note:
- Delimiter: `; === CONSTRAINT INVENTORY v1 ===`
- `"version": 1`
- `"deferred_4j": ["C4(129.4) H8(45.0)"]` — string array, NOT object array
- No `pylsd_mode` field
- No `elim_annotated` field

```lsd
; === CONSTRAINT INVENTORY v1 ===
; {
;   "version": 1, "iteration": 2, "formula": "C13H18O2", "timestamp": "2026-02-17T10:00:00Z",
;   "mult_count": 15, "hsqc_count": 10,
;   "hmbc_batches": [
;     {"batch": 1, "count": 5, "correlations": ["1 13", "2 6", "3 4", "10 11", "4 8"]},
;     {"batch": 2, "count": 5, "correlations": ["1 9", "3 13", "3 9", "5 9", "11 10"]}
;   ],
;   "hmbc_total": 10, "grouped_hmbc": [],
;   "bond_constraints": ["1 14"], "syme_pairs": [],
;   "list_prop_constraints": [], "elim_value": null,
;   "deff_not_patterns": ["C1CC1", "C1CCC1", "C1NC1", "C1NCC1", "C1SC1", "C1SCC1", "C1OC1", "C1OCC1"],
;   "deferred_4j": ["C4(129.4) H8(45.0)"],
;   ...
; }
; === END CONSTRAINT INVENTORY ===
```

[CITED: lucy-lsd-engineer.md Section 5B]

### v2 Inventory Block (proposed replacement)

```lsd
; === CONSTRAINT INVENTORY v2 ===
; {
;   "version": 2, "iteration": 2, "formula": "C13H18O2", "timestamp": "2026-02-17T10:00:00Z",
;   "mult_count": 15, "hsqc_count": 10,
;   "hmbc_batches": [
;     {"batch": 1, "count": 5, "correlations": ["1 13", "2 6", "3 4", "10 11", "4 8"]},
;     {"batch": 2, "count": 5, "correlations": ["1 9", "3 13", "3 9", "5 9", "11 10"]}
;   ],
;   "hmbc_total": 10, "grouped_hmbc": [],
;   "bond_constraints": ["1 14"], "syme_pairs": [],
;   "list_prop_constraints": [], "elim_value": null,
;   "deff_not_patterns": ["C1CC1", "C1CCC1", "C1NC1", "C1NCC1", "C1SC1", "C1SCC1", "C1OC1", "C1OCC1"],
;   "pylsd_mode": true,
;   "elim_annotated": true,
;   "deferred_4j": [
;     {"atom1": 4, "atom2": 8, "shift1": 129.38, "shift2": 45.03, "correlation_type": "HMBC", "annotation": "; ELIM"},
;     {"atom1": 6, "atom2": 9, "shift1": 127.26, "shift2": 44.90, "correlation_type": "HMBC", "annotation": "; ELIM"}
;   ],
;   "deff_fexp": {"status": "none", ...},
;   "detection_results": {}, "applied_from_detection": [], "pending_from_detection": []
; }
; === END CONSTRAINT INVENTORY ===
HMBC 4 8 2 4 ; ELIM
HMBC 6 9 2 4 ; ELIM
```

### Existing Devil's Advocate Section 5A Extraction (verbatim — to be replaced by D-12)

```bash
# Extract inventory JSON from current LSD file
grep "^; " analysis/iteration_NN/compound.lsd | \
  sed -n '/CONSTRAINT INVENTORY v1/,/END CONSTRAINT INVENTORY/p' | \
  sed 's/^; //' | grep -v "===" > /tmp/current_inv.json

# Extract inventory from previous iteration
grep "^; " analysis/iteration_MM/compound.lsd | \
  sed -n '/CONSTRAINT INVENTORY v1/,/END CONSTRAINT INVENTORY/p' | \
  sed 's/^; //' | grep -v "===" > /tmp/prev_inv.json
```

[CITED: lucy-devils-advocate.md Section 5A]

The replacement per D-12:
```bash
# Validate current LSD file inventory
RESULT=$(lucy lsd validate-inventory --format json analysis/iteration_NN/compound.lsd)
VALID=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['valid'])")
if [ "$VALID" != "True" ]; then
    ERRORS=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); [print(e['message']) for e in d.get('errors',[])]")
    # BLOCK with error details
fi
```

### Existing Test Pattern (from tests/test_lsd_generator.py TestPyLSDValidator — to be mirrored)

```python
class TestPyLSDValidator:
    def test_validate_pylsd_carbon_mismatch(self):
        from lucy_ng.lsd.generator import validate_pylsd_input
        problem = LSDProblem(molecular_formula="C13H18O2")
        for i in range(1, 13):  # 12 carbons, formula says 13
            problem.add_atom(LSDAtom(i, "C", Hybridization.SP3, 0))
        with pytest.raises(ValueError, match="FORM/MULT mismatch"):
            validate_pylsd_input(problem)
```

[CITED: tests/test_lsd_generator.py lines 500-511]

New tests follow this pattern: one class per feature (`TestInventorySchemaLoading`, `TestValidateInventoryCLI`, `TestInventorySchemaValidation`), each test method 5-10 lines.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Grep/sed/awk pipeline in agent skill for inventory extraction | `lucy lsd validate-inventory --format json` CLI call | Phase 68 | Elimination of bash pipeline fragility; JSON error objects instead of text parsing |
| `deferred_4j` as string array `["C4(129.4) H8(45.0)"]` | `deferred_4j` as structured object array with `atom1`/`atom2`/`shift1`/`shift2` | Phase 68 | Machine-parseable by PyLSDOrchestrator; identity tuple `(atom1, atom2, correlation_type)` aligned with Phase 67 design |
| No schema file — schema defined only in agent skill markdown | `schemas/constraint_inventory_v2.json` as Source of Truth | Phase 68 | Testable: any v2 inventory can be validated programmatically without reading the skill file |

**Deprecated/outdated:**
- `; === CONSTRAINT INVENTORY v1 ===` delimiter: triggers WARNING in devils-advocate, lsd-engineer writes only v2 going forward.
- `"version": 1` field value: schema `const: 2` rejects v1 instances.
- String-array `deferred_4j`: replaced by object array — agents writing the old format will fail schema validation (catchable by G3 check).

---

## Key Findings: What the Planner Needs to Know

### 1. jsonschema is NOT in pyproject.toml

`jsonschema` 4.25.1 is installed in the current Python environment but is absent from `pyproject.toml` `[project] dependencies`. The plan must add `"jsonschema>=4.18.0"` to `pyproject.toml`. [VERIFIED: pyproject.toml read — no jsonschema entry]

### 2. CLI Registration: Only lsd.py Needs Changing

`src/lucy_ng/cli/main.py` already registers the `lsd` group via `cli.add_command(lsd)` (line 52). New `validate-inventory` subcommand is a `@lsd.command(...)` decorator in `src/lucy_ng/cli/lsd.py` only. No `main.py` changes needed. [CITED: src/lucy_ng/cli/main.py lines 12, 52]

### 3. Schema File Loader Pattern

The HOSE table loader in `lsd.py` lines 112-137 (`_get_default_table_path()`) shows the pattern for finding package-adjacent files. The schema loader should use a similar approach — deriving the path from `__file__`. This avoids CWD-relative path failures when the CLI is invoked from subdirectories.

### 4. Exact Subsections Requiring Rewrite in lsd-engineer.md

| Subsection | Current Content | Required Change |
|------------|-----------------|-----------------|
| 5A JSON Schema Reference table | 18-row table, no `pylsd_mode`/`elim_annotated` rows, `deferred_4j` listed as `string array` | Add 3 new rows for v2 fields; change `deferred_4j` type to `object array` with link to schema file |
| 5B LSD File Format | v1 delimiter `; === CONSTRAINT INVENTORY v1 ===`; multi-line JSON example with string `deferred_4j` | Replace delimiters to v2; replace inline JSON example with v2 example including object `deferred_4j` |
| 5C Initialization Procedure | Step 2: refers to `deferred_4j` as string descriptions | Update step 2a (extract nmr-chemist's flagged 4J as objects); reference `pylsd_mode`/`elim_annotated` init logic |
| 5D Update Procedure | Step 2: `between CONSTRAINT INVENTORY v1 ... END` | Update delimiter string to v2 |
| Workflow step 2a | `add them to deferred_4j in the constraint inventory (as string descriptions)` | Change to object array with atom indices and shifts |

[CITED: lucy-lsd-engineer.md lines 316-416]

### 5. Exact Subsections Requiring Rewrite in devils-advocate.md

| Subsection | Current Content | Required Change |
|------------|-----------------|-----------------|
| 5A Inventory Extraction | Two `grep/sed` bash blocks targeting `v1` delimiter | Replace with `lucy lsd validate-inventory --format json` call; add v1 detection/WARNING path |
| 5B Check 1 (Inventory Accurate?) | No checks for `pylsd_mode`, `elim_annotated`, `deferred_4j` | Add G1/G2/G3 as new CRITICAL checks after existing Check 1/2/3 |
| 5B header comment | "between `; === CONSTRAINT INVENTORY v1 ===`..." | Update delimiter reference to v2 |
| Section 5 intro paragraph | References `CONSTRAINT INVENTORY v1` | Update to v2 |
| Workflow step 3 | "Extract constraint inventory from current LSD file (Section 5A)" | No change needed — refers to section by name, not by implementation |

[CITED: lucy-devils-advocate.md lines 219-280]

### 6. G2 Implementation Detail: Correct Grep Pattern

G2 in the devils-advocate skill needs to detect a bare `ELIM N M` LSD command. The correct grep pattern, verified against the LSD file format:

```bash
# Detects bare ELIM command (G2) — anchored to line start, NOT comment lines
grep -n "^ELIM" analysis/iteration_NN/compound.lsd
# Returns matches if bare ELIM command found; empty if only '; ELIM' comment annotations exist
```

`HMBC 4 8 2 4 ; ELIM` does NOT match `^ELIM` — confirmed by simulation [VERIFIED: local bash test].

---

## Open Questions (RESOLVED)

1. **Schema file loading from installed package** — RESOLVED: Deferred to future phase. Phase 68 loads schema via package-relative `Path(__file__)` navigation per development/CASE context. Wheel-manifest inclusion is out of scope here; flag for a future packaging phase if pip-install distribution is added.

2. **Test file placement: new file or extend existing?** — RESOLVED: Create `tests/test_inventory_schema.py` for (a) schema loading, (b) schema validation happy/error paths, and (c) CLI `validate-inventory` via Click's `CliRunner`. Plans 01 and 02 both target this file (01 creates schema test classes, 02 appends CLI test classes; Plan 02 depends on Plan 01 per checker Blocker 1 fix).

3. **v1 WARNING behavior: exit code** — RESOLVED: `--format json` for v1 blocks emits `{"valid": false, "errors": [{"message": "Legacy v1 inventory detected — upgrade to v2 format", "validator": "version"}]}` and CLI exit code 1. Consistent error-object structure lets devils-advocate's bash pipeline handle it uniformly.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `jsonschema` | CLI validator | Yes (installed) | 4.25.1 | — (must add to pyproject.toml) |
| `Draft202012Validator` | Schema validation | Yes | confirmed in 4.25.1 | — |
| `schemas/` directory | Schema file | No (does not exist yet) | — | Create as part of plan |

**Missing dependencies with no fallback:**
- `schemas/` directory and `schemas/constraint_inventory_v2.json` — must be created by the plan

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 7.x+ |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/test_inventory_schema.py -x` |
| Full suite command | `pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INPUT-05 | v2 schema loads and validates a correct inventory | unit | `pytest tests/test_inventory_schema.py::TestSchemaLoading::test_schema_loads -x` | No — Wave 0 |
| INPUT-05 | v2 schema rejects `version: 1` | unit | `pytest tests/test_inventory_schema.py::TestSchemaValidation::test_rejects_v1_version -x` | No — Wave 0 |
| INPUT-05 | v2 schema rejects string-array `deferred_4j` | unit | `pytest tests/test_inventory_schema.py::TestSchemaValidation::test_rejects_deferred_4j_strings -x` | No — Wave 0 |
| INPUT-05 | CLI validates a correct v2 LSD file → exit 0 | integration | `pytest tests/test_inventory_schema.py::TestValidateInventoryCLI::test_valid_file_exits_0 -x` | No — Wave 0 |
| INPUT-05 | CLI detects v1 block → exit 1 with legacy message | integration | `pytest tests/test_inventory_schema.py::TestValidateInventoryCLI::test_v1_block_exits_1 -x` | No — Wave 0 |
| INPUT-05 | G2: `^ELIM` grep fires on bare ELIM command | unit | `pytest tests/test_inventory_schema.py::TestGateLogic::test_g2_bare_elim_detected -x` | No — Wave 0 |

### Sampling Rate

- Per task commit: `pytest tests/test_inventory_schema.py -x`
- Per wave merge: `pytest` (full suite)
- Phase gate: Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- `tests/test_inventory_schema.py` — covers all INPUT-05 requirements (file does not exist)
- `schemas/constraint_inventory_v2.json` — schema file (directory does not exist)

---

## Security Domain

`security_enforcement` not set in `.planning/config.json` — treated as enabled.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | Yes (LSD file path argument, JSON parsing) | `click.Path(exists=True)` for file arg; `json.loads()` with try/except for JSON parsing |
| V2 Authentication | No | CLI is local tool, no auth |
| V6 Cryptography | No | No crypto operations |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal via `lsd_file` argument | Tampering | `click.Path(exists=True)` resolves and validates path; schema file uses package-relative absolute path |
| JSON parse bomb (deeply nested inventory) | DoS | LSD inventory blocks are agent-written and bounded by practical CASE run size; `json.loads()` is safe for this domain |

---

## Package Legitimacy Audit (full)

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| `jsonschema` | PyPI | ~14 years | Millions/week (top Python ecosystem package) | github.com/python-jsonschema/jsonschema | [OK] | Approved |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `jsonschema>=4.18.0` is the minimum version with stable `Draft202012Validator` support | Standard Stack | If minimum is higher (e.g., 4.20.0), the pyproject.toml constraint would be too loose; actual installed version 4.25.1 is unaffected |
| A2 | `schemas/` directory at repo root does not conflict with any existing tooling (hatch build, mypy, ruff) | Architecture | If hatch or ruff tries to process `schemas/*.json`, minor config change needed; low risk |

**If this table is empty:** All other claims in this research were verified or cited.

---

## Sources

### Primary (HIGH confidence)

- `lucy-lsd-engineer.md` — v1 schema table (Section 5A), v1 file format with inline JSON example (Section 5B), init/update procedures (5C/5D) — read directly
- `lucy-devils-advocate.md` — Section 5A bash extraction pipeline (verbatim), Section 5B three-check protocol — read directly
- `src/lucy_ng/cli/lsd.py` — complete `lsd` Click group structure, `lsd_run`/`lsd_rank`/`lsd_analyze` subcommand patterns, `_get_default_table_path()` schema-loading pattern — read directly
- `src/lucy_ng/cli/main.py` — `cli.add_command(lsd)` at line 52 — read directly
- `src/lucy_ng/lsd/models.py` lines 175-186 — `LSDProblem.pylsd_mode: bool = False` at line 184 — read directly
- `src/lucy_ng/lsd/generator.py` lines 103-110 — FORM/ELIM emission block — read directly
- `pyproject.toml` — confirmed `jsonschema` absent from dependencies — read directly
- `tests/test_lsd_generator.py` lines 389-536 — `TestPyLSDExtensions` and `TestPyLSDValidator` test patterns — read directly
- `jsonschema` 4.25.1 — `Draft202012Validator`, `iter_errors()`, `ValidationError` attributes — verified via local Python execution
- `pip index versions jsonschema` — 4.26.0 latest, 4.25.1 installed — [VERIFIED: pip index]

### Secondary (MEDIUM confidence)

- slopcheck output for `jsonschema` — [OK] verdict — run in this session

### Tertiary (LOW confidence)

- `jsonschema>=4.18.0` as minimum for Draft 2020-12 — [ASSUMED] (see Assumptions Log A1)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — `jsonschema` verified installed, slopcheck OK, `Draft202012Validator` confirmed working
- Architecture: HIGH — all source files read directly; patterns quoted verbatim
- Pitfalls: HIGH — verified via local execution (mid-line semicolons, extraction pipeline, `^ELIM` grep)
- Skill rewrite scope: HIGH — exact subsections and verbatim current text quoted

**Research date:** 2026-05-19
**Valid until:** 2026-07-01 (stable ecosystem; `jsonschema` and Click are mature, non-fast-moving)
