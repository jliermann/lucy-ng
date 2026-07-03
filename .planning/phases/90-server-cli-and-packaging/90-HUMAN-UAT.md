---
status: partial
phase: 90-server-cli-and-packaging
source: [90-VERIFICATION.md]
started: 2026-07-03
updated: 2026-07-03
---

## Current Test

[awaiting human testing]

## Tests

### 1. Clean-venv install + optional-extra lifecycle
expected: In a fresh virtualenv, `pip install lucy-ng` (no extras) followed by `lucy webview serve <dir>` produces the friendly `pip install lucy-ng[webview]` error (no traceback). After `pip install '.[webview]'`, `lucy webview serve/stop/status` complete an end-to-end lifecycle: `serve` writes `.webview.json` and prints the URL, `status` reports running, `stop` terminates the process and removes `.webview.json`.
result: [pending]

## Summary

total: 1
passed: 0
issues: 0
pending: 1
skipped: 0
blocked: 0

## Gaps
