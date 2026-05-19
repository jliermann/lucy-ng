# Phase 70 — Discussion Log

**Date:** 2026-05-19
**Mode:** discuss (default)
**Areas discussed:** 4 of 4 offered

---

## Area 1: Routing-Ort (case.md vs lsd-engineer)

**Question:** Wo lebt die Routing-Entscheidung (`lucy pylsd run` vs `lucy lsd run`)?

**Options:**
1. **lsd-engineer** (Empfohlen) — kapselt Domain-Logik, case.md bleibt CLI-agnostisch
2. case.md (Orchestrator-Routing) — Layering-Verletzung
3. Hybrid mit Cross-Check — Wartungs-Overhead verdoppelt

**Selection:** Option 1 — In lsd-engineer

**Result locked as D-17:** Routing in lsd-engineer (§"Run LSD"). case.md kennt das Inventory-Schema nicht und ändert sein Spawn-Protokoll nicht.

---

## Area 2: Devil's Advocate Permutations-Cap (G4)

**Question:** Wie streng ist G4 (Permutations-Cap)?

**Options:**
1. **Hart BLOCK bei K>3, kein Override** (Empfohlen) — matched Phase 67 ValueError
2. WARNING bei K=4, BLOCK ab K=5
3. Soft Cap mit nmr-chemist-Priorisierung

**Selection:** Option 1 — Hart BLOCK

**Result locked as D-18:** G4 CRITICAL, hart BLOCK bei K>3; konsistent mit Phase 67 ValueError und D-08 (kein neuer Override). Block-Message erklärt 2^N Permutationen + verweist auf nmr-chemist-Priorisierung.

---

## Area 3: Backward-Compatibility für alte Iteration-Files

**Question:** Wie verhält sich lsd-engineer bei LSD-File ohne v2-Inventory?

**Options:**
1. **Default zu `lucy lsd run`, kein Warning** (Empfohlen) — klassischer Modus ist Normalfall
2. WARNING + Default zu `lucy lsd run`
3. BLOCK — erfordere v2-Inventory

**Selection:** Option 1 — Silent fallback

**Result locked as D-19:** ABSENT inventory → silent `lucy lsd run`. MALFORMED (Phase 69 WR-01) bleibt Hard Error. v1 Legacy (Phase 68 D-02) bleibt WARNING+Fallback.

---

## Area 4: lsd-engineer ITERATION-COMPLETE Output bei pylsd_mode

**Question:** Welche Daten aus `lucy pylsd run` in [ITERATION-COMPLETE]?

**Options:**
1. **Per-Permutation + aggregierte Daten + Top-3 SMILES** (Empfohlen)
2. Nur aggregierte Daten (run_report.json für Details)
3. Vollständige run_report.json inlined

**Selection:** Option 1 — Per-Permutation Tabelle + aggregierter Block + Top-3

**Result locked as D-20:** Zwei strukturierte Blöcke in [ITERATION-COMPLETE]:
- Per-Permutation-Tabelle (permutation_id, defer_set, solution_count, top_rank_quality)
- Aggregierter Block (merged_count, top_3_smiles)
Daten aus `run_report.json` + `lucy pylsd run --format json`. Markdown-Tabelle in Code-Fence (mono-spaced + parseable).

---

## Claude's Discretion (Not Discussed — Planner Finalizes)

- Exakter Wortlaut der Routing-Block-Implementation in lsd-engineer §"Run LSD"
- G4 Block-Message Wortlaut
- ITERATION-COMPLETE Markdown-Tabelle Format (Spalten, Truncation)
- Ob `--working-dir` Flag verwendet wird (Default reicht)
- case.md Loop-Detection-Patterns für pylsd_mode (oder defer)

## Deferred Ideas (Not in Phase 70)

- case.md pylsd_mode-Loop-Detection-Pattern
- nmr-chemist 4J-Priorisierungs-Logik
- Parallel Iteration-Strategy
- v1→v2 Inventory Migration-Skript
