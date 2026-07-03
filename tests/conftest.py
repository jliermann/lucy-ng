"""Pytest fixtures for lucy-ng tests."""

from pathlib import Path

import numpy as np
import pytest

from lucy_ng.models import Peak1D, Peak2D, PeakList1D, PeakList2D, Spectrum1D, Spectrum2D


@pytest.fixture
def sample_1d_data() -> tuple[np.ndarray, np.ndarray]:
    """Generate synthetic 1D spectrum data.

    Returns a tuple of (intensity_data, ppm_scale) representing
    a simple 1H spectrum with a few peaks.
    """
    # Create ppm scale from 12 to 0 (typical 1H range)
    ppm_scale = np.linspace(12.0, 0.0, 4096)

    # Create intensity data with some Lorentzian peaks
    data = np.zeros(4096)

    # Add peaks at typical chemical shifts
    peak_positions = [7.2, 3.8, 1.2]  # aromatic, OCH3, CH3
    for pos in peak_positions:
        idx = int((12.0 - pos) / 12.0 * 4096)
        # Simple Lorentzian-like shape
        for i in range(max(0, idx - 50), min(4096, idx + 50)):
            data[i] += 1000 / (1 + ((i - idx) / 5) ** 2)

    return data, ppm_scale


@pytest.fixture
def sample_2d_data() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generate synthetic 2D HSQC spectrum data.

    Returns a tuple of (intensity_data, f1_ppm_scale, f2_ppm_scale).
    """
    # F1 (13C): 200 to 0 ppm
    f1_ppm_scale = np.linspace(200.0, 0.0, 256)
    # F2 (1H): 12 to 0 ppm
    f2_ppm_scale = np.linspace(12.0, 0.0, 1024)

    # Create 2D data matrix
    data = np.zeros((256, 1024))

    # Add correlation peaks (f1_ppm, f2_ppm)
    correlations = [
        (125.0, 7.2),  # aromatic CH
        (55.0, 3.8),  # OCH3
        (20.0, 1.2),  # CH3
    ]

    for f1_pos, f2_pos in correlations:
        f1_idx = int((200.0 - f1_pos) / 200.0 * 256)
        f2_idx = int((12.0 - f2_pos) / 12.0 * 1024)
        # Add 2D peak
        for i in range(max(0, f1_idx - 5), min(256, f1_idx + 5)):
            for j in range(max(0, f2_idx - 10), min(1024, f2_idx + 10)):
                dist_sq = ((i - f1_idx) / 2) ** 2 + ((j - f2_idx) / 5) ** 2
                data[i, j] += 1000 / (1 + dist_sq)

    return data, f1_ppm_scale, f2_ppm_scale


@pytest.fixture
def sample_spectrum_1d(sample_1d_data: tuple[np.ndarray, np.ndarray]) -> Spectrum1D:
    """Create a Spectrum1D instance with test data."""
    data, ppm_scale = sample_1d_data
    return Spectrum1D(
        data=data,
        ppm_scale=ppm_scale,
        nucleus="1H",
        frequency=600.0,
        solvent="CDCl3",
        metadata={"experiment": "zg30", "ns": 16},
    )


@pytest.fixture
def sample_spectrum_2d(
    sample_2d_data: tuple[np.ndarray, np.ndarray, np.ndarray],
) -> Spectrum2D:
    """Create a Spectrum2D instance with test data."""
    data, f1_ppm_scale, f2_ppm_scale = sample_2d_data
    return Spectrum2D(
        data=data,
        f1_ppm_scale=f1_ppm_scale,
        f2_ppm_scale=f2_ppm_scale,
        f1_nucleus="13C",
        f2_nucleus="1H",
        experiment_type="HSQC",
        frequency=600.0,
        metadata={"experiment": "hsqcedetgp", "ns": 4},
    )


@pytest.fixture
def sample_peak_1d() -> Peak1D:
    """Create a sample 1D peak."""
    return Peak1D(
        position=7.26,
        intensity=1000.0,
        assignment="H-1",
        multiplicity="s",
    )


@pytest.fixture
def sample_peak_2d() -> Peak2D:
    """Create a sample 2D peak."""
    return Peak2D(
        f1_position=125.0,
        f2_position=7.26,
        intensity=1000.0,
        f1_assignment="C-1",
        f2_assignment="H-1",
    )


@pytest.fixture
def sample_peak_list_1d() -> PeakList1D:
    """Create a sample 1D peak list."""
    peaks = [
        Peak1D(position=7.26, intensity=1000.0, multiplicity="s"),
        Peak1D(position=3.85, intensity=800.0, multiplicity="s"),
        Peak1D(position=1.25, intensity=1200.0, multiplicity="t"),
    ]
    return PeakList1D(peaks=peaks, nucleus="1H", spectrum_id="test_1h")


@pytest.fixture
def sample_peak_list_2d() -> PeakList2D:
    """Create a sample 2D peak list."""
    peaks = [
        Peak2D(f1_position=125.0, f2_position=7.26, intensity=1000.0),
        Peak2D(f1_position=55.0, f2_position=3.85, intensity=800.0),
        Peak2D(f1_position=20.0, f2_position=1.25, intensity=1200.0),
    ]
    return PeakList2D(
        peaks=peaks,
        f1_nucleus="13C",
        f2_nucleus="1H",
        experiment_type="HSQC",
        spectrum_id="test_hsqc",
    )


# ---------------------------------------------------------------------------
# Webview fixtures (Phase 90)
# All runtime imports are inside fixture bodies — module-level import-safety.
# ---------------------------------------------------------------------------


@pytest.fixture
def webview_analysis_dir(tmp_path: Path) -> Path:
    """Create a minimal analysis/ directory for webview tests.

    Returns a Path to a temporary directory that mimics the analysis_dir
    structure used by the webview server.  Tests can populate files as needed.
    """
    analysis_dir = tmp_path / "analysis"
    analysis_dir.mkdir()
    return analysis_dir


@pytest.fixture
def webview_server(webview_analysis_dir: Path):  # type: ignore[no-untyped-def]
    """Start a real webview server subprocess and yield (state, analysis_dir).

    The fixture invokes ``lucy webview serve`` as a background subprocess so
    that the lifecycle code under test actually writes ``.webview.json``.
    Teardown sends SIGTERM to the server pid recorded in the state file and
    removes the file, guaranteeing no orphan processes.

    Requires the webview extra (fastapi) to be installed; skips otherwise.
    """
    import json as _json
    import os
    import signal
    import subprocess
    import sys
    import time

    # Guard: skip if fastapi not installed (webview extra absent in core env).
    try:
        import fastapi  # noqa: F401  # pyright: ignore[reportMissingModuleSource]
    except ImportError:
        pytest.skip("webview extra (fastapi) not installed")

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "lucy_ng.cli",
            "webview",
            "serve",
            str(webview_analysis_dir),
            "--format",
            "json",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )

    # Poll up to 2 s for .webview.json to appear (written by server.start()).
    state_file = webview_analysis_dir / ".webview.json"
    deadline = time.monotonic() + 2.0
    while not state_file.exists() and time.monotonic() < deadline:
        time.sleep(0.05)

    state = None
    if state_file.exists():
        try:
            from lucy_ng.webview.state import WebviewState  # noqa: PLC0415

            state = WebviewState.model_validate_json(state_file.read_text())
        except Exception:  # noqa: BLE001
            state = None

    yield state, webview_analysis_dir

    # --- Teardown: guaranteed no orphan processes ---

    # 1. Kill the server pid stored in .webview.json (may differ from proc.pid
    #    if serve delegates to a child process for the actual uvicorn run).
    if state_file.exists():
        try:
            stored = _json.loads(state_file.read_text())
            server_pid = stored.get("pid")
            if server_pid:
                os.kill(server_pid, signal.SIGTERM)
        except (ProcessLookupError, OSError, Exception):  # noqa: BLE001
            pass

    # 2. Terminate the CLI subprocess itself (idempotent if already gone).
    try:
        os.kill(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass

    # 3. Remove state file.
    state_file.unlink(missing_ok=True)

    # 4. Wait for subprocess to exit; force-kill if it lingers.
    try:
        proc.wait(timeout=2.0)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
