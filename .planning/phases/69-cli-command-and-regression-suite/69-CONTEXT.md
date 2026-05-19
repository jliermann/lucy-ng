# Phase 69: CLI Command and Regression Suite - Context

**Gathered:** 2026-05-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Neuer CLI-Befehl `lucy pylsd run` als dünner Wrapper über den in Phase 67 gebauten PyLSDOrchestrator + SolutionMerger; integriertes Two-Tier-Ranking via existierendem `lucy lsd rank`; empirische Bestätigung dass die LSD-Binary die in Phase 66 emittierte `FORM`-Zeile toleriert (ignoriert); Regressions-Garantie dass `lucy lsd run` durch die v8.0-Änderungen nicht verändert wurde.

**In scope:**
- Click-Subcommand `lucy pylsd run <file.lsd> --shifts "..."` mit `--format json`-Support
- Default-integriertes Ranking (orchestrate → merge → rank → stdout); `--no-rank` Escape-Hatch
- Source-Resolution für Suspect-Korrelationen aus dem v2-Inventory-Block (per `validate-inventory`-CLI), mit Sanity-Check gegen `; ELIM`-Annotationen
- pytest-Test mit `@skipif(LSD missing)` für FORM-Toleranz
- `.planning/findings/form-tolerance.md` Findings-Dokument (Audit-Trail)
- pytest Regressions-Test (InChI-Set-Vergleich gegen Baseline) für `lucy lsd run` Unveränderlichkeit
- Ibuprofen-Fixture (`tests/fixtures/regression/ibuprofen_no_4j.lsd` + `.expected_inchis.txt`)

**Out of scope:**
- Agent-Skill-Integration (Phase 70 — wann ruft case.md `lucy pylsd` statt `lucy lsd run` auf)
- Live UAT mit Ibuprofen-Aromatic-Ring-Erkennung (Phase 71)
- Constraint-Inventory-Schema-Änderungen (gelockt in Phase 68)
- Neue Permutations-Algorithmen (PyLSDOrchestrator ist fertig in Phase 67)

</domain>

<decisions>
## Implementation Decisions

### Suspect-Korrelationen-Quelle

- **D-13:** `lucy pylsd run` liest Suspect-Korrelationen primär aus dem v2 Constraint-Inventory-Block des LSD-Files via Aufruf von `lucy lsd validate-inventory --format json` (nutzt das in Phase 68 CR-02 Fix hinzugefügte `inventory: {...}` Feld der Success-Response). Aus `inventory.deferred_4j` werden die `(atom1, atom2)`-Paare extrahiert und an PyLSDOrchestrator übergeben.
- **D-13a (Sanity-Check):** Wenn `; ELIM`-Annotationen auf HMBC-Zeilen existieren, müssen sie mit dem Inventory übereinstimmen (gleiche Atom-Paare). Mismatch → CLI exit 1 mit klarer Fehlermeldung. Devil's Advocate G3 (Phase 68) blockt schon vor dem CLI-Aufruf — der CLI-Check ist Defense-in-Depth.
- **D-13b (Fallback):** Wenn KEIN Inventory-Block vorhanden ist, fällt der CLI-Befehl auf `grep "^HMBC.*; ELIM"` zurück und extrahiert Atom-Paare aus den HMBC-Argumenten. Warnt aber: "No inventory block — using annotation fallback (recommended: write inventory)."
- **D-13c (Beide leer):** Wenn weder Inventory noch Annotationen existieren, ist `lucy pylsd run` semantisch gleich `lucy lsd run` (0 Permutationen). CLI gibt eine Warning aus und führt einfach einen einzelnen LSD-Lauf aus statt zu erroren.

### Output-Pipeline-Integration

- **D-14:** Default-Pipeline ist integriert: `lucy pylsd run <file> --shifts "..."` führt aus:
  1. PyLSDOrchestrator generiert 2^K Permutationen
  2. PyLSDOrchestrator führt LSD pro Permutation aus
  3. SolutionMerger dedupliziert via InChI → `merged.smi` + `run_report.json`
  4. `lucy lsd rank merged.smi --shifts ...` (intern aufgerufen, nicht subprocess — Python-Function-Aufruf)
  5. Ranked-Solutions-Output auf stdout (gleiche Format-Konventionen wie `lucy lsd rank`)
- **D-14a (`--no-rank`):** Mit `--no-rank` wird Schritt 4 + 5 übersprungen. Output: nur `merged.smi` + `run_report.json` im Working-Dir; stdout zeigt Pfade.
- **D-14b (`--shifts` required wenn Ranking aktiv):** Wenn weder `--no-rank` noch `--shifts` gegeben ist, exit 1 mit Fehlermeldung. Konsistent mit `lucy lsd rank`-Verhalten.
- **D-14c (`--format json`):** Wie alle `lucy`-Befehle muss `lucy pylsd run --format json` strukturierten Output liefern: `{permutations, merged_count, ranked_solutions: [...], run_report_path}` für Agent-Konsum (Phase 70 wird das parsen).

### FORM-Toleranz-Bestätigung

- **D-15:** Zwei Artefakte werden geliefert:
  - **`.planning/findings/form-tolerance.md`** — wissenschaftlicher Audit-Trail mit: LSD-Binary-Version, Test-Datum, Test-LSD-File (klein, minimal), Output mit FORM-Zeile vs. ohne FORM-Zeile, identische Solution-Sets bewiesen, Decision-Statement.
  - **`tests/test_lsd_form_tolerance.py`** — pytest-Test mit `@pytest.mark.skipif(shutil.which('LSD') is None, reason='LSD binary not installed')`. Living-Regression: Test läuft lokal (Entwickler) und in CI nur wenn LSD installiert ist. Fängt zukünftige LSD-Versions-Updates die das Verhalten ändern.
- **D-15a (LSD-Version in Findings-Doc):** Die Findings-Doc enthält den Output von `LSD -V` (oder äquivalent) zum Zeitpunkt des Tests, damit die Aussage version-spezifisch attribuiert ist.

### Regression-Strategie

- **D-16:** `tests/test_lsd_regression.py` mit `@pytest.mark.skipif(shutil.which('LSD') is None)`:
  - Input-Fixture: `tests/fixtures/regression/ibuprofen_no_4j.lsd` (echeckt — ibuprofen LSD-File ohne `; ELIM`-Annotationen, ohne v2-Inventory; das ist die "klassischer-lucy-lsd-run"-Form)
  - Baseline: `tests/fixtures/regression/ibuprofen_no_4j.expected_inchis.txt` (sortiert, eine InChI pro Zeile, manuell verifiziert beim Erst-Erzeugen)
  - Test ruft `lucy lsd run` auf das Fixture an, konvertiert Solutions zu InChIs via RDKit, vergleicht Set-equal mit Baseline (Order-unabhängig)
- **D-16a (Baseline-Verifikation):** Baseline-File wird beim Plan-Implementieren einmal manuell erzeugt: Entwickler lässt aktuelles `lucy lsd run` auf das Fixture laufen, inspiziert Solutions, bestätigt sie sind chemisch plausibel, schreibt sie ins Baseline-File. Spätere Test-Runs vergleichen nur noch — keine erneute manuelle Verifikation.
- **D-16b (Baseline-Updates):** Wenn LSD-Version-Update das Set ändert: kein automatisches Auto-Update. Test failed → Entwickler analysiert, entscheidet ob neue Solutions chemisch valide sind, regeneriert Baseline manuell, committet mit klarer Begründung. Die Failure-Mode ist genau wünschenswert.

### Claude's Discretion

- Exakte CLI-Flag-Namen (Vorschläge: `--shifts`, `--no-rank`, `--working-dir`, `--max-defer`) — Planner finalisiert
- Output-File-Naming und Default-Working-Directory (vermutlich `dirname(input.lsd)` oder Temp-Dir)
- JSON-Schema-Struktur für `--format json`-Output von `lucy pylsd run` (kein striktes JSON-Schema, da intern für Agent-Konsum; konsistent mit `lucy lsd rank --format json`)
- Wortlaut der Warnings (D-13b "no inventory" Fallback, D-13c "no permutations" Single-Run)
- Implementation: ruft `lucy pylsd run` `lucy lsd rank` als Python-Function-Aufruf (kein subprocess) — wegen Performance + sauberer Errror-Propagation. Planner darf bestätigen.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap & Requirements
- `.planning/ROADMAP.md` §"Phase 69: CLI Command and Regression Suite" — Goal, dependencies, success criteria
- `.planning/REQUIREMENTS.md` §CLI — CLI-01, CLI-02, CLI-03 wording

### Prior Phase Artefakte (v8.0)
- `.planning/phases/66-lsdinputgenerator-extensions/66-01-SUMMARY.md` + `66-02-SUMMARY.md` — LSDInputGenerator `pylsd_mode`, FORM/ELIM/SHIX-Emission
- `.planning/phases/67-pylsdorchestrator-and-solutionmerger/67-01-SUMMARY.md` + `67-02-SUMMARY.md` — PyLSDOrchestrator (Permutation-Engine, K≤3-Cap), SolutionMerger (InChI-Dedup, run_report.json), Dataclasses (PermutationResult, OrchestrationResult, MergedSolution, MergeResult)
- `.planning/phases/68-constraint-inventory-v2-schema/68-VERIFICATION.md` und `.planning/phases/68-constraint-inventory-v2-schema/68-*-SUMMARY.md` — JSON Schema v2, `lucy lsd validate-inventory --format json` CLI mit `inventory: {...}` Success-Response (CR-02 Fix)

### Code (bereits implementiert)
- `src/lucy_ng/lsd/orchestrator.py` — `PyLSDOrchestrator` (Zeile 112), `SolutionMerger` (Zeile 303), Dataclasses
- `src/lucy_ng/lsd/__init__.py` — Exporte für SolutionMerger, MergedSolution, MergeResult
- `src/lucy_ng/cli/lsd.py` — bestehende Click-Subcommands: `check` (Z22), `run` (Z42), `validate-inventory` (Z207), `rank` (Z341); neue `pylsd`-Gruppe folgt diesem Pattern
- `src/lucy_ng/cli/main.py:52` — `lsd`-Group-Registrierung; neue `pylsd`-Group analog registrieren
- `schemas/constraint_inventory_v2.json` — Schema für `inventory.deferred_4j` Lesepfad

### Agent Skills (werden in Phase 70 erweitert — Phase 69 berührt sie nur indirekt)
- `~/.claude/agents/lucy-lsd-engineer.md` §5 — v2-Inventory-Format (Source-of-Truth für `deferred_4j`)
- `~/.claude/agents/lucy-devils-advocate.md` §5B — G1/G2/G3 Gates (laufen VOR `lucy pylsd run`)

### External
- LSD Manual (lokal: `external/lsd-doc.pdf` falls vorhanden — sonst http://eos.univ-reims.fr/LSD/) — für FORM-Toleranz-Verifikation
- RDKit Python API — für InChI-Generierung in Regressions-Tests (`Chem.MolFromSmiles` → `Chem.MolToInchi`)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`src/lucy_ng/lsd/orchestrator.py:PyLSDOrchestrator`** — Phase 67 hat den vollständigen Permutations-Engine + LSD-Runner-Loop fertig. `lucy pylsd run` ist im Wesentlichen: `PyLSDOrchestrator(...).run() → SolutionMerger(...).merge() → optional rank`.
- **`src/lucy_ng/lsd/orchestrator.py:SolutionMerger`** — InChI-Dedup und `run_report.json`-Generierung bereits implementiert. CLI ruft `.merge()` direkt.
- **`src/lucy_ng/cli/lsd.py:lsd_rank`** (Z341+) — vorhandene Ranking-CLI mit Two-Tier-Sortierung (Match-Count primary, MAE secondary). `lucy pylsd run` ruft die Funktion direkt im selben Prozess (nicht via subprocess).
- **`src/lucy_ng/cli/lsd.py:lsd_validate_inventory`** (Z207+, Phase 68 + CR-02 Fix) — `--format json` Output enthält jetzt `inventory: {...}`. `lucy pylsd run` parst die Bash-Output via `subprocess.run([..., '--format', 'json'])` ODER ruft die Python-Function direkt. Letzteres bevorzugt für Performance + Type-Safety.
- **`tests/test_inventory_schema.py`** und **`tests/test_lsd_generator.py`** — Test-Pattern für CLI-Tests via `CliRunner` + `tmp_path`-Fixtures.

### Established Patterns
- **Click-Subgroup-Registrierung** — `src/lucy_ng/cli/main.py:52` registriert die `lsd`-Group. Neue `pylsd`-Group folgt dem identischen Pattern.
- **`--format json` Konvention** — alle `lucy`-Befehle bieten das. `lucy pylsd run --format json` muss ranked-solutions + meta liefern, parsebar für den Agent in Phase 70.
- **`@skipif(shutil.which('LSD') is None)`** — bereits-genutztes Pattern in existierenden LSD-Integration-Tests; übernehmen.
- **Test-Fixtures unter `tests/fixtures/`** — etablierter Pfad; `tests/fixtures/regression/` als Sub-Folder ist konsistent.
- **`raise SystemExit(1)`** statt `sys.exit(1)` — Click-Konvention, durchgesetzt in Phase 68.

### Integration Points
- **`src/lucy_ng/cli/lsd.py`** — neue `pylsd`-Group + `pylsd run`-Command leben hier ODER in einem neuen `src/lucy_ng/cli/pylsd.py` Modul. Letzteres bevorzugt für Trennung (Planner finalisiert).
- **`src/lucy_ng/cli/main.py`** — eine Zeile Group-Registrierung hinzufügen.
- **`pyproject.toml`** — keine neuen Dependencies erwartet (RDKit, click, jsonschema sind alle schon da).

</code_context>

<specifics>
## Specific Ideas

- **Findings-Doc-Template:** Die `form-tolerance.md` sollte einem reproducible-research-Style folgen: Hypothese → Setup → Methode → Output → Conclusion → Reproducibility-Notes. So kann ein zukünftiger Wissenschaftler den Test selbst nachvollziehen.
- **Regression-Baseline-Erzeugung als Wave-0-Task:** Den `expected_inchis.txt` Baseline-File im selben Plan generieren wie den Test, mit explizitem manuellen Verifikations-Schritt im PLAN.md (Acceptance-Criterion: "Entwickler hat Baseline-Set chemisch inspiziert und committet").
- **Skipping behavior:** Bei `@skipif(LSD missing)` soll pytest klar reporten "skipped (LSD not installed)" statt silent skip — Standard pytest-Verhalten ist gut, aber Planner soll explizit confirmen.

</specifics>

<deferred>
## Deferred Ideas

- **Parallelisierung der LSD-Läufe** — PyLSDOrchestrator führt aktuell sequentiell aus. Bei K=3 sind 8 Permutationen × ~20s LSD = ~3 min. Könnte mit `concurrent.futures` parallelisiert werden. Defer bis UAT zeigt dass es zu langsam ist.
- **Resume-on-failure** — wenn eine Permutation crasht, die anderen laufen weiter, aber neu-starten ist heute "alles nochmal". Eine `--resume`-Option könnte teilweise Ergebnisse cachen. Defer.
- **`lucy pylsd run --dry-run`** — Permutations-Files schreiben aber nicht LSD aufrufen, für Debugging. Defer; aktueller `lucy lsd run` hat das auch nicht.
- **CI mit LSD-Binary in Docker** — würde `@skipif` obsolet machen. Defer als Infrastructure-Verbesserung.

</deferred>

---

*Phase: 69-cli-command-and-regression-suite*
*Context gathered: 2026-05-19*
