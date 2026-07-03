"""FastAPI application factory for the lucy-ng webview dashboard.

This is the ONLY module in the webview package that imports FastAPI at
module level.  All other modules (server.py, state.py, __init__.py) must
remain fastapi-free so that the core ``lucy`` CLI stays importable without
the webview optional extra (WV-08).

Phase 91 will dock additional routers here via ``app.include_router()``.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI


def create_app(analysis_dir: Path) -> FastAPI:
    """Create the webview FastAPI application for a given analysis directory.

    Args:
        analysis_dir: Path to the CASE analysis directory to serve.
            Resolved to an absolute path immediately.

    Returns:
        A :class:`FastAPI` application with:
        - ``GET /health`` → ``{"status": "ok", "analysis_dir": "<path>"}``
        - Swagger/ReDoc UI suppressed (``docs_url=None``, ``redoc_url=None``)

    Phase 91 adds routers via ``app.include_router(router)`` after this call.
    """
    app = FastAPI(title="lucy-ng webview", docs_url=None, redoc_url=None)
    analysis_dir = analysis_dir.resolve()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "analysis_dir": str(analysis_dir)}

    return app
