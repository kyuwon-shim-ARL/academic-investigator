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

1. Ask which conference (name, dates, location)
2. Load config: `Read conferences/[ID].yml`
3. Read conference source files (ebook PDF, timetable, etc.)
4. Confirm successful data loading with user

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
