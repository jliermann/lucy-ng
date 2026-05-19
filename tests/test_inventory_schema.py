"""Tests for constraint inventory v2 JSON schema."""

import json
import re
import pytest
from pathlib import Path

from click.testing import CliRunner
from jsonschema import Draft202012Validator

from lucy_ng.cli.lsd import lsd


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_schema() -> dict:
    """Load the constraint inventory v2 JSON Schema from the repo root."""
    schema_path = Path(__file__).parent.parent / "schemas" / "constraint_inventory_v2.json"
    with schema_path.open() as f:
        return json.load(f)


def _minimal_valid_v2() -> dict:
    """Return a minimal, fully-valid constraint inventory v2 instance."""
    return {
        "version": 2,
        "iteration": 1,
        "formula": "C13H18O2",
        "timestamp": "2026-01-01T00:00:00Z",
        "mult_count": 13,
        "hsqc_count": 9,
        "hmbc_batches": [],
        "hmbc_total": 0,
        "pylsd_mode": False,
        "elim_annotated": False,
        "deferred_4j": [],
    }


def _valid_deferred_4j_item() -> dict:
    """Return a valid deferred_4j object item."""
    return {
        "atom1": 4,
        "atom2": 8,
        "shift1": 129.38,
        "shift2": 45.03,
        "correlation_type": "HMBC",
        "annotation": "; ELIM",
    }


# ---------------------------------------------------------------------------
# TestSchemaLoading
# ---------------------------------------------------------------------------


class TestSchemaLoading:
    """Tests that the schema file can be loaded and is structurally correct."""

    def test_schema_file_exists(self):
        """Schema file must exist at repo_root/schemas/constraint_inventory_v2.json."""
        schema_path = Path(__file__).parent.parent / "schemas" / "constraint_inventory_v2.json"
        assert schema_path.exists(), f"Schema file not found at {schema_path}"

    def test_schema_is_valid_json(self):
        """Schema file must parse as valid JSON without exception."""
        schema_path = Path(__file__).parent.parent / "schemas" / "constraint_inventory_v2.json"
        # Should not raise
        schema = json.loads(schema_path.read_text())
        assert isinstance(schema, dict), "Schema must be a JSON object"

    def test_schema_has_draft_2020_12(self):
        """Schema must declare JSON Schema Draft 2020-12 in its $schema field."""
        schema = _load_schema()
        assert "$schema" in schema, "Schema must have a $schema field"
        assert "2020-12" in schema["$schema"], (
            f"Schema must reference Draft 2020-12, got: {schema['$schema']}"
        )

    def test_schema_passes_meta_schema_check(self):
        """Schema must be a valid JSON Schema document (passes meta-schema validation)."""
        schema = _load_schema()
        # Should not raise
        Draft202012Validator.check_schema(schema)

    def test_schema_has_required_fields_list(self):
        """Schema required array must include all 11 mandatory v2 fields."""
        schema = _load_schema()
        required = schema.get("required", [])
        expected_required = [
            "version", "iteration", "formula", "timestamp",
            "mult_count", "hsqc_count", "hmbc_batches", "hmbc_total",
            "pylsd_mode", "elim_annotated", "deferred_4j",
        ]
        for field in expected_required:
            assert field in required, f"Required field '{field}' missing from schema.required"

    def test_schema_readable_via_get_schema_path(self):
        """_get_schema_path() must return a readable file (packaging regression test).

        This test verifies that the schema is accessible via the same path-resolution
        function used by the CLI, catching any future packaging regressions where the
        schema file is not bundled in the wheel (CR-01).
        """
        from lucy_ng.cli.lsd import _get_schema_path
        schema_path = _get_schema_path()
        assert schema_path.exists(), f"_get_schema_path() returned non-existent path: {schema_path}"
        content = schema_path.read_text()
        schema = json.loads(content)
        assert schema.get("title") == "Constraint Inventory v2", (
            f"Schema title mismatch — expected 'Constraint Inventory v2', got: {schema.get('title')}"
        )


# ---------------------------------------------------------------------------
# TestSchemaValidation
# ---------------------------------------------------------------------------


class TestSchemaValidation:
    """Tests that the schema correctly accepts valid v2 instances and rejects invalid ones."""

    def test_accepts_minimal_valid_v2(self):
        """Minimal correct v2 instance must produce zero validation errors."""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        instance = _minimal_valid_v2()
        errors = list(validator.iter_errors(instance))
        # Should not raise
        assert errors == [], f"Expected no errors but got: {[e.message for e in errors]}"

    def test_accepts_full_v2_with_pylsd_mode(self):
        """Full v2 instance with pylsd_mode=True and non-empty deferred_4j must be valid."""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        instance = _minimal_valid_v2()
        instance.update({
            "pylsd_mode": True,
            "elim_annotated": True,
            "deferred_4j": [_valid_deferred_4j_item()],
            "hmbc_batches": [{"batch": 1, "count": 2, "correlations": ["4 8", "6 9"]}],
            "hmbc_total": 2,
        })
        errors = list(validator.iter_errors(instance))
        # Should not raise
        assert errors == [], f"Expected no errors but got: {[e.message for e in errors]}"

    def test_rejects_v1_version(self):
        """Instance with version=1 must fail with a validation error on the version field."""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        instance = _minimal_valid_v2()
        instance["version"] = 1
        errors = list(validator.iter_errors(instance))
        assert len(errors) >= 1, "Expected at least one error for version=1"
        # Error should reference the version field
        version_errors = [e for e in errors if "version" in str(e.path) or "2 was expected" in e.message]
        assert version_errors, f"Expected version-related error, got: {[e.message for e in errors]}"

    def test_rejects_deferred_4j_string_array(self):
        """Instance with deferred_4j as a string array (v1 format) must fail validation."""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        instance = _minimal_valid_v2()
        instance["deferred_4j"] = ["C4(129.4) H8(45.0)"]
        errors = list(validator.iter_errors(instance))
        assert len(errors) >= 1, "Expected at least one error for string-array deferred_4j"

    def test_rejects_missing_pylsd_mode(self):
        """Instance without pylsd_mode must fail required-field validation."""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        instance = _minimal_valid_v2()
        del instance["pylsd_mode"]
        errors = list(validator.iter_errors(instance))
        assert len(errors) >= 1, "Expected error for missing pylsd_mode field"

    def test_rejects_missing_elim_annotated(self):
        """Instance without elim_annotated must fail required-field validation."""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        instance = _minimal_valid_v2()
        del instance["elim_annotated"]
        errors = list(validator.iter_errors(instance))
        assert len(errors) >= 1, "Expected error for missing elim_annotated field"

    def test_rejects_missing_version(self):
        """Instance without version must fail required-field validation."""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        instance = _minimal_valid_v2()
        del instance["version"]
        errors = list(validator.iter_errors(instance))
        assert len(errors) >= 1, "Expected error for missing version field"

    def test_allows_extra_fields_at_top_level(self):
        """Top-level additionalProperties=true means extra fields must not cause errors."""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        instance = _minimal_valid_v2()
        instance["agent_notes"] = "Extra field from future schema version"
        instance["custom_field"] = 42
        errors = list(validator.iter_errors(instance))
        # Should not raise — top-level additionalProperties is true
        assert errors == [], f"Expected no errors with extra top-level fields, got: {[e.message for e in errors]}"


# ---------------------------------------------------------------------------
# TestDeferred4jSchema
# ---------------------------------------------------------------------------


class TestDeferred4jSchema:
    """Tests for the strict deferred_4j item schema (additionalProperties=false)."""

    def test_accepts_valid_deferred_4j_item(self):
        """A complete, correct deferred_4j item must produce no validation errors."""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        instance = _minimal_valid_v2()
        instance["deferred_4j"] = [_valid_deferred_4j_item()]
        errors = list(validator.iter_errors(instance))
        # Should not raise
        assert errors == [], f"Expected no errors but got: {[e.message for e in errors]}"

    def test_rejects_deferred_4j_item_missing_atom2(self):
        """deferred_4j item without atom2 must fail additionalProperties or required check."""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        instance = _minimal_valid_v2()
        item = _valid_deferred_4j_item()
        del item["atom2"]
        instance["deferred_4j"] = [item]
        errors = list(validator.iter_errors(instance))
        assert len(errors) >= 1, "Expected error for deferred_4j item missing atom2"

    def test_rejects_deferred_4j_wrong_annotation(self):
        """deferred_4j item with annotation='elim' (not '; ELIM') must fail const check."""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        instance = _minimal_valid_v2()
        item = _valid_deferred_4j_item()
        item["annotation"] = "elim"
        instance["deferred_4j"] = [item]
        errors = list(validator.iter_errors(instance))
        assert len(errors) >= 1, "Expected error for wrong annotation value 'elim'"
        # Error should mention the const constraint
        const_errors = [e for e in errors if "; ELIM" in e.message or e.validator == "const"]
        assert const_errors, f"Expected const error, got: {[e.message for e in errors]}"

    def test_rejects_deferred_4j_wrong_correlation_type(self):
        """deferred_4j item with correlation_type='COSY' must fail const check."""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        instance = _minimal_valid_v2()
        item = _valid_deferred_4j_item()
        item["correlation_type"] = "COSY"
        instance["deferred_4j"] = [item]
        errors = list(validator.iter_errors(instance))
        assert len(errors) >= 1, "Expected error for correlation_type='COSY' (must be 'HMBC')"

    def test_rejects_deferred_4j_item_extra_field(self):
        """deferred_4j item with an extra unknown field must fail additionalProperties=false."""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        instance = _minimal_valid_v2()
        item = _valid_deferred_4j_item()
        item["extra_field"] = "unexpected"
        instance["deferred_4j"] = [item]
        errors = list(validator.iter_errors(instance))
        assert len(errors) >= 1, "Expected error for extra field in deferred_4j item"

    def test_rejects_deferred_4j_item_atom1_zero(self):
        """deferred_4j item with atom1=0 must fail minimum=1 constraint."""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        instance = _minimal_valid_v2()
        item = _valid_deferred_4j_item()
        item["atom1"] = 0
        instance["deferred_4j"] = [item]
        errors = list(validator.iter_errors(instance))
        assert len(errors) >= 1, "Expected error for atom1=0 (minimum is 1)"

    def test_accepts_multiple_valid_deferred_4j_items(self):
        """Two valid deferred_4j items in the array must produce no errors."""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        instance = _minimal_valid_v2()
        instance["deferred_4j"] = [
            {"atom1": 4, "atom2": 8, "shift1": 129.38, "shift2": 45.03,
             "correlation_type": "HMBC", "annotation": "; ELIM"},
            {"atom1": 6, "atom2": 9, "shift1": 127.26, "shift2": 44.90,
             "correlation_type": "HMBC", "annotation": "; ELIM"},
        ]
        errors = list(validator.iter_errors(instance))
        # Should not raise
        assert errors == [], f"Expected no errors for two valid items, got: {[e.message for e in errors]}"


# ---------------------------------------------------------------------------
# TestSchemaOptionalFields
# ---------------------------------------------------------------------------


class TestSchemaOptionalFields:
    """Tests for optional fields that are typed when present."""

    def test_accepts_hmbc_batches_with_items(self):
        """Non-empty hmbc_batches with correct item structure must be valid."""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        instance = _minimal_valid_v2()
        instance["hmbc_batches"] = [
            {"batch": 1, "count": 3, "correlations": ["4 8", "6 9", "1 13"]}
        ]
        instance["hmbc_total"] = 3
        errors = list(validator.iter_errors(instance))
        # Should not raise
        assert errors == [], f"Expected no errors, got: {[e.message for e in errors]}"

    def test_rejects_hmbc_batches_item_missing_correlations(self):
        """hmbc_batches item without correlations field must fail required check."""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        instance = _minimal_valid_v2()
        instance["hmbc_batches"] = [{"batch": 1, "count": 3}]  # missing correlations
        errors = list(validator.iter_errors(instance))
        assert len(errors) >= 1, "Expected error for hmbc_batches item missing correlations"

    def test_accepts_deff_not_patterns(self):
        """deff_not_patterns as string array must be valid."""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        instance = _minimal_valid_v2()
        instance["deff_not_patterns"] = ["C1CC1", "C1CCC1", "C1NC1"]
        errors = list(validator.iter_errors(instance))
        # Should not raise
        assert errors == [], f"Expected no errors, got: {[e.message for e in errors]}"

    def test_accepts_elim_value_null(self):
        """elim_value=null must be valid (standard run with no bare ELIM command)."""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        instance = _minimal_valid_v2()
        instance["elim_value"] = None
        errors = list(validator.iter_errors(instance))
        # Should not raise
        assert errors == [], f"Expected no errors with elim_value=null, got: {[e.message for e in errors]}"

    def test_accepts_elim_value_integer(self):
        """elim_value as integer must be valid (last-resort zero-solution recovery)."""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        instance = _minimal_valid_v2()
        instance["elim_value"] = 4
        errors = list(validator.iter_errors(instance))
        # Should not raise
        assert errors == [], f"Expected no errors with elim_value=4, got: {[e.message for e in errors]}"


# ---------------------------------------------------------------------------
# Helpers for CLI tests
# ---------------------------------------------------------------------------


def _make_v2_lsd_content(inventory_json: str) -> str:
    """Wrap a JSON string as a v2 inventory block inside a minimal LSD file."""
    lines = []
    lines.append("; === CONSTRAINT INVENTORY v2 ===")
    for line in inventory_json.splitlines():
        lines.append(f"; {line}" if line else ";")
    lines.append("; === END CONSTRAINT INVENTORY ===")
    lines.append("; End of inventory")
    return "\n".join(lines) + "\n"


def _minimal_v2_inventory_json() -> str:
    """Return JSON string for a minimal valid v2 inventory."""
    return json.dumps({
        "version": 2,
        "iteration": 1,
        "formula": "C6H6",
        "timestamp": "2026-01-01T00:00:00Z",
        "mult_count": 6,
        "hsqc_count": 6,
        "hmbc_batches": [],
        "hmbc_total": 0,
        "pylsd_mode": False,
        "elim_annotated": False,
        "deferred_4j": [],
    }, indent=2)


# ---------------------------------------------------------------------------
# TestValidateInventoryCLI
# ---------------------------------------------------------------------------


class TestValidateInventoryCLI:
    """Integration tests for lucy lsd validate-inventory via CliRunner."""

    def test_valid_v2_file_exits_0(self, tmp_path):
        """Valid v2 LSD file must cause validate-inventory to exit with code 0."""
        lsd_file = tmp_path / "compound.lsd"
        lsd_file.write_text(_make_v2_lsd_content(_minimal_v2_inventory_json()))
        runner = CliRunner()
        result = runner.invoke(lsd, ["validate-inventory", str(lsd_file)], catch_exceptions=False)
        assert result.exit_code == 0, f"Expected exit 0, got {result.exit_code}. Output: {result.output}"

    def test_valid_v2_file_format_json(self, tmp_path):
        """Valid v2 LSD file with --format json must exit 0 and return valid:true JSON."""
        lsd_file = tmp_path / "compound.lsd"
        lsd_file.write_text(_make_v2_lsd_content(_minimal_v2_inventory_json()))
        runner = CliRunner()
        result = runner.invoke(lsd, ["validate-inventory", str(lsd_file), "--format", "json"], catch_exceptions=False)
        assert result.exit_code == 0, f"Expected exit 0, got {result.exit_code}. Output: {result.output}"
        data = json.loads(result.output)
        assert data["valid"] is True, f"Expected valid=true, got: {data}"

    def test_v1_block_exits_1(self, tmp_path):
        """LSD file with v1 inventory delimiter must cause validate-inventory to exit 1."""
        v1_content = "; === CONSTRAINT INVENTORY v1 ===\n; {}\n; === END CONSTRAINT INVENTORY ===\n"
        lsd_file = tmp_path / "compound.lsd"
        lsd_file.write_text(v1_content)
        runner = CliRunner()
        result = runner.invoke(lsd, ["validate-inventory", str(lsd_file)])
        assert result.exit_code == 1, f"Expected exit 1 for v1 block, got {result.exit_code}. Output: {result.output}"

    def test_v1_block_format_json_legacy_message(self, tmp_path):
        """v1 LSD file with --format json must exit 1 and include legacy error message."""
        v1_content = "; === CONSTRAINT INVENTORY v1 ===\n; {}\n; === END CONSTRAINT INVENTORY ===\n"
        lsd_file = tmp_path / "compound.lsd"
        lsd_file.write_text(v1_content)
        runner = CliRunner()
        result = runner.invoke(lsd, ["validate-inventory", str(lsd_file), "--format", "json"])
        assert result.exit_code == 1, f"Expected exit 1, got {result.exit_code}. Output: {result.output}"
        data = json.loads(result.output)
        assert data["valid"] is False
        assert "Legacy v1 inventory detected" in data["errors"][0]["message"]

    def test_no_inventory_block_exits_1(self, tmp_path):
        """LSD file with no inventory block at all must cause validate-inventory to exit 1."""
        lsd_file = tmp_path / "compound.lsd"
        lsd_file.write_text("; Plain LSD file without any inventory block\nMULT 1 C 2 0\n")
        runner = CliRunner()
        result = runner.invoke(lsd, ["validate-inventory", str(lsd_file)])
        assert result.exit_code == 1, f"Expected exit 1 for missing block, got {result.exit_code}. Output: {result.output}"

    def test_invalid_schema_exits_1(self, tmp_path):
        """v2 LSD file with version:1 inside inventory block must cause validate-inventory to exit 1."""
        bad_json = json.dumps({
            "version": 1,
            "iteration": 1,
            "formula": "C6H6",
            "timestamp": "2026-01-01T00:00:00Z",
            "mult_count": 6,
            "hsqc_count": 6,
            "hmbc_batches": [],
            "hmbc_total": 0,
            "pylsd_mode": False,
            "elim_annotated": False,
            "deferred_4j": [],
        }, indent=2)
        lsd_file = tmp_path / "compound.lsd"
        lsd_file.write_text(_make_v2_lsd_content(bad_json))
        runner = CliRunner()
        result = runner.invoke(lsd, ["validate-inventory", str(lsd_file)])
        assert result.exit_code == 1, f"Expected exit 1 for schema violation, got {result.exit_code}. Output: {result.output}"


# ---------------------------------------------------------------------------
# TestGateLogic
# ---------------------------------------------------------------------------


class TestGateLogic:
    """Unit tests for G2 gate: bare ELIM command detection vs ; ELIM annotation."""

    def test_g2_bare_elim_detected(self):
        """G2 grep pattern ^ELIM must match a bare ELIM command line."""
        assert re.match(r"^ELIM", "ELIM 4 4") is not None

    def test_g2_hmbc_elim_annotation_not_matched(self):
        """G2 grep pattern ^ELIM must NOT match an HMBC line with trailing ; ELIM comment."""
        assert re.match(r"^ELIM", "HMBC 4 8 2 4 ; ELIM") is None

    def test_g2_comment_line_not_matched(self):
        """G2 grep pattern ^ELIM must NOT match a comment line starting with semicolon."""
        assert re.match(r"^ELIM", "; ELIM") is None
