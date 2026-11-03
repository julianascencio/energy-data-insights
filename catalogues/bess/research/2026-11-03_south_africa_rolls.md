# South African portfolios, Finnish owner evidence and exact Rolls AGM models

Started 3 November 2026 at 06:46 Atlantic/Canary (UTC on this date). Continued
open PR90 at `d69dfe80b46d5d1cc556a62bfe6521701b5d3f21`, from current main
`15e9d60b84b0e741979437fd8d7172f0d7e30824`. PR44 is historical and merged;
its Australia/Chile crosswalk and held phases remain untouched. Read current main,
CONTRIBUTING, workflow, dictionaries/schemas, source registers, manifests, recent
logs and PV conventions. No AGENTS.md found. PR89 Wind, PR91 PV and PR92 Data
Center titles and changed paths were checked; no BESS data overlap. No subagents.

## Accepted additions and substantive enrichment

- **19 new projects:** South Africa 14 and Finland 5; **one existing project enriched**.
- **24 exact equipment configurations:** Rolls Battery AGM-S, with no new supplier
  or country. Proposed totals: **1,777 projects /37 countries /240 project sources**;
  **591 equipment records /42 suppliers /266 equipment sources**, including
  **578 exact configurations and 13 configurable families**. All six regions remain
  covered. These proposed PR counts are not merged content or a capacity census.
- Mulilo's complete five-project BW2 and four-project BW3 release lists were
  reconciled. Financial close for Hartebeesfontein adds lenders, municipality,
  partnership and 15-year NTCSA PPA; it does not establish construction. Middlepunt
  solar and portfolio aggregates were excluded.
- Vanilla and Bloemhoek's public redacted applications distinguish contracted
  123/124 MW and 492/496 MWh from planned installed 142.17/147.6 MWac and 568.66/574.03 MWh.
  Captured 132 kV connections, substations, planned line lengths, site locality,
  forecast COD, proposed ownership and conditional design metrics. No GPS datum
  was established, so no WGS84 coordinates were fabricated. Applications are not
  issued licences, and forecast construction dates do not establish progress.
- EDF's complete three-site Oasis list supplies individual MW/MWh, construction,
  partners and 15-year PPA. ZAR 7bn is portfolio debt, not per-site capex. Aggeneis/
  Aggeneys is one identity. Northern Cape supply area is not asserted as every
  site's administrative province.
- Split the two explicitly named Umoyilanga battery sites, without a parent row:
  Avondale 30 MW and Dassiesridge 45 MW. The newer 12 December 2025 owner release supersedes
  the undated construction label for provisional Dassiesridge operations. Full
  combined COD remains unverified. Hybrid 75 MW contract and 55 MW provisional delivery
  are not battery capacities. Solar/wind EPC contracts were not assigned to BESS.
- Exilion's portfolio and annual report add Mäntyharju 30 MW / 66 MWh construction,
  Viinamäki/Halmekangas operating reserve service, and Tjusterby/Palanutkangas
  planned hybrid battery portions. Mäntyharju trading/O&M agreement is future
  service evidence, not commissioning. Ii wind location is not Simo battery site.
- A final owner-news crosscheck adds Varevaara: 20 MW / 41 MWh, Merus turnkey
  delivery and hybrid controller, order value over EUR 8m, autumn 2027 forecast
  handover. A supply order does not establish construction. The 2025 annual report
  explicitly identifies Tjusterby and Palanutkangas as battery development projects.
- Kenhardt's existing ID, capacity, ownership and creation timestamp were preserved while
  adding Scatec's developer/EPC roles and dated hybrid-level financing evidence:
  ZAR 16.4bn approximate hybrid capex, ZAR 12.4bn nonrecourse debt and ZAR 13.7bn
  development/EPC contract. These are not battery-only cost fields. O&M remains a
  contracted service observation, not an unsupported current operator assignment.
- Exhausted the selected 24-model AGM-S RE partition. Captured exact model/revision,
  voltage, cell count, rate-dependent component Ah, charge limits with per-cell
  and 25°C boundaries, internal resistance, terminals and physical measurements.
  Missing discharge currents remain null. No Ah-to-energy or power inference,
  warranty extrapolation, graph-derived cycle rating or equipment-project linking.

## Quality, exclusions and source access

**Project field quarantines affect three records:** Viinamäki 5.6 versus 6 MW;
Vanilla/Bloemhoek's inconsistent 18-month schedule versus January 2026–July 2028 dates;
and two incompatible Bloemhoek business registry IDs. Retain both observations.
**Equipment field quarantines affect three records:** two S6-250AGM-RE Ah/current
pairs; S12-33AGM-RE 10 kg versus 22.5 lb mass; S2-1275AGM-RE height pending full newer
brochure review. Zero whole-record rejections. No existing verified fact erased.

The project ledger reviews 25 distinct identities:19 new, 1 enriched, 1 existing unchanged
(Haru), and 4 deferred (Oasis Ararat, Gainfar, Boitekong, Tymbark-mws). Equipment:
26 reviewed including two R-series preflight samples,24 accepted; those two R-series
models remain queued. Retreat/Erfdeel application enrichment is deferred, but their
project identities and capacities are independently accepted from the owner release.

Scalable official inventory was attempted first: South Africa's BW2 eight-site and
BW3 five-site awards. Gov.za terms limit reuse to noncommercial information; no
blanket bulk-reuse licence was assumed and no government price table was ingested.
Independent developer batches supplied accepted facts. TGS Kenhardt control-system
material has internal-use/publication restrictions and remains held; independent
Scatec financing/EPC evidence supplied useful enrichment instead.

Direct Rolls/Mulilo/Scatec downloads returned 403; public web-reader evidence was
used without bypass. Original-byte hashes are null for those sources. The Rolls
adapter hashes extracted text under an explicitly different key. Successful EDF,
Exilion and Merus original captures have byte counts, SHA-256 and UTC retrieval
metadata; source bytes remain outside Git. Two scanned Mulilo applications yielded
no reader text or usable screenshot payload, and large Rolls/Mulilo brochures
exceeded reader size limits. No contact, registration, payment or hidden endpoint.

The selected owner release lists and 24-model partition were exhausted. Project
addition yield below 50 reflects source scope, reuse restrictions and held site/
phase evidence. Equipment objective met with substantive configurations. This is
not a claim that worldwide research is exhausted. The ranked backlog records
exact URLs, editions, fields, terms, processed partitions and retry conditions.

The freshly reopened IEA 29 May 2026 commentary gives comparable **2025 stationary
battery power additions**, among quantified country examples: China >63 GW,
United States 19 GW, Australia nearly 8 GW, Chile approaching 1 GW. Europe 6.2 GW is a
regional comparator. This is not an exhaustive country ranking; operational
stationary GWh remains unavailable/null, with no conversion from GW. See the dated
markets file and its attribution/licence.

## Implementation and reproduction

`rolls_agm.py` and `scripts/stage_bess_rolls_agm.py` stage one reviewed model from
local unnumbered reader text; no crawling or automatic acceptance. Guards cover
exact URL/model, series, units, duplicate labels/rates and required revision;
Ah/current inconsistency is preserved for review. Ten synthetic tests exercise
these boundaries. Existing importer/upsert and schema APIs are retained. Kenhardt's
nested financing addition was explicitly reviewed after null-filling scalar upsert.

```bash
uv run python scripts/stage_bess_rolls_agm.py /outside-git/model.txt \
  --model S12-33AGM-RE \
  --url https://www.rollsbattery.com/battery/s12-33agm-re/ \
  --output /tmp/model-review.json
uv run pytest data-retrieval/tests/test_bess_rolls_agm.py
uv run python -m energy_data_retrieval.bess_catalogue validate
uv run python -m energy_data_retrieval.bess_oem_catalogue validate
```

Typed Zstandard Parquet and completeness/coverage manifests rebuilt twice with
identical results. Binary files remain outside Git under the existing artifact
mechanism. Preservation and review ledgers map accepted IDs and changed fields.
Next highest-value partition: readable Retreat/Erfdeel licence applications for
technical enrichment, then named Ingrid/Locus sites and independent BW2 Ararat/
AMEA site evidence. Recheck freshness before each continuation.

## Validation and measured effort

At 07:11 Atlantic/Canary (UTC), **25.3 minutes** had elapsed from the 06:46 start
through validated commit preparation; subsequent GitHub publication is outside
this measurement. Research/extraction and validation overlapped. The bounded
owner batches and 24-model AGM partition are exhausted; finishing before the
45-minute ceiling avoids padding with unresolved or thin records.

- Full Python suite: **1,764 passed, one optional cdsapi skip**. Final data and
  reference additions: **38 catalogue/parser tests and 28 reference/analysis tests**.
- All **11 viewer tests**, both final offline examples, catalogue validation,
  preservation and 24-model staged measurement reconciliation passed.
- Two identical final typed Zstandard Parquet builds per catalogue; coverage and
  completeness manifests committed, binary snapshots outside Git.
- Ruff, format, ty, citations, repository hygiene and whitespace passed.
- All six distributions rebuilt; strict Twine passed; all three installed-wheel
  smoke tests passed outside the workspace.
- Strict Sphinx and local links/assets passed across **424 HTML pages**.

The initial missing list type annotation was fixed. A reused snapshot destination
was rejected as designed; fresh output directories produced identical results.
Validation JSON records check scope and corrected local helper/command failures.
No new remote CI result is assumed.

Current main and PR90 head remain unchanged. PR89 Wind also appends bibliography
entries on its separate branch; all existing reference objects are preserved and
this change appends only BESS source entries. PR91 PV and PR92 Data Center have no
BESS path overlap. No shared schema/importer changes or merges were performed.
