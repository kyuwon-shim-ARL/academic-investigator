"""Internationalization (i18n) string table for report generation.

Supports Korean (ko) and English (en) with 60+ keys covering report titles,
section headers, impact tier descriptions, lab grade notes, and common labels.

Usage::

    from academic_investigator.reporting.lang import get_string, get_lang_from_args

    title = get_string("report_title_researcher", lang="ko", name="Jane")
    lang = get_lang_from_args("en")
"""

from __future__ import annotations

from typing import Optional

SUPPORTED_LANGUAGES = ("ko", "en")

# ------------------------------------------------------------------
# String tables
# ------------------------------------------------------------------

STRINGS: dict[str, dict[str, str]] = {
    # ---- Report titles ----
    "report_title_researcher": {
        "ko": "{name} 연구자 조사 보고서",
        "en": "Researcher Investigation Report: {name}",
    },
    "report_title_lab": {
        "ko": "{name} 연구실 조사 보고서",
        "en": "Lab Investigation Report: {name}",
    },
    "report_title_org": {
        "ko": "{name} 기관 조사 보고서",
        "en": "Organization Investigation Report: {name}",
    },
    "report_title_conference": {
        "ko": "{name} 학회 분석 보고서",
        "en": "Conference Analysis Report: {name}",
    },
    # ---- Researcher section headers ----
    "section_basic_info": {
        "ko": "기본 정보",
        "en": "Basic Information",
    },
    "section_education": {
        "ko": "학력 및 경력",
        "en": "Education & Career",
    },
    "section_publications": {
        "ko": "주요 논문",
        "en": "Key Publications",
    },
    "section_grants": {
        "ko": "연구비 수주 이력",
        "en": "Grant History",
    },
    "section_activities": {
        "ko": "학술 활동",
        "en": "Academic Activities",
    },
    "section_mentorship": {
        "ko": "멘토링 및 지도",
        "en": "Mentorship & Advising",
    },
    "section_network": {
        "ko": "공동연구 네트워크",
        "en": "Collaboration Network",
    },
    "section_assessment": {
        "ko": "종합 평가",
        "en": "Overall Assessment",
    },
    "section_red_flags": {
        "ko": "주의사항 (Red Flags)",
        "en": "Red Flags",
    },
    "section_questions": {
        "ko": "추가 확인 질문",
        "en": "Follow-up Questions",
    },
    "section_summary": {
        "ko": "요약",
        "en": "Summary",
    },
    # ---- Lab section headers ----
    "section_overview": {
        "ko": "개요",
        "en": "Overview",
    },
    "section_pi_profile": {
        "ko": "PI 프로필",
        "en": "PI Profile",
    },
    "section_research_program": {
        "ko": "연구 프로그램",
        "en": "Research Program",
    },
    "section_members": {
        "ko": "연구실 구성원",
        "en": "Lab Members",
    },
    "section_infrastructure": {
        "ko": "연구 인프라",
        "en": "Research Infrastructure",
    },
    "section_alumni_careers": {
        "ko": "졸업생 진로",
        "en": "Alumni Careers",
    },
    "section_funding": {
        "ko": "연구비 현황",
        "en": "Funding Status",
    },
    "section_culture": {
        "ko": "연구실 문화",
        "en": "Lab Culture",
    },
    "section_considerations": {
        "ko": "고려사항",
        "en": "Considerations",
    },
    # ---- Organization section headers ----
    "section_leadership": {
        "ko": "리더십",
        "en": "Leadership",
    },
    "section_technology": {
        "ko": "기술 및 플랫폼",
        "en": "Technology & Platform",
    },
    "section_products": {
        "ko": "제품 및 서비스",
        "en": "Products & Services",
    },
    "section_competitive_landscape": {
        "ko": "경쟁 환경",
        "en": "Competitive Landscape",
    },
    "section_glossary": {
        "ko": "용어 사전",
        "en": "Glossary",
    },
    # ---- Impact tier descriptions ----
    "tier_elite": {
        "ko": "세계적 수준의 연구자 (상위 1%)",
        "en": "World-leading researcher (Top 1%)",
    },
    "tier_senior_leader": {
        "ko": "분야 선도 연구자 (상위 5%)",
        "en": "Senior field leader (Top 5%)",
    },
    "tier_established": {
        "ko": "안정적 연구 기반 (상위 10%)",
        "en": "Well-established researcher (Top 10%)",
    },
    "tier_mid_career": {
        "ko": "성장 중인 연구자 (상위 25%)",
        "en": "Growing impact researcher (Top 25%)",
    },
    "tier_early_career": {
        "ko": "초기 경력 / 니치 전문가",
        "en": "Early career / niche specialist",
    },
    # ---- Lab grade confidence notes ----
    "lab_confidence_high": {
        "ko": "PI h-index, 연구비, 졸업생 진로 데이터를 기반으로 평가",
        "en": "Assessment based on PI h-index, funding, and alumni career data",
    },
    "lab_confidence_medium": {
        "ko": "일부 데이터 누락 - 완전한 평가를 위해 추가 정보 필요",
        "en": "Partial data available - additional information needed for complete assessment",
    },
    "lab_confidence_low": {
        "ko": "PI h-index만으로 평가 - 참고용으로만 활용",
        "en": "Assessment based on PI h-index only - use as reference only",
    },
    # ---- Common labels ----
    "label_h_index": {
        "ko": "H-인덱스",
        "en": "H-index",
    },
    "label_citations": {
        "ko": "피인용 수",
        "en": "Citations",
    },
    "label_works_count": {
        "ko": "논문 수",
        "en": "Works Count",
    },
    "label_citations_per_paper": {
        "ko": "논문당 피인용 수",
        "en": "Citations per Paper",
    },
    "label_impact_tier": {
        "ko": "영향력 등급",
        "en": "Impact Tier",
    },
    "label_research_grade": {
        "ko": "연구 등급",
        "en": "Research Grade",
    },
    "label_lab_grade": {
        "ko": "연구실 등급",
        "en": "Lab Grade",
    },
    "label_confidence": {
        "ko": "신뢰도",
        "en": "Confidence",
    },
    "label_coauthors": {
        "ko": "공동 저자",
        "en": "Co-authors",
    },
    "label_career_trend": {
        "ko": "경력 추이",
        "en": "Career Trend",
    },
    "label_recommendation": {
        "ko": "추천 의견",
        "en": "Recommendation",
    },
    "label_websearch_required": {
        "ko": "[WebSearch 필요]",
        "en": "[WebSearch required]",
    },
    "label_not_found": {
        "ko": "검색 결과 없음",
        "en": "Not found",
    },
    "label_affiliation": {
        "ko": "소속",
        "en": "Affiliation",
    },
    "label_journal": {
        "ko": "학술지",
        "en": "Journal",
    },
    "label_year": {
        "ko": "연도",
        "en": "Year",
    },
    "label_doi": {
        "ko": "DOI",
        "en": "DOI",
    },
    "label_shared_works": {
        "ko": "공동 논문 수",
        "en": "Shared Works",
    },
    "label_top_concepts": {
        "ko": "주요 연구 분야",
        "en": "Top Research Areas",
    },
    "label_career_length": {
        "ko": "연구 경력",
        "en": "Career Length",
    },
    "label_recent_activity": {
        "ko": "최근 활동",
        "en": "Recent Activity",
    },
    "label_openalex_url": {
        "ko": "OpenAlex URL",
        "en": "OpenAlex URL",
    },
    "label_generated_by": {
        "ko": "Academic Investigator에 의해 생성됨",
        "en": "Generated by Academic Investigator",
    },
}


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------


def get_string(key: str, lang: str = "ko", **kwargs: str) -> str:
    """Look up a localized string by key and format with kwargs.

    Parameters
    ----------
    key : str
        String key (must exist in STRINGS).
    lang : str
        Language code: ``"ko"`` or ``"en"``.
    **kwargs
        Format parameters to substitute into the string.

    Returns
    -------
    str
        Formatted localized string.

    Raises
    ------
    KeyError
        If *key* is not found in STRINGS.
    ValueError
        If *lang* is not a supported language.
    """
    if lang not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language '{lang}'. Supported: {SUPPORTED_LANGUAGES}"
        )
    if key not in STRINGS:
        raise KeyError(f"Unknown string key: '{key}'")
    template = STRINGS[key][lang]
    if kwargs:
        return template.format(**kwargs)
    return template


def get_lang_from_args(lang: Optional[str] = None) -> str:
    """Validate and return a language code.

    Parameters
    ----------
    lang : str or None
        Requested language. Defaults to ``"ko"`` when ``None``.

    Returns
    -------
    str
        Validated language code.

    Raises
    ------
    ValueError
        If *lang* is not supported.
    """
    if lang is None:
        return "ko"
    if lang not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language '{lang}'. Supported: {SUPPORTED_LANGUAGES}"
        )
    return lang
