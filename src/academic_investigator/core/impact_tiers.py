"""Impact tier classification and research/lab grading utilities.

Provides three public functions for categorizing researchers and labs:

- ``calculate_impact_tier`` -- coarse h-index + citation bucketing
- ``calculate_research_grade`` -- letter grade (S/A/B/C/D) for a researcher
- ``calculate_lab_grade`` -- letter grade for a lab/PI (handles partial data)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

IMPACT_TIERS: List[Tuple[int, str, str, str]] = [
    (50, "Elite", "Top 1%", "World-leading researcher with exceptional impact"),
    (30, "Senior Leader", "Top 5%", "Highly influential senior researcher"),
    (20, "Established", "Top 10%", "Well-established researcher with significant impact"),
    (10, "Mid-Career", "Top 25%", "Growing impact in the field"),
    (0, "Early Career", "Emerging", "Early-stage researcher or niche specialist"),
]

RESEARCH_GRADES: Dict[str, Dict[str, int]] = {
    "S": {"h_index": 50, "citations": 10000, "first_author": 50},
    "A": {"h_index": 30, "citations": 3000, "first_author": 30},
    "B": {"h_index": 15, "citations": 1000, "first_author": 15},
    "C": {"h_index": 5, "citations": 100, "first_author": 5},
    "D": {"h_index": 0, "citations": 0, "first_author": 0},
}

LAB_GRADE_THRESHOLDS: Dict[str, Dict[str, int]] = {
    "S": {"pi_h_index": 40, "annual_funding_usd": 1_000_000, "faculty_alumni": 5},
    "A": {"pi_h_index": 25, "annual_funding_usd": 500_000, "faculty_alumni": 3},
    "B": {"pi_h_index": 15, "annual_funding_usd": 200_000, "faculty_alumni": 1},
    "C": {"pi_h_index": 10, "annual_funding_usd": 100_000, "faculty_alumni": 0},
    "D": {"pi_h_index": 0, "annual_funding_usd": 0, "faculty_alumni": 0},
}

LAB_GRADE_DESCRIPTIONS: Dict[str, str] = {
    "S": "World-class lab with exceptional research output and training record",
    "A": "Top-tier lab with strong research program and track record",
    "B": "Solid lab with established research and growing presence",
    "C": "Developing lab with moderate research output",
    "D": "Early-stage or small-scale research group",
}

_GRADE_ORDER: list[str] = ["S", "A", "B", "C", "D"]


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------


def calculate_impact_tier(
    h_index: int, citation_count: int = 0
) -> Dict[str, str]:
    """Classify a researcher into an impact tier based on h-index.

    Parameters
    ----------
    h_index : int
        The researcher's h-index.
    citation_count : int
        Total citation count (reserved for future weighting; currently
        used only as a tiebreaker annotation).

    Returns
    -------
    dict
        Keys: ``tier``, ``label``, ``percentile``, ``description``.
    """
    for threshold, tier, percentile, description in IMPACT_TIERS:
        if h_index >= threshold:
            return {
                "tier": tier,
                "label": tier,
                "percentile": percentile,
                "description": description,
            }
    # Fallback (should not be reached since last threshold is 0)
    last = IMPACT_TIERS[-1]
    return {
        "tier": last[1],
        "label": last[1],
        "percentile": last[2],
        "description": last[3],
    }


def calculate_research_grade(
    h_index: int,
    citation_count: int,
    first_author_count: Optional[int] = None,
) -> Dict[str, str]:
    """Assign a letter grade (S/A/B/C/D) to a researcher.

    The grade is determined by checking each threshold in descending
    order (S first). A researcher must meet **all available** criteria
    at a given level. When ``first_author_count`` is ``None``, only
    ``h_index`` and ``citation_count`` are evaluated.

    Parameters
    ----------
    h_index : int
        The researcher's h-index.
    citation_count : int
        Total citation count.
    first_author_count : int or None
        Number of first-author publications.

    Returns
    -------
    dict
        Keys: ``grade``, ``description``.
    """
    for grade in _GRADE_ORDER:
        thresholds = RESEARCH_GRADES[grade]
        if h_index < thresholds["h_index"]:
            continue
        if citation_count < thresholds["citations"]:
            continue
        if first_author_count is not None and first_author_count < thresholds["first_author"]:
            continue
        tier_info = _tier_for_grade(grade)
        return {"grade": grade, "description": tier_info}

    return {"grade": "D", "description": _tier_for_grade("D")}


def calculate_lab_grade(
    pi_h_index: int,
    annual_funding_usd: Optional[int] = None,
    faculty_alumni: Optional[int] = None,
) -> Dict[str, Any]:
    """Assign a letter grade to a lab / research group.

    Gracefully handles missing data. When only ``pi_h_index`` is
    available, the grade is based solely on that metric and the
    confidence is set to ``"low"``.

    Parameters
    ----------
    pi_h_index : int
        PI's h-index.
    annual_funding_usd : int or None
        Estimated annual funding in USD.
    faculty_alumni : int or None
        Number of former trainees who became faculty.

    Returns
    -------
    dict
        Keys: ``grade``, ``factors_used``, ``factors_missing``,
        ``confidence``, ``description``, ``note``.
    """
    factors_used: list[str] = ["pi_h_index"]
    factors_missing: list[str] = []

    has_funding = annual_funding_usd is not None
    has_alumni = faculty_alumni is not None

    if has_funding:
        factors_used.append("annual_funding_usd")
    else:
        factors_missing.append("annual_funding_usd")

    if has_alumni:
        factors_used.append("faculty_alumni")
    else:
        factors_missing.append("faculty_alumni")

    # Determine confidence level
    n_factors = len(factors_used)
    if n_factors >= 3:
        confidence = "high"
    elif n_factors == 2:
        confidence = "medium"
    else:
        confidence = "low"

    # Grade determination
    grade = _compute_lab_grade(pi_h_index, annual_funding_usd, faculty_alumni)

    note = ""
    if confidence == "low":
        note = "Grade based on PI h-index only; provide funding and alumni data for a more accurate assessment."
    elif confidence == "medium":
        missing_label = factors_missing[0].replace("_", " ") if factors_missing else "additional data"
        note = f"Partial data: {missing_label} not available. Grade may shift with complete information."

    return {
        "grade": grade,
        "factors_used": factors_used,
        "factors_missing": factors_missing,
        "confidence": confidence,
        "description": LAB_GRADE_DESCRIPTIONS[grade],
        "note": note,
    }


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def _tier_for_grade(grade: str) -> str:
    """Map a research grade letter to a human-readable description."""
    mapping = {
        "S": "World-leading researcher with exceptional impact",
        "A": "Highly influential senior researcher",
        "B": "Well-established researcher with significant impact",
        "C": "Growing impact in the field",
        "D": "Early-stage researcher or niche specialist",
    }
    return mapping.get(grade, "Unknown")


def _compute_lab_grade(
    pi_h_index: int,
    annual_funding_usd: Optional[int],
    faculty_alumni: Optional[int],
) -> str:
    """Compute lab grade considering only available factors."""
    for grade in _GRADE_ORDER:
        thresholds = LAB_GRADE_THRESHOLDS[grade]
        if pi_h_index < thresholds["pi_h_index"]:
            continue
        if annual_funding_usd is not None and annual_funding_usd < thresholds["annual_funding_usd"]:
            continue
        if faculty_alumni is not None and faculty_alumni < thresholds["faculty_alumni"]:
            continue
        return grade
    return "D"
