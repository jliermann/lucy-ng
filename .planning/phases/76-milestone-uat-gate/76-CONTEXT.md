# Phase 76: Milestone UAT Gate - Context

**Gathered:** 2026-06-01
**Status:** Ready for planning
**Phase type:** User Acceptance Test (human-in-the-loop, blind run) — partly buildable, NOT a feature-build phase

<domain>
## Phase Boundary

End-to-end User Acceptance Test des gesamten v9.0-Stacks (Phase 72 Design-Re-Validation + Phase 73 Solution-Plumbing + Phase 74 Constraint-Preservation + Phase 75 Skill-Consolidation). Eine **frische, blind agierende Claude-Instanz** löst zwei aromatische Compounds via `/lucy-ng:case` autonom über den *intendierten Mechanismus* (v9.0 Single primary path). Erfolg wird **unabhängig per RDKit gegen On-Disk-Artefakte** verifiziert — kein Agent-Selbstbericht, kein manueller Bypass.

Zwei Compounds:
- **CASE1** = Ibuprofen, C13H18O2 (Regressions-Beweis — der v4.0/v8.0-Failure-Case)
- **CASE9** = 4-(1-hydroxyethyl)benzoic acid isopropylester, C12H16O3 (Generalisierungs-Beweis — gleicher para-aromatischer 4J-Failure-Modus, anderes Molekül, Erst-Run)

**In scope:**
- Build-Teil (vom Bookkeeper/Executor ausführbar): wiederverwendbares RDKit-Verifikations-Skript `verify_case_solution.py`, Sanitisierungs-Verifikation beider Datensätze, Arbeitsverzeichnis-Vorbereitung
- Blind-Run-Protokoll (human-in-the-loop): frische Instanz fährt `/lucy-ng:case` auf CASE1 + CASE9
- Unabhängige Verifikation der zurückgebrachten Artefakte gegen die (für v9.0 umgeschriebenen) Kriterien
- Milestone-Complete-Gate für v9.0; Kopplung an REQUIREMENTS UAT-03 + UAT-04

**Out of scope:**
- Code-Änderungen am CASE-Stack (alles geshippt in Phase 72-75; deckt der Run einen Bug auf → eigene Bug-Phase 77+)
- Neue Testdatensätze jenseits CASE1/CASE9 (CASE2-CASE8 optional, defer)
- Automatisierter Regression-UAT / CI-Integration (defer — Agent-Nichtdeterminismus + LSD-Laufzeit)

</domain>

<decisions>
## Implementation Decisions

### Intended Mechanism / Kriterien-Reconciliation

Die aus Phase 71 geerbten ROADMAP-Kriterien (Stand pyLSD-zentrisch) widersprechen den v9.0-Design-Decisions (Phase 72 D-01/D-02). Sie werden für v9.0 **umgeschrieben**.

- **D-76-01 (Intended Mechanism = Single primary path):** Der "intendierte Mechanismus" für das Gate ist `lucy lsd run` — normales LSD + extended bond range (`HMBC X Y 2 4`) für geflaggte 4J-Korrelationen. pyLSD-Permutation (`lucy pylsd run`) ist NUR Fallback bei 0 oder intraktabel vielen Lösungen aus dem Primary-Path. Konsistent mit [[project_lsd_native_commands]] und Phase 72 D-01/D-02. Die geerbte Pflicht "`lucy pylsd run` mit ≥2 Permutationen" ENTFÄLLT als Erfolgskriterium.
- **D-76-02 (Mechanistischer Nachweis = Native-Constraint-Proof):** Phase-71-Kriterium 4 (run_report.json-Permutationsverteilung) wird ersetzt. Mechanistischer Beweis = das emittierte LSD-File enthält native Constraints (BOND/COSY-Äquivalenz, DEFF F/FEXP Ring-Exclusion) und **KEIN** `SYME`/`DEFF NOT`, plus extended-range HMBC für geflaggte 4J; der aromatische Ring **emergiert ohne SKEL-Forcing** (Phase 72 D-04 EMERGENT). `run_report.json` ist nur erforderlich, falls der pyLSD-Fallback ausgelöst wurde.

### Verifikations-Harness

- **D-76-03 (Committetes Repo-Skript):** Die unabhängige RDKit-Verifikation wird als wiederverwendbares, versioniertes Skript gebaut: `scripts/verify_case_solution.py merged.smi <formel>`. Es prüft die **Top-3** von `merged.smi` auf (a) aromatischen Ring (RDKit, ≥6 aromatische Atome) und (b) exakten Formel-Match (`CalcMolFormula == <formel>`), und gibt PASS/FAIL als JSON aus. Einmal gebaut, für CASE1 + CASE9 und künftige UATs nutzbar. Trennt Verifikation sauber vom Agent-Selbstbericht (v4.0-Lehre: solution-analyst halluzinierte rank #1).
- **D-76-03a (Verifikations-Inhalt):** PASS für einen Compound erfordert: korrekte Struktur ODER ein RDKit-verifizierter aromatischer-Ring-Isomer mit exakter Formel in Top-3; `merged.smi` nicht leer.

### Blind-Protokoll & Intervention-Check

- **D-76-04 (Blindheit):** Der CASE-Run läuft in einer **frischen Claude-Instanz** (neue Session), NICHT in dieser Build-/Bookkeeping-Instanz. Übergeben wird nur die Molekülformel (simuliert HRMS), NICHT Compound-Name/Identität/4J-Hinweise/erwartete Struktur. Befehle: `/lucy-ng:case <CASE1-pfad> C13H18O2` bzw. `/lucy-ng:case <CASE9-pfad> C12H16O3`. Siehe [[feedback_blind_uat]]. Methodische Validität erfordert die Trennung — die Build-Instanz kennt Identität und Design.
- **D-76-05 (Intervention-Metrik, Kriterium 3 objektiv):** "Intervention" ist konkret definiert = manuelle Coordinator-Eingriffe, die den Solver-Pfad ändern (advisory constraint injection, manuelles LSD-File-Edit, erzwungenes SKEL/Fragment). **Schwelle: 0 solcher Bypass-Eingriffe.** Normale autonome Agent-Iterationen (inkrementelle HMBC-Addition, Re-Run nach 0 Lösungen, Ranking-Feedback) zählen NICHT als Intervention. Gemessen durch Auszählung aus `CASE-PROGRESS.md` durch den verifizierenden Bookkeeper (ggf. unterstützt durch das verify-Skript). Dies schließt den zentralen v8.0-Failure-Modus (7-Intervention-Rescue) explizit aus.

### Pass-Scope & Failure-Handling

- **D-76-06 (Pass-Scope = AND, getrennt bewertet):** Beide Compounds müssen bestehen für Milestone-Complete (AND-Gate, deckt UAT-03 + UAT-04). ABER getrennt bewertet: CASE1 = Regressions-Beweis, CASE9 = Generalisierungs-Beweis. Bei CASE9-Fail wird CASE1-Pass dokumentiert und CASE9 als echte Lücke behandelt — kein Force-Pass, der eine Hälfte verdeckt.
- **D-76-07 (Failure-Handling):** Fehlschlag (kein aromatischer Ring in Top-3 / Pfad-Bypass / Interventionen > 0) ist ein **VALIDES Ergebnis** — kein Force-Pass. Ablauf: Bookkeeper-Forensik (welche Stufe versagte: 4J-Detection / Routing / Constraint-Emission / Ranking) → neue Fix-Phase (77+) → Re-Run. `VERIFICATION.md` dokumentiert den Failure-Modus explizit. Spiegelt Phase 71 D-24.

### Plan-Struktur

- **D-76-08 (Build-Plan + Blind-Run-Protokoll getrennt):** Das PLAN.md hat zwei Teile. **Teil 1 (ausführbar, Executor/Bookkeeper):** baut + committet `verify_case_solution.py`, verifiziert CASE1- + CASE9-Sanitisierung, bereitet Arbeitsverzeichnisse vor. **Teil 2 (manuelles Gate, human-in-the-loop):** das Blind-Run-Protokoll, ausgeführt von einer FRISCHEN Instanz — NICHT von dieser Session, NICHT vom Executor. Der Executor baut nur Teil 1; Teil 2 ist als dokumentiertes manuelles Gate im Plan, kein autonom ausführbarer Task.

### Claude's Discretion

- Exaktes Format von `VERIFICATION.md` (Standard gsd-verifier-Struktur)
- Genaue Argument-/Output-Signatur und Test-Coverage von `verify_case_solution.py` (solange D-76-03/03a erfüllt sind)
- Wie tief die Forensik bei einem Failure geht (abhängig vom Failure-Modus)
- Ob CASE9 zuerst oder CASE1 zuerst gefahren wird

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap & Requirements
- `.planning/ROADMAP.md` §"Phase 76: Milestone UAT Gate" — Goal + 4 (zu v9.0 umzuschreibende) Success Criteria
- `.planning/REQUIREMENTS.md` §UAT — UAT-03 (CASE1 blind re-run), UAT-04 (CASE9 blind run)

### v9.0 Design-Decisions (definieren den intendierten Mechanismus)
- `.planning/phases/72-design-re-validation/72-DECISIONS.md` — D-01 (extended bond range PRIMARY, pyLSD FALLBACK), D-02 (single solver path), D-03 (native-only generator, SYME→BOND/COSY, DEFF NOT→DEFF F/FEXP), D-04 (aromatischer Ring EMERGENT, kein SKEL im Normalfall)

### Phase-71-Vorlage (UAT-Protokoll, pyLSD-zentrische Kriterien zum Umschreiben)
- `.planning/phases/71-ibuprofen-case-uat/71-CONTEXT.md` — Blind-Protokoll-Vorlage (D-21..D-24), Verifikations-Tooling-Hinweise, die 4 Original-Kriterien

### v8.0 Failure-Forensik (was NICHT wieder passieren darf)
- `.planning/v8.0-UAT-POSTMORTEM.md` — merge=0-Bug, Permutations-Constraint-Loss, 7-Intervention-Rescue-Pattern, SYME/DEFF NOT non-native
- Memory `MEMORY.md` §"v4.0 UAT Findings" — die 3 4J-Korrelationen, solution-analyst-Halluzination

### v9.0 Stack (das hier Getestete — geshippt Phase 73-75)
- `.planning/phases/73-solution-plumbing-fix/*-SUMMARY.md` — `lucy lsd run` auto-produces solutions.smi, outlsd file-arg
- `.planning/phases/74-constraint-preservation-and-merge/*-SUMMARY.md` — native constraint preservation, ring3/ring4 filter, emergent-aromatic e2e
- `.planning/phases/75-skill-consolidation/*-SUMMARY.md` — native BOND/COSY/DEFF-F skills, single-path, devils-advocate G5-G8

### Testdaten (außerhalb Repo)
- `~/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE1` — sanitisierter Ibuprofen-Datensatz (C13H18O2); Experimente 2=13C, 3=DEPT135, 4=DEPT90, 5=COSY, 6=HSQC, 7=HMBC
- `~/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE9` — sanitisierter C12H16O3-Datensatz (`NAME [REDACTED]`, Titel nur Formel); Experimente 1=1H, 4=HMBC, 5=HSQC, 8=COSY, 12=13C, 13=DEPT135 — **kein DEPT-90**, andere Nummerierung als CASE1

### Skills/Agents (vom Blind-Run genutzt)
- `~/.claude/commands/lucy-ng/case.md` — Orchestrator
- `~/.claude/agents/lucy-lsd-engineer.md`, `lucy-devils-advocate.md`, `lucy-nmr-chemist.md`, `lucy-solution-analyst.md` — v9.0-Team

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Der gesamte v9.0-Stack ist deployed: `lucy lsd run` (auto solutions.smi, Phase 73), native constraint emission + ring3/ring4-Filter (Phase 74), konsolidierte native-only Agent-Skills (Phase 75). Phase 76 baut am Stack NICHTS — sie übt das Deployed aus.
- `lucy lsd rank --format json` für Top-3-Ranking; SMILES daraus gehen in den RDKit-Check.

### Verification Tooling (für D-76-03 Skript)
- RDKit `Chem.MolFromSmiles(s)` → `mol.GetAromaticAtoms()` / Ring-Info für Aromatic-Ring-Check (≥6 aromatische Atome) auf merged.smi Top-3
- `Chem.rdMolDescriptors.CalcMolFormula(mol)` für exakten Formel-Match (== C13H18O2 / == C12H16O3)
- Skript-Ort: `scripts/` im Repo-Root (neues wiederverwendbares Harness-Artefakt)

### Integration Points
- Dies ist das v9.0-Milestone-Complete-Gate. Nach bestandenem UAT (beide Compounds) → `/gsd-complete-milestone` für v9.0-Archivierung.

</code_context>

<specifics>
## Specific Ideas

- **Verifikation MUSS unabhängig sein:** v4.0-Lehre — der solution-analyst behauptete rank #1 = ibuprofen, RDKit zeigte 7-gliedrigen Ring. Daher prüft `verify_case_solution.py` die merged.smi-SMILES selbst, nie via Agent-Behauptung.
- **Native-Constraint-Provenance prüfen:** Das emittierte LSD-File (im CASE-Arbeitsverzeichnis) muss BOND/COSY-Äquivalenz + DEFF F/FEXP enthalten und SYME/DEFF NOT-frei sein — das ist der mechanistische Beweis, dass der v9.0-Stack über den intendierten Pfad löste (nicht Zufall, nicht Rescue).
- **CASE9-Sanitisierung bereits verifiziert (2026-06-01):** `NAME [REDACTED]`, Titel zeigen nur `C12H16O3`, keine `.mol`/`.sdf`-Files. Der Plan soll dies dennoch als expliziten Pre-Run-Check festhalten.

</specifics>

<deferred>
## Deferred Ideas

- **Zusatz-UAT auf CASE2-CASE8** — breitere Validierung über mehr Compounds. Defer bis CASE1 + CASE9 bestehen.
- **Automatisierter Regression-UAT** — CASE1/CASE9 als wiederholbarer CI-UAT (schwierig wegen Agent-Nichtdeterminismus + LSD-Laufzeit). Defer.
- **`verify_case_solution.py` → `lucy lsd verify-uat` CLI-Subcommand** — falls das Skript sich bewährt, später als erste-Klasse CLI-Command promoten. Defer (Scope: Tests, JSON-Schema, Doku).

</deferred>

---

*Phase: 76-milestone-uat-gate*
*Context gathered: 2026-06-01 — UAT-Gate-Phase, human-in-the-loop blind run, v9.0 milestone gate*
