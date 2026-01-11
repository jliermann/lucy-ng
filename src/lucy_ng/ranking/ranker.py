"""Solution ranking by 13C spectrum prediction."""

from lucy_ng.lsd.parser import LSDSolution
from lucy_ng.prediction import C13Predictor, PredictedShift

from .models import RankedSolution, RankingResult, ShiftAssignment


class SolutionRanker:
    """Rank LSD solutions by comparing predicted vs experimental 13C shifts.

    Uses the local HOSE-based C13Predictor to predict shifts for each
    candidate structure, then ranks by Mean Absolute Error (MAE) between
    predicted and experimental shifts.

    Example:
        >>> from lucy_ng import C13Predictor, SolutionRanker
        >>> predictor = C13Predictor.from_table_file("hose_lookup.json.gz")
        >>> ranker = SolutionRanker(predictor, tolerance=3.0)
        >>> result = ranker.rank(solutions, experimental_shifts=[180.5, 140.8, 129.4])
        >>> print(result.solutions[0].smiles)  # Best match
    """

    def __init__(
        self,
        predictor: C13Predictor,
        tolerance: float = 3.0,
    ) -> None:
        """Initialize the solution ranker.

        Args:
            predictor: C13Predictor instance for shift prediction
            tolerance: Maximum ppm difference for matching peaks (default: 3.0)
        """
        self.predictor = predictor
        self.tolerance = tolerance

    def rank(
        self,
        solutions: list[LSDSolution],
        experimental_shifts: list[float],
        top_n: int | None = None,
    ) -> RankingResult:
        """Rank LSD solutions by 13C spectrum similarity.

        Args:
            solutions: List of LSD solutions (must have SMILES for ranking)
            experimental_shifts: List of experimental 13C peak positions in ppm
            top_n: If specified, only return top N results

        Returns:
            RankingResult with solutions sorted by MAE (best first)
        """
        ranked: list[RankedSolution] = []
        skipped = 0

        for solution in solutions:
            # Skip solutions without SMILES
            if not solution.smiles:
                skipped += 1
                continue

            # Predict shifts for this structure
            try:
                prediction = self.predictor.predict_from_smiles(solution.smiles)
            except Exception:
                skipped += 1
                continue

            if not prediction.predictions:
                skipped += 1
                continue

            # Match predicted to experimental shifts
            assignments, mae = self._match_shifts(
                prediction.predictions,
                experimental_shifts,
            )

            # Count successful matches
            matched_count = sum(1 for a in assignments if a.is_matched)

            ranked_solution = RankedSolution(
                solution_index=solution.index,
                smiles=solution.smiles,
                mae=mae,
                matched_count=matched_count,
                total_carbons=prediction.carbon_count,
                prediction_rate=prediction.success_rate,
                assignments=assignments,
            )
            ranked.append(ranked_solution)

        # Sort by MAE (lower is better), then by match count (higher is better)
        ranked.sort(key=lambda r: (r.mae, -r.matched_count))

        # Limit results if requested
        if top_n is not None:
            ranked = ranked[:top_n]

        return RankingResult(
            solutions=ranked,
            experimental_shifts=experimental_shifts,
            total_solutions=len(solutions),
            ranked_count=len(ranked),
            skipped_count=skipped,
            tolerance=self.tolerance,
        )

    def _match_shifts(
        self,
        predictions: list[PredictedShift],
        experimental: list[float],
    ) -> tuple[list[ShiftAssignment], float]:
        """Match predicted shifts to experimental peaks using greedy algorithm.

        For each predicted shift (sorted by value, high to low), finds the
        closest unassigned experimental peak within tolerance.

        Args:
            predictions: List of predicted shifts from C13Predictor
            experimental: List of experimental 13C peaks in ppm

        Returns:
            Tuple of (list of ShiftAssignments, MAE for matched pairs)
        """
        assignments: list[ShiftAssignment] = []
        used_experimental: set[int] = set()

        # Sort predictions by shift value (high to low, like typical NMR display)
        sorted_preds = sorted(predictions, key=lambda p: -p.shift)

        # Sort experimental for efficient matching
        exp_sorted = sorted(enumerate(experimental), key=lambda x: -x[1])

        errors: list[float] = []

        for pred in sorted_preds:
            best_match_idx: int | None = None
            best_match_shift: float | None = None
            best_error: float | None = None

            # Find closest unassigned experimental peak within tolerance
            for exp_idx, exp_shift in exp_sorted:
                if exp_idx in used_experimental:
                    continue

                error = abs(pred.shift - exp_shift)
                if error <= self.tolerance:
                    if best_error is None or error < best_error:
                        best_match_idx = exp_idx
                        best_match_shift = exp_shift
                        best_error = error

            # Record assignment
            if best_match_idx is not None:
                used_experimental.add(best_match_idx)
                errors.append(best_error)  # type: ignore
                assignment = ShiftAssignment(
                    atom_index=pred.atom_index,
                    predicted_shift=pred.shift,
                    experimental_shift=best_match_shift,
                    error=best_error,
                )
            else:
                # Unmatched - penalize with tolerance value
                errors.append(self.tolerance)
                assignment = ShiftAssignment(
                    atom_index=pred.atom_index,
                    predicted_shift=pred.shift,
                    experimental_shift=None,
                    error=None,
                )

            assignments.append(assignment)

        # Calculate MAE (includes penalty for unmatched)
        mae = sum(errors) / len(errors) if errors else float("inf")

        return assignments, mae

    @classmethod
    def from_table_file(
        cls,
        table_path: str,
        tolerance: float = 3.0,
        max_radius: int = 6,
    ) -> "SolutionRanker":
        """Create a SolutionRanker from a HOSE lookup table file.

        Convenience method that creates the C13Predictor from a table file.

        Args:
            table_path: Path to HOSE lookup table (JSON or compressed)
            tolerance: Maximum ppm difference for matching (default: 3.0)
            max_radius: Maximum HOSE radius for prediction (default: 6)

        Returns:
            Configured SolutionRanker instance
        """
        from pathlib import Path

        predictor = C13Predictor.from_table_file(Path(table_path), max_radius=max_radius)
        return cls(predictor, tolerance=tolerance)
