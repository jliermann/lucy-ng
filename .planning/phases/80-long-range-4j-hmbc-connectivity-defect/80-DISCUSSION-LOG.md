# Phase 80: Long-Range (4J) HMBC Connectivity Defect - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-09
**Phase:** 80-long-range-4j-hmbc-connectivity-defect
**Areas discussed:** 4J Mechanism, Detection Strategy, Solver Path, Explosion Guardrail / Ranking

---

## 4J Mechanism

| Option | Description | Selected |
|--------|-------------|----------|
| Global ELIM tolerance | All HMBC as normal 2-3J + `ELIM N`; solver drops ≤N internally, no pre-classification (sidesteps the v7.0 100%-FP detection problem) | ✓ |
| Per-correlation `2 4` | Relax only flagged suspects to extended-range; needs reliable detection (the v8.0 path that was buggy/bypassed) | |
| Hybrid | Detection narrows a suspect pool, ELIM/extended-range resolves within it | |

**User's choice:** Global ELIM tolerance.

### Sub-question — ELIM budget N

| Option | Description | Selected |
|--------|-------------|----------|
| Iterative escalation | Start `ELIM 0`; raise N (0→1→2…) only until a plausible solution emerges | ✓ |
| Small fixed value | Constant small N (e.g. 2-3) from the start | |
| Proportional to HMBC count | N as a fraction of total HMBC | |

**User's choice:** Iterative escalation.

---

## Detection Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Post-hoc explanation only | No detection as constraint driver; identify which correlation ELIM dropped as a plausibility check | (✓ — see notes) |
| Abandon entirely | No 4J detection at all | |
| Broaden heuristic | Extend aromatic↔aliphatic heuristic to carbonyl↔oxygenated-CH, keep as pre-filter | |

**User's choice:** Free-text — "Es ist in der Tat besser, wenn die KI keine Annahmen macht, welche Kopplungen 4J sind oder nicht. Wir hatten ja schonmal pyLSD in Betracht gezogen, das kombinatorisch vorgegebene Mengen von 4J Kopplungen in mehreren Läufen automatisch in Betracht zieht. Vielleicht sollte man das nochmal in Betracht ziehen."

**Notes:** Confirms no AI classification (aligns with post-hoc-only). User raised reconsidering
the pyLSD combinatorial multi-run approach. Resolved in the Solver Path discussion: ELIM is the
cleaner native realisation of the same "no assumptions, let combinatorics decide" intent —
pyLSD would need a suspect pool (= classification) or 2^N runs to make no assumptions. 4J
detection survives only as post-hoc explanation/plausibility (CONTEXT D-04).

---

## Solver Path

| Option | Description | Selected |
|--------|-------------|----------|
| Native ELIM, single-path | One LSD run, `ELIM N` iterative; pyLSD machinery stood down; resolves DESIGN-02 toward single-path; accepts info-loss of dropped correlations | ✓ |
| Revive pyLSD | Fix the multi-run permutation system, keep 4J subsets as extended-range `HMBC 2 4` | |
| ELIM now, pyLSD later | Native ELIM as the fix; pyLSD/extended-range deferred to backlog | (partial — adopted as deferral) |

**User's choice:** Free-text — "Ok, dann machen wir das erstmal so wie Du vorschlägst.
Allerdings müssen wir dann auch den Skill so anpassen, dass er nicht auf Teufel-komm-raus
versucht, die Zahl der Lösungen zu minimieren, denn ELIM wird die Zahl der Lösungen
explodieren lassen. Wir müssen also irgendwie sicherstellen, dass eine große Zahl von Lösungen
auf die plausibelste reduziert werden kann. Vermutlich wird eine NMR-Prediction mit Ranking
wieder aktuell."

**Notes:** Adopted native ELIM single-path now; pyLSD/extended-range deferred to backlog
(CONTEXT D-05/D-06). User flagged the solution-explosion consequence → drove the Guardrail/Ranking
area below.

---

## Explosion Guardrail / Ranking

### Stopping rule

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal N, then rank | Stop at smallest ELIM N with ≥1 plausible solution, rank ALL; remove the >10-solutions reflex | ✓ |
| Hard solution ceiling | As above + a max-solutions cap; over the cap → add real constraints first | |
| Ranking only, no limit | Always rank all, no solution-count guard | |

**User's choice:** Minimal N, then rank.

### Ranking robustness

| Option | Description | Selected |
|--------|-------------|----------|
| Existing + plausibility pre-filter | Keep 13C ranking (signal-match → MAE), add DBE / aromatic / HSQC-multiplicity pre-filter | ✓ |
| Ranking unchanged | No change; test in UAT whether existing ranking suffices | |
| Ranking overhaul | Deeper multi-criteria / confidence-score rework | |

**User's choice:** Existing + plausibility pre-filter.

---

## Claude's Discretion

- Exact LSD `ELIM I J` syntax/semantics, the precise N escalation ceiling, and the pipeline
  location of the plausibility pre-filter — left to research + planning.

## Deferred Ideas

- Revive pyLSD permutation / extended-range `HMBC a b 2 4` to retain dropped-correlation info
  (vs ELIM's info-loss) — backlog, revisit only if info-loss causes real failures.
- Deeper ranking overhaul — out of Phase-80 scope.
- Exact devils-advocate ELIM gate wording — planning detail.
