"""Check or regenerate citation exports from the packaged reference catalogue.

Run ``uv run python scripts/check_citations.py --write`` after a reviewed metadata
change, then run without ``--write`` in CI. No external service is contacted.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_methods.references import citation_cff, references_bibtex, references_markdown

INTRO = """# Scientific references and attribution

## Main scientific reference

**Julián Andrés Ascencio Vásquez (2021). _Modelling and worldwide assessment
of performance and aging of photovoltaic modules and systems_. Doctoral
dissertation, University of Ljubljana, Faculty of Electrical Engineering.**
[Permanent national-library record](https://www.dlib.si/details/URN:NBN:SI:DOC-TMG3QFI9).

The thesis is the preferred citation in the root `CITATION.cff` and appears
first in analysis report bibliographies. Its institutional catalogue identifier
is **COBISS 77808131**. The university records the defense on **21 September 2021**:
[LPVO thesis catalogue](https://lpvo.fe.uni-lj.si/en/education/final-theses/completed/)
and [defense announcement](https://lpvo.fe.uni-lj.si/en/2021/).
The later national-library upload date is not the thesis publication year.
Marko Topič is the advisor, not a thesis coauthor. No thesis DOI is asserted.

## How to cite work using this repository

1. Cite the thesis as the main scientific reference.
2. Cite the individual algorithm papers, software and data sources actually used
   by your analysis. A primary thesis citation does not replace their attribution.
3. Cite the repository URL and exact Git commit, and retain the input hashes,
   parameters, software versions and source-access timestamps in your manifest.

The catalogue is scoped to the methods, sources and documentation used or
discussed in this repository. It is not the thesis's complete bibliography.
`implemented` identifies method lineage; it does not claim identical reproduction
of published author software. `background` is explanatory context. A `data`
entry documents an available source and does not prove that a particular run
downloaded it. Use the run's acquisition provenance for that determination.

| Component | Attribution and implementation boundary |
| --- | --- |
| Typical Daily Profiles | Ascencio-Vásquez et al. (2021); project qualification/pooling rules. |
| CCYA | Thesis (2021), sections 7.5.1-7.5.3; adaptations documented in docs/ccya.md. |
| Acceptance bands | Ascencio-Vásquez et al. (2020); documented roughness/distance interpretation. |
| Effective POA | Reda-Andreas, Erbs, Hay-Davies, Spencer and pvlib. |
| Single-axis geometry | Anderson-Mikofski and Lorenzo et al. through pvlib; inferred geometry. |
| LightGBM | Ke et al. and LightGBM documentation; project chronology and monotonic settings. |
| Physical response | Stark-Parker BVLS through SciPy; repository-specific PV basis. |
| Operational screening | IEC TS 63019 context; no conformity or certified availability claim. |
| Generation and weather | Worldwide providers and measured PV; see run provenance. |

Subhourly irradiance redistribution and geometry/lag search are project choices.
The shape-constrained physical basis is not attributed to the solver authors.
Screening thresholds cannot establish verified operating causes.

## Maintaining the bibliography

The single metadata source is
`methods/src/energy_methods/references.json`, packaged with `energy_methods`.
The immutable Python API is `energy_methods.references`. This page,
`references.bib` and `CITATION.cff` are generated together. The CFF file uses
JSON syntax, which is valid YAML, so its consistency can be checked without a
runtime YAML dependency. Its schema version is CFF 1.2.0.

```bash
uv run python scripts/check_citations.py --write
uv run python scripts/check_citations.py
```

Add a verified entry and connect it to the relevant implementation when a new
method or source is introduced. Do not invent a DOI, assume a publication year
from a web-page upload date, imply unimplemented algorithms are available, or
substitute a metadata-verification date for the actual data-access date.
No license is inferred from bibliographic metadata.

## Complete catalogue

"""


def documents() -> dict[str, str]:
    """Expected export contents; reused by the offline consistency tests."""
    return {
        "CITATION.cff": json.dumps(citation_cff(), indent=2, ensure_ascii=False) + "\n",
        "references.bib": references_bibtex(),
        "docs/references.md": INTRO + references_markdown(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Regenerate all citation exports")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    stale = []
    for relative, content in documents().items():
        path = root / relative
        if args.write:
            path.write_text(content, encoding="utf-8")
        elif not path.exists() or path.read_text(encoding="utf-8") != content:
            stale.append(relative)
    if stale:
        print("Stale citation exports: " + ", ".join(stale))
        print("Run: uv run python scripts/check_citations.py --write")
        return 1
    print("Citation catalogue and all exports are consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
