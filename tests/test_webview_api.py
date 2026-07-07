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
