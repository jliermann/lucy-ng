# Phase 68: Constraint Inventory v2 Schema - Context

**Gathered:** 2026-05-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Erweiterung des Constraint-Inventory-JSON-Schemas (im LSD-Datei-Header) um pyLSD-spezifische Felder, Versionierung auf v2 mit sauberem Bruch, Aufbau eines maschinenlesbaren Schema-Files plus CLI-Validator, und Erweiterung der devils-advocate-Validation-Gates um drei neue blockierende Checks (FORM/MULT-Konsistenz, ELIM-vs-bond-range-Semantik, Annotation-vs-Mode-Konsistenz).

**In scope:**
- JSON-Schema-Datei (`schemas/constraint_inventory_v2.json`) als Source of Truth
- Drei neue Inventory-Felder: `pylsd_mode` (bool), `deferred_4j` (Objekt-Array), `elim_annotated` (bool)
- Strukturiertes `deferred_4j` mit `atom1`/`atom2`/`shift1`/`shift2`/`correlation_type`/`annotation`
- Neuer CLI-Befehl `lucy lsd validate-inventory <file.lsd>`
- Drei neue devils-advocate-Gates (alle CRITICAL/blockierend)
- Update der Skill-Dokumentation in `lucy-lsd-engineer.md` und `lucy-devils-advocate.md`

**Out of scope:**
- `lucy pylsd run` CLI-Befehl (Phase 69)
- Agent-Routing zu pyLSD (Phase 70)
- Live UAT mit Ibuprofen (Phase 71)
- Python-Modell `LSDProblem.pylsd_mode` (bereits in Phase 66 implementiert, `src/lucy_ng/lsd/models.py:184`)

</domain>

<decisions>
## Implementation Decisions

### Schema Versioning

- **D-01:** Sauberer Bruch zu v2 — neue Delimiter `; === CONSTRAINT INVENTORY v2 ===` und `; === END CONSTRAINT INVENTORY ===`. Der Writer (lsd-engineer) schreibt ausschließlich v2.
- **D-02:** Reader (devils-advocate) erkennt v1-Blöcke und gibt WARNING aus („Legacy v1 inventory — using fallback validation"), startet aber den Run nicht ab. Kein expliziter v1→v2-Migrations-Reader nötig, weil jeder CASE-Run bei iteration_01 neu beginnt und v1-Inventories nur in archivierten Compound-Ordnern existieren.
- **D-03:** Feld `"version": 2` ist Pflicht in jedem v2-Block (zur Doppel-Sicherheit zusätzlich zur Delimiter-Erkennung).

### deferred_4j Semantik

- **D-04:** `deferred_4j` ist in v2 ein Array strukturierter Objekte (kein String-Array wie in v1). Schema pro Eintrag:
  ```json
  {
    "atom1": <int, LSD-Index>,
    "atom2": <int, LSD-Index>,
    "shift1": <float, ppm>,
    "shift2": <float, ppm>,
    "correlation_type": "HMBC",
    "annotation": "; ELIM"
  }
  ```
- **D-05:** Identität via `(atom1, atom2, correlation_type)`-Tupel — bewusst aligned mit PyLSDOrchestrator (siehe `src/lucy_ng/lsd/orchestrator.py` und STATE.md-Decision Phase 67-01).
- **D-06:** Strikte Trennung: Inventory = **Pre-Run Constraint-State**. Run-Resultate (Solution-Counts, Top-Rank pro Permutation) bleiben in `run_report.json` (vom SolutionMerger, Phase 67). Keine Duplikation, keine Sync-Risiken.

### Validation Severity

- **D-07:** Alle drei neuen Gates sind **CRITICAL** (blockierend) und einheitlich:
  - **G1: FORM/MULT-Konsistenz** — wenn `pylsd_mode=true` und `FORM C13H18O2` im File, dann muss die Summe über alle `MULT`-Zeilen exakt `C13H18O2` ergeben. Mismatch → BLOCK.
  - **G2: ELIM-vs-bond-range-Semantik** — wenn `pylsd_mode=true` und eine Zeile `ELIM N M` (LSD-Befehl, nicht Kommentar) erscheint, BLOCK. v8.0-Konvention ist `HMBC X Y 2 4 ; ELIM` (Bond-Range-Erweiterung + Kommentar-Annotation). Der LSD-Befehl `ELIM` wirft Korrelationen weg statt sie zu permutieren — genau der v7.0-Trap.
  - **G3: Annotation-vs-Mode-Konsistenz** — wenn HMBC-Zeilen mit `; ELIM`-Kommentar existieren, muss `pylsd_mode=true` UND `elim_annotated=true` sein UND `deferred_4j` darf nicht leer sein. Inkonsistenz → BLOCK.
- **D-08:** Override-Mechanismus: bestehende devils-advocate APPROVED/BLOCKED-Semantik bleibt unverändert. Bei berechtigten Sonderfällen kann der User per Intervention die Devils-Advocate-Entscheidung überschreiben — wir bauen keinen neuen Override-Pfad.

### Schema Documentation & Testability

- **D-09:** Source of Truth ist eine maschinenlesbare JSON-Schema-Datei: `schemas/constraint_inventory_v2.json` (JSON Schema Draft 2020-12, kompatibel mit `jsonschema`-Lib).
- **D-10:** Neuer CLI-Befehl: `lucy lsd validate-inventory <file.lsd>`. Implementierung extrahiert Block zwischen Delimitern, strippt `;`-Präfixe, validiert via `jsonschema.validate()`. Exit-Code 0 = valid, 1 = invalid (mit JSON-Schema-Fehlermeldung auf stderr). `--format json` für maschinenlesbares Resultat (für devils-advocate-Aufruf).
- **D-11:** Skill-Markdown-Dateien (`lucy-lsd-engineer.md`, `lucy-devils-advocate.md`) referenzieren die Schema-Datei mit Pfad; das aktuelle v1-Inline-Beispiel wird durch ein v2-Inline-Beispiel ersetzt. Das Beispiel ist *Illustration*, das Schema-File ist *Wahrheit*.
- **D-12:** Devil's-Advocate ruft `lucy lsd validate-inventory --format json` per Bash auf — ersetzt die heutige Grep/Sed/Awk-Pipeline aus Section 5A der devils-advocate-Skill-Datei.

### Claude's Discretion

- Exakte JSON-Schema-Struktur (welche Felder `required`, welche `additionalProperties: false` haben) — wird im Planungs-Schritt finalisiert.
- Genauer Output-Format des CLI-Validators für `--format json` (Felder im Fehler-Objekt) — Standard-`jsonschema`-Output ist akzeptabel als Startpunkt.
- Wie der WARNING-Pfad für v1-Legacy-Blöcke in der Devil's-Advocate-Skill formuliert wird (Wortlaut der Message).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap & Requirements
- `.planning/ROADMAP.md` §"Phase 68: Constraint Inventory v2 Schema" — Goal, dependencies, success criteria
- `.planning/REQUIREMENTS.md` §INPUT-05 — „Constraint inventory schema v2 tracks 4J suspect correlations with `pylsd_mode`, `deferred_4j` metadata"
- `.planning/PROJECT.md` §"Current Milestone: v8.0 pyLSD Integration" — Milestone-Kontext

### Agent Skill Files (Bestehende v1-Schema-Definition + Validation-Logik)
- `~/.claude/agents/lucy-lsd-engineer.md` §5 „Constraint Inventory System", insbesondere 5A (Schema-Tabelle), 5B (LSD-Datei-Format), 5C (Initialisierung), 5D (Update-Prozedur) — die v1-Definition, die wir zu v2 erweitern
- `~/.claude/agents/lucy-devils-advocate.md` §5 „Inventory Validation Protocol", insbesondere 5A (Extraktion), 5B (Three-Check Reconciliation) — die bestehenden Gates, an die G1/G2/G3 anschließen

### Prior Phase Decisions (v8.0)
- `.planning/STATE.md` §"Decisions" — alle v8.0-Entscheidungen, besonders:
  - „ELIM does NOT extend bond ranges — it drops correlations entirely. Use `HMBC X Y 2 4` for 4J handling." (Begründung G2 als CRITICAL)
  - „Suspect correlations identified by (atom1_index, atom2_index, correlation_type) tuple — not id()" (Begründung Identität in D-05)
  - „SHIH placed after SHIX in same Chemical shifts section; generate() unchanged for pylsd_mode=False" (Format-Präzedenz)
- `.planning/phases/66-lsdinputgenerator-extensions/66-01-SUMMARY.md` und `66-02-SUMMARY.md` — bestehendes Format
- `.planning/phases/67-pylsdorchestrator-and-solutionmerger/67-01-SUMMARY.md` — PyLSDOrchestrator + SolutionMerger + run_report.json (Trennung zur Inventory in D-06)

### Code (bereits implementiert in v8.0)
- `src/lucy_ng/lsd/models.py:184` — `LSDProblem.pylsd_mode: bool = False` (Python-Feld existiert schon)
- `src/lucy_ng/lsd/generator.py:103-104` — `pylsd_mode`-Trigger für FORM/ELIM-Emission
- `src/lucy_ng/lsd/orchestrator.py` — PyLSDOrchestrator nutzt `(atom1, atom2, type)`-Tupel
- `src/lucy_ng/lsd/__init__.py` — Exporte für SolutionMerger, MergedSolution, MergeResult

### External Tooling
- JSON Schema Draft 2020-12 spec (https://json-schema.org/specification.html) — Schema-Sprache für `schemas/constraint_inventory_v2.json`
- `jsonschema` Python-Library (bereits oder neu in `pyproject.toml` aufzunehmen) — für CLI-Validator

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`src/lucy_ng/lsd/models.py`** — Pydantic v2 Datenmodelle. `LSDProblem.pylsd_mode` existiert bereits; Planung kann einen `ConstraintInventoryV2`-Pydantic-Modell hier ergänzen für interne Konsistenz (optional, da Schema bereits per JSON Schema gelockt).
- **`src/lucy_ng/lsd/generator.py`** — emit-Pipeline für LSD-Dateien. Falls der Inventory-Block aus dem Generator selbst kommen soll (statt nur aus dem Agent), wäre das hier der Anschlusspunkt. Aktuell schreibt nur der lsd-engineer Agent den Inventory-Block — Phase 68 bleibt vermutlich bei diesem Pattern, aber Planung sollte die Frage explizit beantworten.
- **`src/lucy_ng/cli/`** — Click-basierte CLI-Struktur (genaues Modul über `find src/lucy_ng/cli -name "lsd*"`). Neuer Subcommand `validate-inventory` fügt sich dort ein.
- **`tests/test_lsd_models.py` und `tests/test_lsd_generator.py`** — bestehende Test-Patterns für `pylsd_mode`-relevante Logik. Tests für JSON-Schema-Validierung und CLI-Validator analog.

### Established Patterns
- **Pydantic v2 für interne Datenmodelle** — kann optional als zweite Validations-Schicht zum JSON-Schema dienen.
- **`--format json` als CLI-Konvention** — alle `lucy`-Befehle bieten diese Option. CLI-Validator muss das ebenfalls unterstützen, damit Devil's-Advocate ihn parsen kann.
- **Skill-Markdown referenziert reale Pfade** — `lucy-lsd-engineer.md` zeigt heute Inline-JSON; in v2 verweist sie auf `schemas/constraint_inventory_v2.json` (Source of Truth) und behält ein kürzeres Inline-Beispiel als Illustration.
- **devils-advocate-Schema (BLOCKED/APPROVED/WARNING)** — drei klare Severities, an die G1/G2/G3 einfach andocken (alle BLOCKED, also CRITICAL).

### Integration Points
- **lsd-engineer Skill** (`~/.claude/agents/lucy-lsd-engineer.md`): Section 5 wird umgeschrieben — Schema-Tabelle aktualisiert, v2-Initialisierungs- und Update-Prozedur dokumentiert.
- **devils-advocate Skill** (`~/.claude/agents/lucy-devils-advocate.md`): Section 5A (Extraktion) wird auf `lucy lsd validate-inventory`-CLI umgestellt; Section 5B wird um Check 4 (G1/G2/G3) erweitert.
- **case.md Orchestrator** (`~/.claude/commands/lucy-ng/case.md`): keine Änderung in Phase 68 — das routet erst Phase 70.

</code_context>

<specifics>
## Specific Ideas

- **Trap-vermeidung explizit dokumentieren**: In der Skill-Doku den v7.0-Post-Mortem-Kontext zitieren („Statistical 4J detection non-viable — 100% FP rate"), damit der Agent versteht, warum G2 so streng ist. Lernen sichtbar machen, statt nur Regel auflisten.
- **Schema-Datei in repo-relativem Pfad**: `schemas/constraint_inventory_v2.json` (nicht `src/lucy_ng/schemas/` und nicht `tests/`), damit beides — Agent-Doku und Python-Code — den gleichen kanonischen Pfad referenzieren.

</specifics>

<deferred>
## Deferred Ideas

- **Override-CLI für Devils-Advocate-Blocks** — User möchte vielleicht einen geplanten Override-Mechanismus (z. B. `lucy lsd run --override-inventory-check`). Heute nicht nötig; ggf. später in einer v9.x-Phase, wenn echte Edge-Cases auftreten.
- **Inventory-Diff-Tool** — `lucy lsd diff-inventory iteration_NN/compound.lsd iteration_MM/compound.lsd` für Debugging. Phase 68 baut nur Validierung, nicht Diffing.
- **Pydantic-Model `ConstraintInventoryV2`** — als Python-seitiges Mirror des JSON-Schemas. Nur sinnvoll, wenn der Python-Code Inventory-Blöcke generiert (aktuell macht das nur der Agent). Defer bis Python-seitige Erzeugung tatsächlich gebraucht wird.
- **Migration aus v1-Blöcken** — wenn jemand wirklich alte Compound-Ordner re-prozessieren will. Wir bauen nur WARNING + Fallback, kein expliziter Konverter. Falls je gebraucht, eigene Wartungs-Phase.

</deferred>

---

*Phase: 68-constraint-inventory-v2-schema*
*Context gathered: 2026-05-19*
