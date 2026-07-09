"""GET /api/tables/{carbon,hsqc,hmbc,cosy} router (TBL-01/02).

Four independent, read-only GET routes serving the Tables tab peaks data:
  - /api/tables/carbon -> analysis/peaks/carbon_signals.json
  - /api/tables/hsqc   -> analysis/peaks/hsqc.json
  - /api/tables/hmbc   -> analysis/peaks/hmbc.json (row.flag passthrough)
  - /api/tables/cosy   -> analysis/peaks/cosy.json

A fifth route, /api/tables/constraints (TBL-03, LSD constraint inventory),
is added in Task 2 of this plan.

Every route degrades to a "waiting" payload (HTTP 200) on any failure —
absent file, partial/malformed JSON. Never raises a 500 (SC4).

WV-08 import-safety: this module imports fastapi at module level, which is
permitted because it is ONLY ever imported from inside create_app() and
from test bodies.  It must NOT be imported from webview/__init__.py,
webview/server.py, or webview/state.py.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter

# Broad except tuple for JSON-parsing readers (RESEARCH.md Pitfall 1 — the
# narrower (FileNotFoundError, OSError) used by log.py is insufficient once
# json.loads()/.get()/indexing are involved).
_JSON_READ_ERRORS = (
    FileNotFoundError,
    json.JSONDecodeError,
    OSError,
    KeyError,
    TypeError,
    ValueError,
)


def make_router(analysis_dir: Path) -> APIRouter:
    """Return an APIRouter(prefix='/api') with the 4 peaks tables routes.

    Args:
        analysis_dir: Path to the CASE analysis directory (already resolved
            by create_app; do NOT call .resolve() here again).

    Returns:
        An APIRouter with GET /tables/{carbon,hsqc,hmbc,cosy} closed over
        analysis_dir.
    """
    router = APIRouter(prefix="/api")

    @router.get("/tables/carbon")
    def get_carbon() -> dict[str, Any]:
        return _read_carbon(analysis_dir)

    @router.get("/tables/hsqc")
    def get_hsqc() -> dict[str, Any]:
        return _read_hsqc(analysis_dir)

    @router.get("/tables/hmbc")
    def get_hmbc() -> dict[str, Any]:
        return _read_hmbc(analysis_dir)

    @router.get("/tables/cosy")
    def get_cosy() -> dict[str, Any]:
        return _read_cosy(analysis_dir)

    return router


# ---------------------------------------------------------------------------
# Internal helpers — peaks JSON readers (TBL-01 / TBL-02)
# ---------------------------------------------------------------------------


def _read_carbon(analysis_dir: Path) -> dict[str, Any]:
    """Read analysis/peaks/carbon_signals.json.

    Returns:
        {"state": "ok", "note", "counts", "rows"} on success.
        {"state": "waiting", "note": None, "counts": {}, "rows": []} on any
        failure (absent file, malformed/partial JSON — never raises).
    """
    p = analysis_dir / "peaks" / "carbon_signals.json"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        signals = data.get("signals", [])
        return {
            "state": "ok",
            "note": data.get("note"),
            "counts": {
                "formula": data.get("formula"),
                "dbe": data.get("dbe"),
                "solvent": data.get("solvent"),
                "count": len(signals),
            },
            "rows": signals,
        }
    except _JSON_READ_ERRORS:
        return {"state": "waiting", "note": None, "counts": {}, "rows": []}


def _read_hsqc(analysis_dir: Path) -> dict[str, Any]:
    """Read analysis/peaks/hsqc.json. Never raises — see _read_carbon."""
    p = analysis_dir / "peaks" / "hsqc.json"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        peaks = data.get("peaks", [])
        return {
            "state": "ok",
            "note": data.get("note"),
            "counts": {"count": data.get("count", len(peaks))},
            "rows": peaks,
        }
    except _JSON_READ_ERRORS:
        return {"state": "waiting", "note": None, "counts": {}, "rows": []}


def _read_hmbc(analysis_dir: Path) -> dict[str, Any]:
    """Read analysis/peaks/hmbc.json. Row `flag` values pass through verbatim.

    Never raises — see _read_carbon.
    """
    p = analysis_dir / "peaks" / "hmbc.json"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        peaks = data.get("peaks", [])
        return {
            "state": "ok",
            "note": data.get("note"),
            "counts": {
                "kept_count": data.get("kept_count", len(peaks)),
                "raw_count": data.get("raw_count"),
            },
            "rows": peaks,
        }
    except _JSON_READ_ERRORS:
        return {"state": "waiting", "note": None, "counts": {}, "rows": []}


def _read_cosy(analysis_dir: Path) -> dict[str, Any]:
    """Read analysis/peaks/cosy.json. Never raises — see _read_carbon."""
    p = analysis_dir / "peaks" / "cosy.json"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        peaks = data.get("peaks", [])
        return {
            "state": "ok",
            "note": data.get("note"),
            "counts": {"count": data.get("count", len(peaks))},
            "rows": peaks,
        }
    except _JSON_READ_ERRORS:
        return {"state": "waiting", "note": None, "counts": {}, "rows": []}
