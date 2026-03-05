"""Tests for academic_investigator.reporting.formatters."""

from __future__ import annotations

import json

import pytest

from academic_investigator.reporting.formatters import (
    format_json,
    format_markdown,
    format_researcher_md,
    format_lab_md,
    format_org_md,
    format_conference_md,
)


# ------------------------------------------------------------------
# Sample data fixtures
# ------------------------------------------------------------------


@pytest.fixture
def researcher_data():
    """Minimal researcher profile data for formatting tests."""
    return {
        "status": "found",
        "author_id": "https://openalex.org/A5023888391",
        "openalex_url": "https://openalex.org/A5023888391",
        "display_name": "Jane M. Richardson",
        "metrics": {
            "h_index": 52,
            "citation_count": 18720,
            "works_count": 245,
            "citations_per_paper": 76.4,
        },
        "impact_tier": {
            "tier": "Elite",
            "label": "Elite",
            "percentile": "Top 1%",
            "description": "World-leading researcher with exceptional impact",
            "h_index": 52,
            "citations": 18720,
        },
        "top_concepts": [
            "Computational Biology and Bioinformatics",
            "Machine Learning in Genomics",
        ],
        "top_papers": [
            {
                "title": "Deep learning approaches for protein structure prediction at scale",
                "year": 2023,
                "citations": 1245,
                "journal": "Nature",
                "doi": "https://doi.org/10.1038/s41586-023-06291-2",
                "openalex_id": "W3124567890",
            },
        ],
        "career_metrics": {
            "career_length": 3,
            "earliest_work": 2021,
            "latest_work": 2023,
            "recent_activity": "5 papers in last 3 years",
            "trend": "Stable",
            "avg_citations_recent": 522.6,
            "avg_citations_overall": 522.6,
        },
        "coauthors": [
            {"name": "Robert Chen", "author_id": "A5034567891", "shared_works": 12},
            {"name": "Sarah K. Williams", "author_id": "A5045678912", "shared_works": 8},
        ],
        "recommendation": "Highly Recommended - World-leading researcher (h-index: 52)",
    }


@pytest.fixture
def lab_data():
    """Minimal lab investigation data."""
    return {
        "lab_name": "Richardson Lab",
        "pi_name": "Jane M. Richardson",
        "pi_profile": {
            "metrics": {
                "h_index": 52,
                "citation_count": 18720,
                "works_count": 245,
                "citations_per_paper": 76.4,
            },
            "impact_tier": {
                "tier": "Elite",
                "percentile": "Top 1%",
                "description": "World-leading researcher",
            },
            "top_concepts": [],
            "coauthors": [],
        },
        "lab_grade": {
            "grade": "S",
            "confidence": "high",
            "description": "World-class lab",
        },
        "summary": "Top-tier computational biology lab.",
    }


@pytest.fixture
def org_data():
    """Minimal organization data."""
    return {
        "org_name": "DeepMind",
        "assessment": "Leading AI research lab.",
        "summary": "DeepMind is a world-class AI organization.",
    }


# ==================================================================
# format_json
# ==================================================================


class TestFormatJson:
    """Test JSON formatting."""

    def test_valid_json_output(self, researcher_data):
        output = format_json(researcher_data)
        parsed = json.loads(output)
        assert parsed["status"] == "found"

    def test_non_ascii_preserved(self):
        data = {"name": "Korean text"}
        output = format_json(data)
        assert "Korean" in output

    def test_unicode_preserved(self):
        data = {"name": "김연구원"}
        output = format_json(data)
        assert "김연구원" in output
        assert "\\u" not in output

    def test_indent(self):
        data = {"a": 1}
        output = format_json(data)
        assert "  " in output  # indent=2


# ==================================================================
# format_markdown: researcher
# ==================================================================


class TestFormatResearcherMd:
    """Test researcher Markdown formatting."""

    def test_ko_title(self, researcher_data):
        md = format_researcher_md(researcher_data, lang="ko")
        assert "연구자 조사 보고서" in md

    def test_en_title(self, researcher_data):
        md = format_researcher_md(researcher_data, lang="en")
        assert "Researcher Investigation Report" in md

    def test_sections_present_ko(self, researcher_data):
        md = format_researcher_md(researcher_data, lang="ko")
        assert "## 기본 정보" in md
        assert "## 주요 논문" in md
        assert "## 공동연구 네트워크" in md
        assert "## 종합 평가" in md
        assert "## 요약" in md

    def test_sections_present_en(self, researcher_data):
        md = format_researcher_md(researcher_data, lang="en")
        assert "## Basic Information" in md
        assert "## Key Publications" in md
        assert "## Collaboration Network" in md
        assert "## Overall Assessment" in md
        assert "## Summary" in md

    def test_websearch_placeholder_ko(self, researcher_data):
        md = format_researcher_md(researcher_data, lang="ko")
        assert "[WebSearch 필요]" in md

    def test_websearch_placeholder_en(self, researcher_data):
        md = format_researcher_md(researcher_data, lang="en")
        assert "[WebSearch required]" in md

    def test_api_data_filled(self, researcher_data):
        md = format_researcher_md(researcher_data, lang="en")
        assert "52" in md  # h-index
        assert "18720" in md  # citations
        assert "Nature" in md  # journal

    def test_coauthors_displayed(self, researcher_data):
        md = format_researcher_md(researcher_data, lang="en")
        assert "Robert Chen" in md
        assert "Sarah K. Williams" in md

    def test_top_paper_title(self, researcher_data):
        md = format_researcher_md(researcher_data, lang="en")
        assert "Deep learning approaches" in md


# ==================================================================
# format_markdown: lab
# ==================================================================


class TestFormatLabMd:
    """Test lab Markdown formatting."""

    def test_ko_title(self, lab_data):
        md = format_lab_md(lab_data, lang="ko")
        assert "연구실 조사 보고서" in md

    def test_en_title(self, lab_data):
        md = format_lab_md(lab_data, lang="en")
        assert "Lab Investigation Report" in md

    def test_lab_sections_present(self, lab_data):
        md = format_lab_md(lab_data, lang="en")
        assert "## Overview" in md
        assert "## PI Profile" in md
        assert "## Summary" in md

    def test_websearch_placeholders(self, lab_data):
        md = format_lab_md(lab_data, lang="en")
        assert "[WebSearch required]" in md


# ==================================================================
# format_markdown: org
# ==================================================================


class TestFormatOrgMd:
    """Test organization Markdown formatting."""

    def test_ko_title(self, org_data):
        md = format_org_md(org_data, lang="ko")
        assert "기관 조사 보고서" in md

    def test_en_title(self, org_data):
        md = format_org_md(org_data, lang="en")
        assert "Organization Investigation Report" in md

    def test_org_sections_present(self, org_data):
        md = format_org_md(org_data, lang="en")
        assert "## Overview" in md
        assert "## Summary" in md

    def test_websearch_placeholders(self, org_data):
        md = format_org_md(org_data, lang="en")
        assert "[WebSearch required]" in md


# ==================================================================
# format_markdown: conference
# ==================================================================


class TestFormatConferenceMd:
    """Test conference Markdown formatting."""

    def test_conference_title(self):
        data = {"conference_name": "ISMB 2025"}
        md = format_conference_md(data, lang="en")
        assert "ISMB 2025" in md

    def test_websearch_placeholders(self):
        data = {"conference_name": "ISMB 2025"}
        md = format_conference_md(data, lang="en")
        assert "[WebSearch required]" in md


# ==================================================================
# format_markdown: dispatcher
# ==================================================================


class TestFormatMarkdownDispatcher:
    """Test the top-level format_markdown dispatcher."""

    def test_researcher_dispatch(self, researcher_data):
        md = format_markdown(researcher_data, mode="researcher", lang="en")
        assert "Researcher Investigation Report" in md

    def test_lab_dispatch(self, lab_data):
        md = format_markdown(lab_data, mode="lab", lang="en")
        assert "Lab Investigation Report" in md

    def test_org_dispatch(self, org_data):
        md = format_markdown(org_data, mode="org", lang="en")
        assert "Organization Investigation Report" in md

    def test_conference_dispatch(self):
        data = {"conference_name": "Test Conf"}
        md = format_markdown(data, mode="conference", lang="en")
        assert "Test Conf" in md

    def test_unknown_mode_raises(self, researcher_data):
        with pytest.raises(ValueError, match="Unknown mode"):
            format_markdown(researcher_data, mode="invalid")
