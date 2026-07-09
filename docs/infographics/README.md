# lucy-ng infographics

An editable 7-slide **16:9 infographic deck** about the lucy-ng project, for talking
to scientific colleagues. Light + dark theme, print-to-PDF ready.

The slides are **generated** from a Python build script — that script is the source of
truth, not the HTML. Edit `build.py`, re-run it, and the HTML/PDF regenerate.

## The slides

1. **Overview** — the combination thesis (domain skill-set + thin tools + Claude Code's
   agent-team feature), spectrum motif, GitHub repo
2. **The idea** — why an agent; spectra in, structure out; emergent (not forced) rings
3. **The pipeline** — Bruker data → pick → detect → build → LSD solve → rank → identity
   gate, plus the input-directory layout
4. **The agent team** — orchestrator + 4 specialists (+ diagnostic on escalation)
5. **nmrXiv data source** — `lucy fetch nmrxiv <DOI>`; where the CASE test set comes from
6. **Test set CASE1–9** — RDKit structures, formula, nmrXiv ID, solved status
7. **By the numbers** — DB / HOSE / fragments / tests; credits (Nuzillard/LSD, Bremser/HOSE)

## Files

| File | Role |
|------|------|
| `build.py` | **Source of truth.** Assembles `deck.html` from the structure SVGs + slide content (HTML/CSS live inline here). |
| `gen_structures.py` | Regenerates `structures.json` — draws the 9 CASE structures from SMILES via RDKit. Only needed if you change a molecule. |
| `structures.json` | Cached RDKit SVG depictions (so a plain layout edit needs no RDKit). |
| `deck.html` | **Generated** — the rendered deck. Don't hand-edit; `build.py` overwrites it. |
| `lucy-ng-infographics.pdf` | **Generated** — 16:9 PDF, one slide per page. |

## Rebuild

```bash
cd docs/infographics

# 1. (only if you changed a structure/SMILES) regenerate the depictions — needs rdkit
python gen_structures.py

# 2. regenerate deck.html
python build.py

# 3. (optional) export the 16:9 PDF, one slide per page
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --no-pdf-header-footer \
  --print-to-pdf="lucy-ng-infographics.pdf" "file://$PWD/deck.html"
```

## Editing tips

- **Text / wording / layout / colours** → edit the inline HTML+CSS strings in `build.py`,
  re-run step 2. All design tokens (palette, type, spacing) are CSS custom properties at
  the top of the `<style>` block, defined for both light and dark themes.
- **A molecule** → edit its SMILES in the `CASES` list in `gen_structures.py`, run step 1
  then step 2. Structures render on deliberately light "paper" cards so they stay legible
  in dark theme too.
- **Slide order / count** → slides are `<section class="slide">` blocks in `build.py`;
  keep the footer counters (`0N / 07`) in sync if you add/remove one.
- **Ground-truth data** (SMILES, formulas, nmrXiv IDs, solved status) came from
  `.planning/CASE-DATASET-IDENTITIES.md` + `PROJECT.md`/`STATE.md` — update there first,
  then mirror here.

## Live version

Published as a private Claude artifact (viewer can toggle light/dark):
https://claude.ai/code/artifact/5ea64f67-64ac-407e-a549-7066a66a93e4
