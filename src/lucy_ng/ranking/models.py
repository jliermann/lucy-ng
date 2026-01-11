"""Data models for LSD solution ranking."""

from pydantic import BaseModel, Field


class ShiftAssignment(BaseModel):
    """Assignment of a predicted shift to an experimental peak.

    Represents the mapping between a predicted 13C chemical shift
    for a specific atom and its matched experimental peak.
    """

    atom_index: int = Field(description="Atom index in the molecule (0-indexed)")
    predicted_shift: float = Field(description="Predicted 13C shift in ppm")
    experimental_shift: float | None = Field(
        default=None, description="Matched experimental shift in ppm, None if unmatched"
    )
    error: float | None = Field(
        default=None,
        description="Absolute error |predicted - experimental| in ppm, None if unmatched",
    )

    @property
    def is_matched(self) -> bool:
        """Check if this prediction was matched to an experimental peak."""
        return self.experimental_shift is not None


class RankedSolution(BaseModel):
    """LSD solution with ranking score based on 13C spectrum similarity.

    Contains the predicted shifts, their assignments to experimental peaks,
    and the overall MAE score used for ranking.
    """

    solution_index: int = Field(description="Original solution index (1-based from LSD)")
    smiles: str = Field(description="SMILES string of the structure")
    mae: float = Field(description="Mean Absolute Error in ppm (lower is better)")
    matched_count: int = Field(description="Number of carbons matched to experimental peaks")
    total_carbons: int = Field(description="Total carbons in the structure")
    prediction_rate: float = Field(
        description="Fraction of carbons with successful predictions (0-1)"
    )
    assignments: list[ShiftAssignment] = Field(
        default_factory=list, description="Detailed shift assignments"
    )

    @property
    def match_rate(self) -> float:
        """Fraction of predicted carbons matched to experimental peaks."""
        if self.total_carbons == 0:
            return 0.0
        return self.matched_count / self.total_carbons

    def summary(self) -> str:
        """Return a human-readable summary of the ranking."""
        return (
            f"Solution {self.solution_index}: {self.smiles}\n"
            f"  MAE: {self.mae:.2f} ppm\n"
            f"  Matched: {self.matched_count}/{self.total_carbons} carbons\n"
            f"  Prediction rate: {self.prediction_rate:.1%}"
        )


class RankingResult(BaseModel):
    """Complete result of ranking LSD solutions.

    Contains all ranked solutions sorted by MAE (best first),
    along with metadata about the ranking process.
    """

    solutions: list[RankedSolution] = Field(
        default_factory=list, description="Ranked solutions, sorted by MAE (best first)"
    )
    experimental_shifts: list[float] = Field(
        default_factory=list, description="Experimental 13C shifts used for ranking"
    )
    total_solutions: int = Field(
        default=0, description="Total number of LSD solutions provided"
    )
    ranked_count: int = Field(
        default=0, description="Number of solutions successfully ranked (had valid SMILES)"
    )
    skipped_count: int = Field(
        default=0, description="Number of solutions skipped (no SMILES or prediction failed)"
    )
    tolerance: float = Field(default=3.0, description="Tolerance in ppm used for matching")

    def get_top(self, n: int) -> list[RankedSolution]:
        """Get the top N ranked solutions.

        Args:
            n: Number of top solutions to return

        Returns:
            List of top N RankedSolution objects
        """
        return self.solutions[:n]

    def summary(self) -> str:
        """Return a human-readable summary of the ranking result."""
        lines = [
            f"Ranking Result:",
            f"  Total solutions: {self.total_solutions}",
            f"  Successfully ranked: {self.ranked_count}",
            f"  Skipped: {self.skipped_count}",
            f"  Experimental peaks: {len(self.experimental_shifts)}",
            f"  Tolerance: {self.tolerance} ppm",
        ]
        if self.solutions:
            lines.append(f"\nTop solution:")
            lines.append(f"  {self.solutions[0].smiles}")
            lines.append(f"  MAE: {self.solutions[0].mae:.2f} ppm")
        return "\n".join(lines)
