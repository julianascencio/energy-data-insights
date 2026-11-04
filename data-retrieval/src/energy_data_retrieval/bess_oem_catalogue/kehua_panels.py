"""Stage reviewed Kehua skid/PCS/cabinet panels without interpreting model codes."""

import re
from html import unescape
from typing import Any


def parse_panels(
    content: bytes, *, expected_models: list[str], expected_fields: set[str] | list[set[str]]
) -> list[dict[str, Any]]:
    """Require exact identities, complete paired panels and reviewed field labels.

    Values remain native: channel currents, component IP classes and efficiency
    boundaries must be reviewed before promotion to scalar catalogue fields.
    """
    text = content.decode("utf-8-sig")
    headers = re.findall(r'<div class="xx_xh">\s*((?:<a[^>]*>.*?</a>\s*)+)</div>', text, re.S)
    if len(headers) != 1:
        raise ValueError("Expected one model header")
    models = [unescape(x).strip() for x in re.findall(r"<a[^>]*>(.*?)</a>", headers[0], re.S)]
    if not models or models != expected_models or len(set(models)) != len(models):
        raise ValueError("Model identity/order mismatch")
    field_sets = (
        [expected_fields] * len(models) if isinstance(expected_fields, set) else expected_fields
    )
    if len(field_sets) != len(models):
        raise ValueError("Expected one field set per model")
    panels = re.findall(r'<div class="info_list[^\"]*">(.*?)<div class="g-btn-red">', text, re.S)
    if len(panels) != len(models):
        raise ValueError("Panel count mismatch")
    result = []
    for model, panel, allowed in zip(models, panels, field_sets, strict=True):
        pairs = re.findall(
            r'<div class="attr_item"\s*>\s*<p>(.*?)</p>\s*<p>(.*?)</p>\s*</div>', panel, re.S
        )
        fields = {unescape(k).strip(): unescape(v).strip() for k, v in pairs}
        if len(fields) != len(pairs) or len(pairs) != panel.count('class="attr_item"'):
            raise ValueError("Duplicate or malformed field")
        # Numeric bounds such as <100ms are facts, not HTML. Retain the bound
        # verbatim while still rejecting tags, comments and processing markup.
        if set(fields) != allowed or any(
            not v or re.search(r"<\s*(?:/?[A-Za-z]|[!?])", v) for v in fields.values()
        ):
            raise ValueError("Unreviewed layout or empty/markup value")
        result.append({"model": model, "fields": fields})
    return result
