"""Tests for CLI interface."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

from academic_investigator.cli import main
from academic_investigator._version import __version__


@pytest.fixture
def mock_researcher_investigator(monkeypatch):
    """Mock ResearcherInvestigator for testing."""
    class MockResearcherInvestigator:
        def __init__(self, email=None, api_key=None):
            self.email = email
            self.api_key = api_key

        def investigate(self, name: str, affiliation: str, purpose: str | None = None):
            return {
                "mode": "researcher",
                "profile": {
                    "status": "found",
                    "display_name": name,
                    "author_id": "https://openalex.org/A000000001",
                    "openalex_url": "https://openalex.org/A000000001",
                    "metrics": {
                        "h_index": 42,
                        "citation_count": 1500,
                        "works_count": 75,
                        "citations_per_paper": 20.0,
                    },
                    "impact_tier": {
                        "tier": "Senior Leader",
                        "percentile": "Top 5%",
                        "description": "Highly influential senior researcher",
                    },
                    "top_concepts": ["Molecular Biology"],
                    "top_papers": [
                        {
                            "title": "Test Paper 1",
                            "year": 2023,
                            "citations": 50,
                            "journal": "Nature",
                            "doi": "10.1038/test",
                        }
                    ],
                    "career_metrics": {
                        "career_length": 15,
                        "trend": "Stable",
                    },
                    "coauthors": [
                        {"name": "Collaborator A", "shared_works": 5},
                    ],
                    "recommendation": "Highly Recommended",
                },
                "red_flag_queries": [],
                "report_sections": [],
            }

    def mock_import(original_import):
        def _import(name, *args, **kwargs):
            if name == "academic_investigator.modes.researcher":
                class Module:
                    ResearcherInvestigator = MockResearcherInvestigator
                return Module()
            return original_import(name, *args, **kwargs)
        return _import

    import builtins
    original_import = builtins.__import__
    monkeypatch.setattr(builtins, "__import__", mock_import(original_import))


@pytest.fixture
def mock_researcher_not_found(monkeypatch):
    """Mock ResearcherInvestigator returning not_found."""
    class MockResearcherInvestigator:
        def __init__(self, email=None, api_key=None):
            self.email = email
            self.api_key = api_key

        def investigate(self, name: str, affiliation: str, purpose: str | None = None):
            return {
                "mode": "researcher",
                "profile": {
                    "status": "not_found",
                },
            }

    def mock_import(original_import):
        def _import(name, *args, **kwargs):
            if name == "academic_investigator.modes.researcher":
                class Module:
                    ResearcherInvestigator = MockResearcherInvestigator
                return Module()
            return original_import(name, *args, **kwargs)
        return _import

    import builtins
    original_import = builtins.__import__
    monkeypatch.setattr(builtins, "__import__", mock_import(original_import))


def test_help_exits_successfully(monkeypatch, capsys):
    """Test that --help shows help and exits with code 0."""
    monkeypatch.setattr(sys, "argv", ["acad-inv", "--help"])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 0

    captured = capsys.readouterr()
    assert "Academic Investigator" in captured.out
    assert "profile" in captured.out
    assert "lab" in captured.out
    assert "org" in captured.out
    assert "conference" in captured.out
    assert "red-flags" in captured.out


def test_version_shows_version(monkeypatch, capsys):
    """Test that --version shows version string."""
    monkeypatch.setattr(sys, "argv", ["acad-inv", "--version"])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 0

    captured = capsys.readouterr()
    assert __version__ in captured.out


def test_no_command_shows_help(monkeypatch, capsys):
    """Test that no command shows help."""
    monkeypatch.setattr(sys, "argv", ["acad-inv"])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 0

    captured = capsys.readouterr()
    assert "Academic Investigator" in captured.out


def test_profile_json_output(monkeypatch, capsys, mock_researcher_investigator):
    """Test profile command with JSON output."""
    monkeypatch.setattr(sys, "argv", ["acad-inv", "profile", "Test Author", "-a", "MIT"])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 0

    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["mode"] == "researcher"
    assert result["profile"]["display_name"] == "Test Author"
    assert result["profile"]["metrics"]["h_index"] == 42


def test_profile_markdown_english(monkeypatch, capsys, mock_researcher_investigator):
    """Test profile command with English markdown output."""
    monkeypatch.setattr(sys, "argv", ["acad-inv", "--format", "md", "--lang", "en", "profile", "Test Author", "-a", "MIT"])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 0

    captured = capsys.readouterr()
    output = captured.out

    # Check for English markdown headers
    assert "# Researcher Investigation Report:" in output or "## Basic Information" in output
    assert "**H-index**" in output or "**Citations**" in output
    assert "Test Paper 1" in output


def test_profile_markdown_korean(monkeypatch, capsys, mock_researcher_investigator):
    """Test profile command with Korean markdown output."""
    monkeypatch.setattr(sys, "argv", ["acad-inv", "--format", "md", "--lang", "ko", "profile", "Test Author", "-a", "MIT"])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 0

    captured = capsys.readouterr()
    output = captured.out

    # Check for Korean markdown headers
    assert "# " in output and "연구자 조사 보고서" in output or "## 기본 정보" in output
    assert "**H-인덱스**" in output or "**피인용 수**" in output
    assert "Test Paper 1" in output


def test_profile_not_found_exits_1(monkeypatch, capsys, mock_researcher_not_found):
    """Test profile command returns exit code 1 when author not found."""
    monkeypatch.setattr(sys, "argv", ["acad-inv", "profile", "Nonexistent Author", "-a", "MIT"])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 1

    captured = capsys.readouterr()
    assert "Author not found" in captured.err


def test_profile_output_to_file(monkeypatch, capsys, mock_researcher_investigator, tmp_path):
    """Test profile command with output to file."""
    output_file = tmp_path / "output.json"
    monkeypatch.setattr(sys, "argv", ["acad-inv", "-o", str(output_file), "profile", "Test Author", "-a", "MIT"])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 0

    # Check that file was created
    assert output_file.exists()
    result = json.loads(output_file.read_text())
    assert result["mode"] == "researcher"
    assert result["profile"]["display_name"] == "Test Author"

    # Check stderr message
    captured = capsys.readouterr()
    assert f"Output written to {output_file}" in captured.err


def test_red_flags_person(monkeypatch, capsys):
    """Test red-flags command for person type."""
    monkeypatch.setattr(sys, "argv", ["acad-inv", "red-flags", "Test Person", "--type", "person", "-a", "MIT"])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 0

    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["mode"] == "red_flags"
    assert result["target"] == "Test Person"
    assert result["type"] == "person"
    assert isinstance(result["queries"], list)
    assert len(result["queries"]) > 0

    # Check query structure
    query = result["queries"][0]
    assert "query" in query
    assert "category" in query
    assert "severity" in query
    assert "description" in query


def test_red_flags_org(monkeypatch, capsys):
    """Test red-flags command for org type."""
    monkeypatch.setattr(sys, "argv", ["acad-inv", "red-flags", "Test Company", "--type", "org"])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 0

    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["mode"] == "red_flags"
    assert result["target"] == "Test Company"
    assert result["type"] == "org"
    assert isinstance(result["queries"], list)
    assert len(result["queries"]) > 0


def test_red_flags_lab(monkeypatch, capsys):
    """Test red-flags command for lab type."""
    monkeypatch.setattr(sys, "argv", ["acad-inv", "red-flags", "Test Lab", "--type", "lab", "-a", "Stanford"])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 0

    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["mode"] == "red_flags"
    assert result["target"] == "Test Lab"
    assert result["type"] == "lab"
    assert isinstance(result["queries"], list)
    assert len(result["queries"]) > 0


def test_red_flags_default_person(monkeypatch, capsys):
    """Test red-flags command defaults to person type."""
    monkeypatch.setattr(sys, "argv", ["acad-inv", "red-flags", "Test Person"])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 0

    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["type"] == "person"


def test_keyboard_interrupt_exits_130(monkeypatch):
    """Test that KeyboardInterrupt exits with code 130."""
    def mock_run_profile(args):
        raise KeyboardInterrupt()

    monkeypatch.setattr(sys, "argv", ["acad-inv", "profile", "Test", "-a", "MIT"])
    monkeypatch.setattr("academic_investigator.cli.run_profile", mock_run_profile)

    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 130


def test_generic_exception_exits_2(monkeypatch, capsys):
    """Test that generic exceptions exit with code 2 and print error."""
    def mock_run_profile(args):
        raise ValueError("Test error message")

    monkeypatch.setattr(sys, "argv", ["acad-inv", "profile", "Test", "-a", "MIT"])
    monkeypatch.setattr("academic_investigator.cli.run_profile", mock_run_profile)

    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 2

    captured = capsys.readouterr()
    assert "Error: Test error message" in captured.err


def test_profile_with_purpose(monkeypatch, capsys, mock_researcher_investigator):
    """Test profile command with purpose argument."""
    monkeypatch.setattr(sys, "argv", ["acad-inv", "profile", "Test Author", "-a", "MIT", "--purpose", "collaboration"])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 0

    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["mode"] == "researcher"
