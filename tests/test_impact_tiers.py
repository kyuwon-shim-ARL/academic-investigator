"""Tests for academic_investigator.core.impact_tiers."""

from __future__ import annotations

import pytest

from academic_investigator.core.impact_tiers import (
    IMPACT_TIERS,
    LAB_GRADE_DESCRIPTIONS,
    LAB_GRADE_THRESHOLDS,
    RESEARCH_GRADES,
    calculate_impact_tier,
    calculate_lab_grade,
    calculate_research_grade,
)


# ==================================================================
# calculate_impact_tier
# ==================================================================


class TestCalculateImpactTier:
    """Test impact tier classification boundaries."""

    def test_elite_exactly_50(self):
        result = calculate_impact_tier(50)
        assert result["tier"] == "Elite"
        assert result["label"] == "Elite"
        assert result["percentile"] == "Top 1%"

    def test_elite_above_50(self):
        result = calculate_impact_tier(75)
        assert result["tier"] == "Elite"

    def test_senior_leader_exactly_30(self):
        result = calculate_impact_tier(30)
        assert result["tier"] == "Senior Leader"
        assert result["percentile"] == "Top 5%"

    def test_senior_leader_at_49(self):
        result = calculate_impact_tier(49)
        assert result["tier"] == "Senior Leader"

    def test_established_exactly_20(self):
        result = calculate_impact_tier(20)
        assert result["tier"] == "Established"
        assert result["percentile"] == "Top 10%"

    def test_established_at_29(self):
        result = calculate_impact_tier(29)
        assert result["tier"] == "Established"

    def test_mid_career_exactly_10(self):
        result = calculate_impact_tier(10)
        assert result["tier"] == "Mid-Career"
        assert result["percentile"] == "Top 25%"

    def test_mid_career_at_19(self):
        result = calculate_impact_tier(19)
        assert result["tier"] == "Mid-Career"

    def test_early_career_exactly_0(self):
        result = calculate_impact_tier(0)
        assert result["tier"] == "Early Career"
        assert result["percentile"] == "Emerging"

    def test_early_career_at_9(self):
        result = calculate_impact_tier(9)
        assert result["tier"] == "Early Career"

    def test_returns_all_expected_keys(self):
        result = calculate_impact_tier(25, citation_count=5000)
        assert set(result.keys()) == {"tier", "label", "percentile", "description"}

    def test_citation_count_accepted(self):
        """citation_count is accepted without error."""
        result = calculate_impact_tier(30, citation_count=10000)
        assert result["tier"] == "Senior Leader"


# ==================================================================
# calculate_research_grade
# ==================================================================


class TestCalculateResearchGrade:
    """Test research grade letter assignment."""

    def test_grade_s(self):
        result = calculate_research_grade(50, 10000, first_author_count=50)
        assert result["grade"] == "S"

    def test_grade_a(self):
        result = calculate_research_grade(30, 3000, first_author_count=30)
        assert result["grade"] == "A"

    def test_grade_b(self):
        result = calculate_research_grade(15, 1000, first_author_count=15)
        assert result["grade"] == "B"

    def test_grade_c(self):
        result = calculate_research_grade(5, 100, first_author_count=5)
        assert result["grade"] == "C"

    def test_grade_d(self):
        result = calculate_research_grade(2, 30)
        assert result["grade"] == "D"

    def test_grade_d_zero(self):
        result = calculate_research_grade(0, 0)
        assert result["grade"] == "D"

    def test_no_first_author_ignores_that_criterion(self):
        """When first_author_count is None, only h_index and citations matter."""
        result = calculate_research_grade(50, 10000)
        assert result["grade"] == "S"

    def test_low_first_author_downgrades(self):
        """A researcher with good h-index/citations but few first-author papers
        should be downgraded if first_author_count is provided."""
        result = calculate_research_grade(50, 10000, first_author_count=5)
        assert result["grade"] != "S"

    def test_returns_description(self):
        result = calculate_research_grade(30, 3000)
        assert "description" in result
        assert isinstance(result["description"], str)
        assert len(result["description"]) > 0

    def test_boundary_just_below_s(self):
        result = calculate_research_grade(49, 10000, first_author_count=50)
        assert result["grade"] == "A"

    def test_boundary_just_below_a(self):
        result = calculate_research_grade(29, 3000, first_author_count=30)
        assert result["grade"] == "B"

    def test_h_index_meets_but_citations_dont(self):
        """h_index alone is not sufficient; citations must also meet threshold."""
        result = calculate_research_grade(50, 999, first_author_count=50)
        assert result["grade"] != "S"


# ==================================================================
# calculate_lab_grade
# ==================================================================


class TestCalculateLabGrade:
    """Test lab grading with partial data support."""

    # Full data (high confidence)

    def test_grade_s_full_data(self):
        result = calculate_lab_grade(40, annual_funding_usd=1_000_000, faculty_alumni=5)
        assert result["grade"] == "S"
        assert result["confidence"] == "high"
        assert len(result["factors_missing"]) == 0

    def test_grade_a_full_data(self):
        result = calculate_lab_grade(25, annual_funding_usd=500_000, faculty_alumni=3)
        assert result["grade"] == "A"
        assert result["confidence"] == "high"

    def test_grade_b_full_data(self):
        result = calculate_lab_grade(15, annual_funding_usd=200_000, faculty_alumni=1)
        assert result["grade"] == "B"
        assert result["confidence"] == "high"

    def test_grade_c_full_data(self):
        result = calculate_lab_grade(10, annual_funding_usd=100_000, faculty_alumni=0)
        assert result["grade"] == "C"
        assert result["confidence"] == "high"

    def test_grade_d_full_data(self):
        result = calculate_lab_grade(5, annual_funding_usd=50_000, faculty_alumni=0)
        assert result["grade"] == "D"
        assert result["confidence"] == "high"

    # h-index only (low confidence)

    def test_h_index_only_low_confidence(self):
        result = calculate_lab_grade(40)
        assert result["confidence"] == "low"
        assert "pi_h_index" in result["factors_used"]
        assert "annual_funding_usd" in result["factors_missing"]
        assert "faculty_alumni" in result["factors_missing"]

    def test_h_index_only_grade_s(self):
        result = calculate_lab_grade(40)
        assert result["grade"] == "S"

    def test_h_index_only_grade_d(self):
        result = calculate_lab_grade(5)
        assert result["grade"] == "D"

    def test_h_index_only_note(self):
        result = calculate_lab_grade(30)
        assert "note" in result
        assert len(result["note"]) > 0

    # Medium confidence (one extra factor)

    def test_medium_confidence_with_funding(self):
        result = calculate_lab_grade(25, annual_funding_usd=500_000)
        assert result["confidence"] == "medium"
        assert "annual_funding_usd" in result["factors_used"]
        assert "faculty_alumni" in result["factors_missing"]

    def test_medium_confidence_with_alumni(self):
        result = calculate_lab_grade(25, faculty_alumni=3)
        assert result["confidence"] == "medium"
        assert "faculty_alumni" in result["factors_used"]
        assert "annual_funding_usd" in result["factors_missing"]

    # Return structure

    def test_return_keys(self):
        result = calculate_lab_grade(20, annual_funding_usd=300_000, faculty_alumni=2)
        expected_keys = {
            "grade", "factors_used", "factors_missing",
            "confidence", "description", "note",
        }
        assert set(result.keys()) == expected_keys

    def test_description_matches_grade(self):
        result = calculate_lab_grade(40, annual_funding_usd=1_000_000, faculty_alumni=5)
        assert result["description"] == LAB_GRADE_DESCRIPTIONS["S"]

    def test_grade_d_description(self):
        result = calculate_lab_grade(3)
        assert result["description"] == LAB_GRADE_DESCRIPTIONS["D"]

    # Edge: funding doesn't meet threshold but h-index does
    def test_funding_blocks_upgrade(self):
        """High h-index but low funding should prevent top grade."""
        result = calculate_lab_grade(40, annual_funding_usd=100_000, faculty_alumni=5)
        assert result["grade"] != "S"

    def test_alumni_blocks_upgrade(self):
        """High h-index and funding but insufficient alumni."""
        result = calculate_lab_grade(40, annual_funding_usd=1_000_000, faculty_alumni=0)
        assert result["grade"] != "S"


# ==================================================================
# Constants sanity checks
# ==================================================================


class TestConstants:
    """Verify tier/grade constant integrity."""

    def test_impact_tiers_descending(self):
        thresholds = [t[0] for t in IMPACT_TIERS]
        assert thresholds == sorted(thresholds, reverse=True)

    def test_research_grades_all_present(self):
        assert set(RESEARCH_GRADES.keys()) == {"S", "A", "B", "C", "D"}

    def test_lab_grade_thresholds_all_present(self):
        assert set(LAB_GRADE_THRESHOLDS.keys()) == {"S", "A", "B", "C", "D"}

    def test_lab_grade_descriptions_all_present(self):
        assert set(LAB_GRADE_DESCRIPTIONS.keys()) == {"S", "A", "B", "C", "D"}
