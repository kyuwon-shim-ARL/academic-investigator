"""Investigation modes: researcher check, lab check, org check, conference analysis."""

from academic_investigator.modes.researcher import ResearcherInvestigator
from academic_investigator.modes.lab import LabInvestigator
from academic_investigator.modes.organization import OrgInvestigator
from academic_investigator.modes.conference import ConferenceInvestigator

__all__ = [
    "ResearcherInvestigator",
    "LabInvestigator",
    "OrgInvestigator",
    "ConferenceInvestigator",
]
