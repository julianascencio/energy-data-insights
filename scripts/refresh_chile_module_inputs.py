"""Acquire fresh Chile registry/static maps for review without replacing the pinned study."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from energy_data_retrieval.transport import HTTPClient


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_directory
    output.mkdir(parents=True, exist_ok=False)
    data = Path(__file__).resolve().parents[1] / "examples/analysis/data/chile_modules"
    manifest = json.loads((data / "chile_module_study.json").read_text())
    requests = [("registry.json", manifest["registry_source"]["url"], {})]
    for key, site in manifest["sites"].items():
        for label in ("detail_capture", "overview_capture"):
            if label in site:
                capture = site[label]
                requests.append((capture["filename"], capture["endpoint"], capture["request"]))
        metadata = site["detail_capture"]["metadata_request"]
        requests.append((f"{key}_metadata.json", metadata["endpoint"], metadata["parameters"]))
    hosts = frozenset({"api-infotecnica.coordinador.cl", "server.arcgisonline.com"})
    with HTTPClient(hosts) as http:
        for filename, url, parameters in requests:
            response = http.request_bytes(url, {k: str(v) for k, v in parameters.items()})
            if filename.endswith(".png") and not response.value.startswith(b"\x89PNG\r\n\x1a\n"):
                raise ValueError("Provider did not return a PNG; do not count an error response")
            if filename.endswith(".json"):
                payload = json.loads(response.value)
                if isinstance(payload, dict) and "error" in payload:
                    raise ValueError("Provider returned an error; refresh remains incomplete")
            (output / filename).write_bytes(response.value)
            (output / f"{filename}.meta.json").write_text(
                json.dumps(asdict(response.record), indent=2) + "\n"
            )
    (output / "REVIEW_REQUIRED.txt").write_text(
        "New acquisition, NOT a validated replacement study.\n"
        "Re-rank the registry; visually verify image content, dates, scope and module frames.\n"
        "A valid PNG can still be a provider placeholder. Retain source attribution.\n"
    )


if __name__ == "__main__":
    main()
