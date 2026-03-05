"""Organization investigation mode.

Profiles key people, searches the institution record, and generates
organization-specific red flag queries.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional

from academic_investigator.core.openalex import OpenAlexClient
from academic_investigator.core.person_profiler import PersonProfiler
from academic_investigator.core.red_flags import generate_org_red_flag_queries
from academic_investigator.reporting.templates import ORG_SECTIONS, SECTION_METADATA


class OrgInvestigator:
    """Run a full organization investigation.

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

    def investigate(
        self,
        org_name: str,
        org_type: str = "company",
        key_people: List[str] | None = None,
    ) -> dict:
        """Run organization investigation.

        Parameters
        ----------
        org_name : str
            Name of the organization.
        org_type : str
            Type of organization (``"company"``, ``"university"``, etc.).
        key_people : list[str] or None
            Names of key people to profile.

        Returns
        -------
        dict
            Investigation results with ``mode``, ``org_name``, ``org_type``,
            ``institution_data``, ``people_profiles``, ``red_flag_queries``,
            and ``report_sections``.
        """
        # 1. Profile each key person
        people_profiles: Dict[str, Any] = {}
        for person in (key_people or []):
            people_profiles[person] = self.profiler.profile_person(person, org_name)

        # 2. Search institution
        institution_data = self.client.search_institution(org_name)

        # 3. Generate org red flags
        founder = key_people[0] if key_people else None
        red_flag_queries = [asdict(q) for q in generate_org_red_flag_queries(org_name, founder)]

        # 4. Report sections from ORG_SECTIONS
        report_sections = [
            {
                "section": s,
                "source": SECTION_METADATA.get(s, {}).get("source", "unknown"),
                "required": SECTION_METADATA.get(s, {}).get("required", True),
            }
            for s in ORG_SECTIONS
        ]

        return {
            "mode": "org",
            "org_name": org_name,
            "org_type": org_type,
            "institution_data": institution_data,
            "people_profiles": people_profiles,
            "red_flag_queries": red_flag_queries,
            "report_sections": report_sections,
        }
