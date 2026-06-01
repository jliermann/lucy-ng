# Phase 76: Milestone UAT Gate - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-01
**Phase:** 76-milestone-uat-gate
**Areas discussed:** Intended Mechanism / Kriterien, Verifikations-Harness, Blind-Protokoll & Intervention-Check, Pass-Scope & Failure-Handling

---

## Intended Mechanism / Kriterien

| Option | Description | Selected |
|--------|-------------|----------|
| Single primary path | Intended = `lucy lsd run` (normales LSD + `HMBC X Y 2 4`); pyLSD nur Fallback. Geerbte "pyLSD + ≥2 Permutationen"-Pflicht entfällt. Konsistent D-01/D-02. | ✓ |
| ROADMAP-Wortlaut behalten | pyLSD `lucy pylsd run` + ≥2 Permutationen verpflichtend (Phase-71-Erbe). Widerspricht D-02. | |
| Beide Pfade ok | Gate besteht, sobald aromatischer Ring + Formel in Top-3, egal welcher Pfad. | |

**User's choice:** Single primary path
**Notes:** Löst die zentrale ROADMAP-vs-D-02-Spannung. Die 4 Phase-71-Kriterien werden für v9.0 umgeschrieben.

---

## Verifikations-Harness (inkl. Provenance-Kriterium)

| Option | Description | Selected |
|--------|-------------|----------|
| Native-Constraint-Nachweis (Provenance) | Mechanistischer Beweis = LSD-File mit BOND/COSY + DEFF F/FEXP, KEIN SYME/DEFF NOT, extended-range HMBC; Ring emergiert ohne SKEL. run_report nur bei Fallback. | ✓ |
| run_report nur bei Fallback | Permutations-Provenance entfällt im Primary; kein Native-Constraint-Check. | |
| Nur Ergebnis zählt | Kein mechanistischer Nachweis, nur Ring + Formel in Top-3. | |
| Committetes Repo-Skript | `scripts/verify_case_solution.py merged.smi <formel>` → Top-3 Aromatic-Ring (≥6 Atome) + Formel-Match → PASS/FAIL JSON. Wiederverwendbar. | ✓ |
| Ad-hoc inline RDKit | Pro Compound inline, kein committetes Artefakt. | |
| Als lucy CLI-Subcommand | `lucy lsd verify-uat` als erste-Klasse Command. | |

**User's choice:** Native-Constraint-Nachweis + Committetes Repo-Skript
**Notes:** Provenance-Check ersetzt das pyLSD-Permutations-Kriterium 4. CLI-Promotion ist deferred.

---

## Blind-Protokoll & Intervention-Check

| Option | Description | Selected |
|--------|-------------|----------|
| Zählbare Bypass-Interventionen | "Intervention" = manuelle Pfad-ändernde Eingriffe (advisory injection, manuelles LSD-Edit, erzwungenes SKEL/Fragment). Schwelle 0. Autonome Iterationen zählen nicht. | ✓ |
| Qualitative Beurteilung | Freie Bookkeeper-Beurteilung, kein hartes Zähl-Kriterium. | |
| Kriterium streichen | Kriterium 3 als zu unscharf entfernen. | |

**User's choice:** Zählbare Bypass-Interventionen
**Notes:** Schließt den v8.0-7-Intervention-Rescue-Modus explizit aus.

---

## Pass-Scope & Failure-Handling

| Option | Description | Selected |
|--------|-------------|----------|
| CASE1 hartes Gate, CASE9 verpflichtend aber separat | AND-Gate, getrennt bewertet: CASE1 Regression, CASE9 Generalisierung. Kein Force-Pass. | ✓ |
| Striktes AND-Gate | Beide bestehen, ein Pass/Fail. Vermischt Signale. | |
| CASE1 Gate, CASE9 Bonus | Nur CASE1 hart; CASE9 optional. Würde UAT-04 unerfüllt lassen. | |
| Forensik → Bug-Phase → Re-Run | Failure ist valides Ergebnis; Forensik → Fix-Phase 77+ → Re-Run; VERIFICATION.md dokumentiert Failure-Modus. | ✓ |
| Nur dokumentieren, kein Auto-Folgeschritt | Failure festhalten, nächste Schritte ad-hoc. | |
| Build-Plan + Blind-Run-Protokoll getrennt | Teil 1 ausführbar (verify-Skript, Sanitisierungs-Check, Prep); Teil 2 manuelles Blind-Run-Gate (frische Instanz, nicht Executor). | ✓ |
| Reines Protokoll-Dokument | Kein Executor-Build; verify-Skript ad-hoc. | |

**User's choice:** CASE1 hartes Gate + CASE9 separat verpflichtend; Forensik → Bug-Phase → Re-Run; Build-Plan + Blind-Run-Protokoll getrennt
**Notes:** Spiegelt Phase 71 D-24. Plan-Struktur trennt autonom Ausführbares vom human-in-the-loop-Gate.

---

## Claude's Discretion

- Exaktes Format von VERIFICATION.md (Standard gsd-verifier)
- Argument-/Output-Signatur + Test-Coverage von `verify_case_solution.py`
- Forensik-Tiefe bei Failure (failure-modus-abhängig)
- Reihenfolge CASE1/CASE9 im Blind-Run

## Deferred Ideas

- Zusatz-UAT auf CASE2-CASE8 (nach CASE1+CASE9-Pass)
- Automatisierter Regression-UAT / CI (Agent-Nichtdeterminismus + LSD-Laufzeit)
- `verify_case_solution.py` → `lucy lsd verify-uat` CLI-Promotion
