"""Shared test fixtures for academic-investigator tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

import pytest

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture
def mock_author() -> Dict[str, Any]:
    """Load the author fixture."""
    with open(FIXTURES_DIR / "author_response.json") as f:
        return json.load(f)


@pytest.fixture
def mock_works() -> List[Dict[str, Any]]:
    """Load the works list fixture."""
    with open(FIXTURES_DIR / "works_response.json") as f:
        return json.load(f)


@pytest.fixture
def mock_work_detail() -> Dict[str, Any]:
    """Load the single work detail fixture."""
    with open(FIXTURES_DIR / "work_detail_response.json") as f:
        return json.load(f)


@pytest.fixture
def mock_openalex_client(monkeypatch, mock_author, mock_works, mock_work_detail):
    """Return an OpenAlexClient with all external calls mocked.

    The returned client's methods use fixture data instead of hitting
    the real OpenAlex API.
    """
    from academic_investigator.core.openalex import OpenAlexClient

    client = OpenAlexClient.__new__(OpenAlexClient)
    # Initialize state without calling __init__ (avoids pyalex config side effects)
    client.email = "test@example.com"
    client.api_key = None
    client.timeout = 30
    client.base_url = "https://api.openalex.org"
    client.failed_requests = []
    client.request_count = 0

    # Mock search_author
    original_search_author = OpenAlexClient.search_author

    def _search_author(self, name, affiliation=None):
        self.request_count += 1
        if "notfound" in name.lower():
            return None
        return mock_author

    monkeypatch.setattr(OpenAlexClient, "search_author", _search_author)

    # Mock fetch_author_works
    def _fetch_author_works(self, author_id, limit=10, sort="cited_by_count:desc"):
        self.request_count += 1
        return mock_works[:limit]

    monkeypatch.setattr(OpenAlexClient, "fetch_author_works", _fetch_author_works)

    # Mock fetch_work
    def _fetch_work(self, work_id):
        self.request_count += 1
        return mock_work_detail

    monkeypatch.setattr(OpenAlexClient, "fetch_work", _fetch_work)

    # Mock fetch_author_coauthors
    def _fetch_author_coauthors(self, author_id, limit=20):
        self.request_count += 1
        return [
            {"name": "Robert Chen", "author_id": "A5034567891", "shared_works": 12},
            {"name": "Sarah K. Williams", "author_id": "A5045678912", "shared_works": 8},
            {"name": "David Park", "author_id": "A5056789123", "shared_works": 5},
        ][:limit]

    monkeypatch.setattr(OpenAlexClient, "fetch_author_coauthors", _fetch_author_coauthors)

    # Mock search_institution
    def _search_institution(self, name, country=None):
        self.request_count += 1
        return {
            "id": "https://openalex.org/I27837315",
            "display_name": "University of Cambridge",
            "country_code": "GB",
            "type": "education",
            "works_count": 320000,
            "cited_by_count": 12000000,
        }

    monkeypatch.setattr(OpenAlexClient, "search_institution", _search_institution)

    return client
