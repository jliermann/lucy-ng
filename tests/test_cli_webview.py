"""Tests for CLI webview commands (Phase 90 — Wave 0 Nyquist scaffold).

These tests are RED until waves 1-2 land (target modules not yet built).
Each class maps to a requirement group from 90-VALIDATION.md.

Test status legend:
  RED  = ImportError / AssertionError expected until implementation ships
  SKIP = webview extra absent or Wave 0 modules not yet available
"""

from __future__ import annotations

import importlib
import json
import os
import socket
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner

# Top-level import: RED until wave 2 delivers lucy_ng.cli.webview.
# Use try/except so pytest can still *collect* this file in Wave 0.
try:
    from lucy_ng.cli.webview import webview  # pyright: ignore[reportMissingModuleSource]
except ImportError:
    webview = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# TestImportSafety — WV-08: core CLI stays fastapi-free
# ---------------------------------------------------------------------------


class TestImportSafety:
    """WV-08: importing lucy_ng.cli.main must not pull in fastapi/uvicorn."""

    def test_main_importable_without_fastapi(self) -> None:
        """Core CLI main imports cleanly without loading fastapi into sys.modules.

        Uses a fresh subprocess so the current process's cached imports cannot
        mask a real dependency leak.
        """
        check_code = (
            "import lucy_ng.cli.main, sys; "
            "leaked = {k for k in sys.modules if k == 'fastapi' or k.startswith('fastapi.')}; "
            "assert not leaked, f'fastapi leaked into core CLI import: {leaked}'"
        )
        result = subprocess.run(
            [sys.executable, "-c", check_code],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"lucy_ng.cli.main import leaked fastapi.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    def test_serve_without_webview_extra(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``webview serve`` prints a friendly install hint when fastapi is absent.

        Asserts exit_code != 0 and that the output contains the install
        instruction (no raw ImportError traceback).
        """
        if webview is None:
            pytest.skip("lucy_ng.cli.webview not yet available (Wave 0)")

        import builtins

        original_import = builtins.__import__

        def blocking_import(name: str, *args: Any, **kwargs: Any) -> Any:
            if name in ("fastapi", "uvicorn"):
                raise ImportError(f"No module named '{name}'")
            return original_import(name, *args, **kwargs)

        # Remove fastapi/uvicorn from the module cache so the mock is called.
        for mod in list(sys.modules.keys()):
            if (
                mod == "fastapi"
                or mod.startswith("fastapi.")
                or mod == "uvicorn"
                or mod.startswith("uvicorn.")
            ):
                monkeypatch.delitem(sys.modules, mod, raising=False)

        monkeypatch.setattr(builtins, "__import__", blocking_import)

        runner = CliRunner()
        result = runner.invoke(webview, ["serve", str(tmp_path)])

        assert result.exit_code != 0, (
            "Expected non-zero exit when fastapi absent, got 0.\n"
            f"Output: {result.output}"
        )
        assert "pip install lucy-ng[webview]" in result.output, (
            "Expected friendly install hint in output.\n"
            f"Got: {result.output}"
        )


# ---------------------------------------------------------------------------
# TestPackaging — WV-08: pyproject.toml declares webview optional extra
# ---------------------------------------------------------------------------


class TestPackaging:
    """WV-08: fastapi/uvicorn are optional-dependencies, not core deps."""

    def test_webview_extra_declared(self) -> None:
        """[project.optional-dependencies].webview lists fastapi + uvicorn.

        Also asserts that neither appears in [project.dependencies] (core).
        """
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as fh:
            pyproject = tomllib.load(fh)

        optional_deps = pyproject.get("project", {}).get("optional-dependencies", {})
        assert "webview" in optional_deps, (
            "[project.optional-dependencies].webview not declared in pyproject.toml"
        )

        webview_deps: list[str] = optional_deps["webview"]
        dep_names_lower = [d.lower() for d in webview_deps]

        assert any("fastapi" in d for d in dep_names_lower), (
            "fastapi not listed in [project.optional-dependencies].webview"
        )
        assert any("uvicorn" in d for d in dep_names_lower), (
            "uvicorn not listed in [project.optional-dependencies].webview"
        )

        # Core dependencies must NOT include fastapi or uvicorn.
        core_deps: list[str] = pyproject.get("project", {}).get("dependencies", [])
        for dep in core_deps:
            dep_lower = dep.lower()
            assert "fastapi" not in dep_lower, (
                f"fastapi found in core [project.dependencies]: {dep}"
            )
            assert "uvicorn" not in dep_lower, (
                f"uvicorn found in core [project.dependencies]: {dep}"
            )


# ---------------------------------------------------------------------------
# TestWebviewApp — WV-01: FastAPI app factory health endpoint
# ---------------------------------------------------------------------------


class TestWebviewApp:
    """WV-01: create_app() returns a FastAPI app with a working /health route."""

    def test_health_endpoint(self, tmp_path: Path) -> None:
        """GET /health returns 200 with {status: ok, analysis_dir: <path>}."""
        try:
            from fastapi.testclient import TestClient  # pyright: ignore[reportMissingModuleSource]

            from lucy_ng.webview.app import create_app  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("webview extra not installed or webview.app not yet available")

        app = create_app(tmp_path)
        with TestClient(app) as client:
            response = client.get("/health")

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Body: {response.text}"
        )
        data = response.json()
        assert data.get("status") == "ok", f"Expected status=ok, got: {data}"
        assert "analysis_dir" in data, f"analysis_dir missing from /health response: {data}"


# ---------------------------------------------------------------------------
# TestFreePort — WV-01: automatic free-port selection
# ---------------------------------------------------------------------------


class TestFreePort:
    """WV-01: server._pick_free_port() returns a bindable ephemeral port."""

    def test_pick_free_port(self) -> None:
        """_pick_free_port() returns an int in [1024, 65535] that can be bound."""
        try:
            from lucy_ng.webview import server  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("webview extra not installed or webview.server not yet available")

        port = server._pick_free_port()

        assert isinstance(port, int), f"Expected int, got {type(port)}"
        assert 1024 <= port <= 65535, f"Port {port} outside expected range [1024, 65535]"

        # Verify a socket can actually bind the returned port.
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        finally:
            sock.close()


# ---------------------------------------------------------------------------
# TestWebviewStatus — WV-02: status() unit tests (no subprocess required)
# ---------------------------------------------------------------------------


class TestWebviewStatus:
    """WV-02: server.status() handles missing and stale state files."""

    def test_status_no_file(self, webview_analysis_dir: Path) -> None:
        """status() returns None when no .webview.json exists."""
        try:
            from lucy_ng.webview import server  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("webview extra not installed or webview.server not yet available")

        result = server.status(webview_analysis_dir)
        assert result is None, (
            f"Expected None for directory without .webview.json, got: {result}"
        )

    def test_status_stale_pid(self, webview_analysis_dir: Path) -> None:
        """status() returns None for a stale .webview.json and removes the file."""
        try:
            from lucy_ng.webview import server  # pyright: ignore[reportMissingModuleSource]
            from lucy_ng.webview.state import WebviewState  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("webview extra not installed or webview modules not yet available")

        # Find a guaranteed-dead PID.
        dead_pid = 99999
        try:
            os.kill(dead_pid, 0)
            # PID is alive — try the next candidate.
            dead_pid = 99998
            try:
                os.kill(dead_pid, 0)
                pytest.skip(f"Cannot find a dead PID near 99999 on this system")
            except (ProcessLookupError, PermissionError):
                pass
        except ProcessLookupError:
            pass  # confirmed dead
        except PermissionError:
            # PID exists but belongs to another user — still counts as "alive"
            dead_pid = 99998
            try:
                os.kill(dead_pid, 0)
                pytest.skip(f"Cannot find a dead PID near 99999 on this system")
            except (ProcessLookupError, PermissionError):
                pass

        # Write a stale state file using the model's save() method.
        state = WebviewState.create(
            pid=dead_pid,
            port=9999,
            host="127.0.0.1",
            analysis_dir=webview_analysis_dir,
        )
        state.save(webview_analysis_dir)

        state_file = webview_analysis_dir / ".webview.json"
        assert state_file.exists(), "Precondition: .webview.json should exist before status() call"

        result = server.status(webview_analysis_dir)

        assert result is None, (
            f"Expected None for stale pid={dead_pid}, got: {result}"
        )
        assert not state_file.exists(), (
            "server.status() must remove the stale .webview.json file"
        )


# ---------------------------------------------------------------------------
# TestWebviewLifecycle — WV-01/WV-02: subprocess integration (real server)
# ---------------------------------------------------------------------------


class TestWebviewLifecycle:
    """WV-01/WV-02: subprocess integration tests using the webview_server fixture.

    All tests in this class require a running server and skip automatically
    if the webview extra is absent (handled by the webview_server fixture).
    """

    def test_serve_writes_state_file(
        self, webview_server: tuple[Any, Path]
    ) -> None:
        """After serve, .webview.json exists and contains pid/port/url."""
        state, analysis_dir = webview_server
        if state is None:
            pytest.skip("Server did not start — .webview.json not created")

        state_file = analysis_dir / ".webview.json"
        assert state_file.exists(), ".webview.json not written by serve command"

        data = json.loads(state_file.read_text())
        assert "pid" in data, f"pid missing from .webview.json: {data}"
        assert "port" in data, f"port missing from .webview.json: {data}"
        assert "url" in data, f"url missing from .webview.json: {data}"

    def test_serve_idempotent(
        self, webview_server: tuple[Any, Path]
    ) -> None:
        """A second serve on a live dir returns the same URL without rebinding."""
        if webview is None:
            pytest.skip("lucy_ng.cli.webview not yet available (Wave 0)")

        state, analysis_dir = webview_server
        if state is None:
            pytest.skip("Server did not start")

        first_url: str = state.url  # type: ignore[union-attr]

        runner = CliRunner()
        result = runner.invoke(webview, ["serve", str(analysis_dir), "--format", "json"])
        assert result.exit_code == 0, (
            f"Second serve invocation failed.\nOutput: {result.output}"
        )

        second_data = json.loads(result.output)
        assert second_data.get("url") == first_url, (
            f"Second serve returned different URL.\n"
            f"First: {first_url}\nSecond: {second_data.get('url')}"
        )

    def test_stop_terminates(
        self, webview_server: tuple[Any, Path]
    ) -> None:
        """stop() removes .webview.json and the server process is dead."""
        if webview is None:
            pytest.skip("lucy_ng.cli.webview not yet available (Wave 0)")

        state, analysis_dir = webview_server
        if state is None:
            pytest.skip("Server did not start")

        pid: int = state.pid  # type: ignore[union-attr]

        runner = CliRunner()
        result = runner.invoke(webview, ["stop", str(analysis_dir)])
        assert result.exit_code == 0, (
            f"stop command failed.\nOutput: {result.output}"
        )

        # State file must be gone.
        assert not (analysis_dir / ".webview.json").exists(), (
            ".webview.json not removed after stop"
        )

        # PID must be dead (os.kill(pid, 0) must raise ProcessLookupError).
        with pytest.raises(ProcessLookupError):
            os.kill(pid, 0)

    def test_status_running(
        self, webview_server: tuple[Any, Path]
    ) -> None:
        """status() reports a running server while the fixture server is live."""
        try:
            from lucy_ng.webview import server  # pyright: ignore[reportMissingModuleSource]
        except ImportError:
            pytest.skip("webview extra not installed or webview.server not yet available")

        state, analysis_dir = webview_server
        if state is None:
            pytest.skip("Server did not start")

        running_state = server.status(analysis_dir)
        assert running_state is not None, (
            "server.status() returned None while fixture server is live"
        )
