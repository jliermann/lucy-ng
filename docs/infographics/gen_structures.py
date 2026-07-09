"""Generate consistent, clean 2D structure SVGs for the CASE1-9 test set."""
import json
from rdkit import Chem
from rdkit.Chem import Draw, AllChem
from rdkit.Chem.Draw import rdMolDraw2D

CASES = [
    ("CASE1", "Ibuprofen",   "C13H18O2",   "CC(C)Cc1ccc(C(C)C(=O)O)cc1"),
    ("CASE2", "Caffeine",    "C8H10N4O2",  "Cn1c(=O)c2c(ncn2C)n(C)c1=O"),
    ("CASE3", "(R)-Pulegone","C10H16O",    "CC(C)=C1CCC(C)CC1=O"),
    ("CASE4", "Chamazulene", "C14H16",     "CCc1ccc2ccc(C)c-2c(C)c1"),
    ("CASE5", "Indigo",      "C16H10N2O2", "O=C1/C(=C2\\Nc3ccccc3C2=O)Nc2ccccc21"),
    ("CASE6", "(R)-Citronellol","C10H20O", "OCCC(C)CCC=C(C)C"),
    ("CASE7", "Virgiline",   "C15H24N2O2", "O=C1[C@@H]2C[C@@H](CN3CC[C@H](O)C[C@@H]23)[C@H]2CCCCN12"),
    ("CASE8", "Eugenol",     "C10H12O2",   "COc1cc(CC=C)ccc1O"),
    ("CASE9", "Isopropyl 4-(1-hydroxyethyl)benzoate","C12H16O3","CC(C)OC(=O)c1ccc(C(C)O)cc1"),
]

W, H = 320, 220
out = {}
for cid, name, formula, smi in CASES:
    mol = Chem.MolFromSmiles(smi)
    assert mol is not None, cid
    AllChem.Compute2DCoords(mol)
    d = rdMolDraw2D.MolDraw2DSVG(W, H)
    opts = d.drawOptions()
    opts.padding = 0.12
    opts.bondLineWidth = 2
    opts.clearBackground = False          # transparent
    # dark carbon skeleton that reads on a light card; keep heteroatom colours
    opts.updateAtomPalette({6: (0.10, 0.13, 0.18)})
    rdMolDraw2D.PrepareAndDrawMolecule(d, mol)
    d.FinishDrawing()
    svg = d.GetDrawingText()
    # strip the xml prolog so it inlines cleanly
    svg = svg.split("?>", 1)[-1].strip() if "?>" in svg else svg
    out[cid] = {"name": name, "formula": formula, "smiles": smi, "svg": svg}

with open("structures.json", "w") as f:
    json.dump(out, f)
print("generated", len(out), "structures")
for cid in out:
    print(cid, out[cid]["name"], len(out[cid]["svg"]), "bytes svg")
