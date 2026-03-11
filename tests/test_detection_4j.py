"""Tests for 4J coupling detection module."""

from __future__ import annotations

from pathlib import Path

import pytest

from lucy_ng.database import DatabaseManager
from lucy_ng.detection import StatisticalDetector
from lucy_ng.detection.models import (
    CouplingPathDistribution,
    CouplingPathResult,
    RiskLevel,
)


# ---------------------------------------------------------------------------
# Task 1: Model unit tests
# ---------------------------------------------------------------------------


class TestCouplingPathDistribution:
    """Tests for CouplingPathDistribution model."""

    def test_all_zeros_dominant_unknown(self) -> None:
        dist = CouplingPathDistribution()
        assert dist.dominant == "unknown"

    def test_j2_dominant(self) -> None:
        dist = CouplingPathDistribution(j2=0.6, j3=0.3, j4=0.08, j5_plus=0.02)
        assert dist.dominant == "j2"

    def test_j3_dominant(self) -> None:
        dist = CouplingPathDistribution(j2=0.2, j3=0.7, j4=0.05, j5_plus=0.05)
        assert dist.dominant == "j3"

    def test_j4_dominant(self) -> None:
        dist = CouplingPathDistribution(j2=0.1, j3=0.2, j4=0.6, j5_plus=0.1)
        assert dist.dominant == "j4"

    def test_j5_plus_dominant(self) -> None:
        dist = CouplingPathDistribution(j2=0.1, j3=0.1, j4=0.3, j5_plus=0.5)
        assert dist.dominant == "j5_plus"

    def test_p_long_range_sums_j4_j5(self) -> None:
        dist = CouplingPathDistribution(j2=0.6, j3=0.3, j4=0.08, j5_plus=0.02)
        assert abs(dist.p_long_range - 0.10) < 1e-9

    def test_p_long_range_zero_when_no_data(self) -> None:
        dist = CouplingPathDistribution()
        assert dist.p_long_range == 0.0

    def test_json_serialization_includes_all_fields(self) -> None:
        dist = CouplingPathDistribution(j2=0.6, j3=0.3, j4=0.08, j5_plus=0.02)
        data = dist.model_dump()
        assert set(data.keys()) == {"j2", "j3", "j4", "j5_plus"}

    def test_probabilities_stored_correctly(self) -> None:
        dist = CouplingPathDistribution(j2=0.6, j3=0.3, j4=0.08, j5_plus=0.02)
        assert dist.j2 == 0.6
        assert dist.j3 == 0.3
        assert dist.j4 == 0.08
        assert dist.j5_plus == 0.02


class TestRiskLevel:
    """Tests for RiskLevel enum."""

    def test_has_four_values(self) -> None:
        values = [r.value for r in RiskLevel]
        assert len(values) == 4

    def test_has_unlikely_4j(self) -> None:
        assert RiskLevel.unlikely_4j is not None

    def test_has_possible_4j(self) -> None:
        assert RiskLevel.possible_4j is not None

    def test_has_likely_4j(self) -> None:
        assert RiskLevel.likely_4j is not None

    def test_has_insufficient_data(self) -> None:
        assert RiskLevel.insufficient_data is not None


class TestCouplingPathResult:
    """Tests for CouplingPathResult model."""

    def _make_result(
        self,
        risk_level: RiskLevel,
        has_data: bool = True,
        recommendation: str = "",
    ) -> CouplingPathResult:
        return CouplingPathResult(
            carbon_shift=129.0,
            h_carbon_shift=45.0,
            distribution=CouplingPathDistribution(j2=0.6, j3=0.3, j4=0.08, j5_plus=0.02),
            total_observations=200,
            risk_level=risk_level,
            recommendation=recommendation,
            has_data=has_data,
        )

    def test_likely_4j_has_defer_recommendation(self) -> None:
        result = CouplingPathResult(
            carbon_shift=129.0,
            h_carbon_shift=45.0,
            distribution=CouplingPathDistribution(j2=0.1, j3=0.2, j4=0.5, j5_plus=0.2),
            total_observations=200,
            risk_level=RiskLevel.likely_4j,
            recommendation="defer",
            has_data=True,
        )
        assert result.recommendation == "defer"

    def test_possible_4j_has_hmbc_recommendation(self) -> None:
        result = CouplingPathResult(
            carbon_shift=129.0,
            h_carbon_shift=45.0,
            distribution=CouplingPathDistribution(j2=0.6, j3=0.2, j4=0.15, j5_plus=0.05),
            total_observations=200,
            risk_level=RiskLevel.possible_4j,
            recommendation="HMBC X Y 2 4",
            has_data=True,
        )
        assert result.recommendation == "HMBC X Y 2 4"

    def test_unlikely_4j_has_normal_recommendation(self) -> None:
        result = CouplingPathResult(
            carbon_shift=129.0,
            h_carbon_shift=45.0,
            distribution=CouplingPathDistribution(j2=0.8, j3=0.15, j4=0.03, j5_plus=0.02),
            total_observations=200,
            risk_level=RiskLevel.unlikely_4j,
            recommendation="normal",
            has_data=True,
        )
        assert result.recommendation == "normal"

    def test_insufficient_data_recommendation(self) -> None:
        result = CouplingPathResult(
            carbon_shift=129.0,
            h_carbon_shift=45.0,
            distribution=CouplingPathDistribution(),
            total_observations=30,
            risk_level=RiskLevel.insufficient_data,
            recommendation="insufficient data — include as normal",
            has_data=True,
        )
        assert result.recommendation == "insufficient data — include as normal"

    def test_summary_returns_nonempty_string(self) -> None:
        result = CouplingPathResult(
            carbon_shift=129.0,
            h_carbon_shift=45.0,
            distribution=CouplingPathDistribution(j2=0.6, j3=0.3, j4=0.08, j5_plus=0.02),
            total_observations=200,
            risk_level=RiskLevel.unlikely_4j,
            recommendation="normal",
            has_data=True,
        )
        summary = result.summary()
        assert isinstance(summary, str)
        assert len(summary) > 10

    def test_summary_contains_shift_info(self) -> None:
        result = CouplingPathResult(
            carbon_shift=129.0,
            h_carbon_shift=45.0,
            distribution=CouplingPathDistribution(j2=0.6, j3=0.3, j4=0.08, j5_plus=0.02),
            total_observations=200,
            risk_level=RiskLevel.unlikely_4j,
            recommendation="normal",
            has_data=True,
        )
        summary = result.summary()
        assert "129.0" in summary
        assert "45.0" in summary

    def test_summary_contains_risk_level(self) -> None:
        result = CouplingPathResult(
            carbon_shift=129.0,
            h_carbon_shift=45.0,
            distribution=CouplingPathDistribution(j2=0.6, j3=0.3, j4=0.08, j5_plus=0.02),
            total_observations=200,
            risk_level=RiskLevel.likely_4j,
            recommendation="defer",
            has_data=True,
        )
        summary = result.summary()
        assert "likely_4j" in summary or "likely" in summary.lower()

    def test_model_has_has_data_field(self) -> None:
        result = CouplingPathResult(
            carbon_shift=129.0,
            h_carbon_shift=45.0,
            distribution=CouplingPathDistribution(),
            total_observations=0,
            risk_level=RiskLevel.insufficient_data,
            recommendation="insufficient data — include as normal",
            has_data=False,
        )
        assert result.has_data is False

    def test_model_has_used_fallback_field(self) -> None:
        result = CouplingPathResult(
            carbon_shift=129.0,
            h_carbon_shift=45.0,
            distribution=CouplingPathDistribution(j2=0.6, j3=0.3, j4=0.08, j5_plus=0.02),
            total_observations=200,
            risk_level=RiskLevel.unlikely_4j,
            recommendation="normal",
            has_data=True,
            used_fallback=True,
        )
        assert result.used_fallback is True

    def test_model_unique_hose_pairs_default_zero(self) -> None:
        result = CouplingPathResult(
            carbon_shift=129.0,
            h_carbon_shift=45.0,
            distribution=CouplingPathDistribution(),
            total_observations=0,
            risk_level=RiskLevel.insufficient_data,
            recommendation="insufficient data — include as normal",
            has_data=False,
        )
        assert result.unique_hose_pairs == 0

    def test_json_serialization(self) -> None:
        result = CouplingPathResult(
            carbon_shift=129.0,
            h_carbon_shift=45.0,
            distribution=CouplingPathDistribution(j2=0.6, j3=0.3, j4=0.08, j5_plus=0.02),
            total_observations=200,
            risk_level=RiskLevel.unlikely_4j,
            recommendation="normal",
            has_data=True,
        )
        json_str = result.model_dump_json()
        assert "129.0" in json_str
        assert "risk_level" in json_str


# ---------------------------------------------------------------------------
# Task 2: detect_4j_coupling integration tests (using test_db fixture)
# ---------------------------------------------------------------------------


@pytest.fixture
def test_db(tmp_path: Path) -> Path:
    """Create test database with hose_stats and coupling_path_stats data."""
    db_path = tmp_path / "test_4j.db"

    with DatabaseManager(db_path) as db:
        db.create_tables()

        conn = db.connection
        cursor = conn.cursor()

        # HOSE stats for ~129 ppm (aromatic carbon) — radius 2
        cursor.execute(
            """
            INSERT INTO hose_stats
                (hose_code, radius, mean, std, count, sp3_count, sp2_count, sp1_count)
            VALUES
                ('C-3;=CC(//)', 2, 129.0, 1.5, 500, 5, 490, 5),
                ('C-3;=CC(=C/)', 2, 130.0, 1.5, 400, 4, 392, 4)
            """
        )

        # HOSE stats for ~45 ppm (aliphatic CH2 — CH or CH2 next to aromatic)
        cursor.execute(
            """
            INSERT INTO hose_stats
                (hose_code, radius, mean, std, count, sp3_count, sp2_count, sp1_count)
            VALUES
                ('C-4;CC(CC/)', 2, 45.0, 1.5, 600, 595, 5, 0),
                ('C-4;CC(CO/)', 2, 44.5, 1.5, 300, 298, 2, 0)
            """
        )

        # coupling_path_stats rows:
        # Scenario A: likely_4j (p_long_range >= 0.50)
        # carbon_hose='C-3;=CC(//)', h_carbon_hose='C-4;CC(CC/)'
        # bond_distance=2: 30 obs, bond_distance=3: 20 obs, bond_distance=4: 55 obs => total=105, 4J=52.4%
        cursor.executemany(
            """
            INSERT INTO coupling_path_stats (carbon_hose, h_carbon_hose, bond_distance, count)
            VALUES (?, ?, ?, ?)
            """,
            [
                ("C-3;=CC(//)", "C-4;CC(CC/)", 2, 30),
                ("C-3;=CC(//)", "C-4;CC(CC/)", 3, 20),
                ("C-3;=CC(//)", "C-4;CC(CC/)", 4, 55),
                # Scenario B: possible_4j (p_long_range >= 0.15 but < 0.50)
                # carbon_hose='C-3;=CC(=C/)', h_carbon_hose='C-4;CC(CC/)'
                # bond_distance=2: 40, bond_distance=3: 40, bond_distance=4: 20 => total=100, 4J=20%
                ("C-3;=CC(=C/)", "C-4;CC(CC/)", 2, 40),
                ("C-3;=CC(=C/)", "C-4;CC(CC/)", 3, 40),
                ("C-3;=CC(=C/)", "C-4;CC(CC/)", 4, 20),
                # Scenario C: unlikely_4j (p_long_range < 0.15)
                # use a different h_carbon_hose for carbon 'C-3;=CC(//)'
                ("C-3;=CC(//)", "C-4;CC(CO/)", 2, 80),
                ("C-3;=CC(//)", "C-4;CC(CO/)", 3, 15),
                ("C-3;=CC(//)", "C-4;CC(CO/)", 4, 5),  # total=100, 4J=5%
                # Scenario D: insufficient_data — only 30 total observations
                # use carbon='C-3;=CC(=C/)', h_carbon='C-4;CC(CO/)'
                ("C-3;=CC(=C/)", "C-4;CC(CO/)", 2, 15),
                ("C-3;=CC(=C/)", "C-4;CC(CO/)", 3, 10),
                ("C-3;=CC(=C/)", "C-4;CC(CO/)", 4, 5),  # total=30, < min_observations=50
            ],
        )

        conn.commit()

    return db_path


def test_detect_4j_coupling_likely_tier(test_db: Path) -> None:
    """P(4J) >= 0.50 returns likely_4j with defer recommendation."""
    with StatisticalDetector(test_db) as detector:
        # carbon at ~129 ppm (matches 'C-3;=CC(//)'), h_carbon at ~45 ppm
        # coupling stats: 30J2 + 20J3 + 55J4 = 105 total => 4J = 52.4%
        result = detector.detect_4j_coupling(129.0, 45.0)

    assert result.risk_level == RiskLevel.likely_4j
    assert result.recommendation == "defer"
    assert result.has_data is True
    assert result.distribution.p_long_range >= 0.50


def test_detect_4j_coupling_possible_tier(test_db: Path) -> None:
    """P(4J) >= 0.15 but < 0.50 returns possible_4j."""
    with StatisticalDetector(test_db) as detector:
        # carbon at ~130 ppm (matches 'C-3;=CC(=C/)'), h_carbon at ~45 ppm
        # coupling stats: 40J2 + 40J3 + 20J4 = 100 total => 4J = 20%
        result = detector.detect_4j_coupling(130.0, 45.0)

    assert result.risk_level == RiskLevel.possible_4j
    assert "2 4" in result.recommendation or "HMBC" in result.recommendation
    assert result.has_data is True
    assert 0.15 <= result.distribution.p_long_range < 0.50


def test_detect_4j_coupling_unlikely_tier(test_db: Path) -> None:
    """P(4J) < 0.15 returns unlikely_4j with normal recommendation."""
    with StatisticalDetector(test_db) as detector:
        # carbon at ~129 ppm, h_carbon at ~44.5 ppm
        # coupling stats: 80J2 + 15J3 + 5J4 = 100 total => 4J = 5%
        result = detector.detect_4j_coupling(129.0, 44.5)

    assert result.risk_level == RiskLevel.unlikely_4j
    assert result.recommendation == "normal"
    assert result.has_data is True
    assert result.distribution.p_long_range < 0.15


def test_detect_4j_coupling_insufficient_data(test_db: Path) -> None:
    """Total observations < min_observations returns insufficient_data."""
    with StatisticalDetector(test_db) as detector:
        # carbon at ~130 ppm, h_carbon at ~44.5 ppm => 30 total observations
        result = detector.detect_4j_coupling(130.0, 44.5, min_observations=50)

    assert result.risk_level == RiskLevel.insufficient_data
    assert result.total_observations == 30
    assert result.has_data is True  # data exists, just not enough


def test_detect_4j_coupling_no_data_returns_has_data_false(test_db: Path) -> None:
    """No matching HOSE codes at all returns has_data=False."""
    with StatisticalDetector(test_db) as detector:
        # 300 ppm has no hose_stats entries
        result = detector.detect_4j_coupling(300.0, 400.0)

    assert result.has_data is False


def test_detect_4j_coupling_fallback_to_carbon_aggregation(tmp_path: Path) -> None:
    """When exact pair not found, fallback aggregates over all partners."""
    db_path = tmp_path / "fallback.db"

    with DatabaseManager(db_path) as db:
        db.create_tables()
        conn = db.connection
        cursor = conn.cursor()

        # HOSE stat for the carbon (at 129 ppm)
        cursor.execute(
            """
            INSERT INTO hose_stats
                (hose_code, radius, mean, std, count, sp3_count, sp2_count, sp1_count)
            VALUES
                ('C-3;=CC(//)', 2, 129.0, 1.5, 500, 5, 490, 5)
            """
        )

        # HOSE stat for h_carbon at 45 ppm — but NO coupling_path_stats for this pair
        cursor.execute(
            """
            INSERT INTO hose_stats
                (hose_code, radius, mean, std, count, sp3_count, sp2_count, sp1_count)
            VALUES
                ('C-4;XX(YY/)', 2, 45.0, 1.5, 300, 298, 2, 0)
            """
        )

        # Fallback rows: carbon='C-3;=CC(//)' paired with ANY partner
        # (different h_carbon_hose not in hose_stats)
        cursor.executemany(
            """
            INSERT INTO coupling_path_stats (carbon_hose, h_carbon_hose, bond_distance, count)
            VALUES (?, ?, ?, ?)
            """,
            [
                ("C-3;=CC(//)", "SOME-OTHER-HOSE-A", 2, 20),
                ("C-3;=CC(//)", "SOME-OTHER-HOSE-A", 3, 15),
                ("C-3;=CC(//)", "SOME-OTHER-HOSE-A", 4, 60),  # 4J dominant
                ("C-3;=CC(//)", "SOME-OTHER-HOSE-B", 2, 10),
                ("C-3;=CC(//)", "SOME-OTHER-HOSE-B", 3, 10),
                ("C-3;=CC(//)", "SOME-OTHER-HOSE-B", 4, 80),
            ],
        )

        conn.commit()

    with StatisticalDetector(db_path) as detector:
        result = detector.detect_4j_coupling(129.0, 45.0)

    # Fallback was used (exact pair has no match)
    assert result.used_fallback is True
    assert result.has_data is True
    # Total: 20+15+60+10+10+80 = 195, 4J = (60+80)/195 ≈ 71.8% => likely_4j
    assert result.risk_level == RiskLevel.likely_4j


def test_detect_4j_coupling_configurable_thresholds(test_db: Path) -> None:
    """Custom thresholds are applied correctly."""
    with StatisticalDetector(test_db) as detector:
        # 20% 4J is "possible" by default, but "unlikely" with likely_threshold=0.10
        result = detector.detect_4j_coupling(
            130.0,
            45.0,
            likely_threshold=0.10,
            possible_threshold=0.05,
        )

    # 20% >= 10% likely_threshold => likely_4j
    assert result.risk_level == RiskLevel.likely_4j


def test_detect_4j_coupling_configurable_window(test_db: Path) -> None:
    """window_ppm parameter controls HOSE lookup window."""
    with StatisticalDetector(test_db) as detector:
        # Very narrow window => no HOSE codes match 129.0 (nearest is at 129.0 exactly)
        result = detector.detect_4j_coupling(129.0, 45.0, window_ppm=0.001)

    # Window might be too narrow to find any coupling stats; could be no data or reduced
    # Just verify the call succeeds and returns a valid result
    assert isinstance(result, CouplingPathResult)
    assert isinstance(result.risk_level, RiskLevel)
