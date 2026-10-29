"""Run an applied degradation map study using the repository's providers and methods."""

from __future__ import annotations

import argparse
import os
from collections.abc import Sequence
from pathlib import Path

import httpx

from energy_analysis.degradation.config import load_config
from energy_analysis.degradation.pipeline import retrieve, run
from energy_data_retrieval.sources.cru_ts.client import CRU_TS_HOSTS
from energy_data_retrieval.sources.open_meteo.client import OPEN_METEO_HOSTS
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, RetrievalError


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("retrieve", "run", "all"))
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument(
        "--use-environment-proxy",
        action="store_true",
        help="Explicitly use HTTPS_PROXY for this public-data retrieval",
    )
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if args.command != "retrieve" and args.output is None:
            raise ValueError("--output is required for run/all")
        if args.command != "run":
            proxy = None
            if args.use_environment_proxy:
                proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
                if not proxy:
                    raise ValueError("--use-environment-proxy requires HTTPS_PROXY")
            with HTTPClient(
                OPEN_METEO_HOSTS | CRU_TS_HOSTS,
                config=HTTPConfig(
                    minimum_interval_seconds=3,
                    maximum_response_bytes=256 * 1024**2,
                    maximum_retry_seconds=30,
                ),
                cache_directory=args.data_dir / "http-cache",
                transport=httpx.HTTPTransport(proxy=proxy),
            ) as http:
                print(retrieve(config, args.data_dir, http, workers=args.workers))
        if args.command != "retrieve":
            print(run(config, args.data_dir, args.output))
    except (ValueError, TypeError, KeyError, OSError, RetrievalError) as error:
        parser.exit(2, f"Degradation study failed: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
