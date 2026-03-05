"""Report section definitions and skeleton generator.

Defines the ordered section lists for each investigation mode and metadata
about each section (data source, whether it is required).  The
``get_report_skeleton`` function produces a ready-to-fill Markdown skeleton.
"""

from __future__ import annotations

from typing import Any, Dict

from academic_investigator.reporting.lang import get_string

# ------------------------------------------------------------------
# Section lists per mode
# ------------------------------------------------------------------

RESEARCHER_SECTIONS: list[str] = [
    "basic_info",
    "education",
    "publications",
    "grants",
    "activities",
    "mentorship",
    "network",
    "assessment",
    "red_flags",
    "questions",
    "summary",
]

LAB_SECTIONS: list[str] = [
    "overview",
    "pi_profile",
    "research_program",
    "members",
    "infrastructure",
    "alumni_careers",
    "funding",
    "network",
    "culture",
    "assessment",
    "considerations",
    "questions",
    "summary",
]

ORG_SECTIONS: list[str] = [
    "overview",
    "leadership",
    "technology",
    "products",
    "competitive_landscape",
    "funding",
    "assessment",
    "red_flags",
    "questions",
    "glossary",
    "summary",
]

# ------------------------------------------------------------------
# Section metadata
# ------------------------------------------------------------------

SECTION_METADATA: Dict[str, Dict[str, Any]] = {
    # Researcher sections
    "basic_info": {"source": "api", "required": True},
    "education": {"source": "websearch", "required": True},
    "publications": {"source": "api", "required": True},
    "grants": {"source": "websearch", "required": False},
    "activities": {"source": "websearch", "required": False},
    "mentorship": {"source": "websearch", "required": False},
    "network": {"source": "api", "required": True},
    "assessment": {"source": "api", "required": True},
    "red_flags": {"source": "websearch", "required": True},
    "questions": {"source": "manual", "required": False},
    "summary": {"source": "api", "required": True},
    # Lab sections
    "overview": {"source": "api", "required": True},
    "pi_profile": {"source": "api", "required": True},
    "research_program": {"source": "websearch", "required": True},
    "members": {"source": "websearch", "required": False},
    "infrastructure": {"source": "websearch", "required": False},
    "alumni_careers": {"source": "websearch", "required": False},
    "funding": {"source": "websearch", "required": False},
    "culture": {"source": "websearch", "required": False},
    "considerations": {"source": "websearch", "required": False},
    # Organization sections
    "leadership": {"source": "websearch", "required": True},
    "technology": {"source": "websearch", "required": False},
    "products": {"source": "websearch", "required": False},
    "competitive_landscape": {"source": "websearch", "required": False},
    "glossary": {"source": "manual", "required": False},
}

# Map mode name to section list
_MODE_SECTIONS: Dict[str, list[str]] = {
    "researcher": RESEARCHER_SECTIONS,
    "lab": LAB_SECTIONS,
    "org": ORG_SECTIONS,
}


def _section_header(section_key: str, lang: str) -> str:
    """Return the localized section header for a given key.

    Looks up ``section_{key}`` in the lang table.  Falls back to a
    title-cased version of the key if the lang key is missing.
    """
    lang_key = f"section_{section_key}"
    try:
        return get_string(lang_key, lang=lang)
    except KeyError:
        return section_key.replace("_", " ").title()


def get_report_skeleton(mode: str, lang: str = "ko", **context: str) -> str:
    """Generate a Markdown report skeleton for *mode*.

    API-sourced sections contain a placeholder noting that data will be filled
    from the OpenAlex API.  WebSearch-sourced sections contain
    ``[WebSearch required]`` markers.

    Parameters
    ----------
    mode : str
        One of ``"researcher"``, ``"lab"``, ``"org"``.
    lang : str
        Language code (``"ko"`` or ``"en"``).
    **context
        Extra substitution variables (e.g. ``name``).

    Returns
    -------
    str
        Markdown skeleton string.

    Raises
    ------
    ValueError
        If *mode* is not recognized.
    """
    if mode not in _MODE_SECTIONS:
        raise ValueError(
            f"Unknown report mode '{mode}'. Supported: {list(_MODE_SECTIONS)}"
        )

    sections = _MODE_SECTIONS[mode]

    # Title
    title_key = f"report_title_{mode}"
    try:
        title = get_string(title_key, lang=lang, **context)
    except (KeyError, IndexError):
        title = f"{mode.title()} Report"

    websearch_label = get_string("label_websearch_required", lang=lang)

    lines: list[str] = [f"# {title}", ""]

    for section_key in sections:
        header = _section_header(section_key, lang)
        meta = SECTION_METADATA.get(section_key, {"source": "manual", "required": False})
        source = meta["source"]

        lines.append(f"## {header}")
        lines.append("")

        if source == "api":
            lines.append("<!-- API data -->" if lang == "en" else "<!-- API 데이터 -->")
        elif source == "websearch":
            lines.append(websearch_label)
        else:
            lines.append("---")

        lines.append("")

    return "\n".join(lines)
