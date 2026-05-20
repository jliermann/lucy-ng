# Phase 71: Ibuprofen CASE UAT - Context

**Gathered:** 2026-05-20
**Status:** Ready for planning
**Phase type:** User Acceptance Test (human-in-the-loop, blind run) — NOT a build phase

<domain>
## Phase Boundary

End-to-end User Acceptance Test des gesamten v8.0-Stacks (Python-Infrastruktur Phase 65-67 + Schema/CLI Phase 68-69 + Agent-Skills Phase 70). Eine **frische, blind agierende Claude-Instanz** löst die Ibuprofen-Struktur via `/lucy-ng:case` autonom. Erfolg = aromatischer Ring in den Top-3 ranked Solutions — das ist exakt der v4.0-UAT-Failure, den die ganze v8.0-Investition adressiert.

**In scope:**
- Blind-CASE-Run durch frische Instanz auf sanitisiertem Datensatz
- Verifikation gegen UAT-01 + UAT-02
- Milestone-Complete-Gate für v8.0

**Out of scope:**
- Code-Änderungen (alles geshippt in Phase 65-70; falls der Run einen Bug aufdeckt → eigene Bug-Phase)
- Neue Testdatensätze (separater nmrxiv-Workflow, vom User erwähnt aber später)

</domain>

<decisions>
## UAT Setup Decisions

### Datensatz

- **D-21:** Testdatensatz ist `~/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE1` (außerhalb des Repos, in der Testdaten-Sammlung des Users). Es ist Ibuprofen (C13H18O2), 7 Bruker-Experimente: 1=?, 2=13C, 3=DEPT-135, 4=DEPT-90, 5=COSY, 6=HSQC, 7=HMBC.
- **D-21a (Sanitisierung):** CASE1 wurde 2026-05-20 vollständig blind-gemacht: 60 Metadaten-Files redigiert (`Ibuprofen`/`ibuprof` → `[REDACTED]` inkl. `##$NAME2` und `$$`-Pfad-Kommentare), keine `.mol`/`.sdf`-Struktur-Files, `molecular-formula.txt` = `C13H18O2`. Spektraldaten via nmrglue voll lesbar (zerstörungsfrei verifiziert).
- **D-21b (Formel-Übergabe):** Molekülformel C13H18O2 wird der frischen Instanz explizit übergeben (simuliert HRMS), Compound-Name NICHT.

### Run-Protokoll

- **D-22:** Der CASE-Run läuft in einer **frischen Claude-Instanz** (neue Session), NICHT in der Build-/Bookkeeping-Instanz. Begründung: Die Build-Instanz kennt Compound-Identität, 4J-Korrelationen und pyLSD-Design — würde die Hausaufgabe mit Lösungsschlüssel benoten. Methodische Validität erfordert Trennung.
- **D-22a (Befehl):** `/lucy-ng:case ~/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE1 C13H18O2`
- **D-22b (Keine Kontamination):** Der UAT-Operator gibt der frischen Instanz keine Hinweise auf Identität, 4J-Korrelationen oder erwartete Struktur. Der Agent muss autonom 4J-Risiko erkennen, `pylsd_mode` aktivieren, deferred_4j schreiben, permutieren.

### Erfolgskriterien (aus ROADMAP, gekoppelt an REQUIREMENTS UAT-01/02)

- **D-23:** UAT besteht wenn ALLE vier ROADMAP-Success-Criteria TRUE sind:
  1. CASE-Run nutzt `lucy pylsd run` mit ≥2 Permutationen die die 3 bekannten 4J-Korrelationen abdecken (Atome 4-8, 6-9, 8-4 in Standard-Nummerierung)
  2. Ibuprofen (oder Struktur mit verifiziertem aromatischem Ring + Formel C13H18O2) in Top-3 von `merged.smi`
  3. `CASE-PROGRESS.md` dokumentiert welche Permutations-Konfiguration die korrekte Lösung erzeugte + welche Korrelationen als 4J deferred wurden
  4. `run_report.json` geschrieben, zeigt Solution-Verteilung über Permutationen — mind. 1 Permutation erzeugt aromatische-Ring-Lösung
- **D-23a (Verifikation):** Die Build-/Bookkeeping-Instanz (ich) verifiziert die zurückgebrachten Artefakte (CASE-PROGRESS.md, merged.smi, run_report.json) gegen D-23. RDKit-Aromatic-Ring-Check + Formel-Check auf die Top-3, kein Vertrauen auf Agent-Selbstbericht (v4.0-Lehre: solution-analyst halluzinierte rank #1 = ibuprofen).

### Failure-Handling

- **D-24:** Wenn der UAT scheitert (kein aromatischer Ring in Top-3), ist das ein VALIDES Ergebnis — es zeigt eine echte Lücke im v8.0-Stack. Kein Force-Pass. Stattdessen: Forensik (welche Stufe versagte — 4J-Detection? Routing? Permutation? Ranking?) → Bug-Phase oder Skill-Fix → Re-Run.
- **D-24a (v4.0-Vergleich):** Der v4.0-UAT fand 7 Lösungen, alle ohne aromatischen Ring (5/7/9-gliedrige Ringe). Wenn v8.0 dasselbe Muster zeigt, hat die pyLSD-Integration ihren Zweck verfehlt — kritisch zu dokumentieren.

### Claude's Discretion

- Exaktes Format des Verifikations-Reports (VERIFICATION.md) — Standard gsd-verifier-Struktur
- Ob ein zweiter Compound (CASE2-CASE8 existieren) als zusätzliche UAT-Bestätigung gefahren wird — optional, defer
- Wie tief die Forensik bei einem Failure geht — abhängig vom Failure-Modus

</decisions>

<canonical_refs>
## Canonical References

### Roadmap & Requirements
- `.planning/ROADMAP.md` §"Phase 71: Ibuprofen CASE UAT" — Goal, 4 Success Criteria
- `.planning/REQUIREMENTS.md` §UAT — UAT-01, UAT-02

### v8.0 Stack (das hier Getestete)
- `.planning/phases/65-hypothesis-gate/65-01-SUMMARY.md` — 4J-Hypothese (aromatischer Ring erscheint wenn 3 4J entfernt)
- `.planning/phases/66/67/68/69/70-*-SUMMARY.md` — vollständiger Stack
- `.planning/findings/form-tolerance.md` — FORM-Toleranz-Befund (`; FORM` Kommentar-Form)

### v4.0 Failure (das hier zu Behebende)
- Memory `MEMORY.md` §"v4.0 UAT Findings (2026-02-18, Ibuprofen CASE1 — Team Run)" — die 3 4J-Korrelationen (C4a 129.38↔C6 45.03, C5a 127.26↔C7 44.90), warum sie nicht gefangen wurden, solution-analyst-Halluzination

### Testdaten
- `~/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE1` — sanitisierter Ibuprofen-Datensatz (außerhalb Repo)
- `~/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE2..CASE8` — weitere Testcompounds (optional für Zusatz-UAT)

### Skills/Agents (vom Run genutzt)
- `~/.claude/commands/lucy-ng/case.md` — Orchestrator
- `~/.claude/agents/lucy-lsd-engineer.md`, `lucy-devils-advocate.md`, `lucy-nmr-chemist.md`, `lucy-solution-analyst.md` — Team

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Der gesamte v8.0-Stack ist deployed: `lucy pylsd run`, `lucy lsd validate-inventory`, v2-Inventory-Schema, G1-G4-Gates, Routing in lsd-engineer. Phase 71 baut NICHTS — sie übt das Deployed aus.
- `lucy lsd rank --format json` für die Verifikation der Top-3 (RDKit-Aromatic-Check kann über die SMILES laufen).

### Verification Tooling
- RDKit `Chem.MolFromSmiles(s)` → `mol.GetAromaticAtoms()` / Ring-Info für Aromatic-Ring-Check auf merged.smi Top-3
- `Chem.rdMolDescriptors.CalcMolFormula(mol)` für Formel-Verifikation == C13H18O2

### Integration Points
- Dies ist das Milestone-Complete-Gate. Nach bestandenem UAT → `/gsd:complete-milestone` für v8.0-Archivierung.

</code_context>

<specifics>
## Specific Ideas

- **Verifikation MUSS unabhängig sein**: v4.0-Lehre — der solution-analyst behauptete rank #1 = ibuprofen, RDKit zeigte 7-gliedrigen Ring. Daher: VERIFICATION.md prüft die merged.smi-SMILES selbst per RDKit, nicht via Agent-Behauptung.
- **Permutations-Provenance prüfen**: run_report.json sollte zeigen, dass GERADE die Permutation, die die suspekten 4J ausschließt, den aromatischen Ring produziert — das ist der mechanistische Beweis dass pyLSD funktioniert (nicht Zufall).

</specifics>

<deferred>
## Deferred Ideas

- **Zusatz-UAT auf CASE2-CASE8** — Breitere Validierung über mehr Compounds. Defer bis CASE1 (das v4.0-Failure-Case) besteht.
- **Neuer nmrxiv-Testdatensatz** — User will via `lucy fetch nmrxiv` einen neuen Datensatz bauen. Eigener Workflow, nach v8.0.
- **Automatisierter Regression-UAT** — CASE1 als wiederholbarer CI-UAT (schwierig wegen Agent-Nichtdeterminismus + LSD-Laufzeit). Defer.

</deferred>

---

*Phase: 71-ibuprofen-case-uat*
*Context gathered: 2026-05-20 — UAT phase, human-in-the-loop blind run*
