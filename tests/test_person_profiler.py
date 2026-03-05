"""Tests for academic_investigator.core.person_profiler."""

from __future__ import annotations

import pytest

from academic_investigator.core.person_profiler import PersonProfiler, quick_profile


# ==================================================================
# profile_person: found
# ==================================================================


class TestProfilePersonFound:
    """Test profile_person when author is found."""

    def test_status_found(self, mock_openalex_client):
        profiler = PersonProfiler(client=mock_openalex_client)
        result = profiler.profile_person("Jane Richardson", "Cambridge")
        assert result["status"] == "found"

    def test_author_id_present(self, mock_openalex_client):
        profiler = PersonProfiler(client=mock_openalex_client)
        result = profiler.profile_person("Jane Richardson")
        assert "author_id" in result
        assert result["author_id"] == "https://openalex.org/A5023888391"

    def test_openalex_url(self, mock_openalex_client):
        profiler = PersonProfiler(client=mock_openalex_client)
        result = profiler.profile_person("Jane Richardson")
        assert result["openalex_url"] == "https://openalex.org/A5023888391"

    def test_metrics_keys(self, mock_openalex_client):
        profiler = PersonProfiler(client=mock_openalex_client)
        result = profiler.profile_person("Jane Richardson")
        metrics = result["metrics"]
        assert "h_index" in metrics
        assert "citation_count" in metrics
        assert "works_count" in metrics
        assert "citations_per_paper" in metrics

    def test_metrics_values(self, mock_openalex_client):
        profiler = PersonProfiler(client=mock_openalex_client)
        result = profiler.profile_person("Jane Richardson")
        metrics = result["metrics"]
        assert metrics["h_index"] == 52
        assert metrics["citation_count"] == 18720
        assert metrics["works_count"] == 245
        assert isinstance(metrics["citations_per_paper"], float)

    def test_citations_per_paper_calculation(self, mock_openalex_client):
        profiler = PersonProfiler(client=mock_openalex_client)
        result = profiler.profile_person("Jane Richardson")
        expected = round(18720 / 245, 1)
        assert result["metrics"]["citations_per_paper"] == expected

    def test_return_keys_complete(self, mock_openalex_client):
        profiler = PersonProfiler(client=mock_openalex_client)
        result = profiler.profile_person("Jane Richardson")
        expected_keys = {
            "status", "display_name", "author_id", "openalex_url", "metrics",
            "impact_tier", "top_concepts", "top_papers",
            "career_metrics", "coauthors", "recommendation",
        }
        assert set(result.keys()) == expected_keys


# ==================================================================
# profile_person: not found
# ==================================================================


class TestProfilePersonNotFound:
    """Test profile_person when author is NOT found."""

    def test_status_not_found(self, mock_openalex_client):
        profiler = PersonProfiler(client=mock_openalex_client)
        result = profiler.profile_person("NotFound Person", "Nowhere")
        assert result["status"] == "not_found"

    def test_message_contains_name(self, mock_openalex_client):
        profiler = PersonProfiler(client=mock_openalex_client)
        result = profiler.profile_person("NotFound Person")
        assert "NotFound Person" in result["message"]

    def test_message_contains_affiliation(self, mock_openalex_client):
        profiler = PersonProfiler(client=mock_openalex_client)
        result = profiler.profile_person("NotFound Person", "Nowhere")
        assert "Nowhere" in result["message"]


# ==================================================================
# impact_tier
# ==================================================================


class TestImpactTier:
    """Test that impact_tier is properly calculated and enriched."""

    def test_impact_tier_present(self, mock_openalex_client):
        profiler = PersonProfiler(client=mock_openalex_client)
        result = profiler.profile_person("Jane Richardson")
        tier = result["impact_tier"]
        assert "tier" in tier
        assert "percentile" in tier
        assert "description" in tier

    def test_impact_tier_elite_for_h52(self, mock_openalex_client):
        """Author fixture has h_index=52, should be Elite."""
        profiler = PersonProfiler(client=mock_openalex_client)
        result = profiler.profile_person("Jane Richardson")
        assert result["impact_tier"]["tier"] == "Elite"

    def test_impact_tier_enriched_with_h_index(self, mock_openalex_client):
        profiler = PersonProfiler(client=mock_openalex_client)
        result = profiler.profile_person("Jane Richardson")
        assert result["impact_tier"]["h_index"] == 52

    def test_impact_tier_enriched_with_citations(self, mock_openalex_client):
        profiler = PersonProfiler(client=mock_openalex_client)
        result = profiler.profile_person("Jane Richardson")
        assert result["impact_tier"]["citations"] == 18720


# ==================================================================
# coauthors
# ==================================================================


class TestCoauthors:
    """Test that coauthors are extracted via client."""

    def test_coauthors_present(self, mock_openalex_client):
        profiler = PersonProfiler(client=mock_openalex_client)
        result = profiler.profile_person("Jane Richardson")
        assert "coauthors" in result
        assert isinstance(result["coauthors"], list)

    def test_coauthors_count(self, mock_openalex_client):
        profiler = PersonProfiler(client=mock_openalex_client)
        result = profiler.profile_person("Jane Richardson")
        # conftest mock returns 3 coauthors
        assert len(result["coauthors"]) == 3

    def test_coauthor_fields(self, mock_openalex_client):
        profiler = PersonProfiler(client=mock_openalex_client)
        result = profiler.profile_person("Jane Richardson")
        for ca in result["coauthors"]:
            assert "name" in ca
            assert "author_id" in ca
            assert "shared_works" in ca


# ==================================================================
# career_metrics
# ==================================================================


class TestCareerMetrics:
    """Test career metrics calculation."""

    def test_career_metrics_present(self, mock_openalex_client):
        profiler = PersonProfiler(client=mock_openalex_client)
        result = profiler.profile_person("Jane Richardson")
        cm = result["career_metrics"]
        assert "career_length" in cm
        assert "trend" in cm

    def test_career_length(self, mock_openalex_client):
        profiler = PersonProfiler(client=mock_openalex_client)
        result = profiler.profile_person("Jane Richardson")
        cm = result["career_metrics"]
        # Works span 2021-2023, so length = 3
        assert cm["career_length"] == 3

    def test_earliest_latest_work(self, mock_openalex_client):
        profiler = PersonProfiler(client=mock_openalex_client)
        result = profiler.profile_person("Jane Richardson")
        cm = result["career_metrics"]
        assert cm["earliest_work"] == 2021
        assert cm["latest_work"] == 2023

    def test_trend_value(self, mock_openalex_client):
        profiler = PersonProfiler(client=mock_openalex_client)
        result = profiler.profile_person("Jane Richardson")
        cm = result["career_metrics"]
        assert cm["trend"] in ("Rising", "Stable", "Established")

    def test_empty_works_career_metrics(self, mock_openalex_client):
        """Edge case: no works -> safe defaults."""
        profiler = PersonProfiler(client=mock_openalex_client)
        metrics = profiler._calculate_career_metrics([])
        assert metrics["career_length"] == 0
        assert metrics["trend"] == "Unknown"


# ==================================================================
# journal from primary_location (FIX verification)
# ==================================================================


class TestJournalExtraction:
    """Verify journal is extracted from primary_location.source.display_name."""

    def test_journal_from_primary_location(self, mock_openalex_client):
        profiler = PersonProfiler(client=mock_openalex_client)
        result = profiler.profile_person("Jane Richardson")
        first_paper = result["top_papers"][0]
        # First work in fixture has source.display_name = "Nature"
        assert first_paper["journal"] == "Nature"

    def test_all_papers_have_journal(self, mock_openalex_client):
        profiler = PersonProfiler(client=mock_openalex_client)
        result = profiler.profile_person("Jane Richardson")
        for paper in result["top_papers"]:
            assert "journal" in paper
            assert paper["journal"] != ""

    def test_journal_not_host_venue(self, mock_openalex_client, mock_works):
        """Ensure we use primary_location.source.display_name, not host_venue."""
        profiler = PersonProfiler(client=mock_openalex_client)
        # The mock_works fixture uses primary_location, not host_venue
        papers = profiler._format_top_papers(mock_works[:1])
        assert papers[0]["journal"] == "Nature"

    def test_missing_primary_location_graceful(self, mock_openalex_client):
        """When primary_location is None, journal should be 'Unknown'."""
        profiler = PersonProfiler(client=mock_openalex_client)
        papers = profiler._format_top_papers([{"title": "Test", "publication_year": 2024}])
        assert papers[0]["journal"] == "Unknown"


# ==================================================================
# recommendation
# ==================================================================


class TestRecommendation:
    """Test recommendation generation."""

    def test_recommendation_present(self, mock_openalex_client):
        profiler = PersonProfiler(client=mock_openalex_client)
        result = profiler.profile_person("Jane Richardson")
        assert "recommendation" in result
        assert isinstance(result["recommendation"], str)
        assert len(result["recommendation"]) > 0

    def test_recommendation_no_emoji(self, mock_openalex_client):
        """Recommendation should not contain emoji characters."""
        profiler = PersonProfiler(client=mock_openalex_client)
        result = profiler.profile_person("Jane Richardson")
        rec = result["recommendation"]
        # Check that no common emoji codepoints are present
        for ch in rec:
            assert ord(ch) < 0x1F600 or ord(ch) > 0x1F9FF, \
                f"Found emoji character in recommendation: {ch}"

    def test_elite_recommendation_highly_recommended(self, mock_openalex_client):
        """Elite tier should produce 'Highly Recommended'."""
        profiler = PersonProfiler(client=mock_openalex_client)
        result = profiler.profile_person("Jane Richardson")
        assert "Highly Recommended" in result["recommendation"]

    def test_recommendation_contains_top_paper(self, mock_openalex_client):
        profiler = PersonProfiler(client=mock_openalex_client)
        result = profiler.profile_person("Jane Richardson")
        assert "Most cited work" in result["recommendation"]


# ==================================================================
# quick_profile convenience function
# ==================================================================


class TestQuickProfile:
    """Test the quick_profile convenience function."""

    def test_quick_profile_returns_dict(self, mock_openalex_client, monkeypatch):
        # Patch PersonProfiler to use mock client
        original_init = PersonProfiler.__init__

        def patched_init(self, client=None):
            self.client = mock_openalex_client

        monkeypatch.setattr(PersonProfiler, "__init__", patched_init)
        result = quick_profile("Jane Richardson", "Cambridge")
        assert isinstance(result, dict)
        assert result["status"] == "found"

    def test_quick_profile_not_found_returns_none(self, mock_openalex_client, monkeypatch):
        original_init = PersonProfiler.__init__

        def patched_init(self, client=None):
            self.client = mock_openalex_client

        monkeypatch.setattr(PersonProfiler, "__init__", patched_init)
        result = quick_profile("NotFound Person")
        assert result is None
