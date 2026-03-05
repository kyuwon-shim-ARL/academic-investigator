"""Output formatters for investigation reports.

Provides JSON and Markdown formatters.  Markdown output fills API-sourced
sections with real data and marks WebSearch-sourced sections with placeholder
queries.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from academic_investigator.reporting.lang import get_string
from academic_investigator.reporting.templates import (
    SECTION_METADATA,
    RESEARCHER_SECTIONS,
    LAB_SECTIONS,
    ORG_SECTIONS,
)


# ------------------------------------------------------------------
# JSON
# ------------------------------------------------------------------


def format_json(data: dict) -> str:
    """Serialize *data* as pretty-printed JSON.

    Parameters
    ----------
    data : dict
        Any serializable data structure.

    Returns
    -------
    str
        JSON string with indent=2 and non-ASCII characters preserved.
    """
    return json.dumps(data, indent=2, ensure_ascii=False)


# ------------------------------------------------------------------
# Markdown dispatcher
# ------------------------------------------------------------------


def format_markdown(data: dict, mode: str, lang: str = "ko") -> str:
    """Dispatch to the mode-specific Markdown formatter.

    Parameters
    ----------
    data : dict
        Profile / investigation data.
    mode : str
        One of ``"researcher"``, ``"lab"``, ``"org"``, ``"conference"``.
    lang : str
        Language code.

    Returns
    -------
    str
        Formatted Markdown string.

    Raises
    ------
    ValueError
        If *mode* is not recognized.
    """
    formatters = {
        "researcher": format_researcher_md,
        "lab": format_lab_md,
        "org": format_org_md,
        "conference": format_conference_md,
    }
    fn = formatters.get(mode)
    if fn is None:
        raise ValueError(
            f"Unknown mode '{mode}'. Supported: {list(formatters)}"
        )
    return fn(data, lang)


# ------------------------------------------------------------------
# Researcher Markdown
# ------------------------------------------------------------------


def format_researcher_md(data: dict, lang: str = "ko") -> str:
    """Format a researcher profile as Markdown.

    API-sourced sections are filled from *data*; websearch sections show
    placeholder queries.  Accepts both flat profile dicts and investigate()
    output (which nests the profile under a ``"profile"`` key).
    """
    # Unwrap nested investigation output
    if "profile" in data and isinstance(data["profile"], dict):
        profile = data["profile"]
    else:
        profile = data
    name = _get_display_name(profile)
    title = get_string("report_title_researcher", lang=lang, name=name)
    lines: list[str] = [f"# {title}", ""]

    websearch_label = get_string("label_websearch_required", lang=lang)

    for section_key in RESEARCHER_SECTIONS:
        header = _section_header(section_key, lang)
        meta = SECTION_METADATA.get(section_key, {"source": "manual"})
        source = meta["source"]

        lines.append(f"## {header}")
        lines.append("")

        if source == "api":
            content = _render_researcher_api_section(section_key, profile, lang)
            lines.append(content)
        elif source == "websearch":
            lines.append(websearch_label)
            queries = _websearch_queries_for_section(section_key, name, profile)
            if queries:
                lines.append("")
                for q in queries:
                    lines.append(f"- `{q}`")
        else:
            lines.append("---")

        lines.append("")

    return "\n".join(lines)


# ------------------------------------------------------------------
# Lab Markdown
# ------------------------------------------------------------------


def format_lab_md(data: dict, lang: str = "ko") -> str:
    """Format a lab investigation report as Markdown."""
    name = data.get("lab_name", data.get("pi_name", "Unknown Lab"))
    title = get_string("report_title_lab", lang=lang, name=name)
    lines: list[str] = [f"# {title}", ""]

    websearch_label = get_string("label_websearch_required", lang=lang)

    for section_key in LAB_SECTIONS:
        header = _section_header(section_key, lang)
        meta = SECTION_METADATA.get(section_key, {"source": "manual"})
        source = meta["source"]

        lines.append(f"## {header}")
        lines.append("")

        if source == "api":
            content = _render_lab_api_section(section_key, data, lang)
            lines.append(content)
        elif source == "websearch":
            lines.append(websearch_label)
        else:
            lines.append("---")

        lines.append("")

    return "\n".join(lines)


# ------------------------------------------------------------------
# Organization Markdown
# ------------------------------------------------------------------


def format_org_md(data: dict, lang: str = "ko") -> str:
    """Format an organization investigation report as Markdown."""
    name = data.get("org_name", "Unknown Organization")
    title = get_string("report_title_org", lang=lang, name=name)
    lines: list[str] = [f"# {title}", ""]

    websearch_label = get_string("label_websearch_required", lang=lang)

    for section_key in ORG_SECTIONS:
        header = _section_header(section_key, lang)
        meta = SECTION_METADATA.get(section_key, {"source": "manual"})
        source = meta["source"]

        lines.append(f"## {header}")
        lines.append("")

        if source == "api":
            content = _render_org_api_section(section_key, data, lang)
            lines.append(content)
        elif source == "websearch":
            lines.append(websearch_label)
        else:
            lines.append("---")

        lines.append("")

    return "\n".join(lines)


# ------------------------------------------------------------------
# Conference Markdown
# ------------------------------------------------------------------


def format_conference_md(data: dict, lang: str = "ko") -> str:
    """Format a conference analysis report as Markdown."""
    name = data.get("conference_name", "Unknown Conference")
    title = get_string("report_title_conference", lang=lang, name=name)
    lines: list[str] = [f"# {title}", ""]

    # Conference reports are simpler; dump available data
    for key in ("overview", "speakers", "topics", "assessment", "summary"):
        header = _section_header(key, lang)
        lines.append(f"## {header}")
        lines.append("")
        if key in data:
            lines.append(_format_value(data[key]))
        else:
            websearch_label = get_string("label_websearch_required", lang=lang)
            lines.append(websearch_label)
        lines.append("")

    return "\n".join(lines)


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def _get_display_name(data: dict) -> str:
    """Extract a display name from profile data."""
    # Try common fields
    for key in ("display_name", "name", "author_name", "pi_name"):
        if key in data and data[key]:
            return data[key]
    # Fallback from openalex_url
    url = data.get("openalex_url", "")
    if url:
        return url.split("/")[-1]
    return "Unknown"


def _section_header(section_key: str, lang: str) -> str:
    """Localized section header, with fallback."""
    lang_key = f"section_{section_key}"
    try:
        return get_string(lang_key, lang=lang)
    except KeyError:
        return section_key.replace("_", " ").title()


def _format_value(value: Any) -> str:
    """Convert a value to a Markdown-friendly string."""
    if isinstance(value, list):
        if not value:
            return "- (none)"
        lines = []
        for item in value:
            if isinstance(item, dict):
                parts = [f"{k}: {v}" for k, v in item.items()]
                lines.append(f"- {', '.join(parts)}")
            else:
                lines.append(f"- {item}")
        return "\n".join(lines)
    if isinstance(value, dict):
        lines = []
        for k, v in value.items():
            lines.append(f"- **{k}**: {v}")
        return "\n".join(lines)
    return str(value)


def _render_researcher_api_section(
    section_key: str, data: dict, lang: str
) -> str:
    """Render an API-sourced researcher section from profile data."""
    if section_key == "basic_info":
        return _render_basic_info(data, lang)
    if section_key == "publications":
        return _render_publications(data, lang)
    if section_key == "network":
        return _render_network(data, lang)
    if section_key == "assessment":
        return _render_assessment(data, lang)
    if section_key == "summary":
        return _render_researcher_summary(data, lang)
    return "---"


def _render_basic_info(data: dict, lang: str) -> str:
    """Render basic info section."""
    metrics = data.get("metrics", {})
    impact = data.get("impact_tier", {})
    concepts = data.get("top_concepts", [])

    lines = []
    lines.append(f"- **{get_string('label_h_index', lang=lang)}**: {metrics.get('h_index', 'N/A')}")
    lines.append(f"- **{get_string('label_citations', lang=lang)}**: {metrics.get('citation_count', 'N/A')}")
    lines.append(f"- **{get_string('label_works_count', lang=lang)}**: {metrics.get('works_count', 'N/A')}")
    lines.append(f"- **{get_string('label_citations_per_paper', lang=lang)}**: {metrics.get('citations_per_paper', 'N/A')}")
    lines.append(f"- **{get_string('label_impact_tier', lang=lang)}**: {impact.get('tier', 'N/A')} ({impact.get('percentile', '')})")

    if concepts:
        concept_str = ", ".join(concepts)
        lines.append(f"- **{get_string('label_top_concepts', lang=lang)}**: {concept_str}")

    url = data.get("openalex_url", "")
    if url:
        lines.append(f"- **OpenAlex**: [{url}]({url})")

    return "\n".join(lines)


def _render_publications(data: dict, lang: str) -> str:
    """Render top publications section."""
    papers = data.get("top_papers", [])
    if not papers:
        return get_string("label_not_found", lang=lang)

    lines = []
    for i, p in enumerate(papers, 1):
        title = p.get("title", "Unknown")
        year = p.get("year", "")
        cites = p.get("citations", 0)
        journal = p.get("journal", "Unknown")
        doi = p.get("doi", "")
        line = f"{i}. **{title}** ({year})"
        line += f"\n   - {get_string('label_journal', lang=lang)}: {journal}"
        line += f" | {get_string('label_citations', lang=lang)}: {cites}"
        if doi:
            line += f"\n   - {get_string('label_doi', lang=lang)}: {doi}"
        lines.append(line)
    return "\n".join(lines)


def _render_network(data: dict, lang: str) -> str:
    """Render collaboration network section."""
    coauthors = data.get("coauthors", [])
    if not coauthors:
        return get_string("label_not_found", lang=lang)

    lines = [f"**{get_string('label_coauthors', lang=lang)}**:", ""]
    for ca in coauthors:
        name = ca.get("name", "Unknown")
        shared = ca.get("shared_works", 0)
        lines.append(
            f"- {name} ({get_string('label_shared_works', lang=lang)}: {shared})"
        )
    return "\n".join(lines)


def _render_assessment(data: dict, lang: str) -> str:
    """Render overall assessment section."""
    impact = data.get("impact_tier", {})
    career = data.get("career_metrics", {})
    rec = data.get("recommendation", "")

    lines = []
    lines.append(f"- **{get_string('label_impact_tier', lang=lang)}**: {impact.get('tier', 'N/A')} - {impact.get('description', '')}")
    if career.get("trend"):
        lines.append(f"- **{get_string('label_career_trend', lang=lang)}**: {career['trend']}")
    if rec:
        lines.append(f"- **{get_string('label_recommendation', lang=lang)}**: {rec}")
    return "\n".join(lines)


def _render_researcher_summary(data: dict, lang: str) -> str:
    """Render researcher summary section."""
    name = _get_display_name(data)
    metrics = data.get("metrics", {})
    impact = data.get("impact_tier", {})
    return (
        f"{name}: {impact.get('tier', 'N/A')} "
        f"(h-index {metrics.get('h_index', 'N/A')}, "
        f"{metrics.get('citation_count', 0)} citations, "
        f"{metrics.get('works_count', 0)} works)"
    )


def _render_lab_api_section(section_key: str, data: dict, lang: str) -> str:
    """Render an API-sourced lab section."""
    if section_key == "overview":
        lab_name = data.get("lab_name", "")
        pi = data.get("pi_name", "")
        return f"- Lab: {lab_name}\n- PI: {pi}"
    if section_key == "pi_profile":
        pi_data = data.get("pi_profile", data)
        return _render_basic_info(pi_data, lang)
    if section_key == "network":
        return _render_network(data.get("pi_profile", data), lang)
    if section_key == "assessment":
        grade = data.get("lab_grade", {})
        if grade:
            return _format_value(grade)
        return "---"
    if section_key == "summary":
        return data.get("summary", "---")
    return "---"


def _render_org_api_section(section_key: str, data: dict, lang: str) -> str:
    """Render an API-sourced org section."""
    if section_key == "overview":
        name = data.get("org_name", "")
        return f"- Organization: {name}"
    if section_key == "assessment":
        return data.get("assessment", "---")
    if section_key == "summary":
        return data.get("summary", "---")
    return "---"


def _websearch_queries_for_section(
    section_key: str, name: str, data: dict
) -> List[str]:
    """Generate suggested WebSearch queries for a websearch-sourced section."""
    affiliation = ""
    metrics = data.get("metrics", {})
    if data.get("openalex_url"):
        affiliation = data.get("affiliation", "")

    queries: Dict[str, List[str]] = {
        "education": [
            f"{name} education background CV",
            f"{name} PhD thesis advisor",
        ],
        "grants": [
            f"{name} research grant funding NIH NSF",
            f"{name} principal investigator award",
        ],
        "activities": [
            f"{name} conference keynote invited speaker",
            f"{name} editorial board journal reviewer",
        ],
        "mentorship": [
            f"{name} graduate students postdoc mentees",
            f"{name} lab alumni career",
        ],
        "red_flags": [
            f"{name} retraction misconduct",
            f"{name} controversy",
        ],
    }
    return queries.get(section_key, [])
