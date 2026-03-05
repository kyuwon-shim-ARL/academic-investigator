"""Tests for academic_investigator.core.openalex.OpenAlexClient."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from academic_investigator.core.openalex import OpenAlexClient


# ------------------------------------------------------------------
# Construction & env var fallback
# ------------------------------------------------------------------


class TestOpenAlexClientInit:
    """Test client initialization and env-var fallbacks."""

    def test_explicit_email(self):
        client = OpenAlexClient(email="user@example.com")
        assert client.email == "user@example.com"

    def test_env_email_fallback(self, monkeypatch):
        monkeypatch.setenv("OPENALEX_EMAIL", "env@example.com")
        monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
        client = OpenAlexClient()
        assert client.email == "env@example.com"

    def test_explicit_api_key(self):
        client = OpenAlexClient(api_key="my-key-123")
        assert client.api_key == "my-key-123"

    def test_env_api_key_fallback(self, monkeypatch):
        monkeypatch.setenv("OPENALEX_API_KEY", "env-key-456")
        monkeypatch.delenv("OPENALEX_EMAIL", raising=False)
        client = OpenAlexClient()
        assert client.api_key == "env-key-456"

    def test_custom_timeout(self):
        client = OpenAlexClient(timeout=60)
        assert client.timeout == 60

    def test_default_timeout(self):
        client = OpenAlexClient()
        assert client.timeout == 30


# ------------------------------------------------------------------
# search_author
# ------------------------------------------------------------------


class TestSearchAuthor:
    """Test author search via mocked client."""

    def test_search_author_found(self, mock_openalex_client, mock_author):
        result = mock_openalex_client.search_author("Jane Richardson")
        assert result is not None
        assert result["display_name"] == "Jane M. Richardson"
        assert result["summary_stats"]["h_index"] == 52

    def test_search_author_not_found(self, mock_openalex_client):
        result = mock_openalex_client.search_author("NotFound Person")
        assert result is None

    def test_search_author_with_affiliation(self, mock_openalex_client, mock_author):
        result = mock_openalex_client.search_author(
            "Jane Richardson", affiliation="Cambridge"
        )
        assert result is not None

    def test_search_author_increments_request_count(self, mock_openalex_client):
        mock_openalex_client.search_author("Jane Richardson")
        assert mock_openalex_client.request_count >= 1


# ------------------------------------------------------------------
# fetch_author_works
# ------------------------------------------------------------------


class TestFetchAuthorWorks:
    """Test fetching works for an author."""

    def test_fetch_works_returns_list(self, mock_openalex_client, mock_works):
        works = mock_openalex_client.fetch_author_works("A5023888391")
        assert isinstance(works, list)
        assert len(works) == len(mock_works)

    def test_fetch_works_limit(self, mock_openalex_client):
        works = mock_openalex_client.fetch_author_works("A5023888391", limit=2)
        assert len(works) == 2

    def test_fetch_works_has_required_fields(self, mock_openalex_client):
        works = mock_openalex_client.fetch_author_works("A5023888391", limit=1)
        work = works[0]
        assert "title" in work
        assert "cited_by_count" in work
        assert "publication_year" in work
        assert "primary_location" in work

    def test_fetch_works_uses_display_name_in_source(self, mock_openalex_client):
        works = mock_openalex_client.fetch_author_works("A5023888391", limit=1)
        source = works[0]["primary_location"]["source"]
        assert "display_name" in source


# ------------------------------------------------------------------
# fetch_work
# ------------------------------------------------------------------


class TestFetchWork:
    """Test fetching a single work."""

    def test_fetch_work_by_id(self, mock_openalex_client, mock_work_detail):
        work = mock_openalex_client.fetch_work("W3124567890")
        assert work is not None
        assert work["title"] == mock_work_detail["title"]

    def test_fetch_work_by_full_url(self, mock_openalex_client):
        work = mock_openalex_client.fetch_work(
            "https://openalex.org/W3124567890"
        )
        assert work is not None

    def test_fetch_work_has_authorships(self, mock_openalex_client):
        work = mock_openalex_client.fetch_work("W3124567890")
        assert "authorships" in work
        assert len(work["authorships"]) > 0


# ------------------------------------------------------------------
# search_institution
# ------------------------------------------------------------------


class TestSearchInstitution:
    """Test institution search."""

    def test_search_institution_found(self, mock_openalex_client):
        result = mock_openalex_client.search_institution("Cambridge")
        assert result is not None
        assert result["display_name"] == "University of Cambridge"
        assert result["country_code"] == "GB"

    def test_search_institution_with_country(self, mock_openalex_client):
        result = mock_openalex_client.search_institution(
            "Cambridge", country="GB"
        )
        assert result is not None


# ------------------------------------------------------------------
# fetch_author_coauthors
# ------------------------------------------------------------------


class TestFetchAuthorCoauthors:
    """Test coauthor extraction."""

    def test_coauthors_returns_list(self, mock_openalex_client):
        coauthors = mock_openalex_client.fetch_author_coauthors("A5023888391")
        assert isinstance(coauthors, list)
        assert len(coauthors) == 3

    def test_coauthors_have_required_fields(self, mock_openalex_client):
        coauthors = mock_openalex_client.fetch_author_coauthors("A5023888391")
        for ca in coauthors:
            assert "name" in ca
            assert "author_id" in ca
            assert "shared_works" in ca

    def test_coauthors_sorted_by_shared_works(self, mock_openalex_client):
        coauthors = mock_openalex_client.fetch_author_coauthors("A5023888391")
        counts = [c["shared_works"] for c in coauthors]
        assert counts == sorted(counts, reverse=True)

    def test_coauthors_limit(self, mock_openalex_client):
        coauthors = mock_openalex_client.fetch_author_coauthors(
            "A5023888391", limit=1
        )
        assert len(coauthors) == 1


# ------------------------------------------------------------------
# get_stats
# ------------------------------------------------------------------


class TestGetStats:
    """Test statistics tracking."""

    def test_initial_stats(self):
        client = OpenAlexClient()
        stats = client.get_stats()
        assert stats["total_requests"] == 0
        assert stats["failed_requests"] == 0
        assert stats["success_rate"] == 1.0

    def test_stats_after_requests(self, mock_openalex_client):
        mock_openalex_client.search_author("Jane Richardson")
        mock_openalex_client.fetch_author_works("A5023888391")
        stats = mock_openalex_client.get_stats()
        assert stats["total_requests"] >= 2

    def test_stats_success_rate_format(self, mock_openalex_client):
        stats = mock_openalex_client.get_stats()
        assert 0.0 <= stats["success_rate"] <= 1.0


# ------------------------------------------------------------------
# _normalize_id (static method)
# ------------------------------------------------------------------


class TestNormalizeId:
    """Test ID normalization helper."""

    def test_full_url(self):
        assert OpenAlexClient._normalize_id("https://openalex.org/A123") == "A123"

    def test_short_id(self):
        assert OpenAlexClient._normalize_id("A123") == "A123"

    def test_work_url(self):
        assert OpenAlexClient._normalize_id("https://openalex.org/W999") == "W999"
