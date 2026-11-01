# Research pass: Australia, Chile and Belgium

Verified on November 1, 2026. The catalogue grows from **1,113 to 1,239 records**,
from **27 to 28 countries**, and from **41 to 54 primary sources**. This batch
adds **126 rows** and enriches **five existing Australian records**. These are
catalogue records with explicit scopes, not a count of independently verified
operating commercial projects worldwide.

| Workstream | Reviewed | Published outcome |
| --- | ---: | --- |
| AEMO October 30 NEM workbook | 655 battery unit rows, 639 survey sites | 58 existing/commissioning units at 54 sites; 46 new site records, five matches to existing records, three sites consolidated into one new MREH record |
| Chile CNE October 30 construction declarations | 76 BESS entries | 73 accepted; three held for rating/phase review |
| Chile owner announcements | Five additional projects; DAS II enrichment | Four operating ENGIE projects, Celda Solar commissioning, and cold-commissioning evidence for DAS II |
| Belgium owner evidence | Vilvoorde | One operating project; possible expansion excluded |

New rows: Australia 47, Chile 78, Belgium one. The
[machine-readable reconciliation ledger](2026-11-01_australia_chile_review.json)
maps all 54 AEMO sites to catalogue IDs and lists every accepted/withheld CNE row.
The earlier [EIA/REPD audit](2026-11-01_expansion.md) remains historical evidence.

## Sources and interpretation

- [AEMO October workbook](https://www.aemo.com.au/-/media/files/electricity/nem/planning_and_forecasting/generation_information/2026/nem-generation-information-oct-2026.xlsx?rev=e4625386b864409786cd79986dd0ac04&sc_lang=en):
  use the unit aggregate AC power and nameplate storage columns. The workbook's
  definitions identify these as unit totals; do not multiply by Unit Count.
  Shared-site maximum dispatch MW, scheduled seasonal ratings and generation MW
  are excluded from battery totals. A missing component makes a total unknown;
  reported zero remains zero. This source covers the NEM, not Western Australia
  or Northern Territory. NSW1 is a market region including ACT.
- [CNE workbook](https://www.cne.cl/wp-content/uploads/2026/10/Tablas-Declaracion-Construccion-octubre-2026.xlsx)
  and [dated resolution](https://www.cne.cl/wp-content/uploads/2026/10/Resolucion-Exenta-603-2026.pdf):
  these are administrative construction declarations. Past interconnection
  forecasts never imply operation. Native monthly dates, associated-generation
  MW and incremental injection MW remain separate metadata. Hybrid PMGD net MW
  is withheld from normalized battery power. Schedule noncompliance is flagged;
  lengthy regulatory notes are represented by factual flags, not reproduced.
- [SEC MREH](https://www.secvictoria.com.au/investments/melbourne-renewable-energy-hub)
  defines one operating 600 MW / 1,600 MWh project. Its A1/A2/A3 AEMO nameplates
  total 647.92 MW / 1,600.48 MWh. The owner rating is retained, with the different
  registry ratings visible as unresolved engineering-basis observations.
- [Edify](https://edifyenergy.com/project/riverina-darlington-point/) identifies
  Riverina 1, Riverina 2 and Darlington Point as three independent co-located
  projects. They stay separate without a fourth aggregate row. Two owner ratings
  differ from AEMO nameplates and are retained as conflicts.
- [ENGIE Libélula/Los Loros](https://www.engie.cl/impulsamos-la-transicion-energetica-con-la-entrada-en-operacion-de-dos-nuevos-parques-de-almacenamiento/),
  [Tocopilla](https://www.engie.cl/obtuvimos-la-entrada-en-operacion-comercial-de-bess-tocopilla/)
  and [Lile](https://www.engie.cl/concluimos-la-primera-etapa-de-la-reconversion-del-complejo-energetico-mejillones/)
  support four distinct operating projects. Battery-only capex is separated from
  solar/site investment. Tocopilla's February 19 commercial date is explicit;
  Lile's September 25 authorization is retained as a milestone, not exact COD.
- [Colbún Q3 update](https://www.colbun.cl/corporativo/sala-de-prensa/noticias-y-comunicados/detalle/2026/10/28/colbun-informa-ebitda-de-us196-6-millones-durante-el-tercer-trimestre-de-2026)
  supports commissioning status for Celda Solar and cold commissioning for DAS II.
  [Celda's project page](https://www.colbun.cl/nuestras-energias/proyectos-de-energia-renovable/proyectos-de-almacenamiento/celda-solar)
  gives 228 MW / 912 MWh. The [DAS II page](https://www.colbun.cl/nuestras-energias/proyectos-de-energia-renovable/proyectos-de-almacenamiento/bess-ii-das)
  corroborates the named project and equipment supplier; annual GWh and apparent
  equipment-level unit errors are not imported as storage capacity.
- [ENGIE Vilvoorde](https://corporate.engie.be/en/energy/batteries/bess-battery-park-vilvoorde)
  confirms operation at 200 MW / 800 MWh. The indexed primary
  [commercial-operation release](https://corporate.engie.be/nl/pers/batterijpark-van-engie-in-vilvoorde-volledig-operationeel)
  explicitly dates full COD to November 14, 2025; direct opening returned 403,
  and that access limitation is recorded.

## Reconciliation decisions

Hornsdale, Victorian Big Battery, Hazelwood, Blyth and Western Downs keep their
existing IDs, creation times, owner-rated capacities and phase descriptions.
Their AEMO observations are attached without silently replacing curated facts.
Differences are marked `needs_review`; neither set is labelled universally correct.

Eraring, Bungama and New England retain future battery units outside published
capacity totals. In-commissioning unit nameplates may be included in the explicit
scope but do not become operational capacity. Future-only AEMO sites are not
published in this pass.

Atacama II and Atacama Solar BESS phase III are both withheld until the shared
owner's facility/phase boundary is reconciled. Solar Ray 1 is withheld because
reported net power equals associated PV power and battery-only scope remains
unclear. The CNE workbook is not merged with owner operating announcements by
name similarity alone. Celda Solar is not in the October declaration subset;
owner evidence supports its separate addition.

## Reproduction and next work

Both new adapters are offline and checksum-pinned by the source registry:

```bash
uv run python scripts/stage_bess_inventory.py aemo /path/to/aemo-oct2026.xlsx \
  --source-id aemo_nem_oct2026_bess --output artifacts/aemo-candidates.jsonl
uv run python scripts/stage_bess_inventory.py cne /path/to/cne-oct2026.xlsx \
  --source-id cne_oct2026_bess --output artifacts/cne-candidates.jsonl
uv run python -m energy_data_retrieval.bess_catalogue validate
```

These commands stage candidates, not automatic imports. Input files stay outside
Git. Follow the [research workflow](../RESEARCH_WORKFLOW.md) for recurring work.
Next priorities are underrepresented countries, Western Australia, and resolving
the recorded phase/rating discrepancies. This sample remains heavily influenced
by U.S. and UK registry availability; it cannot support global market-share claims.

## Validation

- Catalogue validation: 1,239 records, 28 countries, 54 sources; 26 records carry
  explicit review flags (rating disagreements, hybrid scope or schedule warnings).
- Full Python suite: 1,442 passed. The focused BESS subset passed 28 tests,
  including unit aggregation, missing values, retained zero, hybrid power scope,
  past forecasts, workbook headers, duplicate IDs and the reconciliation ledger.
- Ruff format/lint, type checking, repository hygiene, citation consistency and
  `git diff --check` passed. All three packages built and passed installed-wheel
  smoke checks and wheel metadata checks.
- Strict Sphinx build passed; all 372 generated HTML pages passed local-link and
  asset checks. Four viewer core tests and DOM integration passed for BESS load,
  country filtering, evidence dialog, filtered CSV, reset and PV regression.
  Browser visual layout was not assessed; the generated coverage figure was
  inspected. No viewer layout code changes were required.
- Canonical input, exported Parquet manifest and executed gallery fingerprint
  agree: `8cdf4a3f9dd1695553ef864d8029ea7878d88618685fff2469e11f65172ca440`.
