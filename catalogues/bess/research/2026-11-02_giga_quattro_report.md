# GIGA portfolio and exact Victron configurations — 2 November 2026

This iteration continues open PR #62 from `2d15b2f47b9b27dcc9620c955b9afea9f57d0260`.
Main was `65931a16f949d3e5db1c014d8330914a971f3d80`. PR #44 is historical;
its accepted Australia/Chile ledger and held phases were not reimported. The
existing BESS schemas, source registers, current manifests, research workflow,
previous Scatec/Victron review, root contribution rules and PV conventions were
read. No repository AGENTS.md was found. Work used an isolated checkout; no agents
were spawned. Open PRs were inspected by title and paths; PV #61 is separate.

## Accepted changes

- Projects: nine named owner-portfolio candidates reviewed, **eight new and one
  substantively enriched**. Giraffe, Lion, Leopard, Hippo and Rhino are in the
  Netherlands; Green Turtle and Blue Marlin in Belgium; Albatross in Germany.
  Existing Buffalo gains wind-asset relationships, applications, site, delivery
  year, Eneco's service role and a capacity conflict. No new country.
- Equipment: **15 candidates, 15 new exact configurations**, nine Quattro 230 V
  and six MultiPlus-II 120 V; **zero existing equipment enrichments**, no new OEM.
  Victron is retained as the inverter/charger manufacturer, not a cell supplier.
- **Four project fields carry quarantined observations**: Lion and Rhino energy,
  Buffalo power, Albatross status. Zero whole-record quarantines or rejections;
  no equipment field quarantines in this batch. Earlier conflicts remain intact.
- Current totals: **1,312 projects / 31 countries / 138 sources** and
  **270 equipment records / 35 suppliers / 93 sources** (257 configurations,
  13 configurable families). These are PR-head totals, not merged content or a
  global installed-capacity census. Regional scope remains Africa, Asia, Europe,
  Latin America/Caribbean, North America and Oceania.

Project metadata includes explicitly stated chemistry, equipment models/counts,
voltage/substation, developer/owner/EPC and contractor roles, financing, contract
terms, construction milestones and planned operation periods. Inverter metadata
includes active and apparent power, 25/40/65 °C ratings, peak-power conditions,
DC limits, charger current, maximum conversion efficiency with boundary,
standby consumption, mass/dimensions, IP, communications and qualified standards.
Unknown energy/chemistry, system RTE and warranty remain null for these PCS units.

## Source batches and reconciliation

The scalable project workstream started with the [GIGA owner portfolio](https://giga-storage.com/en/projects/),
then reviewed all nine project/navigation sites and five supporting pages/releases.
Original HTML was downloaded and hashed outside Git. The footer privacy notice
was inspected before factual extraction; it is not an open bulk-reuse licence.
Only bounded factual metadata and attribution are committed, not source prose.
The two OEM datasheets were downloaded, byte-hash pinned and their second pages
visually inspected. Printed table columns, slash-separated model values and
footnotes were checked; no product-family Cartesian combinations were generated.
PDF modification dates are retained as metadata, not claimed publication dates.

The review ledger maps every accepted identity and source. Lion and Giraffe have
different named port sites and construction histories, so they remain distinct.
Lion's dated construction release says 43 MWh, the Dutch project page 47 MWh, and the
English page incorrectly uses MW for stored energy. Its MWh scalar is withheld.
Rhino's 7/7.5 MWh disagreement is likewise preserved without assuming rounding.
Buffalo's existing 25 MW remains; the 24 MW summary is quarantined. Albatross has
permits and financial close, but its specific schedule places construction in 2027;
a portfolio-wide under-construction statement does not promote its status.
The English EPC label “equations” is retained as unresolved source text only,
not a fabricated legal entity. No date forecast is treated as actual COD.

The [IEA market comparison](2026-11-02_dyness_baltic_markets.json) was reopened:
2025 annual stationary battery **power additions in GW** rank quantified country
examples China, United States, Australia and Chile in that order. Europe is a
separate regional total. A comparable operational-energyGWh table remains
unavailable; no conversion or exhaustive ranking is asserted. Continental Europe
was selected because the baseline contained only 4 NLD, 1 BEL and 10 DEU projects.

## Implementation and reproducibility

The existing upsert API accepted all additions without duplicate IDs or conflicts.
Buffalo's creation timestamp and original facts were preserved; its explicit
review flag records the new conflict. All 1,303 other existing projects and all 255
existing equipment rows remained unchanged. No empty value erased a fact.
Sources have exact URLs, retrieval timestamps, locators and original-byte hashes;
field maps distinguish the project pages from dated releases.

The offline Victron adapter now stages the nine Quattro 230 V codes from five
merged columns. It checks the exact model set/grouping, regional output voltage,
W versus VA, charge-current cardinality, positive values and thermal-rating order.
Ten synthetic tests cover identity, changed units, missing values, regional
mismatch, duplicates and column order. It never imports candidates automatically.
The existing four-column new MultiPlus-II 230 V staging behavior is retained.

```bash
pdftotext -layout /outside-git/quattro.pdf /outside-git/quattro.txt
uv run python scripts/stage_bess_victron.py --layout quattro-230v \
  --document /outside-git/quattro.pdf --text /outside-git/quattro.txt \
  --output artifacts/quattro-candidates.json
```

Typed Zstandard Parquet was built twice per catalogue with identical manifests;
reviewable manifests are committed, binary artifacts remain outside Git. Full
validation results and elapsed effort are recorded below after checks complete.

## Yield and next partition

The selected owner portfolio is exhausted: nine supported named sites, not a
50-project inventory. The project target was therefore not reached; the 15 exact
models meet the equipment planning range. This pass did not repeat the blocked
India CEA endpoint or Eskom's restricted collection path merely to count attempts.
No source was gated during the selected GIGA/Victron downloads. Known CEA 503 and
Scatec large-PDF limits remain in the inherited backlog. The highest-value follow-up
is Lion's corrected rating/commissioning evidence; for model volume, inspect the
unprocessed Quattro 120 V/277 V tables. A new Asian/African or Latin American registry
partition should lead the next project iteration when accessible and licensed.
See the [ranked backlog](2026-11-02_giga_quattro_backlog.json) for retry conditions,
partitions, fields and expected yield. This pass ends after its selected batches
and validation complete, without waiting to fill a duration.

## Validation and effort

Validation completed at **06:02 Atlantic/Canary (UTC)**, after a 05:47 start:
**15.23 minutes before publication**, approximately 10 minutes research/reconciliation
and 5 minutes validation/documentation with independent checks overlapping.
The two equipment tables and nine-site portfolio were exhausted; no idle wait
was used to satisfy a duration. Publication and final remote verification follow.

- Full Python suite: **1,597 passed, 1 skipped** (optional `cdsapi` unavailable).
- Focused catalogue and Victron suites: **48 passed**, including 20 parser cases.
- Viewer DOM suite: **4 passed**. Ruff, formatting, ty, catalogue validation,
  repository hygiene and citation consistency passed.
- Strict Sphinx succeeded in the documented Python 3.13 imagery/docs environment;
  **395 HTML pages** passed local link/asset checks.
- Both offline BESS examples executed; all six workspace wheel/sdist archives
  built and were inspected for accidental raw documents/artifacts.
- Two final typed Zstandard snapshots per catalogue produced identical manifests.
  Direct baseline comparison confirmed 8 new projects, 1 changed Buffalo record, 15 new equipment records,
  zero removals and all original creation timestamps preserved.

Immediately before publication, main and PR #62 remained at the checked hashes.
PV #61's 113 changed paths were all under `catalogues/pv`; Dependabot #47–49 touched
workflows only. No in-progress GitHub workflow run was reported. The branch will
be advanced through an expected-head lease, without force or automatic merge.
