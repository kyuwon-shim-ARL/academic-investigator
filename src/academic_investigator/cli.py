"""Academic Investigator CLI."""
from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

from academic_investigator._version import __version__


def _load_config() -> dict:
    """Load config from ~/.config/academic-investigator/config.toml if it exists."""
    config_path = Path.home() / ".config" / "academic-investigator" / "config.toml"
    if config_path.exists():
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    return {}


def _get_credentials(args) -> tuple[str | None, str | None]:
    """Get email and api_key from args, env vars, or config file."""
    import os
    config = _load_config()
    openalex_config = config.get("openalex", {})

    email = args.email or os.environ.get("OPENALEX_EMAIL") or openalex_config.get("email")
    api_key = getattr(args, 'api_key', None) or os.environ.get("OPENALEX_API_KEY") or openalex_config.get("api_key")

    return email, api_key


def _output_result(result: dict, args) -> None:
    """Output result in requested format."""
    from academic_investigator.reporting.formatters import format_json, format_markdown

    if args.format == "md":
        mode = args.command
        if mode == "profile":
            mode = "researcher"
        output = format_markdown(result, mode, args.lang)
    else:
        output = format_json(result)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Output written to {args.output}", file=sys.stderr)
    else:
        print(output)


def run_profile(args) -> int:
    """Run researcher profile investigation."""
    from academic_investigator.modes.researcher import ResearcherInvestigator

    email, api_key = _get_credentials(args)
    investigator = ResearcherInvestigator(email=email, api_key=api_key)
    result = investigator.investigate(args.name, args.affiliation or "", purpose=args.purpose)

    if result.get("profile", {}).get("status") == "not_found":
        print(f"Author not found: {args.name}", file=sys.stderr)
        return 1

    _output_result(result, args)
    return 0


def run_lab(args) -> int:
    """Run lab investigation."""
    from academic_investigator.modes.lab import LabInvestigator

    email, api_key = _get_credentials(args)
    investigator = LabInvestigator(email=email, api_key=api_key)
    pi_name = args.pi or args.name
    result = investigator.investigate(pi_name, args.affiliation or "", lab_name=args.name, purpose=args.purpose)

    if result.get("pi_profile", {}).get("status") == "not_found":
        print(f"PI not found: {pi_name}", file=sys.stderr)
        return 1

    _output_result(result, args)
    return 0


def run_org(args) -> int:
    """Run organization investigation."""
    from academic_investigator.modes.organization import OrgInvestigator

    email, api_key = _get_credentials(args)
    investigator = OrgInvestigator(email=email, api_key=api_key)
    result = investigator.investigate(args.name, org_type=args.type, key_people=args.people)

    _output_result(result, args)
    return 0


def run_conference(args) -> int:
    """Run conference speaker analysis."""
    from academic_investigator.modes.conference import ConferenceInvestigator

    email, api_key = _get_credentials(args)
    investigator = ConferenceInvestigator(email=email, api_key=api_key)

    if args.config:
        config = investigator.load_config(args.config)
        speakers = investigator._extract_speakers_from_config(config)
    elif args.speakers:
        affiliations = args.affiliations or []
        speakers = [
            {"name": name, "affiliation": affiliations[i] if i < len(affiliations) else "", "talk_title": None, "type": None}
            for i, name in enumerate(args.speakers)
        ]
    else:
        print("Either --config or --speakers is required", file=sys.stderr)
        return 2

    result = investigator.investigate_speakers(speakers)
    _output_result(result, args)
    return 0


def run_red_flags(args) -> int:
    """Run red flag query generation."""
    from academic_investigator.core.red_flags import (
        generate_person_red_flag_queries,
        generate_org_red_flag_queries,
        generate_lab_red_flag_queries,
    )
    from dataclasses import asdict

    if args.type == "person":
        queries = generate_person_red_flag_queries(args.name, args.affiliation)
    elif args.type == "org":
        queries = generate_org_red_flag_queries(args.name)
    elif args.type == "lab":
        queries = generate_lab_red_flag_queries(args.name, args.affiliation)
    else:
        queries = generate_person_red_flag_queries(args.name, args.affiliation)

    result = {"mode": "red_flags", "target": args.name, "type": args.type, "queries": [asdict(q) for q in queries]}
    _output_result(result, args)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="acad-inv", description="Academic Investigator - Unified academic investigation toolkit")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--email", help="Email for OpenAlex polite pool")
    parser.add_argument("--api-key", dest="api_key", help="OpenAlex API key (optional)")
    parser.add_argument("--lang", choices=["ko", "en"], default="ko", help="Output language (default: ko)")
    parser.add_argument("--format", choices=["json", "md"], default="json", help="Output format (default: json)")
    parser.add_argument("-o", "--output", help="Output file path (default: stdout)")

    subparsers = parser.add_subparsers(dest="command")

    # profile
    p_profile = subparsers.add_parser("profile", help="Investigate individual researcher")
    p_profile.add_argument("name", help="Researcher name")
    p_profile.add_argument("--affiliation", "-a", help="Institution name")
    p_profile.add_argument("--purpose", "-p", help="Purpose of investigation")
    p_profile.set_defaults(func=run_profile)

    # lab
    p_lab = subparsers.add_parser("lab", help="Investigate research lab")
    p_lab.add_argument("name", help="Lab name or PI name")
    p_lab.add_argument("--pi", help="PI name (if different from lab name)")
    p_lab.add_argument("--affiliation", "-a", help="Institution name")
    p_lab.add_argument("--purpose", "-p", help="Purpose of investigation")
    p_lab.set_defaults(func=run_lab)

    # org
    p_org = subparsers.add_parser("org", help="Investigate organization")
    p_org.add_argument("name", help="Organization name")
    p_org.add_argument("--type", choices=["company", "startup", "institute", "university"], default="company")
    p_org.add_argument("--people", nargs="*", help="Key people names to investigate")
    p_org.set_defaults(func=run_org)

    # conference
    p_conf = subparsers.add_parser("conference", help="Batch analyze conference speakers")
    p_conf.add_argument("--config", "-c", help="Path to conference YAML config")
    p_conf.add_argument("--speakers", nargs="*", help="Individual speaker names")
    p_conf.add_argument("--affiliations", nargs="*", help="Corresponding affiliations")
    p_conf.set_defaults(func=run_conference)

    # red-flags
    p_rf = subparsers.add_parser("red-flags", help="Generate red flag search queries")
    p_rf.add_argument("name", help="Person or organization name")
    p_rf.add_argument("--type", choices=["person", "org", "lab"], default="person")
    p_rf.add_argument("--affiliation", "-a", help="Affiliation or context")
    p_rf.set_defaults(func=run_red_flags)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    try:
        exit_code = args.func(args)
        sys.exit(exit_code)
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
