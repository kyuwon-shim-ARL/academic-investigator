"""Tests for academic_investigator.reporting.lang."""

from __future__ import annotations

import pytest

from academic_investigator.reporting.lang import (
    STRINGS,
    SUPPORTED_LANGUAGES,
    get_lang_from_args,
    get_string,
)


# ==================================================================
# get_string: basic retrieval
# ==================================================================


class TestGetString:
    """Test localized string retrieval."""

    def test_ko_string(self):
        result = get_string("section_basic_info", lang="ko")
        assert result == "기본 정보"

    def test_en_string(self):
        result = get_string("section_basic_info", lang="en")
        assert result == "Basic Information"

    def test_default_lang_is_ko(self):
        result = get_string("section_basic_info")
        assert result == "기본 정보"

    def test_format_args_ko(self):
        result = get_string("report_title_researcher", lang="ko", name="Jane")
        assert "Jane" in result
        assert "연구자 조사 보고서" in result

    def test_format_args_en(self):
        result = get_string("report_title_researcher", lang="en", name="Jane")
        assert "Jane" in result
        assert "Researcher Investigation Report" in result

    def test_all_keys_have_both_languages(self):
        for key, translations in STRINGS.items():
            for lang in SUPPORTED_LANGUAGES:
                assert lang in translations, (
                    f"Key '{key}' missing language '{lang}'"
                )


# ==================================================================
# get_string: error cases
# ==================================================================


class TestGetStringErrors:
    """Test error handling in get_string."""

    def test_unknown_key_raises_key_error(self):
        with pytest.raises(KeyError, match="nonexistent_key"):
            get_string("nonexistent_key", lang="ko")

    def test_unknown_lang_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported language"):
            get_string("section_basic_info", lang="fr")

    def test_empty_lang_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported language"):
            get_string("section_basic_info", lang="")


# ==================================================================
# get_lang_from_args
# ==================================================================


class TestGetLangFromArgs:
    """Test language argument validation."""

    def test_none_returns_ko(self):
        assert get_lang_from_args(None) == "ko"

    def test_ko_passthrough(self):
        assert get_lang_from_args("ko") == "ko"

    def test_en_passthrough(self):
        assert get_lang_from_args("en") == "en"

    def test_invalid_lang_raises(self):
        with pytest.raises(ValueError, match="Unsupported language"):
            get_lang_from_args("de")


# ==================================================================
# String table coverage
# ==================================================================


class TestStringTableCoverage:
    """Verify the string table has sufficient coverage."""

    def test_minimum_60_keys(self):
        assert len(STRINGS) >= 60, (
            f"Expected at least 60 string keys, got {len(STRINGS)}"
        )

    def test_report_titles_present(self):
        for mode in ("researcher", "lab", "org", "conference"):
            key = f"report_title_{mode}"
            assert key in STRINGS, f"Missing report title key: {key}"

    def test_researcher_section_headers(self):
        researcher_sections = [
            "basic_info", "education", "publications", "grants",
            "activities", "mentorship", "network", "assessment",
            "red_flags", "questions", "summary",
        ]
        for s in researcher_sections:
            key = f"section_{s}"
            assert key in STRINGS, f"Missing researcher section key: {key}"

    def test_lab_section_headers(self):
        lab_sections = [
            "overview", "pi_profile", "research_program", "members",
            "infrastructure", "alumni_careers", "funding", "culture",
            "considerations",
        ]
        for s in lab_sections:
            key = f"section_{s}"
            assert key in STRINGS, f"Missing lab section key: {key}"

    def test_org_section_headers(self):
        org_sections = [
            "leadership", "technology", "products",
            "competitive_landscape", "glossary",
        ]
        for s in org_sections:
            key = f"section_{s}"
            assert key in STRINGS, f"Missing org section key: {key}"

    def test_impact_tier_descriptions(self):
        for tier in ("elite", "senior_leader", "established", "mid_career", "early_career"):
            key = f"tier_{tier}"
            assert key in STRINGS, f"Missing tier key: {key}"

    def test_lab_confidence_notes(self):
        for level in ("high", "medium", "low"):
            key = f"lab_confidence_{level}"
            assert key in STRINGS, f"Missing lab confidence key: {key}"

    def test_common_labels(self):
        labels = [
            "label_h_index", "label_citations", "label_works_count",
            "label_citations_per_paper", "label_impact_tier",
            "label_research_grade", "label_lab_grade", "label_confidence",
            "label_coauthors", "label_career_trend", "label_recommendation",
            "label_websearch_required", "label_not_found",
        ]
        for key in labels:
            assert key in STRINGS, f"Missing label key: {key}"
