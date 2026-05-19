# Phase 69 — Discussion Log

**Date:** 2026-05-19
**Mode:** discuss (default)
**Areas discussed:** 4 of 4 offered

---

## Area 1: Suspect-Korrelationen-Quelle

**Question:** Aus welcher Quelle liest `lucy pylsd run` die Suspect-Korrelationen?

**Options presented:**
1. **Inventory primär, Annotation als Sanity-Check** (Empfohlen) — read deferred_4j from inventory via validate-inventory's --format json, verify against `; ELIM` annotations, grep fallback if no inventory
2. Annotation-only (grep `^HMBC.*; ELIM`)
3. Inventory-only (strict, error if missing)
4. CLI args only (`--defer X,Y`)

**Selection:** Option 1 — Inventory primär + Annotation Sanity-Check

**Result locked as D-13:** Inventory primary via `lucy lsd validate-inventory --format json` (uses Phase 68 CR-02 fix `inventory: {...}` key), with D-13a (sanity-check vs annotations), D-13b (grep fallback if no inventory), D-13c (both empty → semantic equivalent to `lucy lsd run`, single run with warning).

---

## Area 2: Output-Pipeline-Integration

**Question:** Wie integriert `lucy pylsd run` das Ranking?

**Options presented:**
1. **Integriert per Default, `--no-rank` für Raw** (Empfohlen) — orchestrate→merge→rank→stdout
2. Zwei-Schritt-Pipeline (user chains `lucy lsd rank` manually)
3. Integriert hart, kein Escape

**Selection:** Option 1 — Integrated rank by default, `--no-rank` escape-hatch

**Result locked as D-14:** Default pipeline orchestriert → merged → ranked → stdout. D-14a (`--no-rank` flag schreibt nur `merged.smi` + `run_report.json`), D-14b (`--shifts` required wenn Ranking aktiv), D-14c (`--format json` Output für Agent-Konsum).

---

## Area 3: FORM-Toleranz-Bestätigung

**Question:** Wie wird LSD-Binary-FORM-Toleranz empirisch bestätigt?

**Options presented:**
1. **Findings-Doc + Smoke-Test mit `@skipif(LSD missing)`** (Empfohlen)
2. Nur Findings-Doc (manuell einmalig)
3. Nur pytest mit `@skipif`

**Selection:** Option 1 — Both Findings-Doc + pytest

**Result locked as D-15:** `.planning/findings/form-tolerance.md` als wissenschaftlicher Audit-Trail (Hypothese, Setup, Output, Conclusion, Reproducibility) PLUS `tests/test_lsd_form_tolerance.py` mit `@pytest.mark.skipif(shutil.which('LSD') is None)`. D-15a (LSD-Version aus `LSD -V` in Findings-Doc dokumentiert).

---

## Area 4: Regression-Strategie

**Question:** Wie wird "lucy lsd run unverändert" gesichert?

**Options presented:**
1. **Set-Vergleich der Solution-SMILES (InChI-Set), ibuprofen-Fixture, CI** (Empfohlen)
2. Snapshot-Test des kompletten LSD-Outputs (brittle)
3. Beides parallel
4. Nur manueller Pre-Phase-71-Check

**Selection:** Option 1 — InChI-Set comparison vs versioned baseline

**Result locked as D-16:** `tests/test_lsd_regression.py` mit `@skipif(LSD missing)`. Input: `tests/fixtures/regression/ibuprofen_no_4j.lsd`. Baseline: `tests/fixtures/regression/ibuprofen_no_4j.expected_inchis.txt` (sortiert, manuell verifiziert bei Erst-Erzeugung). Set-equal Vergleich (order-unabhängig). D-16a (Baseline-Verifikation einmalig durch Entwickler), D-16b (kein Auto-Update bei LSD-Version-Drift — Test failed bewusst, Entwickler analysiert).

---

## Claude's Discretion (Not Discussed — Planner Finalizes)

- Exakte CLI-Flag-Namen (`--shifts`, `--no-rank`, `--working-dir`, `--max-defer`)
- Default Working-Directory (vermutlich `dirname(input.lsd)`)
- JSON-Schema-Struktur für `--format json` Output
- Wortlaut der Warnings (D-13b, D-13c)
- CLI-Modul-Platzierung (`src/lucy_ng/cli/lsd.py` vs neue `src/lucy_ng/cli/pylsd.py`)

## Deferred Ideas (Not in Phase 69)

- Parallelisierung der LSD-Läufe (concurrent.futures)
- Resume-on-failure mit gecachten Permutationen
- `--dry-run` Flag für Debug
- CI mit LSD-Binary in Docker
