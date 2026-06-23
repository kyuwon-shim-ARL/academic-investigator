---
name: academic-investigator-conference
description: "Conference preparation with speaker analysis, session background generation, and attendance recommendations. Uses academic-investigator CLI for speaker metrics. (project)"
allowed-tools:
  - Read
  - Write
  - WebSearch
  - WebFetch
  - Grep
  - Glob
  - Bash
---

# Academic Investigator - Conference Mode v1.0

Companion skill for `academic-investigator`. Handles conference-specific protocols.

## 1. Conference Initialization

### 1a. Authoritative Source Discovery (SoT-first — do this before anything else)

Select the highest available data tier and freeze it into `conferences/[ID]_master.json`
(schema: see `SCHEMA-master.md`). Query master.json as **read-only fact**; never let
OpenAlex overwrite or generate primary identity fields.

Source tier ladder (pick highest available):

| Tier | Source | Examples |
|------|--------|---------|
| 1 | Official API / structured JSON from organizer | conference REST API, exported JSON |
| 2 | Structured program data | CSV, XLSX, XML from organizer |
| 3 | PDF program book | Parse only when Tier 1 and 2 unavailable |

**Discovery protocol:**
```
1. Attempt Tier 1: check for official API endpoint or organizer-published JSON.
   Log outcome: "Tier 1 found: <URL>" or "Tier 1 not available: <reason>"
2. If Tier 1 unavailable, attempt Tier 2: look for CSV/XLSX/XML downloads.
   Log: "Tier 2 found: <file>" or "Tier 2 not available: <reason>"
3. If Tier 2 unavailable, fall back to Tier 3: parse PDF program book.
   Log: "Falling back to Tier 3 (PDF): <filename>"
   MUST surface to user: "API/structured data not found — using program book (Tier 3)."
```

**Discovery failure semantics:**
- "No API" (Tier 1 absent) is NOT a failure — it is a known state. Log it, proceed to Tier 2.
- "No structured data" (Tier 2 absent) is NOT a failure — log it, proceed to Tier 3.
- TRUE failure = all three tiers exhausted with no usable data. Surface this to the user immediately; do not proceed.
- Never silently skip a tier. Every attempt must be logged.

### 1b. Initialization steps

1. Ask which conference (name, dates, location)
2. Run Authoritative Source Discovery (§1a); freeze master.json
3. Load config: `Read conferences/[ID].yml` (supplementary metadata only)
4. Confirm with user: data source tier used, speaker count loaded, any tier-fallback warnings

## 2. Speaker Research Protocol

### 2a: Batch CLI Analysis
```bash
acad-inv conference -c conferences/[ID].yml --format json
```
Parse output JSON. For each speaker, check `speaker_type`:

### 2b: Academic Speakers (speaker_type == "academic")
CLI provides: h-index, citations, top papers, impact tier, career metrics, DOIs

Additional WebSearch:
```
WebSearch: "{name} {affiliation} Google Scholar publications"
WebSearch: "{name} {affiliation} recent paper {year-1} {year}"
WebSearch: "{name} lab website"
```

### 2c: Industry Speakers (speaker_type == "industry")
CLI returns `alternative_research` with queries. Execute ALL:
```
WebSearch: "{affiliation} company overview technology"
WebSearch: "{name} {affiliation} CEO interview"
WebSearch: "{affiliation} technology platform products"
WebSearch: "{affiliation} partnerships collaborations"
WebSearch: "{affiliation} funding investment news"
WebSearch: "{name} {affiliation} presentation talk"
```
Collect: company overview, key technology/products, partnerships, market position

### 2d: Research Institute Speakers (speaker_type == "research_institute")
If CLI found profile: use it. If not: combine academic + institute queries:
```
WebSearch: "{name} {affiliation} publications"
WebSearch: "{affiliation} research center projects"
WebSearch: "{name} {affiliation} recent achievements"
```

### 2e: Speaker Checklist Verification
| Speaker | Affiliation | Type | Status |
|---------|-------------|------|--------|
| [name]  | [affil]     | academic/industry/institute | done/pending |

ALL speakers must be "done" before proceeding.

### 2f: OpenAlex Affiliation Gate and openalex_matched Branch (D2/D3/D6)

The CLI enforces an affiliation hard-gate for every author lookup:

**Gate rule**: A candidate is accepted (`openalex_matched=True`) ONLY when BOTH:
1. `name_aligned(query_name, candidate.display_name)` — name tokens overlap
2. `inst_tokens(query_affiliation) ∩ inst_tokens(candidate_institutions) >= 1` — at least one distinctive institution token matches

**openalex_matched=False branch** (D3): When the gate fails, the speaker record is tagged `openalex_matched=false`. For these speakers:
- `landscape` and `prediction` fields are SKIPPED (never generated from a mismatched identity)
- Only abstract-based fields are returned (title, abstract, keywords from master.json)
- `alternative_research` WebSearch queries are generated instead

**Pre-output validation gate** (H1): Before delivering ANY conference document, run:
```bash
python scripts/validate_conference.py <output.json> <master.json>
```
- Exit 0 = validation passed; proceed to output
- Exit 1 = CRITICAL finding(s); **HALT — do not deliver output**
- warn-and-proceed is FORBIDDEN; any critical finding must block delivery

Failure cases that trigger HALT:
- Name-title leakage (`[a-z][A-Z]` glue or >3 words in name field)
- Phantom presentationCode in output (not present in master.json)
- Identity mismatch (output name does not token-agree with SoT name)
- Array count parity failure (anchors/anchors_en or prediction/prediction_en length mismatch)

## 3. Abstract Deep Analysis Protocol

For each speaker's top papers (DOIs from CLI output):
- Fetch abstracts via WebFetch on DOI URLs
- If unavailable: try PubMed, Google Scholar cache

**Extract from each abstract:**
- Research purpose (why)
- Methodology (how)
- Key findings (what)
- Significance (why it matters)

**FORBIDDEN:**
- Title-only summaries ("This paper is about...")
- WebSearch snippet summaries
- Speculative descriptions ("seems to be about...")

**REQUIRED:**
- Specific methods, numbers, results from abstract
- Connection to the conference talk topic

## 4. Terminology Explanation Protocol

**Placement rule:** Explain terms IN CONTEXT where they first appear, NOT in an upfront glossary.

**Format:**
> **[Term]이 뭔가요?**
> - **쓰임**: What it's used for in practice
> - **관계**: How it connects to other concepts
> - **왜 중요**: Why you need to know this

**Quality check before using analogies:**
- [ ] Does the analogy accurately map to the real relationship?
- [ ] Could it cause misunderstanding?
- [ ] Would a direct explanation be clearer?

## 5. Expected Talk Content Deep Inference

**Step 1: Domain Trend Research**
```
WebSearch: "{research_field} trends challenges {year-1} {year}"
```

**Step 2: Research Journey Analysis**
- Sort speaker's top_papers by year
- Map: early research -> mid-career shifts -> recent direction
- Ask: "Why is this researcher presenting THIS topic?"

**Step 3: Combine talk_title + session_title + recent papers**
- Extract keywords from talk title
- Connect to session theme
- Infer content from most recent publications

**Step 4: Write Structured Prediction**
```markdown
### Expected Talk Content (Deep Inference)

#### Part 1: [Introduction - Problem Definition]
[Current state of the field, problem to solve]
**Specific context:** [concrete numbers/examples]

#### Part 2: [Speaker's Approach]
[Methodology from representative papers]
**Key ideas:** [specific methods]

#### Part 3: [Latest Results and Talk Core]
[Inferred from recent papers + talk title]
**Expected new results:** [specific findings]

#### Part 4: [Future Directions and Challenges]
[Unsolved problems, research direction]
```

**FORBIDDEN:**
- Keyword-only lists: "AI, drug discovery, multimodal"
- Vague statements: "Will cover recent research trends"
- Groundless speculation: "Will probably discuss..."

**REQUIRED:**
- Specific technologies/numbers: "Classified 200M structures into 2.3M clusters using Foldseek"
- Paper-based inference: "Extending the method from their 2024 Nature Biotech paper..."
- Domain context: "Given that protein complex prediction is the current challenge..."

## 6. Session-Level Analysis

- Identify themes connecting talks within a session
- Note complementary/contrasting approaches between speakers
- Highlight networking opportunities between related speakers

## 7. Time Conflict Resolution

- Identify parallel sessions with overlapping times
- Rank by relevance to user's stated research interests
- Suggest alternatives for missed sessions
- Note which talks may have recordings available

## 8. Background Document Generation

For each selected session, generate comprehensive background file:
- Session overview (theme, relevance to user)
- Talk-by-talk analysis (speaker profile, expected content, terminology)
- Cross-talk connections within session
- Pre-reading suggestions (top papers from CLI output)
- Questions to ask each speaker
- Networking notes

Save to: `{output_directory}/{prefix}_session_{id}.md`

## 9. Conference Quality Checklist

Before delivering any conference document:
- [ ] ALL speakers have research profiles (no exceptions)
- [ ] Academic speakers: citations, top papers, research trajectory, recent papers
- [ ] Industry speakers: company info, technology, partnerships (via WebSearch)
- [ ] Institute speakers: center info, projects, achievements
- [ ] Key paper abstracts actually read and analyzed (not title-only)
- [ ] Paper descriptions include specific methodology/findings/numbers
- [ ] No speculative expressions ("seems to be about...")
- [ ] Terminology explained in context with use/relation/importance format
- [ ] No upfront glossary (in-context only)
- [ ] Domain trend WebSearch performed for expected talk content
- [ ] Research journey (early -> mid -> recent) analyzed per speaker
- [ ] Talk title + session + recent papers combined for inference
- [ ] Part 1/2/3/4 structure with logical flow for talk predictions
- [ ] Specific numbers/technologies/examples included
- [ ] No superficial bullet-point lists
