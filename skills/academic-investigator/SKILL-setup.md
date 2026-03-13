---
name: academic-investigator-setup
description: "Setup wizard for academic-investigator plugin - installs Python package and configures OpenAlex API credentials"
allowed-tools:
  - Bash
  - Read
  - Write
---

# Academic Investigator Setup

This skill sets up the academic-investigator CLI and configures credentials.
Run `/academic-investigator-setup` after installing the plugin.

## Setup Procedure

Execute the following steps IN ORDER. Do NOT skip any step.

### Step 1: Check Python Version

```bash
python3 --version
```

Requires Python 3.11+. If not available, tell the user:
> "Python 3.11 이상이 필요합니다. pyenv install 3.11 또는 시스템 패키지 매니저로 설치해주세요."

### Step 2: Install the Package

```bash
pip install "academic-investigator @ git+https://github.com/kyuwon-shim-ARL/academic-investigator.git"
```

If `pip` fails or shows "externally managed" error, try:
```bash
pip install --user "academic-investigator @ git+https://github.com/kyuwon-shim-ARL/academic-investigator.git"
```

If that also fails, try with `pipx`:
```bash
pipx install "git+https://github.com/kyuwon-shim-ARL/academic-investigator.git"
```

### Step 3: Verify Installation

```bash
acad-inv --version
```

Expected output: `acad-inv 0.1.0` (or higher).
If command not found, check PATH includes pip install location.

### Step 4: Configure OpenAlex Email

Ask the user:
> "OpenAlex API의 polite pool을 사용하려면 이메일을 설정해야 합니다 (무료, 가입 불필요)."
> "Please provide your email for OpenAlex polite pool access (free, no signup needed)."

Then create the config file:

```bash
mkdir -p ~/.config/academic-investigator
cat > ~/.config/academic-investigator/config.toml << 'TOML'
[openalex]
email = "USER_PROVIDED_EMAIL"
TOML
```

Replace `USER_PROVIDED_EMAIL` with the actual email the user provides.

If the user declines to provide email, skip this step and note:
> "이메일 없이도 사용 가능하지만, 속도 제한이 있을 수 있습니다."

### Step 5: Quick Smoke Test

Run a red-flags test (no API call needed):

```bash
acad-inv --format json red-flags "Test" --type person -a "Test Univ" 2>&1 | head -5
```

Verify it outputs valid JSON.

### Step 6: Report Success

Tell the user:

**한글:**
> 설정 완료! 사용 방법:
> - `/academic-investigator "연구자이름" 소속기관` — 연구자 검증
> - `/academic-investigator lab "연구실이름" --pi "PI이름"` — 연구실 조사
> - `/academic-investigator org "회사이름"` — 기관 조사

**English:**
> Setup complete! Usage:
> - `/academic-investigator "Researcher Name" Affiliation` — Researcher check
> - `/academic-investigator lab "Lab Name" --pi "PI Name"` — Lab assessment
> - `/academic-investigator org "Company Name"` — Organization due diligence
