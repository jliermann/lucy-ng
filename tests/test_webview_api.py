"""Tests for Phase 91 API endpoints, depiction, frontend, and packaging.

Wave 0 Nyquist scaffold — these tests are RED until Plans 02/03/04 land.
Each class maps to a target plan for traceability.

Test status legend:
  RED  = ImportError / AssertionError expected until implementation ships
  SKIP = webview extra absent or target modules not yet available

Import rule (WV-08): ALL imports of fastapi and lucy_ng.webview.* are
INSIDE test function bodies — never at module level — so this file
collects cleanly even before the router modules exist.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import tomllib

# ---------------------------------------------------------------------------
# TestStatusEndpoint [→ Plan 02]
# ---------------------------------------------------------------------------


class TestStatusEndpoint:
    """WV-03 / WV-06: GET /api/status returns live status or waiting payload."""

    def test_waiting_when_empty(self, empty_analysis_dir: Path) -> None:
        """Empty analysis dir → state == 'waiting', HTTP 200."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.routers import status  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("webview extra or status router not yet available")

        from fastapi import FastAPI  # pyright: ignore[reportMissingModuleSource]

        app = FastAPI()
        app.include_router(status.make_router(empty_analysis_dir))

        with TestClient(app) as client:
            r = client.get("/api/status")

        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        assert r.json()["state"] == "waiting", f"Expected state=waiting: {r.json()}"

    def test_live_from_timing_jsonl(self, live_analysis_dir: Path) -> None:
        """Live run (timing.jsonl only) → state in {running,waiting}, iteration set."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.routers import status  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("webview extra or status router not yet available")

        from fastapi import FastAPI  # pyright: ignore[reportMissingModuleSource]

        app = FastAPI()
        app.include_router(status.make_router(live_analysis_dir))

        with TestClient(app) as client:
            r = client.get("/api/status")

        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data["state"] in ("running", "waiting"), (
            f"Expected state in {{running,waiting}}: {data}"
        )
        assert data.get("iteration") is not None, (
            f"Expected iteration to be set from timing.jsonl: {data}"
        )

    def test_complete_from_timing_json(self, final_analysis_dir: Path) -> None:
        """Finalized run (timing.json) → state == 'complete', elapsed_s == 5400."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.routers import status  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("webview extra or status router not yet available")

        from fastapi import FastAPI  # pyright: ignore[reportMissingModuleSource]

        app = FastAPI()
        app.include_router(status.make_router(final_analysis_dir))

        with TestClient(app) as client:
            r = client.get("/api/status")

        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data["state"] == "complete", f"Expected state=complete: {data}"
        assert data.get("elapsed_s") == 5400, (
            f"Expected elapsed_s=5400 from timing.json total_duration_s: {data}"
        )


# ---------------------------------------------------------------------------
# TestLogEndpoint [→ Plan 02]
# ---------------------------------------------------------------------------


class TestLogEndpoint:
    """WV-05 / WV-06: GET /api/log returns CASE-PROGRESS.md content or waiting."""

    def test_log_returns_content(self, live_analysis_dir: Path) -> None:
        """Live dir with CASE-PROGRESS.md → state=='ok', content contains 'Iteration 1'."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.routers import log  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("webview extra or log router not yet available")

        from fastapi import FastAPI  # pyright: ignore[reportMissingModuleSource]

        app = FastAPI()
        app.include_router(log.make_router(live_analysis_dir))

        with TestClient(app) as client:
            r = client.get("/api/log")

        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data.get("state") == "ok", f"Expected state=ok: {data}"
        assert "Iteration 1" in data.get("content", ""), (
            f"Expected 'Iteration 1' in log content: {data}"
        )

    def test_log_waiting_when_empty(self, empty_analysis_dir: Path) -> None:
        """Empty dir → state=='waiting', HTTP 200."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.routers import log  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("webview extra or log router not yet available")

        from fastapi import FastAPI  # pyright: ignore[reportMissingModuleSource]

        app = FastAPI()
        app.include_router(log.make_router(empty_analysis_dir))

        with TestClient(app) as client:
            r = client.get("/api/log")

        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        assert r.json()["state"] == "waiting", f"Expected state=waiting: {r.json()}"


# ---------------------------------------------------------------------------
# TestStructuresEndpoint [→ Plan 03]
# ---------------------------------------------------------------------------


class TestStructuresEndpoint:
    """WV-04 / WV-06: GET /api/structures and GET /api/structure/{i}.svg."""

    def test_unranked_from_solutions_smi(self, live_analysis_dir: Path) -> None:
        """Live dir (no ranking_results.json) → source=='unranked', <=10 structures."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.routers import (
                structures,  # pyright: ignore[reportMissingModuleSource]
            )
        except ImportError:
            pytest.skip("webview extra or structures router not yet available")

        from fastapi import FastAPI  # pyright: ignore[reportMissingModuleSource]

        app = FastAPI()
        app.include_router(structures.make_router(live_analysis_dir))

        with TestClient(app) as client:
            r = client.get("/api/structures")

        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data["source"] == "unranked", f"Expected source=unranked: {data}"
        assert len(data["structures"]) <= 10, (
            f"Expected at most 10 structures: {len(data['structures'])}"
        )

    def test_ranked_from_ranking_results(self, final_analysis_dir: Path) -> None:
        """Final dir (ranking_results.json) → source=='ranked', first rank==1, mae set."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.routers import (
                structures,  # pyright: ignore[reportMissingModuleSource]
            )
        except ImportError:
            pytest.skip("webview extra or structures router not yet available")

        from fastapi import FastAPI  # pyright: ignore[reportMissingModuleSource]

        app = FastAPI()
        app.include_router(structures.make_router(final_analysis_dir))

        with TestClient(app) as client:
            r = client.get("/api/structures")

        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data["source"] == "ranked", f"Expected source=ranked: {data}"
        assert len(data["structures"]) >= 1, "Expected at least one ranked structure"
        first = data["structures"][0]
        assert first["rank"] == 1, f"Expected first rank==1: {first}"
        assert first["mae"] is not None, f"Expected mae set for ranked: {first}"

    def test_ranked_with_null_rank_does_not_drop_tier(self, tmp_path: Path) -> None:
        """A present-but-null rank must NOT crash the ranked tier into unranked (CR-01)."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.routers import (
                structures,  # pyright: ignore[reportMissingModuleSource]
            )
        except ImportError:
            pytest.skip("webview extra or structures router not yet available")

        import json as _json

        from fastapi import FastAPI  # pyright: ignore[reportMissingModuleSource]

        solutions = [
            {"rank": 2, "solution_index": 1, "smiles": "CCO", "mae": 0.3, "quality": "ok"},
            {"rank": None, "solution_index": 2, "smiles": "CCN", "mae": None, "quality": None},
            {"rank": 1, "solution_index": 0, "smiles": "c1ccccc1", "mae": 0.1, "quality": "ok"},
        ]
        (tmp_path / "ranking_results.json").write_text(
            _json.dumps({"solutions": solutions, "total_solutions": 3}),
            encoding="utf-8",
        )

        app = FastAPI()
        app.include_router(structures.make_router(tmp_path))

        with TestClient(app) as client:
            r = client.get("/api/structures")

        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data["source"] == "ranked", f"null rank must not drop ranked tier: {data}"
        assert data["structures"][0]["rank"] == 1, "rank 1 must sort first"
        assert data["structures"][-1]["rank"] is None, "null rank must sort last"

    def test_out_of_range_svg_returns_404(self, live_analysis_dir: Path) -> None:
        """GET /api/structure/999.svg → 404 when index is out of range."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.routers import (
                structures,  # pyright: ignore[reportMissingModuleSource]
            )
        except ImportError:
            pytest.skip("webview extra or structures router not yet available")

        from fastapi import FastAPI  # pyright: ignore[reportMissingModuleSource]

        app = FastAPI()
        app.include_router(structures.make_router(live_analysis_dir))

        with TestClient(app) as client:
            r = client.get("/api/structure/999.svg")

        assert r.status_code == 404, f"Expected 404 for out-of-range index, got {r.status_code}"

    def test_malformed_smiles_returns_placeholder_svg(self, live_analysis_dir: Path) -> None:
        """Index 2 (malformed SMILES) → 200, image/svg+xml, placeholder content."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.routers import (
                structures,  # pyright: ignore[reportMissingModuleSource]
            )
        except ImportError:
            pytest.skip("webview extra or structures router not yet available")

        from fastapi import FastAPI  # pyright: ignore[reportMissingModuleSource]

        app = FastAPI()
        app.include_router(structures.make_router(live_analysis_dir))

        with TestClient(app) as client:
            # Index 2 is "not_a_real_smiles_XXXX" in the live fixture
            r = client.get("/api/structure/2.svg")

        assert r.status_code == 200, f"Expected 200 for malformed SMILES placeholder, got {r.status_code}"
        assert "image/svg+xml" in r.headers.get("content-type", ""), (
            f"Expected image/svg+xml content-type: {r.headers.get('content-type')}"
        )
        # Placeholder SVG contains grey rect or question mark
        assert "?" in r.text or "rect" in r.text, (
            f"Expected placeholder SVG with '?' or 'rect': {r.text[:200]}"
        )

    def test_valid_smiles_returns_real_svg(self, live_analysis_dir: Path) -> None:
        """Index 0 (aspirin — valid SMILES) → 200, image/svg+xml, RDKit path elements."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.routers import (
                structures,  # pyright: ignore[reportMissingModuleSource]
            )
        except ImportError:
            pytest.skip("webview extra or structures router not yet available")

        from fastapi import FastAPI  # pyright: ignore[reportMissingModuleSource]

        app = FastAPI()
        app.include_router(structures.make_router(live_analysis_dir))

        with TestClient(app) as client:
            # Index 0 is "CC(=O)Oc1ccccc1C(=O)O" (aspirin) — valid SMILES
            r = client.get("/api/structure/0.svg")

        assert r.status_code == 200, f"Expected 200 for valid SMILES, got {r.status_code}"
        assert "image/svg+xml" in r.headers.get("content-type", ""), (
            f"Expected image/svg+xml content-type: {r.headers.get('content-type')}"
        )
        # Real RDKit SVG contains path or line drawing elements
        assert "<path" in r.text or "<line" in r.text, (
            f"Expected RDKit SVG drawing elements: {r.text[:300]}"
        )


# ---------------------------------------------------------------------------
# TestDepiction [→ Plan 03]
# ---------------------------------------------------------------------------


class TestDepiction:
    """WV-04: lucy_ng.webview.depiction render/placeholder functions."""

    def test_render_valid_smiles_returns_svg_string(self) -> None:
        """render_smiles('c1ccccc1') returns a str containing 'svg'."""
        try:
            from lucy_ng.webview.depiction import (
                render_smiles,  # pyright: ignore[reportMissingModuleSource]
            )
        except ImportError:
            pytest.skip("lucy_ng.webview.depiction not yet available")

        result = render_smiles("c1ccccc1")
        assert result is not None, "Expected SVG string for valid benzene SMILES"
        assert isinstance(result, str), f"Expected str, got {type(result)}"
        assert "svg" in result.lower(), "Expected 'svg' in render result"

    def test_render_malformed_smiles_returns_none(self) -> None:
        """render_smiles('not_a_real_smiles_XXXX') returns None."""
        try:
            from lucy_ng.webview.depiction import (
                render_smiles,  # pyright: ignore[reportMissingModuleSource]
            )
        except ImportError:
            pytest.skip("lucy_ng.webview.depiction not yet available")

        result = render_smiles("not_a_real_smiles_XXXX")
        assert result is None, f"Expected None for malformed SMILES, got: {result!r}"

    def test_render_never_raises_on_draw_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """render_smiles returns None (never raises) if RDKit drawing fails (CR-02).

        A SMILES can parse via MolFromSmiles yet fail 2D preparation (e.g.
        KekulizeException); the endpoint must degrade to a placeholder, not 500.
        """
        try:
            from lucy_ng.webview import depiction  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("lucy_ng.webview.depiction not yet available")

        def _boom(*_a: object, **_k: object) -> None:
            raise RuntimeError("simulated kekulize/draw failure")

        monkeypatch.setattr(depiction, "PrepareMolForDrawing", _boom)
        result = depiction.render_smiles("c1ccccc1")
        assert result is None, f"Expected None when drawing raises, got: {result!r}"

    def test_placeholder_svg_returns_svg_string(self) -> None:
        """placeholder_svg() returns a str containing 'svg'."""
        try:
            from lucy_ng.webview.depiction import (
                placeholder_svg,  # pyright: ignore[reportMissingModuleSource]
            )
        except ImportError:
            pytest.skip("lucy_ng.webview.depiction not yet available")

        result = placeholder_svg()
        assert isinstance(result, str), f"Expected str, got {type(result)}"
        assert "svg" in result.lower(), "Expected 'svg' in placeholder result"


# ---------------------------------------------------------------------------
# TestFrontend [→ Plan 04]
# ---------------------------------------------------------------------------


class TestFrontend:
    """WV-06: GET / serves index.html with Content-Type text/html."""

    def test_index_html_served(self, live_analysis_dir: Path) -> None:
        """GET / → HTTP 200, Content-Type starts with 'text/html'."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.app import create_app  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("webview extra or create_app not yet available")

        with TestClient(create_app(live_analysis_dir)) as client:
            r = client.get("/")

        assert r.status_code == 200, f"Expected 200 for GET /, got {r.status_code}: {r.text[:200]}"
        content_type = r.headers.get("content-type", "")
        assert content_type.startswith("text/html"), (
            f"Expected content-type to start with text/html: {content_type!r}"
        )

    def test_webview_js_served(self, live_analysis_dir: Path) -> None:
        """GET /webview.js → HTTP 200, Content-Type starts with 'application/javascript'."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.app import create_app  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("webview extra or create_app not yet available")

        with TestClient(create_app(live_analysis_dir)) as client:
            r = client.get("/webview.js")

        assert r.status_code == 200, (
            f"Expected 200 for GET /webview.js, got {r.status_code}: {r.text[:200]}"
        )
        content_type = r.headers.get("content-type", "")
        assert content_type.startswith("application/javascript") or content_type.startswith(
            "text/javascript"
        ), f"Expected content-type to start with application/javascript: {content_type!r}"


# ---------------------------------------------------------------------------
# TestWiring [→ Plan 04]
# ---------------------------------------------------------------------------


class TestWiring:
    """WV-03/04/05: create_app() docks all three routers — each returns 200."""

    def test_all_api_endpoints_reachable(self, live_analysis_dir: Path) -> None:
        """GET /api/status, /api/structures, /api/log each return 200."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.app import create_app  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("webview extra or create_app not yet available")

        with TestClient(create_app(live_analysis_dir)) as client:
            r_status = client.get("/api/status")
            r_structures = client.get("/api/structures")
            r_log = client.get("/api/log")

        assert r_status.status_code == 200, (
            f"GET /api/status expected 200, got {r_status.status_code}: {r_status.text}"
        )
        assert r_structures.status_code == 200, (
            f"GET /api/structures expected 200, got {r_structures.status_code}: {r_structures.text}"
        )
        assert r_log.status_code == 200, (
            f"GET /api/log expected 200, got {r_log.status_code}: {r_log.text}"
        )


# ---------------------------------------------------------------------------
# TestPackaging [→ Plan 04]
# ---------------------------------------------------------------------------


class TestPackaging:
    """WV-08: pyproject.toml hatch artifacts include src/lucy_ng/webview/static/*."""

    def test_hatch_artifacts_include_static(self) -> None:
        """[tool.hatch.build.targets.wheel].artifacts contains 'src/lucy_ng/webview/static/*'."""
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as fh:
            pyproject = tomllib.load(fh)

        artifacts: list[str] = (
            pyproject.get("tool", {})
            .get("hatch", {})
            .get("build", {})
            .get("targets", {})
            .get("wheel", {})
            .get("artifacts", [])
        )

        assert "src/lucy_ng/webview/static/*" in artifacts, (
            f"'src/lucy_ng/webview/static/*' not found in hatch wheel artifacts.\n"
            f"Current artifacts: {artifacts}"
        )

    def test_webview_js_present_in_static(self) -> None:
        """webview.js exists at the flat static/ level so the existing hatch glob packages it."""
        static_dir = Path(__file__).parent.parent / "src" / "lucy_ng" / "webview" / "static"
        assert (static_dir / "webview.js").exists(), (
            "webview.js must exist at the flat static/ level for the existing hatch glob "
            "to cover it"
        )


# ---------------------------------------------------------------------------
# TestMarkdownRendererSafety [→ Plan 02]
# ---------------------------------------------------------------------------


class TestMarkdownRendererSafety:
    """LOG-01 / D-02: static/webview.js must never assign server content via innerHTML."""

    def test_no_innerhtml_in_source(self) -> None:
        """'innerHTML' must not appear anywhere in static/webview.js (regression guard)."""
        js_path = (
            Path(__file__).parent.parent
            / "src" / "lucy_ng" / "webview" / "static" / "webview.js"
        )
        if not js_path.exists():
            pytest.skip("webview.js not yet extracted")
        source = js_path.read_text(encoding="utf-8")
        assert "innerHTML" not in source, (
            "webview.js must never use innerHTML (XSS guard, D-02) — "
            "found the literal substring 'innerHTML' in the source"
        )


# ---------------------------------------------------------------------------
# Phase 94 fixtures — hand-authored to the CONTEXT.md LOCKED peaks-JSON schema.
#
# No on-disk analysis/ directory on this machine matches these exact field
# names (RESEARCH.md Assumptions A1-A5) — these fixtures are built by hand to
# the canonical_refs schema, not copied from any real run.
# ---------------------------------------------------------------------------


@pytest.fixture
def tables_analysis_dir(tmp_path: Path) -> Path:
    """analysis_dir with peaks/{carbon_signals,hsqc,hmbc,cosy}.json (LOCKED schema).

    Hand-authored to CONTEXT.md's `<canonical_refs>` "Data shapes" field names.
    Includes at least one HMBC row per flag value (ok/potential_4J/1J_artifact)
    and one large intensity (5559614) to exercise the compact-intensity
    formatter target downstream (frontend, Plan 03).
    """
    import json as _json

    peaks_dir = tmp_path / "peaks"
    peaks_dir.mkdir()

    (peaks_dir / "carbon_signals.json").write_text(
        _json.dumps(
            {
                "formula": "C14H16",
                "dbe": 6,
                "solvent": "CDCl3",
                "note": "9 signals, 2 overlapping aromatic CH pairs",
                "signals": [
                    {
                        "atom": 1,
                        "ppm": 172.4,
                        "mult": "s",
                        "nC": 1,
                        "assignment": "C=O",
                        "confidence": "high",
                    },
                    {
                        "atom": 2,
                        "ppm": 128.9,
                        "mult": "d",
                        "nC": 2,
                        "assignment": "ArCH",
                        "confidence": "medium",
                    },
                    {
                        "atom": 3,
                        "ppm": 21.3,
                        "mult": "q",
                        "nC": 1,
                        "assignment": "ArCH3",
                        "confidence": "high",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    (peaks_dir / "hsqc.json").write_text(
        _json.dumps(
            {
                "experiment": "hsqcedetgp",
                "count": 3,
                "note": "3 one-bond C-H correlations, all matched to real carbons",
                "peaks": [
                    {
                        "carbon_ppm": 128.9,
                        "proton_ppm": 7.31,
                        "intensity": 5559614,
                        "matched_real_carbon": True,
                        "one_bond": True,
                    },
                    {
                        "carbon_ppm": 21.3,
                        "proton_ppm": 2.35,
                        "intensity": 1520340,
                        "matched_real_carbon": True,
                        "one_bond": True,
                    },
                    {
                        "carbon_ppm": 55.2,
                        "proton_ppm": 3.68,
                        "intensity": 980210,
                        "matched_real_carbon": False,
                        "one_bond": True,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    (peaks_dir / "hmbc.json").write_text(
        _json.dumps(
            {
                "experiment": "hmbcgplpndqf",
                "raw_count": 913,
                "kept_count": 29,
                "flag_rules": "1J_artifact = matches an HSQC one-bond pair; "
                "potential_4J = 4-bond aromatic candidate",
                "note": "29 kept of 913 raw correlations after curation",
                "peaks": [
                    {
                        "carbon_ppm": 172.4,
                        "carbon_ppm_observed": 172.5,
                        "proton_ppm": 7.31,
                        "intensity": 445210,
                        "flag": "ok",
                    },
                    {
                        "carbon_ppm": 128.9,
                        "carbon_ppm_observed": 128.8,
                        "proton_ppm": 2.35,
                        "intensity": 210330,
                        "flag": "potential_4J",
                    },
                    {
                        "carbon_ppm": 21.3,
                        "carbon_ppm_observed": 21.2,
                        "proton_ppm": 2.35,
                        "intensity": 5559614,
                        "flag": "1J_artifact",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    (peaks_dir / "cosy.json").write_text(
        _json.dumps(
            {
                "experiment": "cosygpqf",
                "count": 2,
                "note": "2 vicinal proton-proton correlations",
                "peaks": [
                    {"proton_a_ppm": 7.31, "proton_b_ppm": 7.28, "intensity": 335120},
                    {"proton_a_ppm": 3.68, "proton_b_ppm": 2.35, "intensity": 118400},
                ],
            }
        ),
        encoding="utf-8",
    )

    return tmp_path


@pytest.fixture
def tables_iterations_dir(tmp_path: Path) -> Path:
    """analysis_dir with a multi-iteration compound.lsd set (D-02 selection target).

    iteration_01/compound.lsd    — bare, iteration=1
    iteration_02_anchor_recovery/compound.lsd — family-suffixed, iteration=2,
    HIGHER numeric prefix, exercising the "highest iteration_(\\d+), across
    families" selection logic (D-02).
    """

    def _inventory_block(iteration: int) -> str:
        lines = [
            "; === CONSTRAINT INVENTORY v2 ===",
            f'; {{"version": 2, "iteration": {iteration}, "formula": "C14H16",',
            '; "timestamp": "2026-07-09T10:00:00Z",',
            f'; "mult_count": {9 + iteration}, "hsqc_count": {3 + iteration},',
            '; "hmbc_batches": [{"batch": 1, "count": 2, "correlations": ["1 2", "2 3"]}],',
            f'; "hmbc_total": {2 + iteration},',
            '; "bond_constraints": ["1 2"],',
            '; "cosy_equiv_pairs": [],',
            '; "applied_from_detection": ["no heteroatom constraints (pure-carbon formula)"],',
            '; "pending_from_detection": ["deferred 4J pair still held out"],',
            '; "deff_fexp": {"status": "none", "fragment_smiles": null},',
            '; "elim_budget": 0,',
            '; "ring_exclusion_enabled": true}',
            "; === END CONSTRAINT INVENTORY ===",
            ";",
            "MULT 1 C 3 3    ; CH3",
            "",
        ]
        return "\n".join(lines)

    iter1_dir = tmp_path / "iteration_01"
    iter1_dir.mkdir()
    (iter1_dir / "compound.lsd").write_text(_inventory_block(1), encoding="utf-8")

    iter2_dir = tmp_path / "iteration_02_anchor_recovery"
    iter2_dir.mkdir()
    (iter2_dir / "compound.lsd").write_text(_inventory_block(2), encoding="utf-8")

    return tmp_path


# ---------------------------------------------------------------------------
# TestTablesEndpoint [→ Plan 02]
#
# RED-by-skip until src/lucy_ng/webview/routers/tables.py exists (WV-08).
# Covers TBL-01/02/03 and the SC4 degradation contract independently for
# all 5 panels (carbon, hsqc, hmbc, cosy, constraints).
# ---------------------------------------------------------------------------


class TestTablesEndpoint:
    """TBL-01/02/03: GET /api/tables/{carbon,hsqc,hmbc,cosy,constraints}."""

    def test_carbon_returns_rows(self, tables_analysis_dir: Path) -> None:
        """/api/tables/carbon → state=='ok', rows expose ppm/mult/nC/assignment/confidence."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.routers import tables  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("webview extra or tables router not yet available")

        from fastapi import FastAPI  # pyright: ignore[reportMissingModuleSource]

        app = FastAPI()
        app.include_router(tables.make_router(tables_analysis_dir))

        with TestClient(app) as client:
            r = client.get("/api/tables/carbon")

        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data.get("state") == "ok", f"Expected state=ok: {data}"
        rows = data.get("rows", [])
        assert len(rows) > 0, f"Expected non-empty rows: {data}"
        for field in ("ppm", "mult", "nC", "assignment", "confidence"):
            assert field in rows[0], f"Expected {field!r} in carbon row: {rows[0]}"

    def test_carbon_waiting_when_absent(self, empty_analysis_dir: Path) -> None:
        """/api/tables/carbon on an empty analysis dir → state=='waiting', HTTP 200."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.routers import tables  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("webview extra or tables router not yet available")

        from fastapi import FastAPI  # pyright: ignore[reportMissingModuleSource]

        app = FastAPI()
        app.include_router(tables.make_router(empty_analysis_dir))

        with TestClient(app) as client:
            r = client.get("/api/tables/carbon")

        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        assert r.json().get("state") == "waiting", f"Expected state=waiting: {r.json()}"

    def test_hsqc_cosy_return_ok(self, tables_analysis_dir: Path) -> None:
        """/api/tables/hsqc and /api/tables/cosy both → state=='ok' with their field sets."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.routers import tables  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("webview extra or tables router not yet available")

        from fastapi import FastAPI  # pyright: ignore[reportMissingModuleSource]

        app = FastAPI()
        app.include_router(tables.make_router(tables_analysis_dir))

        with TestClient(app) as client:
            r_hsqc = client.get("/api/tables/hsqc")
            r_cosy = client.get("/api/tables/cosy")

        assert r_hsqc.status_code == 200, f"Expected 200, got {r_hsqc.status_code}: {r_hsqc.text}"
        hsqc_data = r_hsqc.json()
        assert hsqc_data.get("state") == "ok", f"Expected state=ok: {hsqc_data}"
        hsqc_rows = hsqc_data.get("rows", [])
        assert len(hsqc_rows) > 0, f"Expected non-empty hsqc rows: {hsqc_data}"
        for field in ("carbon_ppm", "proton_ppm", "intensity", "matched_real_carbon", "one_bond"):
            assert field in hsqc_rows[0], f"Expected {field!r} in hsqc row: {hsqc_rows[0]}"

        assert r_cosy.status_code == 200, f"Expected 200, got {r_cosy.status_code}: {r_cosy.text}"
        cosy_data = r_cosy.json()
        assert cosy_data.get("state") == "ok", f"Expected state=ok: {cosy_data}"
        cosy_rows = cosy_data.get("rows", [])
        assert len(cosy_rows) > 0, f"Expected non-empty cosy rows: {cosy_data}"
        for field in ("proton_a_ppm", "proton_b_ppm", "intensity"):
            assert field in cosy_rows[0], f"Expected {field!r} in cosy row: {cosy_rows[0]}"

    def test_hmbc_preserves_flag_verbatim(self, tables_analysis_dir: Path) -> None:
        """/api/tables/hmbc rows retain each flag value UNMODIFIED (colouring is frontend-only)."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.routers import tables  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("webview extra or tables router not yet available")

        from fastapi import FastAPI  # pyright: ignore[reportMissingModuleSource]

        app = FastAPI()
        app.include_router(tables.make_router(tables_analysis_dir))

        with TestClient(app) as client:
            r = client.get("/api/tables/hmbc")

        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data.get("state") == "ok", f"Expected state=ok: {data}"
        rows = data.get("rows", [])
        flags = {row.get("flag") for row in rows}
        assert flags == {"ok", "potential_4J", "1J_artifact"}, (
            f"Expected flag set {{'ok','potential_4J','1J_artifact'}}, got {flags}: {data}"
        )

    def test_malformed_json_returns_waiting(self, tmp_path: Path) -> None:
        """Invalid JSON in carbon_signals.json → /api/tables/carbon state=='waiting', never 500."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.routers import tables  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("webview extra or tables router not yet available")

        from fastapi import FastAPI  # pyright: ignore[reportMissingModuleSource]

        peaks_dir = tmp_path / "peaks"
        peaks_dir.mkdir()
        (peaks_dir / "carbon_signals.json").write_text("{not valid", encoding="utf-8")

        app = FastAPI()
        app.include_router(tables.make_router(tmp_path))

        with TestClient(app) as client:
            r = client.get("/api/tables/carbon")

        assert r.status_code == 200, f"Expected 200 (never 500), got {r.status_code}: {r.text}"
        assert r.json().get("state") == "waiting", f"Expected state=waiting: {r.json()}"

    def test_constraints_selects_highest_iteration(self, tables_iterations_dir: Path) -> None:
        """/api/tables/constraints selects iteration_02_anchor_recovery (highest numeric prefix)."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.routers import tables  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("webview extra or tables router not yet available")

        from fastapi import FastAPI  # pyright: ignore[reportMissingModuleSource]

        app = FastAPI()
        app.include_router(tables.make_router(tables_iterations_dir))

        with TestClient(app) as client:
            r = client.get("/api/tables/constraints")

        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data.get("state") == "ok", f"Expected state=ok: {data}"
        inventory = data.get("inventory", {})
        assert inventory.get("iteration") == 2, (
            f"Expected the family-suffixed iteration_02_anchor_recovery (iteration==2) "
            f"to win by highest numeric prefix: {data}"
        )

    def test_constraints_waiting_when_malformed(self, tmp_path: Path) -> None:
        """START delimiter present but no END delimiter → state=='waiting', HTTP 200."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.routers import tables  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("webview extra or tables router not yet available")

        from fastapi import FastAPI  # pyright: ignore[reportMissingModuleSource]

        iter_dir = tmp_path / "iteration_01"
        iter_dir.mkdir()
        (iter_dir / "compound.lsd").write_text(
            '; === CONSTRAINT INVENTORY v2 ===\n'
            '; {"version": 2, "iteration": 1\n'
            "MULT 1 C 3 3    ; CH3\n",
            encoding="utf-8",
        )

        app = FastAPI()
        app.include_router(tables.make_router(tmp_path))

        with TestClient(app) as client:
            r = client.get("/api/tables/constraints")

        assert r.status_code == 200, f"Expected 200 (never 500), got {r.status_code}: {r.text}"
        assert r.json().get("state") == "waiting", f"Expected state=waiting: {r.json()}"

    def test_constraints_waiting_when_absent(self, empty_analysis_dir: Path) -> None:
        """No iteration_NN/compound.lsd at all → state=='waiting', HTTP 200."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.routers import tables  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("webview extra or tables router not yet available")

        from fastapi import FastAPI  # pyright: ignore[reportMissingModuleSource]

        app = FastAPI()
        app.include_router(tables.make_router(empty_analysis_dir))

        with TestClient(app) as client:
            r = client.get("/api/tables/constraints")

        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        assert r.json().get("state") == "waiting", f"Expected state=waiting: {r.json()}"

    def test_hsqc_waiting_when_absent(self, empty_analysis_dir: Path) -> None:
        """/api/tables/hsqc on an empty analysis dir → state=='waiting', HTTP 200."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.routers import tables  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("webview extra or tables router not yet available")

        from fastapi import FastAPI  # pyright: ignore[reportMissingModuleSource]

        app = FastAPI()
        app.include_router(tables.make_router(empty_analysis_dir))

        with TestClient(app) as client:
            r = client.get("/api/tables/hsqc")

        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        assert r.json().get("state") == "waiting", f"Expected state=waiting: {r.json()}"

    def test_hsqc_waiting_when_malformed(self, tmp_path: Path) -> None:
        """Invalid JSON in hsqc.json → state=='waiting', never 500."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.routers import tables  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("webview extra or tables router not yet available")

        from fastapi import FastAPI  # pyright: ignore[reportMissingModuleSource]

        peaks_dir = tmp_path / "peaks"
        peaks_dir.mkdir()
        (peaks_dir / "hsqc.json").write_text("{not valid", encoding="utf-8")

        app = FastAPI()
        app.include_router(tables.make_router(tmp_path))

        with TestClient(app) as client:
            r = client.get("/api/tables/hsqc")

        assert r.status_code == 200, f"Expected 200 (never 500), got {r.status_code}: {r.text}"
        assert r.json().get("state") == "waiting", f"Expected state=waiting: {r.json()}"

    def test_hmbc_waiting_when_absent(self, empty_analysis_dir: Path) -> None:
        """/api/tables/hmbc on an empty analysis dir → state=='waiting', HTTP 200."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.routers import tables  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("webview extra or tables router not yet available")

        from fastapi import FastAPI  # pyright: ignore[reportMissingModuleSource]

        app = FastAPI()
        app.include_router(tables.make_router(empty_analysis_dir))

        with TestClient(app) as client:
            r = client.get("/api/tables/hmbc")

        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        assert r.json().get("state") == "waiting", f"Expected state=waiting: {r.json()}"

    def test_hmbc_waiting_when_malformed(self, tmp_path: Path) -> None:
        """Invalid JSON in hmbc.json → state=='waiting', never 500."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.routers import tables  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("webview extra or tables router not yet available")

        from fastapi import FastAPI  # pyright: ignore[reportMissingModuleSource]

        peaks_dir = tmp_path / "peaks"
        peaks_dir.mkdir()
        (peaks_dir / "hmbc.json").write_text("{not valid", encoding="utf-8")

        app = FastAPI()
        app.include_router(tables.make_router(tmp_path))

        with TestClient(app) as client:
            r = client.get("/api/tables/hmbc")

        assert r.status_code == 200, f"Expected 200 (never 500), got {r.status_code}: {r.text}"
        assert r.json().get("state") == "waiting", f"Expected state=waiting: {r.json()}"

    def test_cosy_waiting_when_absent(self, empty_analysis_dir: Path) -> None:
        """/api/tables/cosy on an empty analysis dir → state=='waiting', HTTP 200."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.routers import tables  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("webview extra or tables router not yet available")

        from fastapi import FastAPI  # pyright: ignore[reportMissingModuleSource]

        app = FastAPI()
        app.include_router(tables.make_router(empty_analysis_dir))

        with TestClient(app) as client:
            r = client.get("/api/tables/cosy")

        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        assert r.json().get("state") == "waiting", f"Expected state=waiting: {r.json()}"

    def test_cosy_waiting_when_malformed(self, tmp_path: Path) -> None:
        """Invalid JSON in cosy.json → state=='waiting', never 500."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.routers import tables  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("webview extra or tables router not yet available")

        from fastapi import FastAPI  # pyright: ignore[reportMissingModuleSource]

        peaks_dir = tmp_path / "peaks"
        peaks_dir.mkdir()
        (peaks_dir / "cosy.json").write_text("{not valid", encoding="utf-8")

        app = FastAPI()
        app.include_router(tables.make_router(tmp_path))

        with TestClient(app) as client:
            r = client.get("/api/tables/cosy")

        assert r.status_code == 200, f"Expected 200 (never 500), got {r.status_code}: {r.text}"
        assert r.json().get("state") == "waiting", f"Expected state=waiting: {r.json()}"
