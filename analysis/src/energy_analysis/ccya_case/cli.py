"""Command-line entry points for the applied CCYA analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config
from .demo import SEED, create_demo
from .pipeline import run_case


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="Run a labelled synthetic thesis-style case")
    demo.add_argument("--output", type=Path, required=True)
    demo.add_argument("--seed", type=int, default=SEED)
    run = commands.add_parser("run", help="Run an explicit monthly CSV/TOML study")
    run.add_argument("--config", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        path = create_demo(args.output, seed=args.seed) if args.command == "demo" else args.config
        config = load_config(path)
        result = run_case(config)
    except (ValueError, OSError) as exc:
        parser.exit(2, f"CCYA study failed: {exc}\n")
    print(
        json.dumps(
            {
                "complete": result["complete"],
                "data_kind": result["data_kind"],
                "report": str(config.output_path / "reports" / "index.html"),
                "summary": str(config.output_path / "summary.csv"),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
