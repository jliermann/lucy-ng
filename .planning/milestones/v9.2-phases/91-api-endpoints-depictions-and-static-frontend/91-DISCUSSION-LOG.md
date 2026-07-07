# Phase 91: API Endpoints, Depictions, and Static Frontend - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-04
**Phase:** 91-api-endpoints-depictions-and-static-frontend
**Areas discussed:** Live-Status-Ableitung, Strukturen-Quelle & Fallback, Frontend-Design & Layout, SVG-Depiction-Details

---

## Live-Status-Ableitung

**Q1 — Live status data source**

| Option | Description | Selected |
|--------|-------------|----------|
| timing.jsonl primär, PROGRESS Fallback | Parse append-only timing.jsonl (last phase_start = active phase, iteration from phase name, run_start = elapsed base); fall back to CASE-PROGRESS.md headers if missing/empty. Covers live and finished. | ✓ |
| Nur timing.jsonl/json | Only the timing logs; simpler but blind if timing instrumentation lags. | |
| Nur CASE-PROGRESS.md parsen | Regex iteration/phase from markdown headers; robust but less precise elapsed. | |

**User's choice:** timing.jsonl primär, PROGRESS Fallback
**Notes:** timing.json only exists at run end — the fallback keeps status alive during the live run.

**Q2 — Elapsed-time computation**

| Option | Description | Selected |
|--------|-------------|----------|
| Server rechnet now−run_start; nach Ende fix | Server returns elapsed_s = now − run_start while live; freeze to total_duration_s once run_end/timing.json exists. Trivial subtraction stays within "dumb server". | ✓ |
| Server liefert nur run_start; Frontend tickt | Server returns run_start_utc; JS computes the display. Fully compute-free server but live seconds depend on client clock. | |

**User's choice:** "Deine Empfehlung" (Other) → Server rechnet now−run_start; nach Ende fix
**Notes:** —

---

## Strukturen-Quelle & Fallback

**Q1 — What /api/structures returns before ranking exists**

| Option | Description | Selected |
|--------|-------------|----------|
| Ungerankte SMILES mit MAE=null zeigen | Show up to 10 SMILES from newest iteration_NN/solutions.smi with rank=null, mae=null, source='unranked'; switch to ranking_results.json once present. | ✓ |
| 'waiting' bis geranked | Empty "waiting for data" until ranking_results.json exists. Cleaner but empty widget for much of the run. | |

**User's choice:** Ungerankte SMILES mit MAE=null zeigen
**Notes:** Cap ~10, unranked entries in file order (no MAE to sort by) — set as default.

---

## Frontend-Design & Layout

**Q1 — Widget arrangement**

| Option | Description | Selected |
|--------|-------------|----------|
| Status oben, darunter 2 Spalten | Slim status bar on top; below it structure grid (left) + scrollable log (right). | |
| Drei gestapelte Panels | Status → structures → log vertically stacked, full width. | |
| Du entscheidest | Claude picks a clean arrangement. | ✓ |

**User's choice:** Du entscheidest (Claude's discretion — default: status-top + 2-column)
**Notes:** —

**Q2 — Styling effort**

| Option | Description | Selected |
|--------|-------------|----------|
| Sauber & funktional, ein index.html | Single index.html (inline CSS+JS, no build), light, subtle cards. | ✓ |
| Poliert, getrennte css/js-Dateien | Dark-mode toggle, finer typo, split static assets. | |
| Du entscheidest | Claude picks the detail level. | |

**User's choice:** Sauber & funktional, ein index.html
**Notes:** —

**Q3 — Log panel rendering**

| Option | Description | Selected |
|--------|-------------|----------|
| Roh-Monospace, auto-scroll wenn unten | Raw content in scrollable `<pre>`; auto-scroll to bottom only when already at bottom, else preserve position. No markdown lib. | ✓ |
| Markdown gerendert | Client-side markdown → HTML; nicer but needs an inlined markdown lib. | |
| Roh-Monospace, immer ans Ende scrollen | Raw mono but hard-jumps to bottom every refresh. | |

**User's choice:** Roh-Monospace, auto-scroll wenn unten
**Notes:** Endpoint returns raw CASE-PROGRESS.md (per success criterion #2). Refresh ~3s is fixed by the requirement.

---

## SVG-Depiction-Details

**Q1 — Depiction appearance**

| Option | Description | Selected |
|--------|-------------|----------|
| Clean, keine Atom-Nummern | Plain 2D structure, ~300×300, no atom indices; rank+MAE as HTML label around the tile. | ✓ |
| Mit Atom-Nummern | RDKit depiction with atom indices; helps HMBC debugging but clutters. | |

**User's choice:** Clean, keine Atom-Nummern
**Notes:** —

**Q2 — SVG refresh/caching under 3s polling**

| Option | Description | Selected |
|--------|-------------|----------|
| Frontend lädt SVG nur bei SMILES-Änderung neu | /api/structures polls every 3s; JS re-requests /api/structure/{i}.svg only when the SMILES at index i changed → no flicker. Server renders on-demand, no cache. | ✓ |
| Server cached SVG pro SMILES | Small in-memory {SMILES→SVG} cache; saves CPU but adds state to the "dumb" server. | |
| Du entscheidest | Claude picks the strategy. | |

**User's choice:** Frontend lädt SVG nur bei SMILES-Änderung neu
**Notes:** Malformed SMILES → placeholder SVG (required, SC #5); out-of-range index → 404 (SC #4).

---

## Claude's Discretion

- Exact widget arrangement (default: status bar on top, structure grid + scrollable log two-column below, stacked on narrow windows).
- Placeholder-SVG visual style, tile grid sizing, "waiting for data" payload field names, and error copy.

## Deferred Ideas

- Markdown-rendered log panel — deferred (keeps single-file / no-build / no-inlined-library constraint).
- Dark-mode toggle + separate css/js assets — deferred (light single-file dashboard is enough for a run monitor).
- Atom-numbered depictions for HMBC-assignment debugging — deferred (dashboard is a monitor, not a verification tool).
