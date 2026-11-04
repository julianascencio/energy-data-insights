"""Regenerate small derived numerical summaries; raw publisher asset stays local."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from energy_analysis.thermal_counterfactual import score_panels, sensitivity_ratios
from energy_data_retrieval.foobot import ARTICLE_URL, SOURCE_URL, fetch_foobot, parse_foobot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Locally saved source asset; otherwise fetch")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.source.read_bytes() if args.source else fetch_foobot().encode("utf-8")
    panels = parse_foobot(raw.decode("utf-8"))
    scores = score_panels(panels)
    args.output.mkdir(parents=True, exist_ok=True)
    scores.to_csv(args.output / "thermal_scores.csv", index=False)
    sensitivity_ratios(scores).to_csv(args.output / "thermal_sensitivity.csv", index=False)
    # Two numerical trajectories illustrate the published January 12 intervention.
    # Do not copy the publisher's JavaScript, prose, charts or interactive UI.
    selected = []
    for p in panels:
        if p.date == "2024-01-12" and p.test == "T2" and p.offset in (0, 60):
            selected.extend(
                {
                    "offset_min": p.offset,
                    "minute": x,
                    "truth_c": y,
                    "median_c": m,
                    "q10_c": lo,
                    "q90_c": hi,
                    "available": u,
                }
                for x, y, m, lo, hi, u in zip(
                    p.minutes, p.truth, p.median, p.lo, p.hi, p.command, strict=True
                )
            )
    pd.DataFrame(selected).to_csv(args.output / "thermal_january12.csv", index=False)
    outputs = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(args.output.glob("thermal_*.csv"))
    }
    provenance = {
        "article": ARTICLE_URL,
        "source": SOURCE_URL,
        "accessed_at": datetime.now(UTC).isoformat(),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "outputs_sha256": outputs,
        "evidence": "Imported published model outputs; not measured building data",
        "reference": "EnergyPlus simulation (publisher run)",
        "prediction": "Timestral-209M (publisher run); no model run performed here",
        "mornings": len({p.date for p in panels}),
        "panels": len(panels),
        "threshold_c": 20.75,
        "consecutive_samples": 2,
        "time_semantics": "Minutes relative to baseline heating start; timezone not supplied",
        "weather": "Simulation weather, not operational archived forecasts",
        "limits": [
            "No EnergyPlus IDF/EPW or original model checkpoint revision supplied",
            "Rounded public trajectories can differ from full precision article metrics",
            "Pointwise q10-q90 is not a comfort-time confidence interval",
            "No energy consumption is supplied; no savings claim is calculated",
            "Public access does not establish a licence for the source asset",
        ],
    }
    (args.output / "thermal_provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(scores.groupby("test")["timing_error_min"].agg(["count", "mean"]))


if __name__ == "__main__":
    main()
