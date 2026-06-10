---
name: lucy-ng
description: Lucy-ng NMR structure elucidation - command listing
---

# Lucy-ng: AI-Powered NMR Structure Elucidation

## What do you want to do?

**I have an unknown compound and want to determine its structure from NMR data**
→ `/lucy-ng:case <compound_path> <formula>` — Full autonomous CASE workflow with 4-agent team

**I have a known structure (SMILES) and want to predict its 13C shifts**
→ `/lucy-ng:predict "<smiles>"` — HOSE-code based 13C shift prediction

**I have a 13C spectrum and want to check if the compound is in the database**
→ `/lucy-ng:dereplicate <bruker_path> <formula>` — Match spectrum against 928K compounds

**I want to prepare an NMR dataset for blind CASE evaluation**
→ `/lucy-ng:sanitise <dataset_path>` — Remove compound names, CAS numbers, structure files

**I want to check if my environment is ready**
→ `/lucy-ng:status` — Verify lucy-ng CLI, LSD solver, and database are installed

## Available Sub-Commands

| Command | Description |
|---------|-------------|
| `/lucy-ng:status` | Check environment readiness (lucy-ng, LSD, database) |
| `/lucy-ng:dereplicate` | Match 13C spectrum against compound database |
| `/lucy-ng:predict` | Predict 13C chemical shifts for a SMILES structure |
| `/lucy-ng:sanitise` | Remove compound identifiers for blind CASE evaluation |
| `/lucy-ng:case` | Full CASE workflow - autonomous structure elucidation from NMR |

## Quick Start

Not sure which command? See the decision tree above.

1. Check your environment: `/lucy-ng:status`
2. Try dereplication: `/lucy-ng:dereplicate data/compound/2 C14H16`
3. Try prediction: `/lucy-ng:predict "CCO"`
4. Sanitise a dataset: `/lucy-ng:sanitise data/compound/Ibuprofen`
5. Run full CASE: `/lucy-ng:case data/compound/virgiline C16H21NO2`
