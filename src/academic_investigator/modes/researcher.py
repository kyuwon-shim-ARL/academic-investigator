"""Researcher investigation mode.

Profiles an individual researcher using OpenAlex data, generates red flag
search queries, and returns the report section checklist.
"""

from __future__ import annotations

from dataclasses import asdict

from academic_investigator.core.openalex import OpenAlexClient
from academic_investigator.core.person_profiler import PersonProfiler
from academic_investigator.core.red_flags import generate_person_red_flag_queries
from academic_investigator.reporting.templates import RESEARCHER_SECTIONS, SECTION_METADATA


class ResearcherInvestigator:
    """Run a full researcher investigation.

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

    def investigate(self, name: str, affiliation: str, purpose: str | None = None) -> dict:
        """Run researcher investigation.

        Returns a dict with ``mode``, ``profile``, ``red_flag_queries``,
        and ``report_sections``.
        """
        profile = self.profiler.profile_person(name, affiliation, purpose=purpose)
        red_flag_queries = [asdict(q) for q in generate_person_red_flag_queries(name, affiliation)]
        report_sections = [
            {
                "section": s,
                "source": SECTION_METADATA.get(s, {}).get("source", "unknown"),
                "required": SECTION_METADATA.get(s, {}).get("required", True),
            }
            for s in RESEARCHER_SECTIONS
        ]
        return {
            "mode": "researcher",
            "profile": profile,
            "red_flag_queries": red_flag_queries,
            "report_sections": report_sections,
        }
