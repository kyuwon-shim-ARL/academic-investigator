# `*_master.json` Schema (Authoritative Source of Truth)

All conference master data files (`*_master.json`) MUST conform to this schema.
This is the join key for D2 (affiliation gate), D3 (branch logic), and D5 (validation).

## Required Fields

| Field              | Type   | Description                                                    |
|--------------------|--------|----------------------------------------------------------------|
| `presentationCode` | string | Unique talk identifier; primary join key for all SoT lookups   |
| `name`             | string | Speaker full name exactly as it appears in the program book    |
| `affiliation`      | string | Institution/organization exactly as printed (no normalization) |
| `title`            | string | Presentation/talk title                                        |
| `abstract`         | string | Full abstract text (may be empty string if not available)      |

## Optional Fields

| Field         | Type   | Description                            |
|---------------|--------|----------------------------------------|
| `session`     | string | Session name or code                   |
| `sessionType` | string | e.g. "invited", "oral", "poster"       |
| `keywords`    | array  | Author-supplied keyword list           |

## Source Tier Ladder (D1)

Master data MUST originate from the highest available tier:

1. **Tier 1 — Official API / structured JSON** (e.g. conference JSON export)
2. **Tier 2 — Structured program data** (e.g. CSV, XML, XLSX from organizer)
3. **Tier 3 — PDF program book** (parse only if Tier 1/2 unavailable)

Discovery failure is NOT the same as "no API":
- Log each tier attempt and outcome.
- Surface "API not found, falling back to Tier N" to the user.
- Never silently skip a tier.

## Invariants

- `presentationCode` must be unique within a master file.
- `name` must NOT contain title text (detect with `[a-z][A-Z]` glue or >3 words for a person name).
- `affiliation` must NOT be empty; use `"Unknown"` explicitly if unavailable.
- `abstract` may be empty string but must be present as a key.

## Usage in Gate Logic

- **D2 (OpenAlex affiliation gate)**: `affiliation` from master.json is used to compute `inst_tokens` for hard-gate matching.
- **D3 (branch)**: When `openalex_matched=false`, only abstract-derived fields are returned; `landscape`/`prediction` are skipped.
- **D5 (validate_conference.py)**: Joins output by `presentationCode`; checks name/title leakage, SoT coverage, identity cross-check, array parity.
