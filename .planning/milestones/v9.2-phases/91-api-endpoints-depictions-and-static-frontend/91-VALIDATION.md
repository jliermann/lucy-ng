---
phase: 91
slug: api-endpoints-depictions-and-static-frontend
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-04
---

# Phase 91 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (existing `tests/` suite) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/ -k webview -q` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~5–15 seconds (webview subset); full suite longer |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -k webview -q`
- **After every plan wave:** Run `pytest`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds (webview subset)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| _(planner fills per task)_ | — | — | WV-03..06 | — | — | unit/integration | `pytest tests/webview/...` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/webview/` fixture folders — live-run state (only `timing.jsonl` + `iteration_NN/solutions.smi`) and final state (`timing.json` + `ranking_results.json`)
- [ ] `tests/webview/conftest.py` — shared `TestClient(create_app(...))` + fixture-dir builders
- [ ] pytest already installed — no framework install needed

*Existing pytest infrastructure covers the phase; only new webview fixtures/tests are added.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Browser shows 3 widgets auto-refreshing ~3 s without JS build | WV-06 / SC #6 | Real-browser rendering + timing not asserted by TestClient | Start server on a fixture analysis dir, open `http://localhost:<port>/`, confirm status bar + structure grid + scrollable log update every ~3 s |
| SVG depictions render as clean 2D structures (no atom indices) | WV-04 | Visual correctness of RDKit output | Open `GET /api/structure/0.svg` in browser; confirm publication-style ~300×300 depiction |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
