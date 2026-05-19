# Phase 68: Constraint Inventory v2 Schema - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-19
**Phase:** 68-constraint-inventory-v2-schema
**Areas discussed:** Schema-Versionierung, deferred_4j-Semantik, Validation-Severity, Schema-Dokumentation & Testbarkeit

---

## Schema-Versionierung

| Option | Description | Selected |
|--------|-------------|----------|
| Sauberer Bruch zu v2 | Neue Delimiter `; === CONSTRAINT INVENTORY v2 ===`. Agent schreibt nur v2, liest nur v2. v1-Blöcke werden mit WARNING übersprungen (Legacy-Validation). Einfachster Agent-Code, klarer Diff in Skill-Docs. | ✓ |
| Additiv in v1 erweitern | Delimiter bleibt `v1`, neue Felder mit Defaults (`pylsd_mode: false`, `elim_annotated: false`). Alte Files lesbar, weniger Migrations-Aufwand. Aber: `v1` wird semantisch überladen. | |
| v2 mit v1-Rückwärtskompat-Reader | Schreiben als v2, lesen v1 ODER v2. Migrations-Sicherheitsnetz für seltene Legacy-Funde. Kostet ~20 Zeilen Extra-Parser-Logik im Skill. | |

**User's choice:** Sauberer Bruch zu v2
**Notes:** Begründet durch die Tatsache, dass Inventory-Blöcke nur INNERHALB eines CASE-Runs gelesen/geschrieben werden (iteration_01 → iteration_02 → …) und jeder Run frisch startet. Es gibt keinen realen Anwendungsfall für v1-Legacy-Reads — WARNING reicht als Sicherheitsnetz.

---

## deferred_4j-Semantik

| Option | Description | Selected |
|--------|-------------|----------|
| String-Array (wie v1) | `["C4(129.4) H8(45.0)"]`. Inventory bleibt deskriptive Pre-Run-Liste. Provenance liegt in run_report.json. | |
| Strukturiertes Objekt mit LSD-Indizes | Jede Korrelation als Objekt mit atom1/atom2/shift1/shift2/correlation_type/annotation. Identität via Tupel, direkt aligned mit PyLSDOrchestrator. | ✓ |
| Volles Provenance-Objekt | Eingangs- UND Run-Resultate (Solution-Counts, Top-Rank pro Permutation). Duplikat zu run_report.json. | |

**User's choice:** Strukturiertes Objekt mit LSD-Indizes (auf Empfehlung)
**Notes:** Der User bat um eine Empfehlung wegen Projekt-Komplexität. Die Empfehlung „Option B" wurde mit 4 Punkten begründet: (1) Konsistenz mit PyLSDOrchestrator-Tupel-Identität aus Phase 67-01, (2) `deff_fexp` ist in v1 bereits ein Objekt, also kein neues Pattern, (3) Option C dupliziert `run_report.json` aus Phase 67, (4) Validation-Gates werden trivial mit Integer-Atom-Indizes. Akzeptiert ohne Rückfrage.

---

## Validation-Severity

| Option | Description | Selected |
|--------|-------------|----------|
| Alle drei = CRITICAL (Empfehlung) | G1 (FORM/MULT), G2 (ELIM-vs-bond-range), G3 (Annotation-vs-Mode) blockieren einheitlich den LSD-Run. Konsistente Devil's-Advocate-Semantik. | ✓ |
| Gemischt: G1+G2 CRITICAL, G3 WARNING | FORM/MULT und ELIM blocken, Annotation-Inkonsistenz nur warnen. | |
| Alle drei = WARNING | Keine harten Blocks, nur Logs. Devil's-Advocate informativ statt restriktiv. | |

**User's choice:** Alle drei = CRITICAL
**Notes:** Empfehlung begründet durch v7.0-Trap (`ELIM` wirft Korrelationen weg statt zu permutieren, 100% FP-Rate-Geschichte). G1 ist immer Bug, nie Intent. G3 signalisiert verlorenes Mental Model. Uniformität reduziert kognitive Last für den Agent.

---

## Schema-Dokumentation & Testbarkeit

| Option | Description | Selected |
|--------|-------------|----------|
| JSON-Schema + CLI-Validator (Empfehlung) | `schemas/constraint_inventory_v2.json` als Source of Truth. CLI: `lucy lsd validate-inventory <file>`. Devil's-Advocate ruft CLI auf statt eigene Bash-Pipeline. | ✓ |
| Nur Inline-Docs (wie v1) | JSON-Beispiel in Skill-Markdown bleibt einzige Quelle. Kein CLI-Validator. Minimaler Aufwand. | |
| Schema-Datei OHNE CLI-Validator | Schema-File als Truth, aber Devil's-Advocate macht weiter Bash-Parsing. Mittlere Variante. | |

**User's choice:** JSON-Schema + CLI-Validator
**Notes:** Empfehlung begründet durch (1) Decision 2 macht Schema komplex genug für Drift-Risiko, (2) CLI-Validator ist Promotion bestehender Devil's-Advocate-Pipeline (~30 Zeilen Python), (3) Phase 70 AGT-04 braucht diese Primitive ohnehin. On-topic mit Success Criterion #4 („testbar/eindeutig").

---

## Claude's Discretion

- Exakte `required`/`additionalProperties: false`-Struktur im JSON-Schema (Planungs-Detail).
- Genauer `--format json`-Output-Schema des CLI-Validators (Standard-`jsonschema`-Output als Default).
- Wortlaut der WARNING-Message für v1-Legacy-Funde im Devil's-Advocate.

## Deferred Ideas

- **Override-CLI** für Devil's-Advocate-Blocks (`--override-inventory-check`) — wenn Edge-Cases auftreten, eigene v9.x-Phase.
- **Inventory-Diff-Tool** (`lucy lsd diff-inventory`) — Debug-Komfort, kein Phase-68-Scope.
- **Pydantic-Model `ConstraintInventoryV2`** — defer bis Python-seitige Inventory-Erzeugung gebraucht wird.
- **Echter v1→v2-Konverter** — defer bis konkreter Migrations-Bedarf entsteht (heute nur WARNING + Fallback).
