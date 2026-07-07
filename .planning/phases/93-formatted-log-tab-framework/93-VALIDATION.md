---
phase: 93
slug: formatted-log-tab-framework
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-07
---

# Phase 93 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `pytest tests/test_webview_api.py -q` |
| **Full suite command** | `pytest -q` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_webview_api.py -q`
- **After every plan wave:** Run `pytest -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| {N}-01-01 | 01 | 1 | LOG-01 / TAB-01 | T-93-01 (XSS) | Server markdown renders as literal escaped text; no innerHTML of server content | unit | `pytest tests/test_webview_api.py -q` | ✅ / ❌ W0 | ⬜ pending |

*Planner fills one row per task. Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Static-source-scan test asserting `webview.js` contains no `innerHTML` assignment of server content (automatable XSS-discipline guard)
- [ ] `/webview.js` route smoke test (200 + JS content-type) added to `tests/test_webview_api.py` under WV-08 import-safety

*Existing pytest infrastructure covers the automatable phase requirements; no framework install needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `# <img src=x onerror=alert(1)>` in a mock CASE-PROGRESS.md renders as literal escaped text in the browser (not an element) | LOG-01 | No JS test runtime exists (no package.json / jsdom / Playwright) | Serve dashboard with a mock CASE-PROGRESS.md containing the payload; open in browser; confirm text appears literally and no alert fires |
| Clicking each tab shows its panel and hides others with no page reload | TAB-01 | Requires a real browser DOM interaction | Open dashboard; click each of Run Log / 1D Spectra / 2D Spectra / Tables; confirm only the active panel is visible; confirm Overview + Structures left column stays visible |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
