"""Person profiler: aggregates OpenAlex data into a comprehensive researcher profile.

Refactored from SpeakerAnalyzer. Uses OpenAlexClient for data retrieval and
impact_tiers for classification. Adds coauthor extraction and uses the correct
primary_location.source.display_name path for journal names.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from academic_investigator.core.openalex import OpenAlexClient
from academic_investigator.core.impact_tiers import calculate_impact_tier


class PersonProfiler:
    """Build a comprehensive academic profile for a researcher.

    Parameters
    ----------
    client : OpenAlexClient, optional
        Pre-configured OpenAlex client. One is created if not provided.
    """

    def __init__(self, client: Optional[OpenAlexClient] = None) -> None:
        self.client = client or OpenAlexClient()

    def profile_person(
        self,
        name: str,
        affiliation: Optional[str] = None,
        purpose: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a comprehensive researcher profile.

        Parameters
        ----------
        name : str
            Full name of the researcher.
        affiliation : str, optional
            Institution name to disambiguate.
        purpose : str, optional
            Context for the profile (e.g. talk title, collaboration topic).

        Returns
        -------
        dict
            Profile with status, metrics, impact_tier, top_concepts,
            top_papers, career_metrics, coauthors, and recommendation.
        """
        author = self.client.search_author(name, affiliation=affiliation)
        if not author:
            return {
                "status": "not_found",
                "message": f"Could not find author: {name}"
                + (f" ({affiliation})" if affiliation else ""),
            }

        author_id = author.get("id", "")
        stats = author.get("summary_stats", {})
        h_index = stats.get("h_index", 0)
        citation_count = author.get("cited_by_count", 0)
        works_count = author.get("works_count", 0)

        # Fetch top works (up to 10, sorted by citations)
        short_id = self.client._normalize_id(author_id) if author_id else author_id
        works = self.client.fetch_author_works(short_id, limit=10, sort="cited_by_count:desc")

        # Classify impact
        impact_tier = calculate_impact_tier(h_index, citation_count)
        # Enrich impact_tier with raw metrics
        impact_tier["h_index"] = h_index
        impact_tier["citations"] = citation_count

        # Extract top concepts from topics
        concepts = [c["display_name"] for c in author.get("topics", [])[:5]]

        # Format top papers
        top_papers = self._format_top_papers(works[:5])

        # Career metrics
        career_metrics = self._calculate_career_metrics(works)

        # Coauthors
        coauthors = self._extract_coauthors(short_id)

        # Recommendation
        recommendation = self._generate_recommendation(
            impact_tier, h_index, top_papers, purpose
        )

        return {
            "status": "found",
            "display_name": author.get("display_name", name),
            "author_id": author_id,
            "openalex_url": f"https://openalex.org/{short_id}",
            "metrics": {
                "h_index": h_index,
                "citation_count": citation_count,
                "works_count": works_count,
                "citations_per_paper": round(
                    citation_count / max(works_count, 1), 1
                ),
            },
            "impact_tier": impact_tier,
            "top_concepts": concepts,
            "top_papers": top_papers,
            "career_metrics": career_metrics,
            "coauthors": coauthors,
            "recommendation": recommendation,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _format_top_papers(self, works: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format work records into a simplified top-papers list.

        Uses ``primary_location.source.display_name`` for journal name
        (not the deprecated ``host_venue``).
        """
        papers: List[Dict[str, Any]] = []
        for w in works:
            # Extract journal from primary_location.source.display_name
            primary_location = w.get("primary_location") or {}
            source = primary_location.get("source") or {}
            journal = source.get("display_name", "Unknown")

            openalex_id = w.get("id", "")
            if openalex_id:
                openalex_id = openalex_id.split("/")[-1]
            else:
                openalex_id = None

            papers.append(
                {
                    "title": w.get("title", "Unknown"),
                    "year": w.get("publication_year"),
                    "citations": w.get("cited_by_count", 0),
                    "journal": journal,
                    "doi": w.get("doi"),
                    "openalex_id": openalex_id,
                }
            )
        return papers

    def _calculate_career_metrics(
        self, works: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Derive career-level metrics from a list of works."""
        if not works:
            return {
                "career_length": 0,
                "recent_activity": "Unknown",
                "trend": "Unknown",
            }

        years = [
            w.get("publication_year")
            for w in works
            if w.get("publication_year")
        ]
        if not years:
            return {
                "career_length": 0,
                "recent_activity": "Unknown",
                "trend": "Unknown",
            }

        earliest_year = min(years)
        latest_year = max(years)
        career_length = latest_year - earliest_year + 1

        # Recent papers: within last 3 years relative to latest work
        recent_papers = [
            w
            for w in works
            if w.get("publication_year", 0) >= latest_year - 2
        ]
        recent_citations = sum(
            w.get("cited_by_count", 0) for w in recent_papers
        )
        avg_recent = round(recent_citations / max(len(recent_papers), 1), 1)

        total_citations = sum(w.get("cited_by_count", 0) for w in works)
        avg_overall = round(total_citations / len(works), 1)

        if avg_recent > avg_overall * 1.5:
            trend = "Rising"
        elif avg_recent > avg_overall * 0.8:
            trend = "Stable"
        else:
            trend = "Established"

        return {
            "career_length": career_length,
            "earliest_work": earliest_year,
            "latest_work": latest_year,
            "recent_activity": f"{len(recent_papers)} papers in last 3 years",
            "trend": trend,
            "avg_citations_recent": avg_recent,
            "avg_citations_overall": avg_overall,
        }

    def _extract_coauthors(self, author_id: str) -> List[Dict[str, Any]]:
        """Fetch coauthors via the OpenAlex client."""
        return self.client.fetch_author_coauthors(author_id)

    def _generate_recommendation(
        self,
        impact_tier: Dict[str, Any],
        h_index: int,
        top_papers: List[Dict[str, Any]],
        purpose: Optional[str],
    ) -> str:
        """Generate a text recommendation based on impact tier and top work.

        No emoji characters are included in the output.
        """
        tier = impact_tier.get("tier", "")
        description = impact_tier.get("description", "")

        if tier in ("Elite", "Senior Leader"):
            rec = f"Highly Recommended - {description} (h-index: {h_index})"
        elif tier == "Established":
            rec = f"Recommended - {description} (h-index: {h_index})"
        elif tier == "Mid-Career":
            rec = f"Valuable - {description} (h-index: {h_index})"
        else:
            rec = f"Niche/Emerging - {description} (h-index: {h_index})"

        if top_papers:
            top = top_papers[0]
            rec += (
                f"\n   Most cited work: \"{top['title']}\""
                f" ({top['year']}, {top['citations']} citations)"
            )

        return rec


def quick_profile(
    name: str,
    affiliation: Optional[str] = None,
    email: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """One-liner convenience to profile a researcher.

    Parameters
    ----------
    name : str
        Researcher name.
    affiliation : str, optional
        Institution name.
    email : str, optional
        Polite-pool email for OpenAlex.

    Returns
    -------
    dict or None
        Profile dict, or None if the researcher was not found.

    >>> result = quick_profile("Jane Smith", "MIT")
    """
    client = OpenAlexClient(email=email) if email else OpenAlexClient()
    profiler = PersonProfiler(client=client)
    result = profiler.profile_person(name, affiliation=affiliation)
    if result.get("status") == "not_found":
        return None
    return result
