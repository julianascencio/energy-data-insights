"""Native request validation; values are never silently unit-converted."""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any


def validate(value: object, schema: dict[str, Any], name: str) -> None:
    alternatives = schema.get("anyOf", schema.get("oneOf"))
    if alternatives:
        for option in alternatives:
            try:
                validate(value, option, name)
                return
            except ValueError:
                continue
        raise ValueError(f"Invalid {name}: value does not match the provider contract")
    kind = schema.get("type")
    valid = {
        "number": type(value) in (int, float),
        "integer": type(value) is int,
        "boolean": type(value) is bool,
        "string": isinstance(value, str),
        "array": isinstance(value, (list, tuple)),
        "null": value is None,
    }.get(kind, False)
    if not valid:
        raise ValueError(f"{name} must have type {kind}")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{name} must be one of {schema['enum']}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite")
        if value < schema.get("minimum", -math.inf) or value > schema.get("maximum", math.inf):
            raise ValueError(f"{name} is outside the provider range")
        if value <= schema.get("exclusiveMinimum", -math.inf):
            raise ValueError(f"{name} must exceed {schema['exclusiveMinimum']}")
        if value >= schema.get("exclusiveMaximum", math.inf):
            raise ValueError(f"{name} must be below {schema['exclusiveMaximum']}")
    if isinstance(value, str):
        if len(value) > 65536 or any(ord(c) < 32 for c in value):
            raise ValueError(f"{name} must be bounded text without control characters")
        if schema.get("format") == "date-time":
            try:
                datetime.fromisoformat(value)
            except ValueError:
                raise ValueError(f"{name} must be an ISO datetime") from None
    if isinstance(value, (list, tuple)):
        if not schema.get("minItems", 1) <= len(value) <= schema.get("maxItems", 10000):
            raise ValueError(f"{name} has an invalid number of items")
        for item in value:
            validate(item, schema["items"], name)


def encode(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)
