"""Export the small, attributed gallery fixtures from a completed degradation run."""

import argparse
from pathlib import Path

from energy_analysis.degradation.gallery import prepare_gallery


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-output", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=root / "examples/analysis")
    args = parser.parse_args()
    print(
        prepare_gallery(
            args.study_output,
            args.output,
            root / "examples/analysis/climate_world_boundaries.geojson",
        )
    )


if __name__ == "__main__":
    main()
