"""Tests for academic_investigator.modes (researcher, lab, org, conference)."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml

from academic_investigator.core.openalex import OpenAlexClient
from academic_investigator.core.person_profiler import PersonProfiler
from academic_investigator.modes.researcher import ResearcherInvestigator
from academic_investigator.modes.lab import LabInvestigator
from academic_investigator.modes.organization import OrgInvestigator
from academic_investigator.modes.conference import ConferenceInvestigator, INDUSTRY_SUFFIXES
from academic_investigator.reporting.templates import (
    RESEARCHER_SECTIONS,
    LAB_SECTIONS,
    ORG_SECTIONS,
)


# ==================================================================
# Helpers
# ==================================================================


def _make_investigator(cls, mock_client):
    """Instantiate a mode investigator with a pre-configured mock client."""
    obj = cls.__new__(cls)
    obj.profiler = PersonProfiler(client=mock_client)
    obj.client = mock_client
    return obj


def _make_researcher_investigator(mock_client):
    """Instantiate ResearcherInvestigator with mock client."""
    obj = ResearcherInvestigator.__new__(ResearcherInvestigator)
    obj.profiler = PersonProfiler(client=mock_client)
    return obj


# ==================================================================
# ResearcherInvestigator
# ==================================================================


class TestResearcherInvestigator:
    """Tests for ResearcherInvestigator.investigate."""

    def test_returns_mode(self, mock_openalex_client):
        inv = _make_researcher_investigator(mock_openalex_client)
        result = inv.investigate("Jane Richardson", "Cambridge")
        assert result["mode"] == "researcher"

    def test_returns_profile(self, mock_openalex_client):
        inv = _make_researcher_investigator(mock_openalex_client)
        result = inv.investigate("Jane Richardson", "Cambridge")
        assert "profile" in result
        assert result["profile"]["status"] == "found"

    def test_profile_has_person_profiler_fields(self, mock_openalex_client):
        inv = _make_researcher_investigator(mock_openalex_client)
        result = inv.investigate("Jane Richardson", "Cambridge")
        profile = result["profile"]
        expected_keys = {
            "status", "display_name", "author_id", "openalex_url", "metrics",
            "impact_tier", "top_concepts", "top_papers",
            "career_metrics", "coauthors", "recommendation",
        }
        assert set(profile.keys()) == expected_keys

    def test_returns_red_flag_queries(self, mock_openalex_client):
        inv = _make_researcher_investigator(mock_openalex_client)
        result = inv.investigate("Jane Richardson", "Cambridge")
        assert "red_flag_queries" in result
        assert isinstance(result["red_flag_queries"], list)
        assert len(result["red_flag_queries"]) > 0

    def test_red_flag_queries_are_dicts(self, mock_openalex_client):
        inv = _make_researcher_investigator(mock_openalex_client)
        result = inv.investigate("Jane Richardson", "Cambridge")
        for q in result["red_flag_queries"]:
            assert isinstance(q, dict)
            assert "category" in q
            assert "query" in q
            assert "severity" in q

    def test_report_sections_count(self, mock_openalex_client):
        inv = _make_researcher_investigator(mock_openalex_client)
        result = inv.investigate("Jane Richardson", "Cambridge")
        assert len(result["report_sections"]) == len(RESEARCHER_SECTIONS)

    def test_report_sections_structure(self, mock_openalex_client):
        inv = _make_researcher_investigator(mock_openalex_client)
        result = inv.investigate("Jane Richardson", "Cambridge")
        for s in result["report_sections"]:
            assert "section" in s
            assert "source" in s
            assert "required" in s

    def test_purpose_forwarded_to_profiler(self, mock_openalex_client):
        inv = _make_researcher_investigator(mock_openalex_client)
        result = inv.investigate("Jane Richardson", "Cambridge", purpose="collaboration")
        assert result["profile"]["status"] == "found"


# ==================================================================
# LabInvestigator
# ==================================================================


class TestLabInvestigator:
    """Tests for LabInvestigator.investigate."""

    def test_returns_mode(self, mock_openalex_client):
        inv = _make_investigator(LabInvestigator, mock_openalex_client)
        result = inv.investigate("Jane Richardson", "Cambridge")
        assert result["mode"] == "lab"

    def test_returns_pi_profile(self, mock_openalex_client):
        inv = _make_investigator(LabInvestigator, mock_openalex_client)
        result = inv.investigate("Jane Richardson", "Cambridge")
        assert "pi_profile" in result
        assert result["pi_profile"]["status"] == "found"

    def test_returns_lab_grade(self, mock_openalex_client):
        inv = _make_investigator(LabInvestigator, mock_openalex_client)
        result = inv.investigate("Jane Richardson", "Cambridge")
        assert "lab_grade" in result
        lab_grade = result["lab_grade"]
        assert "grade" in lab_grade
        assert "confidence" in lab_grade

    def test_lab_grade_has_low_confidence(self, mock_openalex_client):
        inv = _make_investigator(LabInvestigator, mock_openalex_client)
        result = inv.investigate("Jane Richardson", "Cambridge")
        lab_grade = result["lab_grade"]
        assert lab_grade["confidence"] == "low"

    def test_lab_grade_has_factors_missing(self, mock_openalex_client):
        inv = _make_investigator(LabInvestigator, mock_openalex_client)
        result = inv.investigate("Jane Richardson", "Cambridge")
        lab_grade = result["lab_grade"]
        assert "factors_missing" in lab_grade
        assert len(lab_grade["factors_missing"]) > 0

    def test_returns_institution_data(self, mock_openalex_client):
        inv = _make_investigator(LabInvestigator, mock_openalex_client)
        result = inv.investigate("Jane Richardson", "Cambridge")
        assert "institution_data" in result
        assert result["institution_data"] is not None
        assert "display_name" in result["institution_data"]

    def test_returns_red_flag_queries(self, mock_openalex_client):
        inv = _make_investigator(LabInvestigator, mock_openalex_client)
        result = inv.investigate("Jane Richardson", "Cambridge")
        assert "red_flag_queries" in result
        assert isinstance(result["red_flag_queries"], list)
        assert len(result["red_flag_queries"]) > 0

    def test_red_flag_queries_lab_specific(self, mock_openalex_client):
        inv = _make_investigator(LabInvestigator, mock_openalex_client)
        result = inv.investigate("Jane Richardson", "Cambridge")
        categories = {q["category"] for q in result["red_flag_queries"]}
        # Lab red flags include alumni, dropout, graduation, absence, financial
        assert "alumni" in categories or "dropout" in categories

    def test_report_sections_count(self, mock_openalex_client):
        inv = _make_investigator(LabInvestigator, mock_openalex_client)
        result = inv.investigate("Jane Richardson", "Cambridge")
        assert len(result["report_sections"]) == len(LAB_SECTIONS)

    def test_not_found_pi_gives_zero_h_index_grade(self, mock_openalex_client):
        inv = _make_investigator(LabInvestigator, mock_openalex_client)
        result = inv.investigate("NotFound Person", "Nowhere")
        assert result["pi_profile"]["status"] == "not_found"
        # With h_index=0, grade should be D
        assert result["lab_grade"]["grade"] == "D"


# ==================================================================
# OrgInvestigator
# ==================================================================


class TestOrgInvestigator:
    """Tests for OrgInvestigator.investigate."""

    def test_returns_mode(self, mock_openalex_client):
        inv = _make_investigator(OrgInvestigator, mock_openalex_client)
        result = inv.investigate("Acme Corp", key_people=["Jane Richardson"])
        assert result["mode"] == "org"

    def test_returns_org_name(self, mock_openalex_client):
        inv = _make_investigator(OrgInvestigator, mock_openalex_client)
        result = inv.investigate("Acme Corp")
        assert result["org_name"] == "Acme Corp"

    def test_returns_org_type(self, mock_openalex_client):
        inv = _make_investigator(OrgInvestigator, mock_openalex_client)
        result = inv.investigate("Acme Corp", org_type="startup")
        assert result["org_type"] == "startup"

    def test_returns_institution_data(self, mock_openalex_client):
        inv = _make_investigator(OrgInvestigator, mock_openalex_client)
        result = inv.investigate("Acme Corp")
        assert result["institution_data"] is not None

    def test_returns_people_profiles(self, mock_openalex_client):
        inv = _make_investigator(OrgInvestigator, mock_openalex_client)
        result = inv.investigate("Acme Corp", key_people=["Jane Richardson", "NotFound Person"])
        assert "people_profiles" in result
        assert "Jane Richardson" in result["people_profiles"]
        assert result["people_profiles"]["Jane Richardson"]["status"] == "found"
        assert "NotFound Person" in result["people_profiles"]
        assert result["people_profiles"]["NotFound Person"]["status"] == "not_found"

    def test_each_person_has_profiler_output(self, mock_openalex_client):
        inv = _make_investigator(OrgInvestigator, mock_openalex_client)
        result = inv.investigate("Acme Corp", key_people=["Jane Richardson"])
        profile = result["people_profiles"]["Jane Richardson"]
        assert "metrics" in profile
        assert "impact_tier" in profile

    def test_returns_red_flag_queries(self, mock_openalex_client):
        inv = _make_investigator(OrgInvestigator, mock_openalex_client)
        result = inv.investigate("Acme Corp", key_people=["Jane Richardson"])
        assert isinstance(result["red_flag_queries"], list)
        assert len(result["red_flag_queries"]) > 0

    def test_red_flag_queries_org_specific(self, mock_openalex_client):
        inv = _make_investigator(OrgInvestigator, mock_openalex_client)
        result = inv.investigate("Acme Corp", key_people=["Jane Richardson"])
        categories = {q["category"] for q in result["red_flag_queries"]}
        # Org red flags include legal, reputation, financial, transparency
        assert "legal" in categories or "reputation" in categories

    def test_report_sections_count(self, mock_openalex_client):
        inv = _make_investigator(OrgInvestigator, mock_openalex_client)
        result = inv.investigate("Acme Corp")
        assert len(result["report_sections"]) == len(ORG_SECTIONS)

    def test_no_key_people(self, mock_openalex_client):
        inv = _make_investigator(OrgInvestigator, mock_openalex_client)
        result = inv.investigate("Acme Corp")
        assert result["people_profiles"] == {}


# ==================================================================
# ConferenceInvestigator
# ==================================================================


SAMPLE_CONFERENCE_YAML = {
    "conference": {
        "id": "TEST2026",
        "name": "Test Conference 2026",
    },
    "sessions": [
        {
            "id": "S1",
            "title": "Session 1",
            "talks": [
                {
                    "speaker": "Jane Richardson",
                    "affiliation": "University of Cambridge",
                    "title": "Deep Learning for Proteins",
                    "keywords": ["Deep Learning", "Protein"],
                },
                {
                    "speaker": "NotFound Academic",
                    "affiliation": "Unknown University",
                    "title": "Obscure Topic",
                    "keywords": [],
                },
            ],
        },
        {
            "id": "S2",
            "title": "Session 2",
            "talks": [
                {
                    "speaker": "Industry Person",
                    "affiliation": "\u321cIndustry Corp",
                    "title": "Product Launch",
                    "keywords": ["Product"],
                },
            ],
        },
        {
            "id": "Panel",
            "title": "Panel Discussion",
            "type": "Panel Discussion",
            # No talks key -- should be skipped
        },
    ],
    "speakers_summary": {
        "academic": [
            {"name": "Jane Richardson", "affiliation": "University of Cambridge"},
            {"name": "NotFound Academic", "affiliation": "Unknown University"},
        ],
        "industry": [
            {"name": "Industry Person", "affiliation": "\u321cIndustry Corp"},
        ],
        "research_institutes": [],
    },
}


@pytest.fixture
def conference_yaml_path(tmp_path):
    """Write the sample conference YAML to a temp file and return the path."""
    yaml_path = tmp_path / "test_conference.yml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(SAMPLE_CONFERENCE_YAML, f, allow_unicode=True)
    return str(yaml_path)


class TestConferenceLoadConfig:
    """Tests for ConferenceInvestigator.load_config."""

    def test_load_config_returns_conference(self, mock_openalex_client, conference_yaml_path):
        inv = _make_investigator(ConferenceInvestigator, mock_openalex_client)
        config = inv.load_config(conference_yaml_path)
        assert config["conference"]["id"] == "TEST2026"

    def test_load_config_extracts_speakers(self, mock_openalex_client, conference_yaml_path):
        inv = _make_investigator(ConferenceInvestigator, mock_openalex_client)
        config = inv.load_config(conference_yaml_path)
        speakers = config["speakers"]
        assert isinstance(speakers, list)
        # 3 speakers from talks (Panel has none)
        assert len(speakers) == 3

    def test_load_config_skips_sessions_without_talks(self, mock_openalex_client, conference_yaml_path):
        inv = _make_investigator(ConferenceInvestigator, mock_openalex_client)
        config = inv.load_config(conference_yaml_path)
        names = [s["name"] for s in config["speakers"]]
        assert "Jane Richardson" in names
        assert "Industry Person" in names

    def test_load_config_speakers_summary(self, mock_openalex_client, conference_yaml_path):
        inv = _make_investigator(ConferenceInvestigator, mock_openalex_client)
        config = inv.load_config(conference_yaml_path)
        assert config["speakers_summary"] is not None
        assert "academic" in config["speakers_summary"]


class TestConferenceClassifySpeaker:
    """Tests for ConferenceInvestigator._classify_speaker_type."""

    def test_industry_by_suffix(self, mock_openalex_client):
        inv = _make_investigator(ConferenceInvestigator, mock_openalex_client)
        assert inv._classify_speaker_type("\u321c\uc544\ub860\ud2f0\uc5b4") == "industry"

    def test_industry_by_inc(self, mock_openalex_client):
        inv = _make_investigator(ConferenceInvestigator, mock_openalex_client)
        assert inv._classify_speaker_type("Acme Inc") == "industry"

    def test_academic_default(self, mock_openalex_client):
        inv = _make_investigator(ConferenceInvestigator, mock_openalex_client)
        assert inv._classify_speaker_type("Seoul National University") == "academic"

    def test_research_institute_from_summary(self, mock_openalex_client):
        inv = _make_investigator(ConferenceInvestigator, mock_openalex_client)
        summary = {"research_institutes": [{"affiliation": "KIST"}], "academic": [], "industry": []}
        assert inv._classify_speaker_type("KIST", summary) == "research_institute"

    def test_industry_from_summary(self, mock_openalex_client):
        inv = _make_investigator(ConferenceInvestigator, mock_openalex_client)
        summary = {
            "industry": [{"affiliation": "BioStartup"}],
            "academic": [],
            "research_institutes": [],
        }
        assert inv._classify_speaker_type("BioStartup", summary) == "industry"

    def test_empty_affiliation_defaults_academic(self, mock_openalex_client):
        inv = _make_investigator(ConferenceInvestigator, mock_openalex_client)
        assert inv._classify_speaker_type("") == "academic"


class TestConferenceInvestigateSpeakers:
    """Tests for ConferenceInvestigator.investigate_speakers."""

    def test_returns_mode(self, mock_openalex_client, conference_yaml_path):
        inv = _make_investigator(ConferenceInvestigator, mock_openalex_client)
        config = inv.load_config(conference_yaml_path)
        result = inv.investigate_speakers(config["speakers"], config_path=conference_yaml_path)
        assert result["mode"] == "conference"

    def test_returns_speakers_list(self, mock_openalex_client, conference_yaml_path):
        inv = _make_investigator(ConferenceInvestigator, mock_openalex_client)
        config = inv.load_config(conference_yaml_path)
        result = inv.investigate_speakers(config["speakers"], config_path=conference_yaml_path)
        assert isinstance(result["speakers"], list)
        assert len(result["speakers"]) == 3

    def test_academic_found_speaker(self, mock_openalex_client, conference_yaml_path):
        inv = _make_investigator(ConferenceInvestigator, mock_openalex_client)
        config = inv.load_config(conference_yaml_path)
        result = inv.investigate_speakers(config["speakers"], config_path=conference_yaml_path)
        # Jane Richardson should be found
        jane = [s for s in result["speakers"] if s["name"] == "Jane Richardson"][0]
        assert jane["type"] == "academic"
        assert jane["profile"]["status"] == "found"
        assert jane["alternative_research"] is None

    def test_academic_not_found_speaker(self, mock_openalex_client, conference_yaml_path):
        inv = _make_investigator(ConferenceInvestigator, mock_openalex_client)
        config = inv.load_config(conference_yaml_path)
        result = inv.investigate_speakers(config["speakers"], config_path=conference_yaml_path)
        # NotFound Academic -> name contains "notfound" so mock returns None
        nf = [s for s in result["speakers"] if s["name"] == "NotFound Academic"][0]
        assert nf["type"] == "academic_not_found"
        assert nf["profile"]["status"] == "not_found"
        assert nf["alternative_research"] is not None

    def test_industry_speaker(self, mock_openalex_client, conference_yaml_path):
        inv = _make_investigator(ConferenceInvestigator, mock_openalex_client)
        config = inv.load_config(conference_yaml_path)
        result = inv.investigate_speakers(config["speakers"], config_path=conference_yaml_path)
        ind = [s for s in result["speakers"] if s["name"] == "Industry Person"][0]
        assert ind["type"] == "industry"
        assert ind["profile"] is None
        assert ind["alternative_research"] is not None

    def test_industry_speaker_alternative_research_has_queries(self, mock_openalex_client, conference_yaml_path):
        inv = _make_investigator(ConferenceInvestigator, mock_openalex_client)
        config = inv.load_config(conference_yaml_path)
        result = inv.investigate_speakers(config["speakers"], config_path=conference_yaml_path)
        ind = [s for s in result["speakers"] if s["name"] == "Industry Person"][0]
        alt = ind["alternative_research"]
        assert alt["type"] == "websearch"
        assert isinstance(alt["queries"], list)
        assert len(alt["queries"]) > 0

    def test_summary_counts(self, mock_openalex_client, conference_yaml_path):
        inv = _make_investigator(ConferenceInvestigator, mock_openalex_client)
        config = inv.load_config(conference_yaml_path)
        result = inv.investigate_speakers(config["speakers"], config_path=conference_yaml_path)
        summary = result["summary"]
        assert summary["academic_found"] == 1
        assert summary["academic_not_found"] == 1
        assert summary["industry"] == 1
        assert summary["research_institute"] == 0

    def test_checklist_for_missing_profiles(self, mock_openalex_client, conference_yaml_path):
        inv = _make_investigator(ConferenceInvestigator, mock_openalex_client)
        config = inv.load_config(conference_yaml_path)
        result = inv.investigate_speakers(config["speakers"], config_path=conference_yaml_path)
        checklist = result["checklist"]
        assert isinstance(checklist, list)
        # Industry and not_found both need websearch -> 2 items
        assert len(checklist) == 2
        names = [c["speaker"] for c in checklist]
        assert "NotFound Academic" in names
        assert "Industry Person" in names


class TestConferenceKMB2026Compatible:
    """Ensure format is compatible with KMB2026 YAML structure."""

    def test_handles_talks_key(self, mock_openalex_client):
        inv = _make_investigator(ConferenceInvestigator, mock_openalex_client)
        config = {
            "sessions": [
                {
                    "id": "S1",
                    "talks": [
                        {"speaker": "A", "affiliation": "Univ A", "title": "T1"},
                    ],
                }
            ]
        }
        speakers = inv._extract_speakers_from_config(config)
        assert len(speakers) == 1
        assert speakers[0]["name"] == "A"

    def test_handles_presentations_key(self, mock_openalex_client):
        inv = _make_investigator(ConferenceInvestigator, mock_openalex_client)
        config = {
            "sessions": [
                {
                    "id": "S1",
                    "presentations": [
                        {"speaker": "B", "affiliation": "Univ B", "title": "T2"},
                    ],
                }
            ]
        }
        speakers = inv._extract_speakers_from_config(config)
        assert len(speakers) == 1
        assert speakers[0]["name"] == "B"

    def test_handles_speakers_key(self, mock_openalex_client):
        inv = _make_investigator(ConferenceInvestigator, mock_openalex_client)
        config = {
            "sessions": [
                {
                    "id": "S1",
                    "speakers": [
                        {"name": "C", "affiliation": "Univ C", "title": "T3"},
                    ],
                }
            ]
        }
        speakers = inv._extract_speakers_from_config(config)
        assert len(speakers) == 1
        assert speakers[0]["name"] == "C"

    def test_skips_sessions_without_talks(self, mock_openalex_client):
        inv = _make_investigator(ConferenceInvestigator, mock_openalex_client)
        config = {
            "sessions": [
                {
                    "id": "Panel",
                    "title": "Discussion",
                    "type": "Panel Discussion",
                },
                {
                    "id": "S1",
                    "talks": [
                        {"speaker": "D", "affiliation": "Univ D"},
                    ],
                },
            ]
        }
        speakers = inv._extract_speakers_from_config(config)
        assert len(speakers) == 1
        assert speakers[0]["name"] == "D"

    def test_deduplicates_speakers(self, mock_openalex_client):
        inv = _make_investigator(ConferenceInvestigator, mock_openalex_client)
        config = {
            "sessions": [
                {
                    "id": "S1",
                    "talks": [
                        {"speaker": "Same Person", "affiliation": "Univ"},
                    ],
                },
                {
                    "id": "S2",
                    "talks": [
                        {"speaker": "Same Person", "affiliation": "Univ"},
                    ],
                },
            ]
        }
        speakers = inv._extract_speakers_from_config(config)
        assert len(speakers) == 1


class TestConferenceResearchInstituteFlow:
    """Test research_institute speaker classification and profiling."""

    def test_research_institute_found(self, mock_openalex_client):
        inv = _make_investigator(ConferenceInvestigator, mock_openalex_client)
        speakers = [{"name": "Jane Richardson", "affiliation": "KIST"}]
        summary_yaml = {
            "conference": {"id": "T"},
            "sessions": [],
            "speakers_summary": {
                "academic": [],
                "industry": [],
                "research_institutes": [{"name": "Jane Richardson", "affiliation": "KIST"}],
            },
        }
        # Write temp config
        import tempfile, os
        fd, path = tempfile.mkstemp(suffix=".yml")
        with os.fdopen(fd, "w") as f:
            yaml.dump(summary_yaml, f, allow_unicode=True)
        try:
            result = inv.investigate_speakers(speakers, config_path=path)
            ri = result["speakers"][0]
            assert ri["type"] == "research_institute"
            assert result["summary"]["research_institute"] == 1
        finally:
            os.unlink(path)

    def test_research_institute_not_found_gets_alternative(self, mock_openalex_client):
        inv = _make_investigator(ConferenceInvestigator, mock_openalex_client)
        speakers = [{"name": "NotFound Researcher", "affiliation": "KRIBB"}]
        summary_yaml = {
            "conference": {"id": "T"},
            "sessions": [],
            "speakers_summary": {
                "academic": [],
                "industry": [],
                "research_institutes": [{"name": "NotFound Researcher", "affiliation": "KRIBB"}],
            },
        }
        import tempfile, os
        fd, path = tempfile.mkstemp(suffix=".yml")
        with os.fdopen(fd, "w") as f:
            yaml.dump(summary_yaml, f, allow_unicode=True)
        try:
            result = inv.investigate_speakers(speakers, config_path=path)
            ri = result["speakers"][0]
            assert ri["type"] == "research_institute"
            assert ri["alternative_research"] is not None
        finally:
            os.unlink(path)
