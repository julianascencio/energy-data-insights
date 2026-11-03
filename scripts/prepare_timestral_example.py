"""Explicitly download a pinned Timestral checkpoint and capture real CPU inference.

Run from the repository root after installing the optional official package:
``uv run --no-sync python scripts/prepare_timestral_example.py --revision MODEL_COMMIT``.
The checkpoint revision is required; no floating model revision is captured.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
from datetime import UTC, datetime
from importlib import import_module
from importlib.metadata import version
from pathlib import Path

from energy_analysis.timestral_case import (
    FUEL_TYPES,
    HORIZON,
    PROVENANCE_NAME,
    SNAPSHOT_NAME,
    evaluate_timestral_case,
    forecast_timestral_case,
    load_timestral_case,
)
from energy_methods.timestral import TIMESTRAL_SOURCE_REVISION, TimestralConnector


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True, help="Full Hugging Face model commit SHA")
    parser.add_argument("--model", default="mistralai/Timestral-5M")
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument(
        "--data-directory",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "examples/connectors/data",
    )
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.revision):
        parser.error("--revision must be a full 40-character model commit SHA")
    torch = import_module("torch")
    hub = import_module("huggingface_hub")
    timestral = import_module("timestral")
    package_directory = Path(timestral.__file__).parent
    installed_source_hashes = {
        path.relative_to(package_directory).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(package_directory.rglob("*.py"))
    }
    torch.set_num_threads(1)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    checkpoint_hashes = {}
    for filename in ("config.json", "model.safetensors", "LICENSE"):
        path = Path(
            hub.hf_hub_download(
                args.model, filename, revision=args.revision, local_files_only=args.local_files_only
            )
        )
        checkpoint_hashes[filename] = hashlib.sha256(path.read_bytes()).hexdigest()
    case = load_timestral_case(args.data_directory)
    connector = TimestralConnector(
        args.model, revision=args.revision, device="cpu", local_files_only=args.local_files_only
    )
    forecast = forecast_timestral_case(case, connector)
    raw = (
        json.dumps(
            {
                "quantile_levels": forecast.quantile_levels,
                "quantiles": forecast.quantiles.tolist(),
            },
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode()
    manifest = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "kind": "real pretrained Timestral inference on an existing attributed EIA capture",
        "model_id": args.model,
        "model_revision": args.revision,
        "model_url": f"https://huggingface.co/{args.model}/tree/{args.revision}",
        "reference_code_revision": TIMESTRAL_SOURCE_REVISION,
        "reference_code_url": f"https://github.com/mistralai/timestral/tree/{TIMESTRAL_SOURCE_REVISION}",
        "installed_source_sha256": installed_source_hashes,
        "checkpoint_sha256": checkpoint_hashes,
        "source_sha256": case.source_sha256,
        "context_sha256": case.context_sha256,
        "known_covariates_sha256": case.covariates_sha256,
        "forecast_sha256": hashlib.sha256(raw).hexdigest(),
        "context_hours": case.context.shape[-1],
        "horizon_hours": HORIZON,
        "target_order": FUEL_TYPES,
        "unit": "MWh per hourly interval (EIA hour-ending UTC labels)",
        "forecast_start_utc": case.profiles.index[-HORIZON].isoformat(),
        "covariates": ["sin(2*pi*UTC_hour/24)", "cos(2*pi*UTC_hour/24)"],
        "options": {"symmetric_averaging": True, "clip_nonnegative": True, "max_context": 32768},
        "device": "cpu",
        "seed": 0,
        "torch_threads": 1,
        "python": platform.python_version(),
        "versions": {
            name: version(name)
            for name in ("timestral", "torch", "numpy", "pandas", "huggingface_hub", "safetensors")
        },
        "limitations": "One 24-hour holdout; historical data may overlap pretraining. "
        "Not evidence of out-of-sample operational skill or calibrated interval coverage.",
        "licences": {"code": "Apache-2.0", "weights": "Modified MIT (see checkpoint LICENSE)"},
    }
    (args.data_directory / SNAPSHOT_NAME).write_bytes(raw)
    (args.data_directory / PROVENANCE_NAME).write_text(json.dumps(manifest, indent=2) + "\n")
    print(evaluate_timestral_case(case, forecast).to_string(index=False))
    print(f"Saved real forecast and provenance in {args.data_directory}")


if __name__ == "__main__":
    main()
