"""Lab investigation mode.

Profiles a PI, calculates a lab grade, searches the institution, and
generates lab-specific red flag queries.
"""

from __future__ import annotations

from dataclasses import asdict

from academic_investigator.core.openalex import OpenAlexClient
from academic_investigator.core.person_profiler import PersonProfiler
from academic_investigator.core.impact_tiers import calculate_lab_grade
from academic_investigator.core.red_flags import generate_lab_red_flag_queries
from academic_investigator.reporting.templates import LAB_SECTIONS, SECTION_METADATA


class LabInvestigator:
    """Run a full lab / research group investigation.

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
        pi_name: str,
        affiliation: str,
        lab_name: str | None = None,
        purpose: str | None = None,
    ) -> dict:
        """Run lab investigation.

        Returns a dict with ``mode``, ``pi_profile``, ``lab_grade``,
        ``institution_data``, ``red_flag_queries``, and ``report_sections``.
        """
        # 1. Profile the PI
        pi_profile = self.profiler.profile_person(pi_name, affiliation, purpose=purpose)

        # 2. Calculate lab grade (h-index only, confidence="low")
        h_index = 0
        if pi_profile.get("status") == "found":
            h_index = pi_profile.get("metrics", {}).get("h_index", 0)
        lab_grade = calculate_lab_grade(h_index)

        # 3. Search institution
        institution_data = self.client.search_institution(affiliation) if affiliation else None

        # 4. Generate lab-specific red flags
        red_flag_queries = [asdict(q) for q in generate_lab_red_flag_queries(pi_name, lab_name)]

        # 5. Report sections from LAB_SECTIONS
        report_sections = [
            {
                "section": s,
                "source": SECTION_METADATA.get(s, {}).get("source", "unknown"),
                "required": SECTION_METADATA.get(s, {}).get("required", True),
            }
            for s in LAB_SECTIONS
        ]

        return {
            "mode": "lab",
            "lab_name": lab_name or f"{pi_name} Lab",
            "pi_name": pi_name,
            "pi_profile": pi_profile,
            "lab_grade": lab_grade,
            "institution_data": institution_data,
            "red_flag_queries": red_flag_queries,
            "report_sections": report_sections,
        }
