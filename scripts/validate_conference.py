#!/usr/bin/env python3
"""Conference output validator (D5 + H1).

Pure-Python, no LLM required. Checks:
  1. Name-title leakage  -- [a-z][A-Z] glue or >3 words in a name field
  2. SoT join coverage   -- presentationCode in output vs master.json (phantom/missing)
  3. Identity cross-check -- output name vs SoT name (token agreement)
  4. Array count parity  -- anchors/anchors_en, prediction/prediction_en

HALT semantics (H1):
  Any CRITICAL finding causes a non-zero exit. warn-and-proceed is forbidden.
  All gate firings are logged to stderr and optionally to a log file.

Usage:
  python scripts/validate_conference.py <output.json> <master.json> [--log FILE]

Exit codes:
  0 — all checks passed (or only WARNING-level findings)
  1 — CRITICAL findings detected; output must not be used
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# Token helpers (mirrors reresolve.py / openalex.py)
# ---------------------------------------------------------------------------

def _norm_tokens(s: str) -> Set[str]:
    s = re.sub(r"[‐-―\-]", " ", s or "")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return {t for t in re.sub(r"[^a-z ]", " ", s.lower()).split() if len(t) > 1}


def name_token_agreement(output_name: str, sot_name: str) -> bool:
    """Return True when the two names share at least one non-trivial token."""
    a, b = _norm_tokens(output_name), _norm_tokens(sot_name)
    return bool(a & b)


# ---------------------------------------------------------------------------
# Check 1: Name-title leakage
# ---------------------------------------------------------------------------

_GLUE_RE = re.compile(r"[a-z][A-Z]")


def check_name_title_leakage(name: str) -> Optional[str]:
    """Return a description of the leakage problem, or None if clean."""
    if _GLUE_RE.search(name):
        return f"camelCase glue detected (title text leaked into name): {name!r}"
    word_count = len(name.split())
    if word_count > 3:
        return f"name has {word_count} words (>3), title text may be appended: {name!r}"
    return None


# ---------------------------------------------------------------------------
# Check 2: SoT join coverage
# ---------------------------------------------------------------------------

def check_sot_coverage(
    output_codes: Set[str], master_codes: Set[str]
) -> Tuple[Set[str], Set[str]]:
    """Return (phantom_codes, missing_codes).

    phantom  = in output but NOT in master (invented code)
    missing  = in master but NOT in output (dropped speaker)
    """
    phantom = output_codes - master_codes
    missing = master_codes - output_codes
    return phantom, missing


# ---------------------------------------------------------------------------
# Check 3: Identity cross-check
# ---------------------------------------------------------------------------

def check_identity(output_name: str, sot_name: str) -> Optional[str]:
    """Return error description if names do not token-agree, else None."""
    if not name_token_agreement(output_name, sot_name):
        return (
            f"Identity mismatch: output name {output_name!r} "
            f"does not token-agree with SoT name {sot_name!r}"
        )
    return None


# ---------------------------------------------------------------------------
# Check 4: Array count parity
# ---------------------------------------------------------------------------

def check_array_parity(record: Dict[str, Any]) -> List[str]:
    """Check that paired array fields have equal lengths.

    Pairs: (anchors, anchors_en), (prediction, prediction_en)
    """
    issues = []
    for field_a, field_b in [("anchors", "anchors_en"), ("prediction", "prediction_en")]:
        val_a = record.get(field_a)
        val_b = record.get(field_b)
        if val_a is None and val_b is None:
            continue  # neither field present — ok
        len_a = len(val_a) if isinstance(val_a, list) else None
        len_b = len(val_b) if isinstance(val_b, list) else None
        if len_a != len_b:
            issues.append(
                f"Array parity mismatch: {field_a}({len_a}) != {field_b}({len_b})"
            )
    return issues


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

class GateLogger:
    def __init__(self, log_path: Optional[str] = None) -> None:
        self._log_path = log_path
        self._lines: List[str] = []

    def log(self, severity: str, check: str, detail: str) -> None:
        ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        line = f"{ts} [{severity}] [{check}] {detail}"
        self._lines.append(line)
        print(line, file=sys.stderr)

    def flush(self) -> None:
        if self._log_path and self._lines:
            with open(self._log_path, "a", encoding="utf-8") as f:
                for line in self._lines:
                    f.write(line + "\n")


# ---------------------------------------------------------------------------
# Main validation
# ---------------------------------------------------------------------------

def validate(output_path: str, master_path: str, log_path: Optional[str] = None) -> int:
    """Run all checks. Return exit code (0=ok, 1=critical)."""
    logger = GateLogger(log_path)
    critical_count = 0

    # Load files
    try:
        with open(output_path, encoding="utf-8") as f:
            output = json.load(f)
    except Exception as e:
        logger.log("CRITICAL", "load", f"Cannot load output file {output_path!r}: {e}")
        logger.flush()
        return 1

    try:
        with open(master_path, encoding="utf-8") as f:
            master_raw = json.load(f)
    except Exception as e:
        logger.log("CRITICAL", "load", f"Cannot load master file {master_path!r}: {e}")
        logger.flush()
        return 1

    # master.json may be a list or a dict with a "speakers" key
    if isinstance(master_raw, list):
        master_records = master_raw
    elif isinstance(master_raw, dict):
        master_records = master_raw.get("speakers", [master_raw])
    else:
        logger.log("CRITICAL", "load", "master.json has unexpected structure (not list or dict)")
        logger.flush()
        return 1

    master_by_code: Dict[str, Dict[str, Any]] = {}
    for rec in master_records:
        code = rec.get("presentationCode")
        if code:
            master_by_code[code] = rec

    master_codes = set(master_by_code.keys())

    # output may be a list of speaker records or wrapped in a dict
    if isinstance(output, list):
        output_records = output
    elif isinstance(output, dict):
        output_records = output.get("speakers", [output])
    else:
        logger.log("CRITICAL", "load", "output.json has unexpected structure")
        logger.flush()
        return 1

    # Build output index
    output_codes: Set[str] = set()
    for rec in output_records:
        code = rec.get("presentationCode")
        if code:
            output_codes.add(code)

    # ---- Check 2: SoT coverage ----
    if master_codes:
        phantom, missing = check_sot_coverage(output_codes, master_codes)
        for code in sorted(phantom):
            logger.log("CRITICAL", "sot_coverage", f"Phantom code in output (not in master): {code}")
            critical_count += 1
        for code in sorted(missing):
            logger.log("WARNING", "sot_coverage", f"Missing code in output (in master but absent): {code}")

    # ---- Per-record checks ----
    for rec in output_records:
        code = rec.get("presentationCode", "<no_code>")
        name = rec.get("name", "")

        # Check 1: name-title leakage
        if name:
            leak = check_name_title_leakage(name)
            if leak:
                logger.log("CRITICAL", "name_leakage", f"[{code}] {leak}")
                critical_count += 1

        # Check 3: identity cross-check vs SoT
        sot = master_by_code.get(code)
        if sot and name:
            sot_name = sot.get("name", "")
            if sot_name:
                id_err = check_identity(name, sot_name)
                if id_err:
                    logger.log("CRITICAL", "identity", f"[{code}] {id_err}")
                    critical_count += 1

        # Check 4: array parity
        for issue in check_array_parity(rec):
            logger.log("CRITICAL", "array_parity", f"[{code}] {issue}")
            critical_count += 1

    logger.flush()

    if critical_count == 0:
        print(
            f"validate_conference: PASSED ({len(output_records)} records checked, "
            f"{len(master_codes)} master codes)",
            file=sys.stderr,
        )
        return 0
    else:
        print(
            f"validate_conference: HALT — {critical_count} CRITICAL finding(s). "
            "Output must not be used.",
            file=sys.stderr,
        )
        return 1


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate conference output JSON against master.json (D5/H1).",
        epilog=(
            "Exit 0 = all clear.  Exit 1 = CRITICAL findings; output is HALTED.\n"
            "HALT semantics: any CRITICAL finding causes non-zero exit. "
            "warn-and-proceed is forbidden."
        ),
    )
    parser.add_argument("output", help="Path to conference output JSON")
    parser.add_argument("master", help="Path to *_master.json (SoT)")
    parser.add_argument("--log", metavar="FILE", help="Append gate log to FILE")
    args = parser.parse_args()

    sys.exit(validate(args.output, args.master, log_path=args.log))


if __name__ == "__main__":
    main()
