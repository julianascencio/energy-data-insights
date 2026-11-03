# Energa replacement procurement and BYD regional warranty depth

Started 3 November 2026 at 16:49:30 Atlantic/Canary (UTC). Continued open PR #102
at `963b317`, main `5063c416`, in an isolated checkout. Both starting-head CI
workflows passed. Reviewed current instructions, established schemas/dictionaries,
source registers, completeness manifests and the immediately preceding research
ledger. Wind and Data Center heads advanced; their changed paths were inspected.
Wind still overlaps the shared bibliography, so five references are queued here
(101 cumulatively). PV paths remain separate. No shared schema/importer files changed.

## Results and evidence decisions

This pass prioritizes substantive enrichment: **12 existing projects and 16 exact
models enriched, zero new records**. No identity is duplicated or automatically
fuzzy-merged. Source-specific existing upsert API collisions were explicitly reviewed.
All prior verified values and creation dates are preserved; only enriched records
receive new update/verification timestamps.

The owner replacement procurement EGD/0002/2026 has thirteen named tasks, twelve
already represented and one held (Płońsk 1+2). The original 22 July notice maps each
task, specifies a 31 December 2027 construction completion requirement and starts
60-month battery service at final construction acceptance. These are dated original
requirements, not COD, an awarded service contract or a warranty. Later amendments
exist; the original deadline is not asserted to be the current contractual deadline.
The earlier procurement annulment remains in history. No project status is promoted
to construction or operation, and no tender relaunch is counted as a new project.

The 8 September budget notice supplies **887,298,262.18 PLN gross** for the entire
thirteen-task PV and battery procurement. It is stored only as explicitly scoped
portfolio context, never allocated to individual battery capex. Detailed site
specifications still require an NDA and were not requested. Płońsk's physical
battery/phase allocation remains unresolved. The complete public task table and
budget page were visually checked. This is a scalable owner inventory attempt;
the bounded thirteen-task scope and gated technical annexes explain the project
yield below the planning range.

The three manufacturer-authored regional residential warranty letters were obtained
through BYD's named EU service partner's public document listing: HVB V1.3
(September 2025), LVS V1.1 and LVL V1.2. Six LVS configurations, LVL15.4 (2021), and
nine HVB configurations match exact existing models. Individual throughput values,
retention, defect/performance terms, earliest-limit rules, temperature/current/voltage
capacity tests, original-buyer applicability, start-date choices, additional-module
start dates, installation deadlines, compatible-inverter requirements, notification
and nonoperation exclusions are now structured.

HVB covers qualifying European residential purchases from 1 September 2025, with
15-year defect/performance terms, 70% retained usable energy and model-specific
throughput limits. The nine models retain an unresolved **15-year term versus
120-month inoperable-product refund formula** from the same letter. The formula is not
silently changed to 180 months, no refund is computed and no legal conclusion is
inferred. The source discrepancy is quarantined on all nine affected records.

LVS/LVL covers qualifying European installations from 1 December 2021, under
50 kWh combined usable energy, with ten-year terms, 60% retention and separate
model-specific throughput limits. Opening applicability says less than 50 kWh;
a later exclusion says more than 50 kWh. Coverage at exactly 50 kWh is not asserted.
The 59 V contract test charge value is retained as a test condition and does not
replace the 57.6 V datasheet operating maximum. No commercial/large-system warranty
is applied to these residential configurations, and no site-specific coverage is
asserted. Original technical/datasheet observations remain intact. Model/test tables
and the HVB remedy page were rendered and visually checked; exclusions/remedies were
read in extracted text. No certification, cycle life or AC efficiency was inferred.

Five new source registrations preserve URLs, retrieval timestamps, original-byte
checksums, versions and locators. Owner/OEM copyright remains; bounded manual factual
extraction is not described as an open bulk licence. Original PDFs/HTML and typed
Zstandard snapshots remain outside Git. No registration, contact, payment or bypass.

## Coverage and next partition

Totals remain **1,886 projects / 39 countries**, now **289 sources**; equipment
remains **695 records / 44 suppliers**, now **349 sources** (682 exact configurations,
13 families). No new country/OEM, all six regions retained. This increment has one
held project identity, nine equipment remedy discrepancies, zero permanent record
rejections and no newly quarantined project fields. Historical holds are preserved.

The existing same-day [IEA comparison](2026-11-03_poland_containers_markets.json)
uses 2025 stationary battery GW additions among quantified countries; worldwide
operational GWh remains unavailable. No conversion or invented ranking was added.

The selected public owner inventory and all sixteen exact warranty rows are exhausted
for reviewed acceptance. Equipment depth meets the planning range through substantive
enrichment, without cosmetic model variants. A secondary search found PGE's reported
22-site procurement, notice 719197-2026, as the next high-yield lead. The primary TED URL returned a page shell without the notice body in both HTML
and the web reader. No facts from secondary mirrors were ingested: first obtain
the original public XML/PDF notice and terms,
then reconcile Budzyń and other identities. The [backlog](2026-11-03_energa_warranty_backlog.json)
records all attempted sources, partitions and next actions. Energa public award/site
ratings, Płońsk allocation and BYD remedy clarification remain actionable gaps.

## Validation

1,860 Python tests passed without skips;28 final catalogue tests passed. Validators,
preservation audits, two matching final Zstandard Parquet builds per catalogue,
Ruff, formatting, ty, repository hygiene, citation consistency,13 viewer tests,
both offline examples, strict Sphinx and449-page link/asset audit passed.
No code/dependency changes, so package builds were not repeated; starting-head CI passed.

Validated at 16:58:41 Atlantic/Canary, 9.2 minutes actual elapsed effort
through local validation, followed by leased publication. Selected source batches
are exhausted; no idle time was added. No schema or importer code was changed.
