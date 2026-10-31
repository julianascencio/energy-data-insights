"""Extract the reviewed PVGIS 6 request contract from a downloaded OpenAPI JSON.

No network calls. Review upstream changes before replacing the packaged snapshot.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

URL = "https://photovoltaic-geographic-information-system.ec.europa.eu/api/v6/openapi.json"


def extract(source: Path, output: Path, verified_at: str) -> None:
    raw = source.read_bytes()
    spec = json.loads(raw)
    definitions = spec["components"]["schemas"]

    def simplify(schema: dict) -> dict:
        if "$ref" in schema:
            schema = definitions[schema["$ref"].rsplit("/", 1)[1]] | {
                k: v for k, v in schema.items() if k != "$ref"
            }
        result = {
            k: v
            for k, v in schema.items()
            if k
            in {
                "type",
                "enum",
                "minimum",
                "maximum",
                "exclusiveMinimum",
                "exclusiveMaximum",
                "format",
                "default",
                "required",
                "contentMediaType",
                "minItems",
                "maxItems",
            }
        }
        for key in ("anyOf", "oneOf"):
            if key in schema:
                result[key] = [simplify(item) for item in schema[key]]
        if "items" in schema:
            result["items"] = simplify(schema["items"])
        return result

    operations = {}
    schemas = {}
    schema_keys = {}
    for path, methods in spec["paths"].items():
        for method, operation in methods.items():
            parameters = {p["name"]: simplify(p["schema"]) for p in operation.get("parameters", [])}
            required = [p["name"] for p in operation.get("parameters", []) if p.get("required")]
            if method == "post":
                body = operation["requestBody"]["content"]["multipart/form-data"]["schema"]
                body = definitions[body["$ref"].rsplit("/", 1)[1]]
                parameters = {k: simplify(v) for k, v in body["properties"].items()}
                required = body.get("required", [])
            parameter_ids = {}
            for name, schema in parameters.items():
                key = json.dumps(schema, sort_keys=True)
                if key not in schema_keys:
                    schema_keys[key] = f"s{len(schemas)}"
                    schemas[schema_keys[key]] = schema
                parameter_ids[name] = schema_keys[key]
            operations[f"{method.upper()} {path}"] = {
                "parameters": parameter_ids,
                "required": required,
                "response_media_types": list(operation["responses"]["200"]["content"]),
            }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "source_url": URL,
                "source_sha256": hashlib.sha256(raw).hexdigest(),
                "verified_at": verified_at,
                "version": spec["info"]["version"],
                "operations": operations,
                "schemas": schemas,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--verified-at", required=True)
    args = parser.parse_args()
    extract(args.source, args.output, args.verified_at)
