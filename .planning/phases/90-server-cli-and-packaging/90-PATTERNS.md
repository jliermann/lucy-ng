# Phase 90: Server, CLI, and Packaging - Pattern Map

**Mapped:** 2026-07-02
**Files analyzed:** 9 (7 new, 2 modified)
**Analogs found:** 8 / 9

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/lucy_ng/webview/__init__.py` | config | — | `src/lucy_ng/models/__init__.py` | role-match (empty init) |
| `src/lucy_ng/webview/app.py` | service | request-response | `src/lucy_ng/cli/lsd.py` (LSDRunner wrapper) | partial (closest is service wrapping logic) |
| `src/lucy_ng/webview/state.py` | model | CRUD | `src/lucy_ng/models/spectrum.py` | role-match (Pydantic v2 BaseModel) |
| `src/lucy_ng/webview/server.py` | service | event-driven | `src/lucy_ng/cli/database.py` (`generate-hose-stats`) | partial (subprocess/process lifecycle via lazy imports) |
| `src/lucy_ng/cli/webview.py` | controller | request-response | `src/lucy_ng/cli/lsd.py` + `database.py` | exact (Click group + subcommands + `--format json` + lazy import) |
| `tests/test_cli_webview.py` | test | request-response | `tests/test_cli_lsd.py` | exact (CliRunner + tmp_path classes) |
| `src/lucy_ng/cli/main.py` (modified) | config | — | itself | exact (add import + `cli.add_command`) |
| `pyproject.toml` (modified) | config | — | itself | exact (`[project.optional-dependencies]`) |
| `tests/conftest.py` (modified) | test | — | itself | exact (existing `@pytest.fixture` style) |

---

## Pattern Assignments

### `src/lucy_ng/webview/__init__.py` (config)

**Analog:** `src/lucy_ng/models/__init__.py`

Keep empty or re-export `create_app` for ergonomic use by `cli/webview.py _run`:

```python
# src/lucy_ng/webview/__init__.py
```

No content needed for Phase 90; `app.py` is imported directly.

---

### `src/lucy_ng/webview/app.py` (service, request-response)

**Analog:** None exact — FastAPI is new. Use RESEARCH.md Pattern 6 directly.

**Module-level declaration style** (from `src/lucy_ng/cli/lsd.py` lines 1–14 as reference for docstring + import block):
```python
# src/lucy_ng/cli/lsd.py lines 1-14
"""CLI commands for LSD structure elucidation."""

import json
from pathlib import Path

import click
import jsonschema

from lucy_ng.lsd import LSDRunner, LSDSolutionAnalyzer
```

**App factory pattern** (RESEARCH.md Pattern 6 — no codebase analog exists; copy verbatim):
```python
# src/lucy_ng/webview/app.py
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI


def create_app(analysis_dir: Path) -> FastAPI:
    """Create the webview FastAPI application for a given analysis directory.

    Phase 91 docks additional routers here via app.include_router().
    """
    app = FastAPI(title="lucy-ng webview", docs_url=None, redoc_url=None)
    analysis_dir = analysis_dir.resolve()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "analysis_dir": str(analysis_dir)}

    return app
```

---

### `src/lucy_ng/webview/state.py` (model, CRUD)

**Analog:** `src/lucy_ng/models/spectrum.py`

**Pydantic v2 BaseModel imports** (`src/lucy_ng/models/spectrum.py` lines 1–7):
```python
from typing import Any

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, field_validator
```

For `state.py`, the import block is simpler (no numpy/validators needed):
```python
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel
```

**BaseModel class declaration style** (`src/lucy_ng/models/spectrum.py` lines 10–13):
```python
class Spectrum1D(BaseModel):
    """1D NMR spectrum data model."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    data: NDArray[np.float64]
    ...
```

`WebviewState` does not need `arbitrary_types_allowed` (all fields are primitive). Mirror the class declaration without `model_config`:

```python
class WebviewState(BaseModel):
    """Persistent state written to <analysis_dir>/.webview.json."""
    pid: int
    port: int
    host: str
    url: str
    analysis_dir: str      # absolute path, stored as str for JSON portability
    started_at: str        # ISO 8601 UTC
```

**`model_dump_json` / `model_validate_json` pattern** (standard Pydantic v2 — no codebase usage found yet; copy from RESEARCH.md Pattern 5):
```python
    def save(self, analysis_dir: Path) -> None:
        (analysis_dir / ".webview.json").write_text(self.model_dump_json(indent=2))

    @classmethod
    def load(cls, analysis_dir: Path) -> "WebviewState":
        return cls.model_validate_json((analysis_dir / ".webview.json").read_text())
```

---

### `src/lucy_ng/webview/server.py` (service, event-driven)

**Analog:** `src/lucy_ng/cli/database.py` `generate-hose-stats` (lines 280–390) for the lazy-import-inside-body precedent. No subprocess lifecycle analog exists in the codebase.

**Lazy-import-inside-function-body pattern** (`src/lucy_ng/cli/database.py` lines 382–385):
```python
def generate_hose_stats(...) -> None:
    import time

    from lucy_ng.prediction.hose import HOSEGEN_AVAILABLE
```

**Error-branch pattern** (`src/lucy_ng/cli/database.py` lines 386–390):
```python
    if not HOSEGEN_AVAILABLE:
        click.echo("Error: hosegen library not available.", err=True)
        click.echo("Install with: pip install ...", err=True)
        raise click.Abort()
```

**Subprocess lifecycle + PID liveness patterns** come entirely from RESEARCH.md (Patterns 3 and 4) — no codebase analog. Copy verbatim from RESEARCH.md.

---

### `src/lucy_ng/cli/webview.py` (controller, request-response)

This is the most pattern-rich file. Three analogs apply.

**Click group declaration** (`src/lucy_ng/cli/database.py` lines 25–27):
```python
@click.group()
def database() -> None:
    """Database management commands."""
```

Mirror for `webview`:
```python
@click.group()
def webview() -> None:
    """Webview dashboard server commands."""
```

**Subcommand with `--format json` option** (`src/lucy_ng/cli/lsd.py` lines 43–67):
```python
@lsd.command("run")
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--timeout",
    type=int,
    default=60,
    help="Timeout in seconds.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format.",
)
def lsd_run(
    input_file: str, timeout: int, output_dir: str | None, output_format: str
) -> None:
    """Run LSD on an input file."""
```

**`--format json` output branch** (`src/lucy_ng/cli/lsd.py` lines 91–99):
```python
    if output_format == "json":
        data = {
            "success": result.success,
            "solution_count": result.solution_count,
            "return_code": result.return_code,
            "output_files": [str(f) for f in result.output_files],
            "stderr": result.stderr,
        }
        click.echo(json.dumps(data, indent=2))
    else:
        if result.success:
            click.echo(f"LSD completed successfully")
```

**Lazy-import guard** (`src/lucy_ng/cli/database.py` lines 382–390 — `generate_hose_stats` body):
```python
    import time

    from lucy_ng.prediction.hose import HOSEGEN_AVAILABLE

    if not HOSEGEN_AVAILABLE:
        click.echo("Error: hosegen library not available.", err=True)
        click.echo("Install with: pip install git+...", err=True)
        raise click.Abort()
```

For `webview`, the guard is a helper called at the top of each command body (RESEARCH.md Pattern 1):
```python
def _require_webview() -> None:
    """Raise a friendly error if the webview extra is not installed."""
    try:
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401
    except ImportError:
        raise click.ClickException(
            "The webview extra is not installed.\n"
            "Install with: pip install lucy-ng[webview]"
        )
```

**`click.Path(path_type=Path)` argument style** (`src/lucy_ng/cli/database.py` lines 31–35):
```python
@click.option(
    "--nmrshiftdb",
    type=click.Path(exists=True, path_type=Path),
    help="Path to NMRShiftDB SD file",
)
```

For `analysis_dir` argument:
```python
@webview.command("serve")
@click.argument("analysis_dir", type=click.Path(path_type=Path))
```

**Hidden subcommand** — `hidden=True` flag (no codebase example; use Click API):
```python
@webview.command("_run", hidden=True)
```

---

### `tests/test_cli_webview.py` (test, request-response)

**Analog:** `tests/test_cli_lsd.py`

**Imports + CliRunner setup** (`tests/test_cli_lsd.py` lines 1–10):
```python
"""Tests for CLI LSD commands."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from lucy_ng.cli.lsd import lsd
```

Mirror for webview:
```python
"""Tests for CLI webview commands."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from lucy_ng.cli.webview import webview
```

**Class + CliRunner invocation with tmp_path** (`tests/test_cli_lsd.py` lines 109–120):
```python
class TestLSDRun:
    """Tests for lucy lsd run command."""

    def test_run_without_lsd(self, tmp_path: Path) -> None:
        """Test error when LSD not installed."""
        lsd_file = tmp_path / "test.lsd"
        lsd_file.write_text("; Test\nMULT 1 C 3 3\nEXIT\n")

        runner = CliRunner()
        result = runner.invoke(lsd, ["run", str(lsd_file)])

        if result.exit_code != 0:
            assert "not installed" in result.output.lower()
```

**CliRunner help assertion pattern** (`tests/test_cli_lsd.py` lines 122–128):
```python
    def test_run_help(self) -> None:
        """Test run command help."""
        runner = CliRunner()
        result = runner.invoke(lsd, ["run", "--help"])
        assert result.exit_code == 0
        assert "--timeout" in result.output
```

**Class-per-feature grouping** (`tests/test_cli_main.py` lines 9–60):
```python
class TestCLIMain:
    """Tests for CLI entry point."""

    def test_version(self) -> None:
        ...

class TestCLIIntegration:
    """Integration tests for CLI workflow."""
    ...
```

Mirror as:
```
class TestWebviewLifecycle:   # serve/stop/status subprocess integration
class TestWebviewStatus:      # unit tests for status with no/stale file
class TestImportSafety:       # WV-08 import guard tests
class TestWebviewApp:         # FastAPI TestClient / health endpoint
class TestFreePort:           # _pick_free_port unit test
```

**FastAPI TestClient pattern** (RESEARCH.md Code Examples — no codebase analog):
```python
from fastapi.testclient import TestClient
from lucy_ng.webview.app import create_app

def test_health(tmp_path: Path) -> None:
    app = create_app(tmp_path)
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
```

---

### `src/lucy_ng/cli/main.py` (modified — register webview group)

**Analog:** itself (`src/lucy_ng/cli/main.py`)

**Existing import block pattern** (`src/lucy_ng/cli/main.py` lines 1–18):
```python
"""Main CLI entry point for lucy-ng."""

import click

from lucy_ng import __version__
from lucy_ng.cli.analyze import analyze
from lucy_ng.cli.database import database
from lucy_ng.cli.dereplicate import dereplicate
from lucy_ng.cli.detect import detect
from lucy_ng.cli.fetch import fetch
from lucy_ng.cli.fragment import fragment
from lucy_ng.cli.identify import identify
from lucy_ng.cli.lsd import lsd
from lucy_ng.cli.pick import pick
from lucy_ng.cli.predict import predict
from lucy_ng.cli.pylsd import pylsd
from lucy_ng.cli.read import read
from lucy_ng.cli.visualize import visualize
```

Add one line after `from lucy_ng.cli.visualize import visualize`:
```python
from lucy_ng.cli.webview import webview
```

**`cli.add_command` pattern** (`src/lucy_ng/cli/main.py` lines 48–62):
```python
# Register command groups
cli.add_command(read)
cli.add_command(pick)
...
cli.add_command(database)
cli.add_command(fragment)
```

Add one line at the end of the block:
```python
cli.add_command(webview)
```

Also update the docstring's `Commands:` block (lines 29–44) to include `webview   Dashboard server for live CASE runs`.

---

### `pyproject.toml` (modified — webview optional-dependencies)

**Analog:** itself (`pyproject.toml`)

**Existing `[project.optional-dependencies]` block** (`pyproject.toml` lines 45–56):
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "ruff>=0.1",
    "mypy>=1.0",
]
prediction = [
    # NOTE: hose-code-generator has broken dependencies (xmlrunner) on Python 3.12
    # Install manually: pip install git+https://github.com/Ratsemaat/HOSE_code_generator.git --no-deps
    # Then install its actual runtime deps: pip install rdkit
]
```

Add a new `webview` entry after `prediction`:
```toml
webview = [
    "fastapi>=0.100",
    "uvicorn>=0.20",
]
```

No changes to `[project.dependencies]` or `[tool.hatch.build.targets.wheel]` in Phase 90.

---

### `tests/conftest.py` (modified — add webview fixtures)

**Analog:** itself (`tests/conftest.py`)

**Existing `@pytest.fixture` style** (`tests/conftest.py` lines 9–30):
```python
@pytest.fixture
def sample_1d_data() -> tuple[np.ndarray, np.ndarray]:
    """Generate synthetic 1D spectrum data.

    Returns a tuple of (intensity_data, ppm_scale) representing
    a simple 1H spectrum with a few peaks.
    """
    # Create ppm scale from 12 to 0 (typical 1H range)
    ppm_scale = np.linspace(12.0, 0.0, 4096)
    ...
    return data, ppm_scale
```

Add two fixtures following the same style — no import of fastapi at module level in conftest:

```python
@pytest.fixture
def webview_analysis_dir(tmp_path: Path) -> Path:
    """Create a minimal analysis/ directory for webview tests.

    Returns a Path to a temporary directory that mimics the analysis_dir
    structure (empty subdirs; tests can populate files as needed).
    """
    analysis_dir = tmp_path / "analysis"
    analysis_dir.mkdir()
    return analysis_dir


@pytest.fixture
def webview_server(webview_analysis_dir: Path):
    """Start a real webview subprocess and yield (state, analysis_dir).

    Teardown sends SIGTERM and removes .webview.json.
    Requires the webview extra to be installed; skipped otherwise.
    """
    import os
    import signal
    import subprocess
    import sys
    import time
    from lucy_ng.webview.state import WebviewState

    proc = subprocess.Popen(
        [sys.executable, "-m", "lucy_ng.cli", "webview", "_run",
         str(webview_analysis_dir), "--port", "0", "--host", "127.0.0.1"],
        start_new_session=True,
    )
    time.sleep(0.8)  # allow uvicorn to start
    state_file = webview_analysis_dir / ".webview.json"
    state = WebviewState.model_validate_json(state_file.read_text()) if state_file.exists() else None

    yield state, webview_analysis_dir

    # Teardown
    try:
        os.kill(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    state_file.unlink(missing_ok=True)
```

---

## Shared Patterns

### `--format json` convention

**Source:** `src/lucy_ng/cli/lsd.py` lines 58–64 (option declaration) and lines 91–99 (output branch)
**Apply to:** `webview serve`, `webview stop`, `webview status`

Option declaration:
```python
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format.",
)
```

Output branch:
```python
    if output_format == "json":
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"Human-readable message")
```

### `from __future__ import annotations`

**Source:** `src/lucy_ng/cli/database.py` line 3
**Apply to:** all new Python files in this phase

```python
from __future__ import annotations
```

Required for `mypy --strict` with `|` union syntax on Python 3.10.

### `click.ClickException` for user-facing errors

**Source:** `src/lucy_ng/cli/database.py` line 261
**Apply to:** `_require_webview()` in `cli/webview.py` and error branches in `server.py`

```python
raise click.ClickException(
    "Downloaded archive does not contain a .db file"
)
```

---

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `src/lucy_ng/webview/app.py` | service | request-response | No FastAPI app factory exists in the codebase; FastAPI is new |

---

## Metadata

**Analog search scope:** `src/lucy_ng/cli/`, `src/lucy_ng/models/`, `tests/`, `pyproject.toml`
**Files scanned:** 9 (main.py, database.py, lsd.py, spectrum.py, conftest.py, test_cli_main.py, test_cli_lsd.py, pyproject.toml, design spec)
**Pattern extraction date:** 2026-07-02
