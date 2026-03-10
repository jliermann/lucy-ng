"""Generate coupling path statistics from compound database.

This module provides the data pipeline that populates the coupling_path_stats
table with the statistical foundation for 4J HMBC coupling detection.

For each compound in the database, we:
1. Parse SMILES with implicit H (no AddHs — HOSE code convention)
2. Map COCONUT 1-based atom indices to 0-based RDKit indices
3. Validate each atom is carbon (skip non-carbons)
4. Skip compounds with any NULL atom_index in shifts
5. Compute all-pairs shortest bond distances via Chem.GetDistanceMatrix
6. For each (carbon, proton-bearing-carbon) pair, generate HOSE codes at radius 2
7. Accumulate (c_hose, h_hose, distance) -> count statistics
8. Checkpoint every chunk_size compounds for safe resume
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Any

from rdkit import Chem
from tqdm import tqdm

from lucy_ng.database.models import CouplingPathStatsRecord
from lucy_ng.prediction.hose import HOSECodeGenerator

if TYPE_CHECKING:
    from lucy_ng.database import DatabaseManager


# ---------------------------------------------------------------------------
# Checkpoint key constants
# ---------------------------------------------------------------------------

CHECKPOINT_KEY_LAST_COMPOUND_ID = "coupling_path_last_compound_id"
CHECKPOINT_KEY_COMPOUNDS_PROCESSED = "coupling_path_compounds_processed"
CHECKPOINT_KEY_COMPOUNDS_FAILED = "coupling_path_compounds_failed"


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------


class CouplingPathStatsGenerator:
    """Generate (carbon_hose, h_carbon_hose, bond_distance) -> count statistics.

    Iterates over compounds in the database, computes shortest bond-path
    distances for all (carbon, proton-bearing-carbon) pairs using
    RDKit GetDistanceMatrix, generates HOSE codes at radius 2 for both atoms,
    and accumulates the statistics for insertion into coupling_path_stats.

    Supports checkpoint/resume for long-running production database builds.

    Usage::

        with DatabaseManager("compounds.db") as db:
            gen = CouplingPathStatsGenerator(db)
            result = gen.run(chunk_size=10000, fresh=True)
            print(result["unique_entries"], "entries inserted")

    For development with a subset::

        with DatabaseManager("compounds.db") as db:
            gen = CouplingPathStatsGenerator(db)
            counts = gen.generate_all(progress=False, limit=100)
    """

    def __init__(self, db_manager: DatabaseManager) -> None:
        """Initialize the generator.

        Args:
            db_manager: Database manager for compound iteration and stats insertion
        """
        self.db_manager = db_manager
        self._hose_gen = HOSECodeGenerator()
        self._logger = logging.getLogger("lucy_ng.coupling_path_stats")

        # Statistics tracking
        self._compounds_processed = 0
        self._compounds_failed = 0
        self._last_compound_id = 0

    # ------------------------------------------------------------------
    # Checkpoint helpers
    # ------------------------------------------------------------------

    def _load_checkpoint(self) -> bool:
        """Load checkpoint from database if exists.

        Returns:
            True if checkpoint was loaded, False if starting fresh
        """
        last_id = self.db_manager.get_checkpoint(CHECKPOINT_KEY_LAST_COMPOUND_ID)
        if last_id is None:
            return False

        self._last_compound_id = int(last_id)

        processed = self.db_manager.get_checkpoint(CHECKPOINT_KEY_COMPOUNDS_PROCESSED)
        if processed:
            self._compounds_processed = int(processed)

        failed = self.db_manager.get_checkpoint(CHECKPOINT_KEY_COMPOUNDS_FAILED)
        if failed:
            self._compounds_failed = int(failed)

        return True

    def _save_checkpoint(self) -> None:
        """Save current progress to checkpoint."""
        self.db_manager.set_checkpoint(
            CHECKPOINT_KEY_LAST_COMPOUND_ID, str(self._last_compound_id)
        )
        self.db_manager.set_checkpoint(
            CHECKPOINT_KEY_COMPOUNDS_PROCESSED, str(self._compounds_processed)
        )
        self.db_manager.set_checkpoint(
            CHECKPOINT_KEY_COMPOUNDS_FAILED, str(self._compounds_failed)
        )

    def _clear_checkpoint(self) -> None:
        """Clear all checkpoints."""
        self.db_manager.clear_checkpoint(CHECKPOINT_KEY_LAST_COMPOUND_ID)
        self.db_manager.clear_checkpoint(CHECKPOINT_KEY_COMPOUNDS_PROCESSED)
        self.db_manager.clear_checkpoint(CHECKPOINT_KEY_COMPOUNDS_FAILED)

    def _clear_coupling_path_stats(self) -> None:
        """Delete all rows from coupling_path_stats table."""
        conn = self.db_manager.connection
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM coupling_path_stats")
            conn.commit()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Core processing
    # ------------------------------------------------------------------

    def _process_compound(
        self,
        compound_id: int,
        smiles: str,
        shifts: list[tuple[int | None, float]],
        counts: dict[tuple[str, str, int], int],
    ) -> bool:
        """Process one compound and accumulate (c_hose, h_hose, distance) counts.

        Args:
            compound_id: Compound ID (for logging)
            smiles: SMILES string
            shifts: List of (atom_index, shift_ppm) tuples from DB (1-based COCONUT)
            counts: Mutable dict to accumulate counts into

        Returns:
            True if compound was processed successfully, False if it failed/was skipped
        """
        # Skip compound if ANY shift has NULL atom_index (architecture requirement)
        for atom_idx, _ in shifts:
            if atom_idx is None:
                return False

        # Parse SMILES with implicit H (CRITICAL: never call AddHs)
        mol = HOSECodeGenerator.prepare_mol(smiles)
        if mol is None:
            return False

        num_atoms = mol.GetNumAtoms()

        # Convert COCONUT 1-based indices to 0-based and validate
        valid_carbons: list[int] = []
        for atom_idx_1based, _ in shifts:
            # Type narrowed: we checked for None above
            assert atom_idx_1based is not None
            atom_idx_0based = atom_idx_1based - 1

            # Bounds check
            if atom_idx_0based < 0 or atom_idx_0based >= num_atoms:
                continue

            # Validate: must be carbon
            atom = mol.GetAtomWithIdx(atom_idx_0based)
            if atom.GetSymbol() != "C":
                continue

            valid_carbons.append(atom_idx_0based)

        if not valid_carbons:
            # No valid carbons — skip (not a failure per se, but no output)
            return True

        # Compute all-pairs shortest path distances in one call
        dist_matrix = Chem.GetDistanceMatrix(mol)

        # Identify proton-bearing carbons among valid atoms
        # (any carbon with at least 1 implicit or explicit H)
        proton_bearing: set[int] = set()
        for idx in valid_carbons:
            atom = mol.GetAtomWithIdx(idx)
            if atom.GetTotalNumHs() > 0:
                proton_bearing.add(idx)

        # Generate pairs (c_idx, h_idx) where:
        # - c_idx is any valid carbon (the "observed carbon" in HMBC)
        # - h_idx is a proton-bearing carbon (the "H-bearing carbon")
        # - c_idx != h_idx
        for c_idx in valid_carbons:
            for h_idx in proton_bearing:
                if c_idx == h_idx:
                    continue

                raw_dist = dist_matrix[c_idx][h_idx]

                # Skip disconnected (should not happen in a valid molecule)
                if raw_dist <= 0 or raw_dist == float("inf"):
                    continue

                # Cap at 5 for paths >= 5 bonds
                dist = int(min(raw_dist, 5))

                # Generate HOSE codes at radius 2 for both atoms
                try:
                    c_hose = self._hose_gen.generate_for_atom(mol, c_idx, radius=2)
                    if not c_hose:
                        continue
                    h_hose = self._hose_gen.generate_for_atom(mol, h_idx, radius=2)
                    if not h_hose:
                        continue
                except Exception:
                    continue

                counts[(c_hose, h_hose, dist)] += 1

        return True

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def generate_all(
        self,
        progress: bool = True,
        limit: int | None = None,
        start_id: int = 0,
    ) -> dict[tuple[str, str, int], int]:
        """Generate coupling path statistics for all compounds.

        Iterates over all compounds in the DB starting from start_id, builds
        the (carbon_hose, h_carbon_hose, bond_distance) -> count dict.

        Args:
            progress: Show tqdm progress bar
            limit: Stop after processing this many compounds (for dev/testing)
            start_id: Start from this compound ID (exclusive); used for resume

        Returns:
            Dict mapping (carbon_hose, h_carbon_hose, bond_distance) to count
        """
        self._compounds_processed = 0
        self._compounds_failed = 0

        counts: dict[tuple[str, str, int], int] = defaultdict(int)

        total = self.db_manager.get_compound_count()

        compound_iter = self.db_manager.iter_compounds_with_shifts_from(
            start_id=start_id
        )
        if progress:
            compound_iter = tqdm(
                compound_iter,
                total=total,
                desc="Generating coupling path stats",
                unit=" compounds",
            )

        for compound_id, smiles, shifts in compound_iter:
            if limit is not None and self._compounds_processed >= limit:
                break

            self._compounds_processed += 1
            self._last_compound_id = compound_id

            success = self._process_compound(compound_id, smiles, shifts, counts)
            if not success:
                self._compounds_failed += 1

        return dict(counts)

    def populate_database(self, progress: bool = True) -> int:
        """Generate statistics and insert into database.

        Runs generate_all() then converts to CouplingPathStatsRecord list
        and inserts into the coupling_path_stats table.

        Args:
            progress: Show progress bar

        Returns:
            Number of records inserted
        """
        counts = self.generate_all(progress=progress)

        if not counts:
            return 0

        records = [
            CouplingPathStatsRecord(
                carbon_hose=c_hose,
                h_carbon_hose=h_hose,
                bond_distance=dist,
                count=count,
            )
            for (c_hose, h_hose, dist), count in counts.items()
        ]

        return self.db_manager.insert_coupling_path_stats_batch(records)

    def run(
        self,
        resume: bool = True,
        fresh: bool = False,
        chunk_size: int = 10000,
        limit: int | None = None,
        progress: bool = True,
    ) -> dict[str, Any]:
        """Main entry point for production runs with checkpoint/resume.

        Processes compounds in chunks of chunk_size, checkpointing after each
        chunk. Accumulates all counts in memory, then does a single batch insert
        at the end (correct behavior for INSERT OR REPLACE semantics).

        Args:
            resume: If True, resume from checkpoint if one exists
            fresh: If True, clear existing coupling_path_stats and checkpoint first
            chunk_size: Number of compounds to process per checkpoint interval
            limit: Stop after this many compounds total (for testing)
            progress: Show progress bar

        Returns:
            Summary dict with keys: compounds_processed, compounds_failed, unique_entries
        """
        if fresh:
            self._clear_coupling_path_stats()
            self._clear_checkpoint()
            self._last_compound_id = 0
            self._compounds_processed = 0
            self._compounds_failed = 0

        if resume and not fresh:
            if self._load_checkpoint():
                self._logger.info(
                    f"Resuming from checkpoint: last_id={self._last_compound_id}, "
                    f"processed={self._compounds_processed}"
                )
            else:
                self._logger.info("No checkpoint found, starting fresh")

        start_id = self._last_compound_id

        # Accumulate counts in memory; for resume we re-process from checkpoint
        # position forward. INSERT OR REPLACE handles idempotency of the final write.
        all_counts: dict[tuple[str, str, int], int] = defaultdict(int)

        total = self.db_manager.get_compound_count()

        compound_iter = self.db_manager.iter_compounds_with_shifts_from(
            start_id=start_id
        )

        if progress:
            compound_iter = tqdm(
                compound_iter,
                total=total,
                desc="Generating coupling path stats",
                unit=" compounds",
            )

        chunk_count = 0

        for compound_id, smiles, shifts in compound_iter:
            if limit is not None and (self._compounds_processed) >= limit:
                break

            self._compounds_processed += 1
            self._last_compound_id = compound_id

            success = self._process_compound(compound_id, smiles, shifts, all_counts)
            if not success:
                self._compounds_failed += 1

            chunk_count += 1

            # Save checkpoint every chunk_size compounds
            if chunk_count >= chunk_size:
                self._save_checkpoint()
                chunk_count = 0
                self._logger.debug(
                    f"Checkpoint saved: last_id={self._last_compound_id}, "
                    f"processed={self._compounds_processed}"
                )

        # Final batch insert
        records = [
            CouplingPathStatsRecord(
                carbon_hose=c_hose,
                h_carbon_hose=h_hose,
                bond_distance=dist,
                count=count,
            )
            for (c_hose, h_hose, dist), count in all_counts.items()
        ]

        if records:
            self.db_manager.insert_coupling_path_stats_batch(records)

        # Clear checkpoint on successful completion
        self._clear_checkpoint()

        unique_entries = len(all_counts)

        return {
            "compounds_processed": self._compounds_processed,
            "compounds_failed": self._compounds_failed,
            "unique_entries": unique_entries,
        }

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def compounds_processed(self) -> int:
        """Number of compounds processed in last generate_all() or run() call."""
        return self._compounds_processed

    @property
    def compounds_failed(self) -> int:
        """Number of compounds that failed or were skipped in last call."""
        return self._compounds_failed
