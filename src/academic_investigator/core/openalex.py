"""OpenAlex API client for academic data retrieval.

Wraps pyalex and raw HTTP requests to provide a unified interface
for searching authors, works, institutions, and coauthorship data.

Author matching uses an affiliation hard-gate (D2):
  ``openalex_matched=True`` only when BOTH conditions hold:
    1. name_aligned(query_name, candidate.display_name)
    2. inst_tokens(query_affiliation) ∩ inst_tokens(candidate institutions) >= 1

Candidates that fail the gate are rejected — openalex_matched stays False.
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any, Dict, List, Optional, Set

import pyalex
import requests
from pyalex import Authors, Institutions, Works


# ------------------------------------------------------------------
# Affiliation gate helpers (ported from reresolve.py)
# ------------------------------------------------------------------

def _norm(s: str) -> Set[str]:
    """Normalise a string to a set of meaningful word tokens."""
    s = re.sub(r"[‐-―\-]", " ", s or "")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return {t for t in re.sub(r"[^a-z ]", " ", s.lower()).split() if len(t) > 1}


_STOP: Set[str] = _norm(
    "university department of the college school institute national republic "
    "korea science technology center centre research division graduate faculty "
    "laboratory lab co ltd inc and convergence interdisciplinary advanced life "
    "sciences biotechnology engineering medicine medical food animal program major "
    "seoul busan global city institutes"
)


def inst_tokens(affil: str) -> Set[str]:
    """Return distinctive institution tokens (generic words removed)."""
    return _norm(affil) - _STOP


def name_aligned(query: str, display: str) -> bool:
    """Return True when query and display name token sets overlap sufficiently.

    Alignment requires the intersection to equal at least one of the two sets
    (i.e. one name is a subset of the other), mirroring reresolve.py.
    """
    qn, dn = _norm(query), _norm(display)
    if not qn or not dn:
        return False
    i = qn & dn
    return bool(i) and (i == qn or i == dn)


class OpenAlexClient:
    """Client for querying the OpenAlex academic database.

    Parameters
    ----------
    email : str, optional
        Polite-pool email. Falls back to ``OPENALEX_EMAIL`` env var.
    api_key : str, optional
        OpenAlex API key for premium tier. Falls back to ``OPENALEX_API_KEY``.
    timeout : int
        HTTP request timeout in seconds (default 30).
    """

    def __init__(
        self,
        email: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        self.email = email or os.environ.get("OPENALEX_EMAIL")
        self.api_key = api_key or os.environ.get("OPENALEX_API_KEY")
        self.timeout = timeout

        if self.email:
            pyalex.config.email = self.email
        if self.api_key:
            pyalex.config.api_key = self.api_key
        pyalex.config.max_retries = 3

        self.base_url: str = "https://api.openalex.org"
        self.failed_requests: list[str] = []
        self.request_count: int = 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make_request(self, url: str) -> Optional[Dict[str, Any]]:
        """Make a raw HTTP GET request to the OpenAlex API."""
        self.request_count += 1
        try:
            headers: dict[str, str] = {}
            if self.email:
                headers["User-Agent"] = f"mailto:{self.email}"
            params: dict[str, str] = {}
            if self.api_key:
                params["api_key"] = self.api_key
            resp = requests.get(
                url, headers=headers, params=params, timeout=self.timeout
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            self.failed_requests.append(url[:120])
            return None

    @staticmethod
    def _normalize_id(raw_id: str) -> str:
        """Strip full URL prefix, returning the short OpenAlex ID."""
        if raw_id.startswith("http"):
            return raw_id.split("/")[-1]
        return raw_id

    # ------------------------------------------------------------------
    # Author methods
    # ------------------------------------------------------------------

    def search_author(
        self, name: str, affiliation: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Search for an author by name with an affiliation hard-gate (D2).

        When ``affiliation`` is provided, a candidate is accepted ONLY when:
          1. ``name_aligned(name, candidate.display_name)`` is True, AND
          2. ``inst_tokens(affiliation) ∩ inst_tokens(candidate institutions) >= 1``

        The returned dict includes ``openalex_matched=True`` when the gate
        passes, ``openalex_matched=False`` otherwise.  A result is returned
        even when openalex_matched=False so callers can inspect it; callers
        MUST check ``openalex_matched`` before using the profile for
        landscape/prediction generation (see D3).

        When no affiliation is supplied, name alignment alone is applied and
        ``openalex_matched`` reflects whether the top result name-aligned.
        """
        self.request_count += 1
        try:
            results = Authors().search(name).get()
        except Exception:
            self.failed_requests.append(f"search_author:{name}")
            return None

        if not results:
            return None

        want = inst_tokens(affiliation) if affiliation else set()

        # --- affiliation hard-gate path ---
        if affiliation and want:
            best: Optional[Dict[str, Any]] = None
            best_score: float = -1.0
            for candidate in results:
                if not name_aligned(name, candidate.get("display_name", "")):
                    continue
                insts = candidate.get("last_known_institutions") or []
                itoks: Set[str] = set()
                for ins in insts:
                    itoks |= inst_tokens(ins.get("display_name", ""))
                overlap = len(want & itoks)
                if overlap < 1:
                    continue  # hard-gate: must have >= 1 token overlap
                score = (
                    overlap * 100
                    + min((candidate.get("summary_stats", {}).get("h_index") or 0), 50) / 100.0
                )
                if score > best_score:
                    best, best_score = candidate, score

            if best is not None:
                best = dict(best)
                best["openalex_matched"] = True
                return best

            # Gate failed — return top name-aligned result tagged False (D3 will branch)
            for candidate in results:
                if name_aligned(name, candidate.get("display_name", "")):
                    out = dict(candidate)
                    out["openalex_matched"] = False
                    return out
            # No name alignment at all
            out = dict(results[0])
            out["openalex_matched"] = False
            return out

        # --- no affiliation: name-alignment only ---
        for candidate in results:
            if name_aligned(name, candidate.get("display_name", "")):
                out = dict(candidate)
                out["openalex_matched"] = True
                return out
        out = dict(results[0])
        out["openalex_matched"] = False
        return out

    def fetch_author_works(
        self,
        author_id: str,
        limit: int = 10,
        sort: str = "cited_by_count:desc",
    ) -> List[Dict[str, Any]]:
        """Fetch an author's works sorted by the given criterion."""
        self.request_count += 1
        author_id = self._normalize_id(author_id)
        sort_field, sort_dir = sort.split(":")
        try:
            results: list[Dict[str, Any]] = []
            for page in (
                Works()
                .filter(authorships={"author": {"id": author_id}})
                .sort(**{sort_field: sort_dir})
                .paginate(per_page=limit, n_max=limit)
            ):
                results.extend(page)
            return results[:limit]
        except Exception:
            self.failed_requests.append(f"fetch_author_works:{author_id}")
            return []

    def fetch_author_coauthors(
        self, author_id: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Fetch frequent coauthors for an author by analyzing recent works.

        Returns a list of coauthor dicts with ``name``, ``author_id``,
        ``shared_works`` count, sorted by frequency.
        """
        self.request_count += 1
        author_id = self._normalize_id(author_id)

        try:
            works: list[Dict[str, Any]] = []
            for page in (
                Works()
                .filter(authorships={"author": {"id": author_id}})
                .sort(publication_year="desc")
                .paginate(per_page=50, n_max=200)
            ):
                works.extend(page)
        except Exception:
            self.failed_requests.append(f"fetch_author_coauthors:{author_id}")
            return []

        coauthor_counts: dict[str, dict[str, Any]] = {}
        for work in works:
            for authorship in work.get("authorships", []):
                a = authorship.get("author", {})
                aid = a.get("id", "")
                if not aid:
                    continue
                short_id = self._normalize_id(aid)
                if short_id == author_id:
                    continue
                if short_id not in coauthor_counts:
                    coauthor_counts[short_id] = {
                        "name": a.get("display_name", "Unknown"),
                        "author_id": short_id,
                        "shared_works": 0,
                    }
                coauthor_counts[short_id]["shared_works"] += 1

        sorted_coauthors = sorted(
            coauthor_counts.values(),
            key=lambda x: x["shared_works"],
            reverse=True,
        )
        return sorted_coauthors[:limit]

    # ------------------------------------------------------------------
    # Work methods
    # ------------------------------------------------------------------

    def fetch_work(self, work_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single work by its OpenAlex ID or URL."""
        self.request_count += 1
        work_id = self._normalize_id(work_id)
        try:
            return Works()[work_id]
        except Exception:
            self.failed_requests.append(work_id)
            return None

    # ------------------------------------------------------------------
    # Institution methods
    # ------------------------------------------------------------------

    def search_institution(
        self, name: str, country: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Search for an institution by name, optionally filtering by country code.

        Parameters
        ----------
        name : str
            Institution name to search for.
        country : str, optional
            Two-letter ISO country code (e.g. ``"US"``, ``"KR"``).

        Returns
        -------
        dict or None
            The best matching institution record.
        """
        self.request_count += 1
        try:
            query = Institutions().search(name)
            if country:
                query = query.filter(country_code=country.upper())
            results = query.get()
        except Exception:
            self.failed_requests.append(f"search_institution:{name}")
            return None

        if not results:
            return None
        return results[0]

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Return request statistics for this client session."""
        return {
            "total_requests": self.request_count,
            "failed_requests": len(self.failed_requests),
            "success_rate": 1.0
            - (len(self.failed_requests) / max(self.request_count, 1)),
        }
