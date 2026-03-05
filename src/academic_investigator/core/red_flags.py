from __future__ import annotations
from dataclasses import dataclass, asdict


@dataclass
class RedFlagQuery:
    category: str       # "education", "publication", "ethics", "career", "financial", "legal", "reputation", "alumni", "dropout", "graduation", "absence", "transparency"
    query: str          # Formatted WebSearch query string (no unresolved placeholders)
    severity: str       # "high", "medium"
    description: str    # What this flag means


PERSON_RED_FLAG_TEMPLATES = [
    # Education - High severity
    ("education", "{name} {affiliation} retraction", "high", "Retraction history at institution"),
    ("education", "{name} predatory journal", "high", "Predatory journal publishing"),
    ("education", "{name} degree verification fake", "high", "Unverifiable credentials"),
    # Publication - High severity
    ("publication", "Retraction Watch {name}", "high", "Tracked by Retraction Watch"),
    ("publication", "{name} research misconduct", "high", "Research misconduct allegations"),
    ("publication", "{name} plagiarism", "high", "Plagiarism allegations"),
    ("publication", "{name} image manipulation", "high", "Image/data manipulation"),
    # Publication - Medium severity
    ("publication", "{name} self-citation rate", "medium", "Excessive self-citation pattern"),
    # Career
    ("career", "{name} {affiliation} controversy", "medium", "Controversy at institution"),
    ("career", "{name} fired dismissed", "high", "Employment termination"),
]

ORG_RED_FLAG_TEMPLATES = [
    ("legal", "{org_name} lawsuit legal issues", "high", "Legal disputes"),
    ("reputation", "{org_name} controversy scandal", "high", "Public controversies"),
    ("career", "{founder_name} fraud allegations", "high", "Founder fraud risk"),
    ("reputation", "{org_name} reviews complaints", "medium", "Negative reviews"),
    ("reputation", "{org_name} former employee reviews", "medium", "Employee reviews"),
    ("financial", "{org_name} funding problems", "medium", "Financial instability"),
    ("transparency", "{org_name} team leadership page", "high", "Missing team info"),
    ("financial", "{org_name} undisclosed funding source", "medium", "Undisclosed funding"),
    ("career", "{org_name} frequent pivots strategy change", "medium", "Frequent strategic pivots"),
]

LAB_RED_FLAG_TEMPLATES = [
    ("alumni", "{pi_name} lab negative review graduate student", "high", "Negative alumni experiences"),
    ("dropout", "{pi_name} lab dropout rate", "high", "High dropout rate"),
    ("graduation", "{pi_name} PhD graduation delay", "medium", "Graduation delay pattern"),
    ("absence", "{pi_name} lab PI absent", "medium", "PI frequent absence"),
    ("financial", "{pi_name} lab funding instability", "medium", "Lab financial instability"),
]


def generate_person_red_flag_queries(name: str, affiliation: str | None = None) -> list[RedFlagQuery]:
    """Generate red flag search queries for a person.

    Replaces {name} and {affiliation} in templates. If affiliation is None,
    removes the affiliation placeholder gracefully.
    """
    queries = []
    for cat, template, sev, desc in PERSON_RED_FLAG_TEMPLATES:
        query_str = template.format(
            name=name,
            affiliation=affiliation or ""
        ).strip()
        # Clean up double spaces from missing affiliation
        query_str = " ".join(query_str.split())
        queries.append(RedFlagQuery(category=cat, query=query_str, severity=sev, description=desc))
    return queries


def generate_org_red_flag_queries(org_name: str, founder_name: str | None = None) -> list[RedFlagQuery]:
    """Generate red flag search queries for an organization."""
    queries = []
    for cat, template, sev, desc in ORG_RED_FLAG_TEMPLATES:
        query_str = template.format(
            org_name=org_name,
            founder_name=founder_name or org_name
        ).strip()
        query_str = " ".join(query_str.split())
        queries.append(RedFlagQuery(category=cat, query=query_str, severity=sev, description=desc))
    return queries


def generate_lab_red_flag_queries(pi_name: str, lab_name: str | None = None) -> list[RedFlagQuery]:
    """Generate red flag search queries for a lab."""
    queries = []
    for cat, template, sev, desc in LAB_RED_FLAG_TEMPLATES:
        query_str = template.format(
            pi_name=pi_name,
            lab_name=lab_name or f"{pi_name} lab"
        ).strip()
        query_str = " ".join(query_str.split())
        queries.append(RedFlagQuery(category=cat, query=query_str, severity=sev, description=desc))
    return queries
