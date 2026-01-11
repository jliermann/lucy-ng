"""13C NMR chemical shift predictor using HOSE codes."""

import statistics
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import Mol

from .hose import HOSECodeGenerator
from .lookup import HOSELookupTable
from .models import PredictedShift, PredictionResult


class C13Predictor:
    """Predict 13C NMR chemical shifts from molecular structure.

    Uses HOSE codes to look up chemical shifts in a reference database.
    Implements fallback to shorter HOSE radii when exact matches aren't found.
    """

    def __init__(
        self,
        lookup_table: HOSELookupTable,
        max_radius: int = 6,
        min_radius: int = 1,
    ) -> None:
        """Initialize the predictor.

        Args:
            lookup_table: Pre-built HOSE lookup table
            max_radius: Maximum HOSE radius to try (default 6)
            min_radius: Minimum HOSE radius for fallback (default 1)
        """
        self._lookup = lookup_table
        self._hose_gen = HOSECodeGenerator()
        self._max_radius = max_radius
        self._min_radius = min_radius

    @classmethod
    def from_table_file(cls, table_path: Path, **kwargs) -> "C13Predictor":  # type: ignore[no-untyped-def]
        """Create predictor from a saved lookup table file.

        Args:
            table_path: Path to saved lookup table
            **kwargs: Additional arguments passed to __init__

        Returns:
            Configured C13Predictor instance
        """
        table = HOSELookupTable.load(table_path)
        return cls(table, **kwargs)

    def predict_from_smiles(self, smiles: str) -> PredictionResult:
        """Predict 13C shifts for a molecule from SMILES.

        Args:
            smiles: SMILES string

        Returns:
            PredictionResult with predictions for each carbon
        """
        mol = HOSECodeGenerator.prepare_mol(smiles)
        if mol is None:
            return PredictionResult(
                smiles=smiles,
                predictions=[],
                carbon_count=0,
                success_count=0,
            )

        predictions = self.predict_from_mol(mol)

        return PredictionResult(
            smiles=smiles,
            predictions=predictions,
            carbon_count=len(predictions) + self._count_failed_carbons(mol, predictions),
            success_count=len(predictions),
        )

    def predict_from_mol(self, mol: Mol) -> list[PredictedShift]:
        """Predict 13C shifts for a molecule.

        Args:
            mol: RDKit Mol object (should have explicit hydrogens)

        Returns:
            List of PredictedShift for each carbon with successful prediction
        """
        predictions: list[PredictedShift] = []

        # Ensure hydrogens are explicit
        if mol.GetNumAtoms() > 0:
            # Check if hydrogens are already explicit
            has_h = any(atom.GetSymbol() == "H" for atom in mol.GetAtoms())
            if not has_h:
                mol = Chem.AddHs(mol)

        for atom in mol.GetAtoms():
            if atom.GetSymbol() != "C":
                continue

            atom_idx = atom.GetIdx()
            prediction = self._predict_for_atom(mol, atom_idx)

            if prediction is not None:
                predictions.append(prediction)

        return predictions

    def _predict_for_atom(self, mol: Mol, atom_idx: int) -> PredictedShift | None:
        """Predict shift for a single carbon atom with fallback.

        Tries HOSE codes from max_radius down to min_radius until
        a match is found.

        Args:
            mol: RDKit Mol object
            atom_idx: Index of the carbon atom

        Returns:
            PredictedShift or None if no match found at any radius
        """
        # Try each radius from max to min
        for radius in range(self._max_radius, self._min_radius - 1, -1):
            try:
                hose_code = self._hose_gen.generate_for_atom(mol, atom_idx, radius=radius)
            except Exception:
                continue

            shifts = self._lookup.lookup(hose_code)

            if shifts:
                return self._create_prediction(
                    atom_idx=atom_idx,
                    hose_code=hose_code,
                    radius=radius,
                    shifts=shifts,
                )

        return None

    def _create_prediction(
        self,
        atom_idx: int,
        hose_code: str,
        radius: int,
        shifts: list[float],
    ) -> PredictedShift:
        """Create a PredictedShift from lookup results.

        Args:
            atom_idx: Atom index
            hose_code: HOSE code that matched
            radius: Radius at which match was found
            shifts: List of matched shifts

        Returns:
            PredictedShift with statistics
        """
        median_shift = statistics.median(shifts)
        std_dev = statistics.stdev(shifts) if len(shifts) > 1 else 0.0

        # Calculate confidence based on:
        # 1. Radius (higher = more confident)
        # 2. Number of matches (more = more confident, up to a point)
        # 3. Standard deviation (lower = more confident)
        confidence = self._calculate_confidence(
            radius=radius,
            match_count=len(shifts),
            std_dev=std_dev,
        )

        return PredictedShift(
            atom_index=atom_idx,
            shift=median_shift,
            confidence=confidence,
            hose_code=hose_code,
            radius_used=radius,
            match_count=len(shifts),
            std_dev=std_dev,
            min_shift=min(shifts),
            max_shift=max(shifts),
        )

    def _calculate_confidence(
        self,
        radius: int,
        match_count: int,
        std_dev: float,
    ) -> float:
        """Calculate confidence score for a prediction.

        Args:
            radius: HOSE radius used (1-6)
            match_count: Number of reference matches
            std_dev: Standard deviation of matched shifts

        Returns:
            Confidence score between 0 and 1
        """
        # Radius component (0.1 to 1.0)
        # Higher radius = more structural specificity
        radius_score = radius / self._max_radius

        # Match count component (0.5 to 1.0)
        # More matches = more statistical confidence
        # Logarithmic scaling, saturates around 100 matches
        import math

        match_score = min(1.0, 0.5 + 0.5 * math.log10(max(1, match_count)) / 2)

        # Std dev component (0.5 to 1.0)
        # Lower std dev = more consistent predictions
        # Penalize high variance (>10 ppm std)
        std_score = max(0.5, 1.0 - std_dev / 20)

        # Weighted combination
        # Radius is most important for prediction quality
        confidence = 0.5 * radius_score + 0.3 * match_score + 0.2 * std_score

        return round(confidence, 3)

    def _count_failed_carbons(
        self, mol: Mol, predictions: list[PredictedShift]
    ) -> int:
        """Count carbons that weren't successfully predicted.

        Args:
            mol: RDKit Mol object
            predictions: List of successful predictions

        Returns:
            Number of carbons without predictions
        """
        predicted_indices = {p.atom_index for p in predictions}
        failed = 0

        for atom in mol.GetAtoms():
            if atom.GetSymbol() == "C" and atom.GetIdx() not in predicted_indices:
                failed += 1

        return failed

    @property
    def lookup_table(self) -> HOSELookupTable:
        """Access the underlying lookup table."""
        return self._lookup
