---
name: academic-investigator
description: "Unified academic investigation - researcher verification, lab assessment, organization due diligence. Combines OpenAlex API data with web research. Supports Korean/English output. (project)"
allowed-tools:
  - Read
  - Write
  - WebSearch
  - WebFetch
  - Grep
  - Glob
  - Bash
---

# Academic Investigator Skill v1.0

## 0. Pre-flight Check (MUST run before any command)

Before executing ANY `acad-inv` command, run this check:

```bash
command -v acad-inv >/dev/null 2>&1 && echo "INSTALLED" || echo "NOT_INSTALLED"
```

- If `INSTALLED`: proceed to Step 1.
- If `NOT_INSTALLED`: tell the user and auto-install:
  > "acad-inv CLI가 설치되지 않았습니다. 자동으로 설치합니다..."
  > "acad-inv CLI not found. Installing automatically..."
  ```bash
  pip install "academic-investigator @ git+https://github.com/kyuwon-shim-ARL/academic-investigator.git" 2>&1 || pip install --user "academic-investigator @ git+https://github.com/kyuwon-shim-ARL/academic-investigator.git" 2>&1
  ```
  Then verify: `acad-inv --version`
  If still fails, tell the user to run `/academic-investigator-setup` for guided setup.

## 1. Mode Selection

| User Request | Mode | CLI Command |
|---|---|---|
| "연구자 검증" / "researcher check" | profile | `acad-inv profile` |
| "랩 조사" / "lab check" | lab | `acad-inv lab` |
| "협업 파트너 조사" / "collaborator check" | org | `acad-inv org` |
| "학회 준비" / "conference preparation" | → Use `academic-investigator-conference` skill |

## 2. Initialization

사용자의 첫 메시지 언어에 따라 언어를 자동 결정합니다.
Automatically determine language from user's first message.

| Detection | Action |
|---|---|
| 한글 입력 | `--lang ko`, 보고서 한글 출력 |
| English input | `--lang en`, report in English |
| Mixed | Ask user preference |

Before running any CLI command:
1. Check `OPENALEX_EMAIL` env var. If not set, ask user to configure:
   ```bash
   export OPENALEX_EMAIL="user@example.com"
   ```
2. Determine mode from user request
3. Gather required info: target name, affiliation, purpose

## 3. CLI Usage Reference

### Profile (Researcher)
```bash
acad-inv profile "Name" -a "Affiliation" --lang ko --format json
acad-inv profile "Name" -a "Affiliation" --lang en --format md -o report.md
```

### Lab
```bash
acad-inv lab "Lab Name" --pi "PI Name" -a "Affiliation" --format md
```

### Organization
```bash
acad-inv org "Org Name" --type startup --people "Person1" "Person2" --format md
```

### Red Flags (standalone)
```bash
acad-inv red-flags "Name" --type person -a "Affiliation"
acad-inv red-flags "Org" --type org
acad-inv red-flags "PI" --type lab
```

### Parsing JSON Output
The CLI outputs JSON by default. Parse it to extract:
- `profile.metrics.h_index`, `profile.metrics.citation_count`
- `profile.impact_tier.tier` (Elite/Senior/Established/Mid-Career/Early Career)
- `profile.top_papers[]` with DOIs for abstract reading
- `profile.coauthors[]` for network analysis
- `red_flag_queries[]` with ready-to-use WebSearch queries

## 4. Step-by-Step Workflow

### Step 1: Run CLI for Structured Data
Execute the appropriate `acad-inv` command with `--format json`.
Parse the JSON output for metrics, impact tier, and top papers.

### Step 2: WebSearch Supplementation
Run mode-specific WebSearch queries (see Section 5 below).
Use red flag queries from CLI output.

### Step 3: Abstract Deep Analysis (for key papers)
For top papers from CLI output:
- Extract DOIs from `top_papers[].doi`
- WebFetch the DOI URL to read abstract
- Extract: methodology, key findings, significance

### Step 4: Generate Report
Combine CLI data + WebSearch findings:
- Run `acad-inv <mode> --format md --lang <lang>` for base template
- Fill in WebSearch-gathered sections
- Apply language consistently

## 5. Mode-Specific WebSearch Workflows

### 5a: Researcher Mode (~20 queries)

**Education/Career Verification:**
```
WebSearch: "{name} {field} PhD thesis"
WebSearch: "{name} curriculum vitae CV"
WebSearch: "{name} {university} professor"
WebSearch: "{name} LinkedIn profile"
WebSearch: "{name} ORCID"
```

**Grant Funding:**
```
WebSearch: "{name} NIH grant"
WebSearch: "{name} NSF funding"
WebSearch: "{name} 한국연구재단 과제"
WebSearch: "{name} research grant PI"
```

**Society Activities:**
```
WebSearch: "{name} {field} editor"
WebSearch: "{name} keynote invited speaker"
WebSearch: "{name} {field} award"
WebSearch: "{name} {field} society board"
```

**Mentorship/Alumni:**
```
WebSearch: "{name} lab alumni"
WebSearch: "{name} PhD students graduated"
WebSearch: "{name} mentorship"
```

**Red Flags (run all queries from CLI `red-flags` output):**
```
WebSearch: "{name} retraction"
WebSearch: "{name} research misconduct"
WebSearch: "{name} plagiarism"
WebSearch: "Retraction Watch {name}"
WebSearch: "{name} {affiliation} retraction"
WebSearch: "{name} predatory journal"
WebSearch: "{name} self-citation rate"
```

### 5b: Lab Mode (researcher queries for PI + additional)

Run ALL researcher mode queries for PI (section 5a), PLUS:

**Lab Members:**
```
WebSearch: "{lab_name} members"
WebSearch: "{pi_name} lab team"
WebSearch: "{lab_name} people"
```

**Equipment/Infrastructure:**
```
WebSearch: "{lab_name} equipment facilities"
WebSearch: "{pi_name} lab {university} infrastructure"
```

**Alumni Careers (for lab grade refinement):**
```
WebSearch: "{lab_name} alumni"
WebSearch: "{pi_name} former students"
WebSearch: "{pi_name} PhD graduates professor"
```

**Funding (for lab grade refinement):**
```
WebSearch: "{pi_name} research grant {year}"
WebSearch: "{pi_name} {university} funding"
WebSearch: "{pi_name} NIH NSF NRF grant amount"
```

**Lab Culture:**
```
WebSearch: "{lab_name} review"
WebSearch: "{pi_name} mentor"
```

**Lab Red Flags:**
```
WebSearch: "{lab_name} negative review graduate student"
WebSearch: "{pi_name} lab dropout"
WebSearch: "{pi_name} graduation delay"
```

**Lab Grade Refinement Protocol:**
The CLI returns a preliminary lab grade with `confidence: "low"` (h-index only).
After WebSearch, if you find funding or alumni data:
- Display the preliminary grade from CLI
- Note which additional factors were found via WebSearch
- Provide qualitative assessment of whether grade would change
- Example: "예비 등급 A (PI h-index 기준). 연간 연구비 약 5억원 확인 -> 등급 유지 가능성 높음."

### 5c: Organization Mode (~13 queries)

**Company Profile:**
```
WebSearch: "{org_name} company profile"
WebSearch: "{org_name} founding team background"
WebSearch: "{org_name} Crunchbase OR LinkedIn"
WebSearch: "{org_name} funding investment"
WebSearch: "{org_name} technology platform"
```

**Key Personnel:** Run all researcher mode queries (5a) for each person

**Technology Assessment:**
```
WebSearch: "{technology} peer-reviewed publications"
WebSearch: "{technology} patent search"
WebSearch: "{technology} competitors comparison"
WebSearch: "{technology} market size {year}"
```

**Financial:**
```
WebSearch: "{org_name} funding round series"
WebSearch: "{org_name} revenue valuation"
WebSearch: "{org_name} investors"
```

**Red Flags:**
```
WebSearch: "{org_name} lawsuit legal issues"
WebSearch: "{org_name} controversy scandal"
WebSearch: "{founder_name} fraud allegations"
WebSearch: "{org_name} reviews complaints"
WebSearch: "{org_name} former employee reviews"
```

## 6. Report Generation Rules

1. Combine CLI structured data + WebSearch findings
2. Use `acad-inv <mode> --format md --lang <lang>` as base template
3. Fill in WebSearch-gathered sections where it says `[WebSearch required]`
4. Apply language consistently throughout
5. For lab mode: include lab grade with confidence note
6. For org mode: include all key people profiles
7. Always include Red Flags section (even if "none found")
8. **ALWAYS generate BOTH formats** (see Section 6a below)
9. **ALWAYS include "연구 배경지식" section** (see Section 6b below)
10. **ALWAYS generate bilingual outputs** (see Section 6c below)

### 6a. Dual Output: Markdown + Interactive HTML

Every report MUST be generated in two formats:

**Step 0: Determine output directory**
- Default: `./acad-inv-reports/` (created automatically via `mkdir -p`)
- If user specifies a path, use that instead
- All 4 output files go into the same directory

**Step 1: Generate Markdown report**
- Save to `{output_dir}/{subject}_report.md`
- Contains all data, analysis, and background knowledge sections

**Step 2: Generate Interactive HTML report via designer agent**
After the MD report is complete, spawn a designer agent:
```
Agent(subagent_type="oh-my-claudecode:designer", model="sonnet", prompt="
Read the markdown report at {md_path} and create an interactive HTML report at {html_path}.

Design requirements:
- Modern academic dashboard with dark/light mode toggle
- Sticky navigation with smooth scroll
- Researcher profile cards with animated metric counters
- SVG radar chart for multi-dimensional comparison (if multiple researchers)
- Sortable papers table with citation bars and click-to-copy DOI
- Co-author network visualization (CSS/SVG)
- Research background section with story timeline, chapter cards, glossary grid
- DDM/key research highlight cards
- Comparison cards (not just tables) for methodology comparisons
- Survival/experiment data as animated horizontal bars
- Glossary as clickable expandable cards
- Conference prediction cards (if applicable)
- All in single self-contained HTML (no external dependencies)
- Responsive design, print-friendly
- Match report language (Korean or English)
")
```

**File naming convention:**
- `{output_dir}/{subject}_report.md`
- `{output_dir}/{subject}_report.html`

### 6b. Research Background Section (연구 배경지식)

Every report MUST include a plain-language "연구 배경지식" section that explains:

1. **Research Journey** (연구 여정): Each researcher's career as a narrative story
   - Use scientist agent (opus) to deeply analyze key papers and research themes
   - Translate jargon into everyday analogies (e.g., ISR → "식물에게 백신을 맞히는 것")
   - Connect each career stage to the next ("이 발견이 다음 연구로 어떻게 이어졌나")

2. **Key Research Explanation** (핵심 연구 쉬운 설명): Their most important work
   - What it is, why it matters, how it works — all in plain language
   - Comparison tables showing how it differs from existing approaches
   - Experimental results highlighted with clear "so what?" context

3. **Glossary** (용어 사전): Every technical term translated to plain language
   - Format: `전문용어 → 한 문장 쉬운 설명`
   - Include all terms that appear in the report

4. **Conference Prediction** (학회 발표 추론): What they might present
   - 3-5 likely topics with key messages
   - Prerequisites/background knowledge needed for each topic

**Workflow for generating this section:**
```
# Spawn parallel scientist agents for deep paper analysis
Agent(subagent_type="oh-my-claudecode:scientist", model="opus",
      prompt="[연구배경] {researcher_name}의 핵심 논문을 분석하여 비전문가용 설명 작성...")
```

### 6c. Bilingual Output (Korean + English)

Every report MUST be generated in BOTH Korean and English:

**File naming convention (4 files total):**
```
{output_dir}/{subject}_report.md          # Korean markdown
{output_dir}/{subject}_report.html        # Korean interactive HTML
{output_dir}/{subject}_report_EN.md       # English markdown
{output_dir}/{subject}_report_EN.html     # English interactive HTML
```

**Output directory resolution:**
1. If user specifies a path → use that
2. Default → `./acad-inv-reports/` (auto-created via `mkdir -p`)

**Workflow:**
1. Generate Korean MD report first (primary language, most data sources are Korean)
2. Generate Korean HTML via designer agent
3. Generate English MD via executor agent (translate from Korean MD):
```
Agent(subagent_type="oh-my-claudecode:executor", model="sonnet", prompt="
Read the Korean report at {ko_md_path} and create a complete English translation at {en_md_path}.
- Natural professional English, not literal translation
- Keep researcher names in English form, keep DOIs/URLs unchanged
- Narrative sections should read naturally in English
")
```
4. Generate English HTML via designer agent (sed-based approach for large files):
```
Agent(subagent_type="oh-my-claudecode:designer", model="sonnet", prompt="
Read the Korean HTML at {ko_html_path} and create English version at {en_html_path}.
Use cp + sed/python replacement approach to avoid token limits on large HTML files.
Replace all Korean text with English equivalents while keeping identical design/CSS/JS.
Change lang='ko' to lang='en', update profile initials to Latin letters.
")
```

**Translation guidelines:**
- Researcher names: use English romanization (e.g., Choong-Min Ryu)
- Institution names: use official English names (e.g., KRIBB)
- Awards: provide English equivalent with context
- Analogies: adapt culturally if needed, not literal translation
- Keep all URLs, DOIs, journal names unchanged

## 7. Quality Checklist

Before delivering the report:
- [ ] All claims cross-verified (Google Scholar + official pages)
- [ ] Retraction Watch checked for all researchers
- [ ] Field-specific h-index context provided (differs by discipline)
- [ ] No single-metric evaluations (h-index alone is insufficient)
- [ ] All sources cited with links
- [ ] Red Flags section included (even if "none found")
- [ ] Lab grade confidence level noted (lab mode only)
- [ ] Impact tier context explained (not just the label)
- [ ] WebSearch sections all filled (no `[WebSearch required]` remaining)

## 8. Important Notes

- ALWAYS cross-verify Google Scholar with official institution pages
- ALWAYS check Retraction Watch for every researcher investigated
- ALWAYS note field-specific h-index baseline differences
- NEVER evaluate based on single metric
- NEVER cite CV claims without independent verification
- NEVER skip Red Flags section
- OpenAlex email: check `OPENALEX_EMAIL` env var; guide user to set it if missing
- For conference preparation: use `academic-investigator-conference` skill instead
