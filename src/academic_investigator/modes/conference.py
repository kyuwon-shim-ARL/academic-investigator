"""Conference investigation mode.

Loads a YAML conference configuration, classifies speakers as
academic / industry / research_institute, profiles academic speakers via
OpenAlex, and returns a batch analysis with summary counts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from academic_investigator.core.openalex import OpenAlexClient
from academic_investigator.core.person_profiler import PersonProfiler

INDUSTRY_SUFFIXES = (
    "\u321c",  # ㈜ (Parenthesized Hangul Stock -- Korean incorporated)
    "Inc", "Corp", "Ltd", "GmbH", "Co.", "LLC", "Inc.", "Corp.", "Ltd.",
)


class ConferenceInvestigator:
    """Batch-analyze conference speakers.

    Parameters
    ----------
    email : str or None
        Polite-pool email for OpenAlex.
    api_key : str or None
        OpenAlex API key.
    """

    def __init__(self, email: str | None = None, api_key: str | None = None) -> None:
        client = OpenAlexClient(email=email, api_key=api_key)
        self.profiler = PersonProfiler(client=client)
        self.client = self.profiler.client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_config(self, config_path: str) -> dict:
        """Load a YAML conference config and extract speakers.

        Parameters
        ----------
        config_path : str
            Path to YAML config file.

        Returns
        -------
        dict
            Parsed config with ``conference``, ``sessions``, ``speakers``
            (extracted list), and ``speakers_summary``.
        """
        path = Path(config_path)
        with open(path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        speakers = self._extract_speakers_from_config(config)
        return {
            "conference": config.get("conference", {}),
            "sessions": config.get("sessions", []),
            "speakers": speakers,
            "speakers_summary": config.get("speakers_summary"),
        }

    def investigate_speakers(
        self,
        speakers: list[dict],
        config_path: str | None = None,
    ) -> dict:
        """Batch-analyze a list of speakers.

        Each speaker dict must have at least ``name`` and ``affiliation``.
        An optional ``title`` key provides talk context.

        Parameters
        ----------
        speakers : list[dict]
            Speaker dicts with ``name``, ``affiliation``, and optionally
            ``title`` and ``keywords``.
        config_path : str or None
            Path to YAML config (used to load ``speakers_summary`` for
            pre-classification).

        Returns
        -------
        dict
            Keys: ``mode``, ``speakers`` (list of result dicts),
            ``summary`` (counts by type), ``checklist`` (action items).
        """
        # Load speakers_summary for pre-classification if config provided
        speakers_summary: dict | None = None
        if config_path:
            path = Path(config_path)
            with open(path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
            speakers_summary = config.get("speakers_summary")

        results: list[dict] = []
        counts = {
            "academic_found": 0,
            "academic_not_found": 0,
            "industry": 0,
            "research_institute": 0,
        }

        for speaker in speakers:
            name = speaker.get("name", "")
            affiliation = speaker.get("affiliation", "")
            title = speaker.get("title")

            speaker_type = self._classify_speaker_type(affiliation, speakers_summary)

            if speaker_type == "industry":
                # Industry speakers skip profiling
                counts["industry"] += 1
                results.append({
                    "name": name,
                    "affiliation": affiliation,
                    "type": "industry",
                    "profile": None,
                    "alternative_research": self._create_alternative_research(name, affiliation),
                })
            elif speaker_type == "research_institute":
                # Research institute: attempt profiling
                profile = self.profiler.profile_person(name, affiliation, purpose=title)
                if profile.get("status") == "found":
                    counts["research_institute"] += 1
                    results.append({
                        "name": name,
                        "affiliation": affiliation,
                        "type": "research_institute",
                        "profile": profile,
                        "alternative_research": None,
                    })
                else:
                    # Fall back to alternative research
                    counts["research_institute"] += 1
                    results.append({
                        "name": name,
                        "affiliation": affiliation,
                        "type": "research_institute",
                        "profile": profile,
                        "alternative_research": self._create_alternative_research(name, affiliation),
                    })
            else:
                # Academic: attempt profiling
                profile = self.profiler.profile_person(name, affiliation, purpose=title)
                if profile.get("status") == "found":
                    counts["academic_found"] += 1
                    results.append({
                        "name": name,
                        "affiliation": affiliation,
                        "type": "academic",
                        "profile": profile,
                        "alternative_research": None,
                    })
                else:
                    # Academic not found -> fall back to industry path
                    counts["academic_not_found"] += 1
                    results.append({
                        "name": name,
                        "affiliation": affiliation,
                        "type": "academic_not_found",
                        "profile": profile,
                        "alternative_research": self._create_alternative_research(name, affiliation),
                    })

        checklist = self._build_checklist(results)

        return {
            "mode": "conference",
            "speakers": results,
            "summary": counts,
            "checklist": checklist,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_speakers_from_config(self, config: dict) -> list[dict]:
        """Extract speakers from config sessions.

        Handles ``talks[]``, ``presentations[]``, and ``speakers[]`` keys
        within each session. Sessions without any of these keys are skipped.
        """
        speakers: list[dict] = []
        seen: set[str] = set()

        for session in config.get("sessions", []):
            # Try talks, presentations, speakers in order
            items = (
                session.get("talks")
                or session.get("presentations")
                or session.get("speakers")
                or []
            )
            for item in items:
                name = item.get("speaker") or item.get("name", "")
                if not name or name in seen:
                    continue
                seen.add(name)
                speakers.append({
                    "name": name,
                    "affiliation": item.get("affiliation", ""),
                    "title": item.get("title", ""),
                    "keywords": item.get("keywords", []),
                })

        return speakers

    def _classify_speaker_type(
        self, affiliation: str, speakers_summary: dict | None = None
    ) -> str:
        """Classify a speaker as academic, industry, or research_institute.

        Uses speakers_summary for pre-classification if available, then
        falls back to affiliation heuristics.
        """
        # Check speakers_summary first
        if speakers_summary:
            # Check industry list
            for entry in speakers_summary.get("industry", []):
                aff = entry.get("affiliation", "")
                if aff and aff == affiliation:
                    return "industry"
            # Check research_institutes list
            for entry in speakers_summary.get("research_institutes", []):
                aff = entry.get("affiliation", "")
                if aff and aff == affiliation:
                    return "research_institute"
            # Check academic list
            for entry in speakers_summary.get("academic", []):
                aff = entry.get("affiliation", "")
                if aff and aff == affiliation:
                    return "academic"

        # Affiliation-based heuristics
        if not affiliation:
            return "academic"

        # Check industry suffixes
        for suffix in INDUSTRY_SUFFIXES:
            if suffix in affiliation:
                return "industry"

        return "academic"

    def _create_alternative_research(self, name: str, affiliation: str) -> dict:
        """Return WebSearch queries for non-academic or not-found speakers."""
        queries = [
            f"{name} {affiliation} research",
            f"{name} {affiliation} publications",
            f"{name} {affiliation} LinkedIn",
            f"{name} {affiliation} biography",
        ]
        return {
            "type": "websearch",
            "queries": queries,
        }

    def _build_checklist(self, results: list[dict]) -> list[dict]:
        """Build action items for the investigation."""
        checklist: list[dict] = []
        for r in results:
            if r.get("alternative_research"):
                checklist.append({
                    "action": "websearch",
                    "speaker": r["name"],
                    "reason": f"No OpenAlex profile for {r['name']} ({r['affiliation']})",
                    "queries": r["alternative_research"]["queries"],
                })
        return checklist
