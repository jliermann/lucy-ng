# Phase 70: Agent Skill Updates - Context

**Gathered:** 2026-05-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Markdown-Skill-Updates die das in Phase 65-69 gebaute pyLSD-Multi-Run-System in den AI-Agent-Workflow integrieren. lsd-engineer entscheidet basierend auf seinem v2-Inventory welcher CLI-Befehl genutzt wird (`lucy pylsd run` vs `lucy lsd run`); case.md bleibt CLI-agnostisch; devils-advocate fügt G4-Permutations-Cap-Check hinzu.

**In scope:**
- `~/.claude/agents/lucy-lsd-engineer.md` — Routing-Logik in §Run LSD (D-17); ITERATION-COMPLETE-Output-Vertrag für pylsd_mode (D-20)
- `~/.claude/agents/lucy-devils-advocate.md` — neuer G4 (Permutations-Cap K≤3)
- `~/.claude/commands/lucy-ng/case.md` — Loop-Detection-Hooks für pylsd_mode-Iterationen (case.md bleibt CLI-agnostisch, aber muss `lucy pylsd run` Output-Format kennen für Top-Rank-Inspektion)

**Out of scope:**
- Python-Code-Änderungen (alles bereits in Phase 65-69 implementiert)
- Live UAT mit Ibuprofen (Phase 71)
- Neue Devil's-Advocate-Gates über G4 hinaus
- Migration alter Iteration-Files (D-19: silent fallback)

</domain>

<decisions>
## Implementation Decisions

### Routing-Ort

- **D-17:** Routing-Entscheidung (`lucy pylsd run` vs `lucy lsd run`) lebt in **lsd-engineer.md**. Vor jedem LSD-Aufruf liest lsd-engineer sein eigenes Inventory-JSON (per `lucy lsd validate-inventory --format json`), checked `inventory.pylsd_mode`, und wählt den CLI-Befehl. case.md ist und bleibt CLI-agnostisch.
- **D-17a (Kapselung):** Domain-Logik (welcher Solver-Modus für welches Inventory) bleibt beim Agent der das Inventory schreibt. case.md kennt das Schema NICHT.
- **D-17b (Spawn-Protokoll):** case.md ändert sich NICHT an seinem Spawn-Protokoll für lsd-engineer. Der Agent bekommt weiterhin denselben Context-Block, entscheidet aber intern via Inventory-Read welchen CLI-Befehl er via Bash-Tool aufruft.

### Permutations-Cap (G4)

- **D-18:** Devil's-Advocate G4 = harter BLOCK bei K > 3. Wenn `deferred_4j` mehr als 3 Einträge hat, devils-advocate emittiert BLOCKED. Konsistent mit Phase 67's `PyLSDOrchestrator.run()` ValueError(K>3) — Fail-Fast vor dem Solver-Aufruf statt nach.
- **D-18a (Keine Override):** Konsistent mit D-08 (Phase 68) — kein neuer Override-Pfad. User kann per orchestrator-Intervention überschreiben falls echter Sonderfall.
- **D-18b (Severity):** CRITICAL, gleicher Severity-Level wie G1/G2/G3. Block-Nachricht muss klar erklären: "K=N>3 erzeugt 2^N=M Permutationen, PyLSDOrchestrator-Cap ist K≤3. nmr-chemist soll Top-3 wahrscheinlichste 4J-Suspects priorisieren oder Inventory korrigieren."

### Backward-Compatibility

- **D-19:** Wenn lsd-engineer einen LSD-File OHNE v2-Inventory-Block findet (also ABSENT, nicht MALFORMED) → silent default zu `lucy lsd run`. Keine WARNING. Das ist der Normalfall für klassische LSD-Runs ohne 4J-Anliegen.
- **D-19a (MALFORMED Bleibt):** Phase 69's MALFORMED-Detection (WR-01-Fix) bleibt aktiv — falsch geformtes Inventory ist Hard Error, kein silent fallback.
- **D-19b (v1 Legacy):** Phase 68's D-02 deckt v1-Inventory-Detection ab (WARNING + Fallback). Nicht neu erfunden.

### lsd-engineer ITERATION-COMPLETE Output bei pylsd_mode

- **D-20:** Wenn `lucy pylsd run` aufgerufen wurde, schreibt lsd-engineer in [ITERATION-COMPLETE] zwei strukturierte Blöcke:
  1. **Per-Permutation-Tabelle:** eine Zeile pro Permutation mit `permutation_id`, `defer_set` (z.B. "none", "atom4-atom8", "atom4-atom8 + atom6-atom9"), `solution_count`, `top_rank_quality` ("excellent" / "good" / "fair" / "no aromatic ring").
  2. **Aggregierter Block:** `merged_count` (unique InChIs nach SolutionMerger-Dedup), `top_3_smiles` (Top 3 ranked Solutions als SMILES-Strings — gleicher Output wie `lucy lsd rank --format json` Top-N).
- **D-20a (Source):** Daten kommen aus `run_report.json` + `lucy pylsd run --format json` stdout. lsd-engineer extrahiert per `jq` oder Python-One-Liner aus der JSON-Datei.
- **D-20b (Lesbarkeit):** Output ist Markdown-Tabelle für menschliche Reviewer, gleichzeitig parseable für case.md-Loop-Detection ("Hat irgendeine Permutation aromatischen Ring im Top-Rank?").

### Claude's Discretion

- Exakter Wortlaut der lsd-engineer-Section "Run LSD" Routing-Block (Planner finalisiert)
- Exakter Wortlaut der G4-Block-Message in devils-advocate
- Ob lsd-engineer's `lucy pylsd run` mit oder ohne `--working-dir`-Flag aufruft (default `dirname(lsd)/pylsd_run` reicht laut Phase 69 D-14 Discretion)
- Wie die ITERATION-COMPLETE-Markdown-Tabelle exakt formatiert ist (Spalten-Reihenfolge, Truncation für lange SMILES)
- Ob case.md-Loop-Detection neue Patterns für pylsd_mode-Iterationen braucht (z.B. "K-Permutationen aber alle leer" als Diagnostic-Trigger) — Planner darf entscheiden

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap & Requirements
- `.planning/ROADMAP.md` §"Phase 70: Agent Skill Updates" — Goal, dependencies, success criteria
- `.planning/REQUIREMENTS.md` §"Agent Integration" — AGT-01, AGT-02, AGT-03, AGT-04

### Prior Phase Artefakte (v8.0)
- `.planning/phases/65-hypothesis-gate/65-01-SUMMARY.md` — 4J-Hypothesen-Validierung
- `.planning/phases/66-lsdinputgenerator-extensions/66-*-SUMMARY.md` — pylsd_mode-Output (mit Phase-66-Backport: `; FORM` Kommentar-Form)
- `.planning/phases/67-pylsdorchestrator-and-solutionmerger/67-*-SUMMARY.md` — PyLSDOrchestrator (K≤3 ValueError), SolutionMerger, run_report.json
- `.planning/phases/68-constraint-inventory-v2-schema/68-VERIFICATION.md` und alle 68-SUMMARYs — v2 Schema + validate-inventory CLI mit `inventory: {...}` Success-Response
- `.planning/phases/69-cli-command-and-regression-suite/69-VERIFICATION.md` — `lucy pylsd run` CLI mit Suspect-Resolver, `--format json` Output-Shape
- `.planning/findings/form-tolerance.md` — FORM-Toleranz-Audit-Trail (begründet Phase-66-Backport)

### Agent Skill Files (zu erweiternde Files)
- `~/.claude/agents/lucy-lsd-engineer.md` — bereits ~487 Zeilen, schon Phase-68/69-aware. §"Run LSD" und §"ITERATION-COMPLETE" sind die zwei Hauptänderungs-Sektionen.
- `~/.claude/agents/lucy-devils-advocate.md` — §5B Check 4 (G1/G2/G3) — G4 wird als 4. Sub-Gate eingefügt.
- `~/.claude/commands/lucy-ng/case.md` — Loop-Detection-Sektion lesen, ggf. pylsd_mode-spezifische Hooks ergänzen (Discretion).

### Code (read-only, dient als Referenz für Skill-Doku)
- `src/lucy_ng/cli/pylsd.py` — Output-Shape für ITERATION-COMPLETE-Tabelle
- `src/lucy_ng/lsd/orchestrator.py` — `PyLSDOrchestrator.run()` Signatur + ValueError(K>3)
- `src/lucy_ng/lsd/__init__.py` — Exporte für `MergedSolution`, `MergeResult` (Felder die in run_report.json landen)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **lsd-engineer.md ist bereits v2-aware**: Section 5 (Constraint Inventory v2) ist seit Phase 68 vollständig; `HMBC X Y 2 4 ; ELIM` Syntax ist in §"4J Deferral Rule" dokumentiert (Zeile 195+). Phase 70 braucht NUR Routing-Block und Output-Vertrag.
- **devils-advocate.md hat G1/G2/G3**: Phase 68 + Phase 69 (G3-Anchored-Pattern-Fix) + Phase-66-Backport (G1 grep für `; FORM`) sind alle drin. G4 ist ein 4. Sub-Check unter der bestehenden Check-4-Struktur.
- **case.md hat Loop-Detection-Patterns**: bereits in `~/.claude/commands/lucy-ng/references/loop-patterns.md` ausgelagert (Phase 56 Skill-Quality-Overhaul). pylsd_mode-spezifische Patterns gehen dort hinein, nicht in case.md selbst.

### Established Patterns
- **Skill-Section-Renaming-Konvention**: Erst Subsection-Header (`### Section Name`), dann numbered list für Workflow-Steps (`1.`, `2.`, ...). Beispiel: §"4J Deferral Rule" in lsd-engineer.md.
- **Markdown-Block-Citation in Plans**: PLAN.md-Tasks geben in `<read_first>` die zu editierenden Sections + Line-Ranges (z.B. "§5C lines 411-425") an, statt komplette Files. Planner soll dies für die 3 Skill-Files weiterführen.
- **Grep-Verification Pattern**: Plans verifizieren Skill-Edits via `grep "..." ~/.claude/agents/lucy-*.md` — siehe Phase 68 + 69 Plans für Templates.

### Integration Points
- **lsd-engineer ↔ lucy pylsd run**: Bash-Aufruf `lucy pylsd run analysis/iteration_NN/compound.lsd --shifts "155.0,..." --format json | tee pylsd_output.json` — Agent extrahiert JSON in Memory für ITERATION-COMPLETE-Tabelle.
- **devils-advocate G4 ↔ Inventory**: `lucy lsd validate-inventory --format json compound.lsd | jq '.inventory.deferred_4j | length'` — count K. Wenn > 3 → BLOCK.
- **case.md ↔ ITERATION-COMPLETE**: Loop-Detection liest Per-Permutation-Tabelle. Wenn ALLE Permutationen "no aromatic ring" und mehrere Iterationen hintereinander — Trigger Diagnostic-Specialist.

</code_context>

<specifics>
## Specific Ideas

- **G4-Block-Message-Template**: "K=5 exceeds permutation cap (K≤3). PyLSDOrchestrator will raise ValueError. Action: nmr-chemist must prioritize Top-3 most likely 4J suspects (e.g., aromatic-to-aliphatic across known distance > 4J probability threshold); demote remaining entries from deferred_4j or remove `; ELIM` annotation on lower-priority HMBC lines."
- **Routing-Block-Position**: In lsd-engineer.md, der Routing-Code-Block gehört in §"Run LSD" (aktuell Zeile ~268, ~481). Statt unconditional `lucy lsd run compound.lsd` wird es eine 5-Zeilen-Conditional-Block die das Inventory liest und branched.
- **ITERATION-COMPLETE-Markdown-Format**: Inline-Code-Block für Tabelle (Markdown-Tabelle in Code-Fence) damit Output mono-spaced und parseable bleibt.

</specifics>

<deferred>
## Deferred Ideas

- **case.md Pylsd-Mode-Loop-Detection-Pattern** — "K-Permutationen alle leer" als Diagnostic-Trigger. Defer bis UAT (Phase 71) zeigt ob das wirklich ein Loop-Pattern ist oder seltener Edge-Case.
- **nmr-chemist 4J-Priorisierungs-Logik** — wenn K>3, soll der Skill explizit dokumentiert haben wie aus N Suspects die Top-3 ausgewählt werden? Defer als eigene Phase oder als Skill-Quality-Update.
- **Parallel Iteration-Strategy bei pylsd_mode** — case.md könnte 2 Iterationen parallel laufen lassen wenn beide unterschiedliche 4J-Strategien testen. Defer.
- **Inventory-Versions-Schema Migration-Skript** — wenn jemand alte v1-Inventory-Files re-prozessieren will, brauch ein One-Off-Konvertierer. Defer bis tatsächlich gebraucht.

</deferred>

---

*Phase: 70-agent-skill-updates*
*Context gathered: 2026-05-19*
