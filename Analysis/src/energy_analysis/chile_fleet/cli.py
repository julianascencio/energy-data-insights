"""Command-line entry points with explicit file-based, reproducible configuration."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import load_config, utc_datetime
from .demo import create_demo
from .io import json_safe
from .pipeline import run_fleet
from .prepare import prepare_inputs
from .reference import compare_references
from .reports import generate_reports


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Reproducible Chile PV fleet analysis")
    commands = root.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", help="Join site-level generation and weather products")
    prepare.add_argument("--generation", required=True, type=Path)
    prepare.add_argument("--weather", required=True, type=Path)
    prepare.add_argument("--sites", required=True, type=Path)
    prepare.add_argument("--output", required=True, type=Path)
    run = commands.add_parser("run", help="Run all supplied registry sites using a TOML config")
    run.add_argument("--config", required=True, type=Path)
    run.add_argument("--reports", action="store_true", help="Build reports below the run output")
    demo = commands.add_parser("demo", help="Generate and analyze explicitly synthetic inputs")
    demo.add_argument("--output", required=True, type=Path)
    demo.add_argument("--algorithm", choices=("physics", "lightgbm"), default="physics")
    demo.add_argument("--reports", action="store_true", help="Build reports below the run output")
    compare = commands.add_parser(
        "compare", help="Compare supplied frozen references without fitting"
    )
    compare.add_argument("--hourly", required=True, type=Path)
    compare.add_argument("--sites", required=True, type=Path)
    compare.add_argument("--output", required=True, type=Path)
    compare.add_argument("--start", required=True, type=utc_datetime)
    compare.add_argument("--end", required=True, type=utc_datetime)
    compare.add_argument(
        "--reference",
        choices=("expected_mwh", "expected_final_mwh", "expected_heldout_mwh"),
        default="expected_mwh",
    )
    compare.add_argument("--minimum-coverage", type=float, default=0.8)
    compare.add_argument("--tolerance", type=float, default=0.2)
    compare.add_argument(
        "--reports", action="store_true", help="Build reports below the run output"
    )
    compare.add_argument(
        "--synthetic", action="store_true", help="Label comparison inputs synthetic"
    )
    report = commands.add_parser("report", help="Render a completed analysis without refitting")
    report.add_argument(
        "--run", required=True, type=Path, help="Completed run/comparison directory"
    )
    report.add_argument("--output", type=Path, help="Defaults to <run>/reports")
    report.add_argument("--title", default="Chile PV fleet performance")
    report.add_argument("--synthetic", action="store_true", default=None)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare_inputs(args.generation, args.weather, args.sites, args.output)
            print(json.dumps({"complete": result["complete"], "output": str(args.output)}))
            return 0
        if args.command == "report":
            result = generate_reports(
                args.run, args.output, title=args.title, synthetic=args.synthetic
            )
            print(json.dumps(json_safe(result), indent=2, allow_nan=False))
            return 0
        if args.command == "compare":
            result = compare_references(
                args.hourly,
                args.sites,
                args.output,
                start=args.start,
                end=args.end,
                reference=args.reference,
                minimum_reference_coverage=args.minimum_coverage,
                relative_tolerance=args.tolerance,
                data_kind="synthetic" if args.synthetic else "unspecified",
            )
            if args.reports:
                generate_reports(args.output, synthetic=True if args.synthetic else None)
            print(json.dumps(json_safe(result["summary"]), indent=2, allow_nan=False))
            return 0
        if args.command == "demo":
            config = create_demo(args.output, algorithm=args.algorithm)
        else:
            config = load_config(args.config)
        result = run_fleet(config, progress=lambda message: print(message, file=sys.stderr))
        if args.reports:
            generate_reports(config.output_path)
        print(json.dumps(json_safe(result["summary"]), indent=2, allow_nan=False))
        return 0
    except (ValueError, OSError) as error:
        print(f"Analysis failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
