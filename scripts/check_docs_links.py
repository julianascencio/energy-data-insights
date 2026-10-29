"""Check rendered local links, fragments and assets without network requests."""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if identifier := values.get("id"):
            self.ids.add(identifier)
        if tag == "a" and (name := values.get("name")):
            self.ids.add(name)
        for attribute in ("href", "src"):
            if value := values.get(attribute):
                self.links.append(value)


def main() -> int:
    root = Path(sys.argv[1]).resolve()
    pages: dict[Path, Page] = {}
    for path in root.rglob("*.html"):
        # Themes can ship unrendered Jinja helpers as static assets, not pages.
        if "_static" in path.relative_to(root).parts:
            continue
        page = Page()
        page.feed(path.read_text(encoding="utf-8"))
        pages[path] = page
    errors = []
    if root / "index.html" not in pages:
        errors.append("index.html is missing")
    for source, page in pages.items():
        for link in page.links:
            url = urlsplit(link)
            if url.scheme or url.netloc:
                continue
            if url.path.startswith("/"):
                errors.append(f"{source.relative_to(root)}: root-relative URL {link}")
                continue
            target = (source.parent / unquote(url.path)).resolve() if url.path else source
            if not target.is_relative_to(root):
                errors.append(f"{source.relative_to(root)}: link escapes site: {link}")
                continue
            if target.is_dir():
                target /= "index.html"
            if not target.exists():
                errors.append(f"{source.relative_to(root)}: missing {link}")
            elif (
                url.fragment and target in pages and unquote(url.fragment) not in pages[target].ids
            ):
                errors.append(f"{source.relative_to(root)}: missing anchor {link}")
    if errors:
        print("\n".join(sorted(set(errors))))
        return 1
    print(f"Documentation check passed: {len(pages)} HTML pages; local links and assets resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
