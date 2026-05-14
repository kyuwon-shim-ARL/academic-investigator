"""Unit tests for scripts/landscape.py — V1 verification gate.

Covers:
- fallback_grade (paper-year): boundaries + empty input
- topic_grade (OpenAlex counts): ZeroDivisionError safety (H3)
- search_topic relevance threshold boundary (H6)
- get_related_labs institution dedup with ror_id + 'Unknown' kept separate (H5, M8)
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_SCRIPT = Path(__file__).resolve().parent.parent / 'scripts' / 'landscape.py'
_spec = importlib.util.spec_from_file_location('landscape', _SCRIPT)
landscape = importlib.util.module_from_spec(_spec)
sys.modules['landscape'] = landscape
_spec.loader.exec_module(landscape)


# --------- fallback_grade ---------

def test_fallback_grade_empty():
    assert landscape.fallback_grade([], 2026) == ('N/A', None)


def test_fallback_grade_all_recent_is_A():
    papers = [{'year': 2024}, {'year': 2025}, {'year': 2026}]
    grade, ratio = landscape.fallback_grade(papers, 2026)
    assert grade == 'A'
    assert ratio == 1.0


def test_fallback_grade_all_old_is_D():
    papers = [{'year': 2015}, {'year': 2010}, {'year': 2018}]
    grade, _ = landscape.fallback_grade(papers, 2026)
    assert grade == 'D'


def test_fallback_grade_missing_year_field_safe():
    # missing 'year' should not raise — treated as 0 (old)
    papers = [{'doi': 'x'}, {'year': 2025}]
    grade, _ = landscape.fallback_grade(papers, 2026)
    # 1/2 = 0.5 → B (0.4 < ratio ≤ 0.6)
    assert grade == 'B'


# --------- topic_grade (ZeroDivisionError defense) ---------

def test_topic_grade_zero_prior_with_recent_is_A():
    """신진 토픽 — 신진 연구자 케이스 (H3 핵심 방어)."""
    counts = [{'year': 2024, 'works_count': 50}, {'year': 2025, 'works_count': 80}]
    grade, ratio = landscape.topic_grade(counts, 2026)
    assert grade == 'A'
    assert ratio is None  # explicit signal: ratio not computable


def test_topic_grade_all_zero_is_NA():
    counts = []
    grade, ratio = landscape.topic_grade(counts, 2026)
    assert grade == 'N/A'
    assert ratio is None


def test_topic_grade_growing_is_A():
    # last3 mean = (100+120+150)/3 = 123.3, prior3 mean = (50+60+70)/3 = 60
    counts = [
        {'year': 2020, 'works_count': 50}, {'year': 2021, 'works_count': 60},
        {'year': 2022, 'works_count': 70}, {'year': 2023, 'works_count': 100},
        {'year': 2024, 'works_count': 120}, {'year': 2025, 'works_count': 150},
    ]
    grade, ratio = landscape.topic_grade(counts, 2026)
    assert grade == 'A'
    assert ratio > 1.3


def test_topic_grade_declining_is_D():
    counts = [
        {'year': 2020, 'works_count': 200}, {'year': 2021, 'works_count': 180},
        {'year': 2022, 'works_count': 160}, {'year': 2023, 'works_count': 50},
        {'year': 2024, 'works_count': 40}, {'year': 2025, 'works_count': 30},
    ]
    grade, ratio = landscape.topic_grade(counts, 2026)
    assert grade == 'D'


# --------- dominant_topic_for_cluster (post-pivot) ---------

def test_dominant_topic_empty_cluster():
    assert landscape.dominant_topic_for_cluster([]) is None


def test_dominant_topic_no_topic_ids():
    papers = [{'doi': 'x', 'primary_topic_id': '', 'primary_topic_name': ''}]
    assert landscape.dominant_topic_for_cluster(papers) is None


def test_dominant_topic_majority_wins():
    papers = [
        {'primary_topic_id': 'T11048', 'primary_topic_name': 'Bacteriophages'},
        {'primary_topic_id': 'T11048', 'primary_topic_name': 'Bacteriophages'},
        {'primary_topic_id': 'T11048', 'primary_topic_name': 'Bacteriophages'},
        {'primary_topic_id': 'T22222', 'primary_topic_name': 'Other'},
    ]
    result = landscape.dominant_topic_for_cluster(papers)
    assert result is not None
    tid, name, share = result
    assert tid == 'T11048'
    assert name == 'Bacteriophages'
    assert share == 0.75


def test_dominant_topic_below_threshold_returns_none():
    """4가지 다른 topic이 1편씩 → 0.25 < 0.30 threshold → None."""
    papers = [
        {'primary_topic_id': f'T{i}', 'primary_topic_name': f'X{i}'}
        for i in range(4)
    ]
    assert landscape.dominant_topic_for_cluster(papers) is None


def test_dominant_topic_at_and_below_threshold():
    """share == 0.30 (3 of 10) accepted (boundary inclusive). share < 0.30 rejected."""
    # 3 of 10 = exactly 0.30 — accepted (impl uses share < min_ratio for rejection)
    papers_30 = [{'primary_topic_id': 'T1', 'primary_topic_name': 'X'}] * 3 + \
                [{'primary_topic_id': f'T{i}'} for i in range(2, 9)]
    result = landscape.dominant_topic_for_cluster(papers_30)
    assert result is not None and result[0] == 'T1'
    # 2 of 10 = 0.20 — rejected
    papers_20 = [{'primary_topic_id': 'T1'}] * 2 + \
                [{'primary_topic_id': f'T{i}'} for i in range(2, 10)]
    assert landscape.dominant_topic_for_cluster(papers_20) is None


# --------- get_related_labs dedup ---------

def _author(id_, name, inst_name, ror, citations):
    inst = {'display_name': inst_name, 'ror': ror} if inst_name else None
    return {
        'id': f'https://openalex.org/{id_}',
        'display_name': name,
        'cited_by_count': citations,
        'last_known_institutions': [inst] if inst else [],
    }


def test_related_labs_dedup_by_ror():
    """ror_id 같은 5명 → 1개 entry만."""
    mock_authors = [
        _author('A1', 'Alice', 'MIT', 'https://ror.org/042nb2s44', 1000),
        _author('A2', 'Bob', 'Massachusetts Institute of Technology',
                'https://ror.org/042nb2s44', 800),  # same ror, different display
        _author('A3', 'Carol', 'Stanford', 'https://ror.org/00f54p054', 500),
        _author('A4', 'Dave', 'MIT', 'https://ror.org/042nb2s44', 300),
        _author('A5', 'Eve', 'Harvard', 'https://ror.org/03vek6s52', 200),
    ]
    with patch.object(landscape, '_fetch_json', lambda url: {'results': mock_authors}):
        labs = landscape.get_related_labs('T1', exclude_author_id='AXXX',
                                          email='x@example.com', top_n=5)
    # MIT entries dedup → 1 entry; Stanford + Harvard each 1 → 3 total
    assert len(labs) == 3
    ror_ids = [l['ror_id'] for l in labs]
    assert ror_ids.count('https://ror.org/042nb2s44') == 1


def test_related_labs_unknown_kept_separate():
    """institution 정보가 없는 저자들은 dedup하지 않고 각각 별도 entry."""
    mock_authors = [
        _author('A1', 'Alice', None, '', 1000),
        _author('A2', 'Bob', None, '', 800),
        _author('A3', 'Carol', 'MIT', 'https://ror.org/042nb2s44', 500),
    ]
    with patch.object(landscape, '_fetch_json', lambda url: {'results': mock_authors}):
        labs = landscape.get_related_labs('T1', exclude_author_id='AXXX',
                                          email='x@example.com', top_n=5)
    # Alice + Bob (둘 다 Unknown, 각각 entry) + Carol = 3
    assert len(labs) == 3
    unknowns = [l for l in labs if l['institution'] == 'Unknown']
    assert len(unknowns) == 2


def test_related_labs_excludes_self():
    mock_authors = [
        _author('AME', 'me', 'MIT', 'https://ror.org/042nb2s44', 1000),
        _author('A2', 'other', 'Stanford', 'https://ror.org/00f54p054', 500),
    ]
    with patch.object(landscape, '_fetch_json', lambda url: {'results': mock_authors}):
        labs = landscape.get_related_labs('T1', exclude_author_id='AME',
                                          email='x@example.com', top_n=5)
    assert len(labs) == 1
    assert labs[0]['pi'] == 'other'
