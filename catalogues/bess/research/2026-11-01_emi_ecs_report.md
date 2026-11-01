# New Zealand dispatched fleet and Fox ESS ECS configurations

1 November 2026; started 21:48:51 Atlantic/Canary / UTC. Final validation time below.
Main 5b49e55 already includes merged PRs #44, #45 and #50. Their snapshots are
historical baselines, not counts copied into this update. Open PV PR #51 was
inspected by title and changed paths; its PV shards/source register are untouched.
PR #51 subsequently merged; checkout fast-forwarded to main 0cbb824 and the full
suite and strict docs were rerun. Dependabot PRs #47–49 change workflows only. No subagents, force pushes or merges.

## Results

Five New Zealand BAT observations reviewed: **one new project, three enriched,
one held, zero rejected**. Three existing assets gain regulator-reported operators,
POC/unit/operator codes and effective observation intervals. Rotohiko also gains
its reported commissioning date in extensions (not asserted as commercial COD).
Southdown Battery is retained as a historical 1 MW installation, retired according
to the 2 July 2026 inventory, with 23 May 2022 decommissioning and 1 January 2017
reported commissioning dates separately recorded. No MWh or chemistry inferred.
Huntly HLY11 is held: null commissioning date and an effective attribute-start date
cannot establish operation or distinguish stages. Primary Genesis releases are
the next reconciliation step; secondary FY27 report summaries are discovery only.

Sixteen equipment candidates reviewed: **12 new exact configurations, four held,
zero rejected**. ECS2900-H2 through H7 and ECS4300H-H2 through H7 use separate,
visually checked English April 2025 datasheet columns. Energy, DC voltage ranges,
master/slave counts, recommended/maximum/peak current, peak duration, dimensions,
weight, natural convection, IP65, altitude, humidity, storage and separate
charge/discharge temperatures are preserved. RTE is a strictly greater-than-95%
battery-pack claim, not AC system efficiency; cycle life is at least 6,000 at
25°C, 90% DOD and 0.5C, with unspecified retention threshold. Manufacturer-listed
standards remain claims, not independently verified certificates. No active power,
warranty, cell supplier, other configuration or project assignment is inferred.
Older Spanish December 2023 sheets show 2,000 m altitude; the specifically cited
April 2025 English revisions show 3,000 m. They are distinct source revisions,
not competing timeless ratings. No older-language duplicate rows were created.

Freedom Won Encore 3K/5K/8K/10K overview was inspected as the smaller/regional OEM
workstream. These candidates are held for exact SKU/revision and explicit PCS
product-level mapping: current architecture enum describes battery systems and
has no PCS category. Its rated output is kVA, not an inferred battery kW rating.
No schema extension was rushed into this batch.

Current totals: **1,276 projects / 30 countries / 92 sources; 150 equipment
records / 31 suppliers / 73 sources**, including 137 exact configurations and
13 families. No new country or supplier; all six project regions retained.
No new quarantines; existing conflicts including Modhera/ENVA and Chile holds
remain unchanged. Three new sources carry exact URLs, dates/revisions, retrieval
UTC timestamps, hashes and locators. All populated fields map to source IDs.
Original CSV/PDF bytes and rendered pages stay outside Git.

## Inventory, rights and reproducibility

The official EA fleet was attempted before isolated press releases. Its listing
still mentions a 2023 filename in prose, but the actual newest listed file is
20260702; the selected filename and publication date are explicit. The Authority's
CC BY 4.0 default and exclusions were checked before extraction; factual adaptation
is attributed to Electricity Authority, New Zealand. The five BAT rows are the
entire battery partition, not all generating plant. Non-battery technologies are
excluded. POC digits are not interpreted as connection voltage; historical rows
are not automatically merged by plant name.

`energy_data_retrieval.bess_catalogue.emi.parse_emi_batteries` stages downloaded
CSV bytes offline, requiring headers, exact BAT technology, finite nonnegative
power and unique POC/unit/effective-start identities. It preserves separate dated
revisions and does not infer lifecycle status. Six synthetic tests cover these
boundaries. Reviewed records use the existing upsert API. The preservation audit
checks all prior IDs and creation timestamps, three substantive project changes,
and otherwise unchanged canonical records. Typed Zstandard Parquet and
completeness manifests are rebuilt with the existing packages.

The dated [market comparison](2026-11-01_india_fox_freedom_markets.json) remains
applicable: IEA 2025 annual stationary battery power additions in GW, with China,
US, Australia and Chile ordered only among quantified country examples. Regional
aggregates are separate. A comparable worldwide operational-GWh ranking remains
unavailable; no MW/MWh substitution. This pass deepens underserved Oceania while
adding Asian OEM configurations and reviewing South African PCS models.

[Backlog](2026-11-01_emi_ecs_backlog.json) and
[review](2026-11-01_emi_ecs_review.json) record URLs, rights, revisions, fields,
estimated yields, exact partitions, results and retry conditions. Next project
source: Genesis primary FY27 Q1 disclosure for Huntly's stage boundary/lifecycle,
then EA proposed fleet. Next equipment source: ECS4800 and exact Encore PCS sheets.
Project yield is below 50–200 because this official inventory has only five battery
observations, three already represented and one lifecycle hold. All selected
battery inventory rows and both six-column model tables are exhausted; the
12-model equipment objective is met. No timestamp-only changes or thin portfolio
aggregate records were added.

## Validation

Validation completed 21:58 Atlantic/Canary / UTC; approximately 9 minutes elapsed
from 21:48:51 (roughly 4 minutes extraction/reconciliation, 5 minutes checks and
publication preparation). Finishing early because all selected source partitions
are exhausted, rather than padding the window with sparse records.

- Full Python suite after main advanced: 1,524 passed, one skipped (optional cdsapi).
- Focused catalogue/parser tests: 34 passed, including six new EMI boundary tests.
- Ruff lint/format and ty passed; citation exports and repository hygiene passed.
- Strict Sphinx/gallery build passed; 387 rendered pages passed local-link checks.
- Four viewer JavaScript tests passed; no live-browser DOM claim.
- All three packages built; installed-wheel checks passed.
- Both offline BESS usage examples passed; both typed Zstandard snapshots rebuilt
  and independently repeated manifests matched. Final review removed a locality
  inferred only from the Southdown plant name; its locality remains unknown.
- Existing-ID/created-at preservation and incoming/canonical identity review passed.

Checks are local; remote CI is assessed separately on publication. PR remains open;
no database content from this iteration is described as merged.
