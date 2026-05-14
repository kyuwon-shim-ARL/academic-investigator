#!/usr/bin/env python3
"""academic-investigator: cluster saturation landscape analysis.

Strategy (post-pivot):
- Cluster topic mapping = aggregate paper-attached primary_topic.id (NOT free-text search).
- Saturation = /works?filter=topics.id:Tx&group_by=publication_year (since /topics
  no longer exposes counts_by_year).
- Related labs = /authors?filter=topics.id:Tx (unchanged).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

SCHEMA_VERSION = 1
TOP_N_CLUSTERS = 4
RELATED_LABS_PER_CLUSTER = 5
DOMINANT_TOPIC_MIN_RATIO = 0.30  # at least 30% of cluster's papers must share the topic
RATE_LIMIT_SLEEP = 0.5
RETRY_429_SLEEP = 2.0


def fallback_grade(cluster_papers: list[dict], current_year: int) -> tuple[str, float | None]:
    """Paper-year fallback saturation grade."""
    if not cluster_papers:
        return ('N/A', None)
    total = len(cluster_papers)
    recent = sum(1 for p in cluster_papers if (p.get('year') or 0) >= current_year - 3)
    ratio = recent / total
    if ratio > 0.6:
        return ('A', ratio)
    elif ratio > 0.4:
        return ('B', ratio)
    elif ratio > 0.2:
        return ('C', ratio)
    else:
        return ('D', ratio)


def topic_grade(counts_by_year: list[dict], current_year: int) -> tuple[str, float | None]:
    """Saturation grade from year-count list. counts_by_year: [{year:int, works_count:int}, ...].
    ZeroDivisionError-safe (H3)."""
    by_year = {x.get('year'): x.get('works_count', 0) for x in (counts_by_year or [])}
    last3 = sum(by_year.get(y, 0) for y in range(current_year - 3, current_year)) / 3
    prior3 = sum(by_year.get(y, 0) for y in range(current_year - 6, current_year - 3)) / 3
    if prior3 == 0:
        return ('A', None) if last3 > 0 else ('N/A', None)
    r = last3 / prior3
    if r > 1.3:
        return ('A', r)
    elif r > 0.9:
        return ('B', r)
    elif r > 0.5:
        return ('C', r)
    else:
        return ('D', r)


def dominant_topic_for_cluster(cluster_papers: list[dict],
                               min_ratio: float = DOMINANT_TOPIC_MIN_RATIO
                               ) -> tuple[str, str, float] | None:
    """Aggregate primary_topic_id across cluster papers; return dominant if it
    appears in >= min_ratio of papers. Returns (topic_id, topic_name, share) or None."""
    if not cluster_papers:
        return None
    topic_ids = [p.get('primary_topic_id') for p in cluster_papers if p.get('primary_topic_id')]
    if not topic_ids:
        return None
    counter = Counter(topic_ids)
    top_id, top_count = counter.most_common(1)[0]
    share = top_count / len(cluster_papers)
    if share < min_ratio:
        return None
    # pick display name from any paper that has this topic
    name = ''
    for p in cluster_papers:
        if p.get('primary_topic_id') == top_id:
            name = p.get('primary_topic_name') or ''
            break
    return (top_id, name, share)


def _fetch_json(url: str) -> dict | None:
    """GET JSON with one 429 retry. Returns None on persistent failure."""
    for attempt in (0, 1):
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt == 0:
                time.sleep(RETRY_429_SLEEP)
                continue
            return None
        except Exception:
            return None
    return None


def get_topic_year_counts(topic_id: str, email: str) -> list[dict]:
    """Year-bucketed works_count for a topic. Normalizes group_by response to
    [{year:int, works_count:int}, ...] (matches topic_grade signature)."""
    url = (
        f"https://api.openalex.org/works?filter=topics.id:{topic_id}"
        f"&group_by=publication_year&mailto={email}"
    )
    data = _fetch_json(url)
    if not data:
        return []
    out = []
    for g in (data.get('group_by') or []):
        key = g.get('key')
        try:
            yr = int(key)
        except (TypeError, ValueError):
            continue
        out.append({'year': yr, 'works_count': g.get('count') or 0})
    return out


def get_related_labs(topic_id: str, exclude_author_id: str, email: str,
                     top_n: int = RELATED_LABS_PER_CLUSTER) -> list[dict]:
    """ror_id 우선 dedup. 'Unknown' (institution 정보 부재)은 각각 별도 entry로 유지."""
    url = (
        f"https://api.openalex.org/authors?filter=topics.id:{topic_id}"
        f"&sort=cited_by_count:desc&per_page=15&mailto={email}"
    )
    data = _fetch_json(url)
    if not data:
        return []
    authors = data.get('results') or []
    seen_keys: set[str] = set()
    labs: list[dict] = []
    for author in authors:
        author_id_raw = author.get('id') or ''
        short_id = author_id_raw.split('/')[-1] if author_id_raw else ''
        if short_id == exclude_author_id:
            continue
        inst_list = author.get('last_known_institutions') or []
        if not inst_list:
            inst_name = 'Unknown'
            ror_id = ''
            dedup_key = ''
        else:
            inst = inst_list[0] or {}
            inst_name = inst.get('display_name') or 'Unknown'
            ror_id = (inst.get('ror') or '').strip()
            dedup_key = ror_id if ror_id else inst_name.strip().lower()
        if dedup_key and dedup_key in seen_keys:
            continue
        if dedup_key:
            seen_keys.add(dedup_key)
        labs.append({
            'institution': inst_name,
            'ror_id': ror_id,
            'pi': author.get('display_name') or '',
            'citations': author.get('cited_by_count') or 0,
        })
        if len(labs) >= top_n:
            break
    return labs


def build_landscape(author_id: str, papers: list[dict], communities: list[dict],
                    email: str, current_year: int) -> dict:
    paper_by_doi = {p['doi']: p for p in papers if p.get('doi')}
    sorted_communities = sorted(communities, key=lambda c: c.get('size', 0), reverse=True)
    top_clusters = sorted_communities[:TOP_N_CLUSTERS]

    out_clusters = []
    for c in top_clusters:
        cid = c.get('cluster_id')
        size = c.get('size', 0)
        top_entities = c.get('top_entities') or []
        dois = c.get('dois') or []
        cluster_papers = [paper_by_doi[d] for d in dois if d in paper_by_doi]

        years = sorted(p.get('year') for p in cluster_papers if p.get('year'))
        if not years:
            year_range = 'unknown'
        else:
            y_min, y_max = years[0], years[-1]
            year_range = f"{y_min}-present" if y_max >= current_year - 1 else f"{y_min}-{y_max}"

        label_seed = ' '.join(top_entities[:3]) if top_entities else f"cluster-{cid}"

        dominant = dominant_topic_for_cluster(cluster_papers)
        topic_id: str | None = None
        topic_name: str = label_seed
        topic_share: float | None = None
        saturation: str
        saturation_ratio: float | None
        saturation_source: str
        related_labs: list[dict] = []

        # Sub-niche signal — ALWAYS computed from cluster's own paper-year distribution.
        # Captures saturation within the researcher's specific sub-cluster (papersift Leiden),
        # which is finer-grained than OpenAlex's super-topic.
        sub_grade, sub_ratio = fallback_grade(cluster_papers, current_year)

        if dominant:
            topic_id, topic_name, topic_share = dominant
            time.sleep(RATE_LIMIT_SLEEP)
            counts = get_topic_year_counts(topic_id, email)
            if counts:
                saturation, saturation_ratio = topic_grade(counts, current_year)
                saturation_source = 'openalex'
            else:
                saturation, saturation_ratio = sub_grade, sub_ratio
                saturation_source = 'fallback'
            time.sleep(RATE_LIMIT_SLEEP)
            related_labs = get_related_labs(topic_id, author_id, email)
        else:
            saturation, saturation_ratio = sub_grade, sub_ratio
            saturation_source = 'fallback'

        out_clusters.append({
            'cluster_id': cid,
            'label_seed': label_seed,
            'size': size,
            'year_range': year_range,
            'top_entities': top_entities[:10],
            'topic_id': topic_id,
            'topic_name': topic_name,
            'topic_share': topic_share,
            # Field-level signal (OpenAlex topic-wide saturation, the original)
            'saturation': saturation,
            'saturation_ratio': saturation_ratio,
            'saturation_source': saturation_source,
            # Sub-niche signal (cluster paper-year only, ALWAYS present)
            'saturation_subniche': sub_grade,
            'saturation_subniche_ratio': sub_ratio,
            'related_labs': related_labs,
        })

    return {
        'schema_version': SCHEMA_VERSION,
        'author_id': author_id,
        'fetched_at': _dt.date.today().isoformat(),
        'skipped': False,
        'skip_reason': None,
        'n_papers_total': len(papers),
        'n_clusters_total': len(communities),
        'clusters': out_clusters,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--author-id', required=True)
    p.add_argument('--papers', required=True)
    p.add_argument('--communities', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--email', default='noreply@example.com')
    p.add_argument('--year', type=int, default=_dt.date.today().year)
    args = p.parse_args()

    papers = json.loads(Path(args.papers).read_text())
    communities = json.loads(Path(args.communities).read_text())

    if len(communities) < 2:
        skipped = {
            'schema_version': SCHEMA_VERSION,
            'author_id': args.author_id,
            'fetched_at': _dt.date.today().isoformat(),
            'skipped': True,
            'skip_reason': f'클러스터 {len(communities)}개 (2개 미만)',
            'n_papers_total': len(papers),
            'n_clusters_total': len(communities),
            'clusters': [],
        }
        Path(args.out).write_text(json.dumps(skipped, ensure_ascii=False, indent=2))
        print('[Landscape] skipped — clusters<2', file=sys.stderr)
        return 0

    result = build_landscape(args.author_id, papers, communities, args.email, args.year)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(f'[Landscape] {len(result["clusters"])} clusters analyzed → {args.out}', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
