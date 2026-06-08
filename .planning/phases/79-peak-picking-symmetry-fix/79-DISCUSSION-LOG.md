# Phase 79: Peak-Picking & Symmetry Detection Fix - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-08
**Phase:** 79-peak-picking-symmetry-fix
**Areas discussed:** Solvens-Masking-Fix, Intensitäts-Symmetrie, Quality-Loop-Grenzen, DBE-Self-Check-Scope

---

## Solvens-Masking-Fix

### Threshold-Ansatz
| Option | Description | Selected |
|--------|-------------|----------|
| SNR/MAD-absolut + Solvens-Ausschluss (beide) | Rauschbasierter absoluter Threshold + CDCl₃-Multiplett-Ausschluss vor Schwellenberechnung | ✓ |
| Nur SNR/MAD-absolut | Rauschbasierter Threshold allein | |
| Nur Solvens-Region-Ausschluss | CDCl₃-Bereich maskieren, max-relativ sonst | |

### Solvens-Erkennung
| Option | Description | Selected |
|--------|-------------|----------|
| Bruker acqus SOLVENT + Heuristik-Fallback | SOLVENT-Param → Shift-Tabelle, ppm-Heuristik nur Fallback | ✓ |
| Reine ppm-Heuristik (~77 ppm) | Fester CDCl₃-Bereich hartkodiert | |
| Du entscheidest | Claude wählt im Plan | |

### Picker-Philosophie / Gatekeeper (Steinbeck-Refinement)
| Option | Description | Selected |
|--------|-------------|----------|
| Picker großzügig (SNR≥3) + SNR-annotiert, Agent urteilt | Statistischer Floor (IUPAC LoD), chemisches Urteil agentisch | ✓ |
| Picker entscheidet mit moderatem SNR-Cutoff (z.B. 5) | Picker als alleiniger Gatekeeper | |
| Du entscheidest | Claude wählt im Plan | |

**User's choice:** alle drei Empfehlungen (beide-Threshold, Bruker-Param, großzügiger Picker)
**Notes:** Steinbeck-Einwand war zentral: "Das Carbonyl wäre keinem Chemiker entgangen — es liegt
sauber weit jenseits des Rausch-Levels; deshalb fällt es mir schwer, mich auf einen hart
verdrahteten Wert festzulegen." → Reframing: Fragilität saß im Bezug auf `max` statt Rauschen, nicht
im SNR-Cutoff. Lösung: Picker rein statistisch (SNR≥3, kein getunter Wert) + SNR-Annotation, Chemie
agentisch. Plot des realen 13C-Spektrums (full + Carbonyl-Zoom 150–175 ppm) wurde erstellt und nach
~/Downloads exportiert; bestätigt MAD-noise 1.230e5 / max 4.591e7 / Carbonyl SNR≈17 unter 5%·max.

---

## Intensitäts-Symmetrie

### Intensitätsquelle / Vergleichsbasis
| Option | Description | Selected |
|--------|-------------|----------|
| 13C-Intensität, normiert pro Multiplizitäts-Klasse | ~2× Median-1C derselben Klasse = 2C-Kandidat | ✓ |
| HSQC-Kreuzsignal-Volumina (primär) | Robuster für protonierte, aber aufwändiger | |
| Du entscheidest | Claude wählt im Plan | |

### Scope (welche C)
| Option | Description | Selected |
|--------|-------------|----------|
| Nur protonierte aromatische CH | Dort Intensität verlässlich, genau was emergent-COSY braucht | ✓ |
| Protonierte + quartäre mit Vorsicht | Auch symmetrische Cq tentativ | |
| Alle Multiplizitäten gleich | Maximale Sensitivität, höchste FP-Gefahr | |

### Tooling vs Skill boundary (formel-bewusste Plausibilität)
| Option | Description | Selected |
|--------|-------------|----------|
| (A) rein agentisch | Tooling dumm-deterministisch, Skill macht alles | |
| (B) Tooling-Hinweis + Skill-Entscheidung | Deterministisches Sensor-Signal + agentische Entscheidung | ✓ (kombiniert mit A) |
| (C) voll im Tooling | Picker zieht Formel selbst heran, re-picked automatisch | |

**User's choice:** 13C-klassen-normiert + formel-bewusste Plausibilität; nur protonierte arom. CH;
Boundary (B)+(A)
**Notes:** Steinbeck ergänzte, dass Plausibilitätschecks (erwarten wir aus Summenformel notorisch
schwache C=O/Amide?) nötig sind und gut als "agentisches Zusammenspiel" passen → bestätigt den
(B)+(A)-Schnitt: deterministisches Tool-Signal, agentische Entscheidung.

---

## Quality-Loop-Grenzen

### Trigger
| Option | Description | Selected |
|--------|-------------|----------|
| Alle Top-K IMPLAUSIBLE/QUESTIONABLE (primär), MAE sekundär | Verdikt-basiert + MAE als ODER | ✓ |
| Nur best-MAE > Tier-Schwelle | Rein numerisch | |
| Du entscheidest | Claude wählt im Plan | |

### Aktion
| Option | Description | Selected |
|--------|-------------|----------|
| Annahmen-Re-Examination (Symmetrie/Multiplizität/DBE), Re-Pick nur falls indiziert | Prüft Interpretation, nicht stumpf re-pick | ✓ |
| Stumpfer Re-Pick bei niedrigerem Threshold | Bringt wenig, Floor schon niedrig | |
| Du entscheidest | Claude wählt im Plan | |

### Budget
| Option | Description | Selected |
|--------|-------------|----------|
| 1 Re-Look-Zyklus, dann ehrlicher Abbruch | Genau ein Zyklus, dann terminieren | ✓ |
| Bis zu N=2 Zyklen mit Fortschritts-Check | Zwei Zyklen, Abbruch ohne Fortschritt | |
| Du entscheidest | Claude wählt im Plan | |

**User's choice:** Verdikt-basierter Trigger; Annahmen-Re-Examination; genau 1 Zyklus
**Notes:** Kontext-Reframe: durch den großzügigen SNR≥3-Picker ist der Carbonyl gar nicht erst weg,
also ist der Quality-Loop ein Backstop gegen Fehl-Interpretation, kein "nochmal tiefer picken".

---

## DBE-Self-Check-Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Allgemeine DBE-Bilanz, formel-gesteuerte Regions-Hinweise | O→Carbonyl, N→Amid/Nitril/Imin; deckt CASE9 + N-Fälle | ✓ |
| Nur Carbonyl-Region (160–220) bei O-haltigen Formeln | Minimal, nur CASE9 | |
| Du entscheidest | Claude wählt im Plan | |

**User's choice:** Allgemeine DBE-Bilanz mit formel-gesteuerten Regions-Hinweisen (SCOPE-SEED Q4 = ja, N abdecken)
**Notes:** Procedural/mandatory im nmr-chemist (Success Criterion 3).

---

## Claude's Discretion
- Exaktes `k` der SNR-Schwelle (IUPAC LoD-Konvention k=3); MAD-Implementierungsdetails
- Umfang der Solvens-Shift-Tabelle
- Wie die per-Peak-SNR-Annotation durch die CLI/JSON fließt
- Regressionstest-Konstruktion (CASE9-Carbonyl gepickt + CASE1 unverändert)

## Deferred Ideas
None — discussion stayed within phase scope.
