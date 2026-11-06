"""Offline BOE discovery and reviewed notice staging with technology boundaries.

The index adapter selects every Series A notice mentioning wind; it never reads
MW or a lifecycle from the title. Reviewed facts require checksummed originals.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from html.parser import HTMLParser
from typing import Any
from urllib.parse import parse_qs, urljoin, urlsplit

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

from .catalogue import stable_id
from .gppd import evidence_record

REFERENCE_IDS = ("boe_a_2026_22987",)


def _registry_keys(row: dict[str, Any]) -> set[tuple[str, str]]:
    """Only project/procedure registries, never a notice shared by several farms.

    A shared procedure triggers review; it does not prove two farms are identical.
    Namespace and identifier are exact: no punctuation or case-based aliasing.
    """
    identifiers = json.loads(row.get("external_ids_json") or "{}")
    return {
        (namespace, value)
        for namespace, value in identifiers.items()
        if namespace in {"gencat_expediente", "miteco_expediente"}
        and isinstance(value, str)
        and value.strip()
    }


def _normalized(text: str) -> str:
    return " ".join(
        "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
        .casefold()
        .split()
    )


class _Index(HTMLParser):
    def __init__(self, series: str = "A") -> None:
        super().__init__()
        self.series = series
        self.depth = 0
        self.paragraph = False
        self.title: list[str] = []
        self.ids: set[str] = set()
        self.notices: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "li":
            if self.depth:
                self.depth += 1
            elif "dispo" in (values.get("class") or "").split():
                self.depth = 1
                self.title, self.ids = [], set()
        if self.depth and tag == "p":
            self.paragraph = True
        if self.depth and tag == "a":
            url = urlsplit(values.get("href") or "")
            if url.path == "/diario_boe/txt.php":
                self.ids.update(parse_qs(url.query).get("id", []))

    def handle_data(self, data: str) -> None:
        if self.paragraph:
            self.title.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "p":
            self.paragraph = False
        if tag == "li" and self.depth:
            self.depth -= 1
            if not self.depth:
                title = " ".join("".join(self.title).split())
                if "eolic" in _normalized(title):
                    if len(self.ids) != 1:
                        raise ValueError("Wind notice requires one document identifier")
                    ident = next(iter(self.ids))
                    if re.fullmatch(rf"BOE-{self.series}-\d{{4}}-\d+", ident):
                        self.notices.append({"notice_id": ident, "title": title})


def select_wind_notices(html: str, *, series: str = "A") -> list[dict[str, str]]:
    """Select Series A wind mentions, including solar hybrids and auxiliaries.

    Series B announcements require explicit ``series="B"`` selection.
    A selected title is a review candidate, never an automatic project record.
    """
    if "sumario" not in html.casefold() or "dispo" not in html:
        raise ValueError("Expected a complete BOE daily index, not an error/login page")
    if series not in {"A", "B"}:
        raise ValueError("Select exactly one BOE series: A or B")
    parser = _Index(series)
    parser.feed(html)
    parser.close()
    if parser.depth:
        raise ValueError("Truncated BOE index")
    ids = [n["notice_id"] for n in parser.notices]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate BOE notice")
    return parser.notices


def issue_urls(html: str, daily_url: str) -> list[str]:
    """Discover same-day extra issues; callers must fetch every returned URL.

    A default daily index may show only the extraordinary issue. Discovery
    cannot establish completeness of content that has not yet been fetched.
    """
    base = urlsplit(daily_url)
    if (
        base.scheme != "https"
        or base.netloc != "www.boe.es"
        or not re.fullmatch(r"/boe/dias/\d{4}/\d{2}/\d{2}/", base.path)
        or base.query
    ):
        raise ValueError("Expected an official BOE daily directory URL")
    found = {daily_url}

    class Links(HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag != "a":
                return
            href = dict(attrs).get("href", "")
            url = urlsplit(urljoin(daily_url, href))
            query = parse_qs(url.query)
            if (
                url.scheme == base.scheme
                and url.netloc == base.netloc
                and url.path == base.path + "index.php"
                and set(query) == {"d"}
                and len(query["d"]) == 1
                and query["d"][0].isdigit()
            ):
                found.add(urljoin(daily_url, href).split("#")[0])

    Links().feed(html)
    return sorted(found)


def review_daily_indexes(daily_url: str, originals: dict[str, bytes]) -> dict[str, Any]:
    """Replay all discovered issues before declaring a daily title scan complete.

    Missing extra issues fail closed, including when the default issue contains
    no wind titles. Aliased issues may repeat a notice; conflicting titles fail.
    This is title-discovery completeness, not an inventory of every wind project.
    """
    if daily_url not in originals:
        raise ValueError("Missing default daily index")
    expected = set(issue_urls(originals[daily_url].decode("utf-8"), daily_url))
    for raw in originals.values():
        expected.update(issue_urls(raw.decode("utf-8"), daily_url))
    if set(originals) != expected:
        raise ValueError("Missing or unexpected daily issue URLs")
    notices: dict[str, dict[str, str]] = {}
    captures = []
    for url in sorted(originals):
        raw = originals[url]
        text = raw.decode("utf-8")
        for series in ("A", "B"):
            for notice in select_wind_notices(text, series=series):
                ident = notice["notice_id"]
                if ident in notices and notices[ident] != notice:
                    raise ValueError("Conflicting notice titles across issues")
                notices[ident] = notice
        captures.append({"url": url, "sha256": hashlib.sha256(raw).hexdigest()})
    return {
        "daily_url": daily_url,
        "scope": "Complete discovered Series A/B wind-title scan",
        "captures": captures,
        "notices": [notices[key] for key in sorted(notices)],
    }


def stage_boe_notices(
    reviews: list[dict[str, Any]],
    originals: dict[str, bytes],
    existing: list[dict[str, Any]],
    *,
    expected_ids: list[str],
    now: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Stage a complete reviewed partition; keep procedural and plant scopes apart.

    All new records remain excluded from capacity sums until farm boundaries are
    independently reconciled. Existing names require explicit reconciliation.
    """
    ids = [r["notice_id"] for r in reviews]
    if len(ids) != len(set(ids)) or len(expected_ids) != len(set(expected_ids)):
        raise ValueError("Duplicate review/selection identifier")
    if set(ids) != set(expected_ids):
        raise ValueError("Incomplete notice review")
    names = {
        _normalized(r["name"])
        for r in existing
        if r["entity_type"] == "projects" and r.get("country_code") == "ESP"
    }
    record_ids = {r["record_id"] for r in existing}
    registry_keys = set().union(
        *(
            _registry_keys(r)
            for r in existing
            if r["entity_type"] == "projects" and r.get("country_code") == "ESP"
        )
    )
    rows, decisions = [], []
    for review in reviews:
        ident = review["notice_id"]
        if hashlib.sha256(originals[ident]).hexdigest() != review["sha256"]:
            raise ValueError("Original BOE checksum mismatch")
        if "projects" in review:
            if not review["projects"]:
                raise ValueError("Empty multi-project notice")
            for project in review["projects"]:
                child = {k: v for k, v in review.items() if k != "projects"}
                child.update(project)
                if child["notice_id"] != ident or child["sha256"] != review["sha256"]:
                    raise ValueError("Project cannot replace its notice provenance")
                staged, ledger = stage_boe_notices(
                    [child], originals, existing + rows, expected_ids=[ident], now=now
                )
                rows.extend(staged)
                names.update(_normalized(r["name"]) for r in staged)
                record_ids.update(r["record_id"] for r in staged)
                registry_keys.update(key for r in staged for key in _registry_keys(r))
                decisions.extend({**d, "identity": child["identity"]} for d in ledger)
            continue
        if not review.get("values"):
            decisions.append(
                {"notice_id": ident, "decision": "deferred", "reason": review["reason"]}
            )
            continue
        values = dict(review["values"])
        if values.get("country_code") != "ESP" or not values.get("technology"):
            raise ValueError("Reviewed country and turbine technology required")
        target, effect = review["decision_target"], review["decision_effect"]
        if review.get("required_turbine_removals") and any(
            values.get(field) is not None
            for field in ("planned_capacity_mw", "installed_capacity_mw", "turbine_count")
        ):
            raise ValueError(
                "Required turbine removals need a separately reviewed revised design; "
                "retain original proposal and arithmetic in observations"
            )
        if target not in {"wind", "solar", "auxiliary"}:
            raise ValueError("Explicit decision technology boundary required")
        if target != "wind" and values["status"] == "cancelled":
            raise ValueError("Non-wind decision cannot cancel the wind farm")
        if effect in {"application_refusal", "withdrawn"} and values["status"] not in {
            "cancelled",
            "unknown",
        }:
            raise ValueError(
                "Application refusal or withdrawal cannot establish operation or retirement"
            )
        if effect == "public_consultation" and values["status"] not in {"announced", "unknown"}:
            raise ValueError("Public consultation does not establish permission or operation")
        if effect in {"repowering_authorization", "construction_authorization"} and values[
            "status"
        ] not in {
            "permitted",
            "unknown",
        }:
            raise ValueError(
                "Repowering authorization or construction authorization "
                "does not establish replacement operation"
            )
        if effect == "environmental_conditions" and values["status"] == "permitted":
            raise ValueError("Environmental decision alone is not construction authorization")
        if (
            target == "wind"
            and (
                values["status"] in {"announced", "permitted", "cancelled"}
                or effect
                in {
                    "withdrawn",
                    "application_refusal",
                    "public_consultation",
                    "construction_authorization",
                    "repowering_authorization",
                    "environmental_conditions",
                }
            )
            and values.get("installed_capacity_mw") is not None
        ):
            raise ValueError("Proposed authorization MW is not installed capacity")
        if set(values) != set(review["locators"]):
            raise ValueError("Every reviewed field requires a locator")
        rid = stable_id("projects", "BOE", review["identity"])
        shared_keys = _registry_keys(values) & registry_keys
        if shared_keys:
            decisions.append(
                {
                    "notice_id": ident,
                    "decision": "existing_registry_review",
                    "shared_identifiers": [list(key) for key in sorted(shared_keys)],
                    "reason": (
                        "Shared procedure requires farm/phase reconciliation, not automatic merge"
                    ),
                }
            )
            continue
        if rid in record_ids or _normalized(values["name"]) in names:
            decisions.append({"notice_id": ident, "decision": "existing_identity_review"})
            continue
        names.add(_normalized(values["name"]))
        record_ids.add(rid)
        registry_keys.update(_registry_keys(values))
        values.update(
            record_id=rid,
            entity_type="projects",
            record_scope=values.get("record_scope", "farm"),
            aggregation_role="unresolved",
        )
        row = evidence_record(values, source_id=ident, now=now, locator=review["locator"])
        evidence = json.loads(row["evidence_json"])
        for field, locator in review["locators"].items():
            if field in evidence:
                evidence[field].update(locator=locator, publication_date=review["published_at"])
        field_sources = json.loads(row["field_sources_json"])
        for field, observations in review.get("supporting_evidence", {}).items():
            if field not in evidence:
                raise ValueError("Supporting evidence requires an existing factual field")
            for observation in observations:
                sid = observation["source_id"]
                if sid not in ids or not observation.get("locator"):
                    raise ValueError("Supporting notice must be reviewed with a locator")
                row["sources"] = sorted(set(row["sources"] + [sid]))
                field_sources[field] = sorted(set(field_sources[field] + [sid]))
            evidence[field]["supporting_evidence"] = observations
        row["field_sources_json"] = canonical_json(field_sources)
        row["evidence_json"] = canonical_json(evidence)
        rows.append(row)
        decisions.append({"notice_id": ident, "decision": "added", "record_id": rid})
    return sorted(rows, key=lambda r: r["record_id"]), decisions
