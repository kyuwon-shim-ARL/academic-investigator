# Academic Investigator

Claude Code plugin for unified academic investigation — researcher verification, lab assessment, and organization due diligence.

## Installation

```bash
claude plugin add kyuwon-shim-ARL/academic-investigator
```

## Features

- **Researcher profiling** — OpenAlex-based h-index, citations, impact tier, top papers, coauthor network
- **Lab assessment** — PI profile + lab grade (S/A/B/C/D) with confidence levels
- **Organization due diligence** — Key people profiling + institution search + red flag queries
- **Conference speaker analysis** — Batch analyze speakers from YAML config with industry/academic classification
- **Red flag detection** — 24 WebSearch query templates (person/org/lab)
- **Bilingual output** — Korean and English (60+ i18n keys)

## Usage

### As Claude Code Plugin (SKILL.md)

After installation, use the skill in Claude Code:

```
/academic-investigator "김철수" 서울대학교 생명과학부
```

### As CLI

```bash
acad-inv profile "Jane Smith" -a "MIT" --lang en --format md
acad-inv lab "Smith Lab" --pi "Jane Smith" -a "MIT"
acad-inv org "BioTech Inc" --type startup --people "CEO Name"
acad-inv conference -c conference.yml
acad-inv red-flags "John Doe" --type person -a "Harvard"
```

### As Python Library

```python
from academic_investigator import quick_profile

result = quick_profile("Jane Smith", affiliation="MIT")
print(result["impact_tier"]["tier"])  # "Senior Leader"
```

## Impact Tier System

| Tier | H-index | Description |
|------|---------|-------------|
| Elite | 60+ | Top 1% — field-defining researcher |
| Senior Leader | 40-59 | Top 5% — highly influential |
| Established | 20-39 | Solid mid-career researcher |
| Mid-Career | 10-19 | Active and growing |
| Early Career | <10 | Emerging researcher |

## Requirements

- Python >= 3.11
- OpenAlex API (free, email recommended for polite pool)

## License

MIT
