#!/usr/bin/env bash
# academic-investigator: cluster saturation landscape (Phase 1)
# Usage:  bash landscape.sh <profile.json>
# Output: stdout = path to ~/.cache/acad-inv/landscape-{author_id}.json (on success)
#         stderr = [Landscape ...] status messages
# Disable: ACAD_INV_LANDSCAPE=0

set -uo pipefail

if [ "${ACAD_INV_LANDSCAPE:-1}" = "0" ]; then
    echo "[Landscape DISABLED] ACAD_INV_LANDSCAPE=0" >&2
    exit 0
fi

PROFILE_JSON="${1:-}"
if [ -z "$PROFILE_JSON" ] || [ ! -f "$PROFILE_JSON" ]; then
    echo "[Landscape SKIP] profile.json not provided or not found: '$PROFILE_JSON'" >&2
    exit 0
fi

if ! command -v papersift >/dev/null 2>&1; then
    echo "[Landscape SKIP] papersift not installed" >&2
    exit 0
fi

CACHE_DIR="${HOME}/.cache/acad-inv"
mkdir -p "$CACHE_DIR"

# AUTHOR_ID 추출 + 검증 (H4: 빈 문자열 방지)
AUTHOR_ID=$(python3 - "$PROFILE_JSON" <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
    raw = d.get('author_id','') or d.get('id','') or ''
    short = raw.split('/')[-1] if raw else ''
    print(short if short.startswith('A') and short[1:].isdigit() else '')
except Exception:
    print('')
PY
)
if [ -z "$AUTHOR_ID" ]; then
    echo "[Landscape SKIP] author_id 추출 실패 (profile.json에 'author_id' 또는 'id' 키 없음)" >&2
    exit 0
fi

OUT_FILE="$CACHE_DIR/landscape-${AUTHOR_ID}.json"
TMP_DIR=$(mktemp -d -t acad-inv-XXXXXX)
trap "rm -rf $TMP_DIR" EXIT

# OpenAlex 100편 fetch + DOI 정규화 (T1 실측: papersift는 short DOI 요구)
PAPERS_FILE="$TMP_DIR/papers.json"
RAW_FILE="$TMP_DIR/works_raw.json"
EMAIL="${OPENALEX_EMAIL:-noreply@example.com}"
# sort=publication_year:desc — recency-weighted sample (citation-sort biases sub-niche
# toward old papers since recent papers haven't accumulated citations yet).
HTTP=$(curl -s --max-time 30 -o "$RAW_FILE" -w "%{http_code}" \
    "https://api.openalex.org/works?filter=author.id:${AUTHOR_ID}&sort=publication_year:desc&per_page=100&mailto=${EMAIL}")
if [ "$HTTP" != "200" ]; then
    echo "[Landscape SKIP] OpenAlex works HTTP $HTTP" >&2
    exit 0
fi

python3 - "$RAW_FILE" "$PAPERS_FILE" <<'PY'
import json, sys
works = json.load(open(sys.argv[1])).get('results', []) or []
def norm_doi(d):
    if not d: return ''
    return d.replace('https://doi.org/', '').replace('http://doi.org/', '').strip().lower()
papers = []
for w in works:
    title = w.get('title') or ''
    if not title: continue
    pt = w.get('primary_topic') or {}
    pt_id = (pt.get('id') or '').split('/')[-1] if pt else ''
    papers.append({
        'doi': norm_doi(w.get('doi') or ''),
        'title': title,
        'year': w.get('publication_year') or 0,
        'citations': w.get('cited_by_count') or 0,
        'primary_topic_id': pt_id,
        'primary_topic_name': pt.get('display_name') or '',
        'primary_topic_score': pt.get('score') or 0,
    })
json.dump(papers, open(sys.argv[2], 'w'))
print(f'[Landscape] {len(papers)} papers fetched', file=sys.stderr)
PY

N_PAPERS=$(python3 -c "import json; print(len(json.load(open('$PAPERS_FILE'))))")
if [ "$N_PAPERS" -lt 10 ]; then
    echo "[Landscape SKIP] 논문 ${N_PAPERS}편 (10편 미만)" >&2
    exit 0
fi

# papersift 클러스터링
CLUSTER_DIR="$TMP_DIR/clusters"
mkdir -p "$CLUSTER_DIR"
if ! papersift cluster "$PAPERS_FILE" --no-topics -o "$CLUSTER_DIR" 2>"$TMP_DIR/papersift.log"; then
    echo "[Landscape SKIP] papersift 실패: $(tail -1 "$TMP_DIR/papersift.log" 2>/dev/null)" >&2
    exit 0
fi

# Python 분석 호출
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
if ! python3 "$SCRIPT_DIR/landscape.py" \
        --author-id "$AUTHOR_ID" \
        --papers "$PAPERS_FILE" \
        --communities "$CLUSTER_DIR/communities.json" \
        --out "$OUT_FILE" \
        --email "$EMAIL" 2>>"$TMP_DIR/landscape_py.log"; then
    echo "[Landscape SKIP] landscape.py 실패: $(tail -3 "$TMP_DIR/landscape_py.log" 2>/dev/null)" >&2
    exit 0
fi

echo "$OUT_FILE"
