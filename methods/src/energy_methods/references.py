"""One citation catalogue for the repository and generated analysis reports.

The thesis is the primary scientific reference. A catalogue entry records where
a work is used; its presence alone does not mean a particular run used its data
or algorithm. Sources marked as background are not implementations.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from importlib.resources import files
from typing import cast
from urllib.parse import quote

PRIMARY_REFERENCE_ID = "ascencio_vasquez_2021_thesis"


@dataclass(frozen=True, slots=True)
class Reference:
    """Verified bibliographic metadata, with a transparent implementation role."""

    id: str
    title: str
    authors: tuple[str, ...]
    year: int | None
    doi: str | None
    url: str
    kind: str
    role: str
    used_by: tuple[str, ...]
    note: str
    publication: str = ""
    volume: str = ""
    issue: str = ""
    pages: str = ""
    institution: str = ""
    verified_at: str = "2026-10-29"

    @property
    def key(self) -> str:
        """BibTeX/citation key; identical to the stable catalogue ID."""
        return self.id

    def as_dict(self) -> dict[str, object]:
        """Return independent JSON-serializable metadata for a report manifest."""
        return asdict(self)


def _load() -> tuple[Reference, ...]:
    raw = json.loads(files("energy_methods").joinpath("references.json").read_text("utf-8"))
    return tuple(
        Reference(
            id=str(item["id"]),
            title=str(item["title"]),
            authors=tuple(item["authors"]),
            year=cast(int | None, item["year"]),
            doi=cast(str | None, item["doi"]),
            url=str(item["url"]),
            kind=str(item["kind"]),
            role=str(item["role"]),
            used_by=tuple(item["used_by"]),
            note=str(item["note"]),
            publication=str(item.get("publication", "")),
            volume=str(item.get("volume", "")),
            issue=str(item.get("issue", "")),
            pages=str(item.get("pages", "")),
            institution=str(item.get("institution", "")),
            verified_at=str(item["verified_at"]),
        )
        for item in raw
    )


REFERENCES = _load()


def get_references(ids: Iterable[str] | None = None) -> tuple[Reference, ...]:
    """Select known IDs in catalogue order, always including the thesis first.

    Unknown IDs fail instead of silently losing attribution. The full catalogue
    includes optional-source and background entries; consult ``role`` and
    ``note`` before describing a source as used by an individual analysis run.
    """
    if ids is None:
        return REFERENCES
    requested = set(ids)
    known = {reference.id for reference in REFERENCES}
    if missing := requested - known:
        raise ValueError(f"Unknown reference IDs: {', '.join(sorted(missing))}")
    requested.add(PRIMARY_REFERENCE_ID)
    return tuple(reference for reference in REFERENCES if reference.id in requested)


def references_markdown(ids: Iterable[str] | None = None) -> str:
    """Render complete citations and their use without fetching external content."""
    sections = []
    for reference in get_references(ids):
        year = str(reference.year) if reference.year is not None else "n.d."
        citation = f"{'; '.join(reference.authors)} ({year}). **{reference.title}**."
        if reference.publication:
            citation += f" {reference.publication}"
            if reference.volume:
                citation += f", {reference.volume}"
            if reference.issue:
                citation += f"({reference.issue})"
            if reference.pages:
                citation += f", {reference.pages}"
            citation += "."
        if reference.institution:
            citation += f" {reference.institution}."
        locator = (
            f"[DOI: {reference.doi}](https://doi.org/{quote(reference.doi, safe='/')})"
            if reference.doi
            else f"[Source]({reference.url})"
        )
        sections.append(
            f"### {reference.id}\n\n{citation} {locator}\n\n"
            f"**Role:** {reference.role}. {reference.note}\n\n"
            f"**Used by:** {', '.join(f'`{path}`' for path in reference.used_by)}.\n"
        )
    return "\n".join(sections)


def _bibtex_escape(value: str) -> str:
    return value.replace("&", r"\&").replace("%", r"\%").replace("_", r"\_")


def references_bibtex(ids: Iterable[str] | None = None) -> str:
    """Render UTF-8 BibTeX; unknown identifiers and DOIs are never invented."""
    kinds = {
        "thesis": "phdthesis",
        "article": "article",
        "conference-paper": "inproceedings",
        "report": "techreport",
    }
    entries = []
    for reference in get_references(ids):
        kind = kinds.get(reference.kind, "misc")
        authors = " and ".join(
            _bibtex_escape(author) if "," in author else "{" + _bibtex_escape(author) + "}"
            for author in reference.authors
        )
        fields = {"author": authors, "title": "{" + _bibtex_escape(reference.title) + "}"}
        if reference.year is not None:
            fields["year"] = str(reference.year)
        if reference.publication:
            field = {
                "article": "journal",
                "inproceedings": "booktitle",
                "techreport": "number",
            }.get(kind, "howpublished")
            fields[field] = _bibtex_escape(reference.publication)
        for field, value in (
            ("volume", reference.volume),
            ("number", reference.issue),
            ("pages", reference.pages.replace("-", "--")),
            ("school" if kind == "phdthesis" else "institution", reference.institution),
            ("doi", reference.doi),
            ("url", reference.url),
        ):
            if value:
                fields[field] = value
        fields["note"] = _bibtex_escape(f"Role: {reference.role}. {reference.note}")
        body = ",\n".join(f"  {key} = {{{value}}}" for key, value in fields.items())
        entries.append(f"@{kind}{{{reference.id},\n{body}\n}}\n")
    return "\n".join(entries)


def _cff_reference(reference: Reference) -> dict[str, object]:
    authors: list[dict[str, str]] = []
    for author in reference.authors:
        if "," in author:
            family, given = author.split(",", 1)
            authors.append({"family-names": family.strip(), "given-names": given.strip()})
        else:
            authors.append({"name": author})
    result: dict[str, object] = {
        "type": reference.kind,
        "title": reference.title,
        "authors": authors,
        "url": reference.url,
        "notes": f"Role: {reference.role}. {reference.note}",
    }
    if reference.year is not None:
        result["year"] = reference.year
    if reference.doi:
        result["doi"] = reference.doi
    if reference.publication:
        result["journal" if reference.kind == "article" else "collection-title"] = (
            reference.publication
        )
    for key, value in (("volume", reference.volume), ("issue", reference.issue)):
        if value:
            result[key] = value
    if reference.institution:
        result["institution"] = {"name": reference.institution}
    if reference.kind == "thesis":
        result["thesis-type"] = "Doctoral dissertation"
    return result


def citation_cff() -> dict[str, object]:
    """Build CFF 1.2.0 metadata with the thesis as GitHub's preferred citation."""
    thesis = REFERENCES[0]
    return {
        "cff-version": "1.2.0",
        "message": (
            "Please cite Julián Andrés Ascencio Vásquez's doctoral thesis as the main "
            "scientific reference, the method and data references actually used, and "
            "the repository URL plus exact commit for software reproducibility."
        ),
        "title": "energy-data-insights",
        "type": "software",
        "authors": [{"name": "energy-data-insights contributors"}],
        "repository-code": "https://github.com/julianascencio/energy-data-insights",
        "preferred-citation": _cff_reference(thesis),
        "references": [_cff_reference(reference) for reference in REFERENCES[1:]],
    }
