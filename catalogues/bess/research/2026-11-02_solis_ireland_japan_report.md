# Solis exact models and Ireland/Japan project evidence — 2 November 2026

Continues open PR #68 from `dde9853531625922e62d06e0e011c660c17b5c6e`, on main
`7675a0a5e8069fa806de7a9f21923797e8323423`. Isolated checkout; no subagents.
Main, BESS/PV open PR titles and changed paths, and workflow-only PRs #47–49
were inspected. No overlap with PV #69's actual paths. No merge authorized.
Repository workflow, data dictionaries, schemas, source registers, recent
review ledgers and coverage manifests were read. Historical launch reports,
Australia/Chile phase reconciliation and held candidates remain unchanged.

## Accepted changes in this iteration

- **16/16 exact Solis inverter models**, one new supplier/brand (Ginlong Technologies).
  Ten S6-EH3P(3–10)K-H variants, two 15/20 kW models, four 29.9/30/40/50 kW models.
  These are separately named hardware/model configurations, including different
  MPPT counts, battery currents and dimensions, not cosmetic family variants.
- **3 new projects**: Kilmannock and Mucklagh (Ireland, permitted/ready-to-build),
  Kasama (Japan, historical pre-construction announcement). Existing records and
  incoming natural identities checked manually; no fuzzy merge or phase duplication.
- **1 substantive enrichment**: Kelwin-2 gains source-reported 26.6 MWh and civil
  contractor/work-scope metadata. Its prior 26 versus 26.6 MW conflict stays intact,
  canonical MW remains null, and no duration is inferred. Collins BCE is civil
  support, not an invented overall EPC or battery manufacturer. The adjacent
  substation is retained as adjacent infrastructure, not assumed connection topology.
- **6 model efficiency pairs quarantined** inside otherwise accepted records:
  the small-model PDF prints EU efficiency above maximum for six columns. Visual
  rendering confirms this is in the document. Both assertions are retained with
  source IDs; neither becomes a selected conversion efficiency or RTE.
- Seven project candidates received detailed review: three new, one enriched,
  three held (Stephenstown, Lisdrumdoagh and Lumcloon). Turlough Hill was separately
  excluded as pumped hydro. No whole equipment records rejected; no new project
  conflicts introduced. Prior project holds remain pending.

Current proposed totals: **1,328 projects / 32 countries / 163 catalogue sources**;
**331 equipment records / 38 suppliers / 117 catalogue sources** (318 configurations
and 13 families). No new countries. All six geographical regions retain coverage.
Relative to main, the cumulative PR has **6 new projects, 1 pre-existing project
enriched (Poolbeg), and 26 new equipment records**. Kelwin-2 was newly introduced
in the first PR commit and enriched in this second iteration; it is not counted
as both a new and an enriched main-branch record.

## Source batches and limits

Inventory-first work inspected ESI's June 2025 pipeline survey and its current
publication index. The report removes identities from 155 development projects;
those cannot become project records. The operating slide has 23 batteries and
one pumped-storage site; it is discovery evidence, not an openly licensed bulk
project feed. The 32-card Gore Street Capital manager portfolio was screened,
but whole-portfolio ingestion was not attempted under an assumed bulk licence.
Three acquisition projects were instead verified from detailed manager releases.

The separate Gore Street **fund** site presents jurisdiction/access and
redistribution restrictions. No fund-site content was admitted, no eligibility
confirmation submitted, and no access controls bypassed. The manager's independent
public press releases have a different scope and no corresponding gate. Manager
copyright and privacy terms were inspected; selected factual observations only.
RWE's two Irish owner pages were initially promising, but its disclaimer requires
permission to reproduce information/data. Both candidates were held, and downloaded
RWE pages removed; only URL/checksum/access metadata retained.

A DECC parliamentary answer supplies January 2025 transmission/distribution
storage tables. It is a promising next source, but explicitly credits EirGrid/ESB
network statistics. General Oireachtas CC BY policy does not settle third-party
rights. Production licence access returned 403; no collection was imported.
MEC is a connection export limit, not battery nameplate MW. Poolbeg voltage and
Gardnershill county discrepancies require reconciliation. Lumcloon also remains
held: VPI's owner figures differ from SMA Altenso's equipment-delivery figures.

All **three selected Solis datasheet tables are exhausted**. Original bytes were
downloaded and SHA256 recorded; model columns, merged cells and footnotes visually
checked. Specifications include active/apparent power, battery voltage/current,
PV/MPPT limits, one-way efficiencies, enclosure/dimensions, cooling, temperature,
altitude, auxiliary consumption, interfaces, controls and stated safety standards.
Standards are manufacturer claims, not independent certifications. Batteries are
external: chemistry/energy/cycle life/warranty remain null. Table operating voltage
120–600 V and the separate supported-maximum 700 V footnote are preserved without
silently changing the operating range. Parallel switching-time conditions remain
attached. No marketing life, duration, or peak active power was calculated.

The smaller/regional OEM stream was considered against the prior Hubble/Freedom
Won batches; this selected pass expands a previously absent supplier instead of
repeating exhausted tables. Smaller/regional manufacturers remain in the backlog
for future selection. No claim of covering every equipment level in this pass.

## Market comparison and regional priority

IEA's 29 May 2026 commentary was reopened. The comparable metric remains **2025
annual stationary battery power additions (GW), utility + behind-the-meter**:
China just over 63, USA 19, Australia nearly 8, Chile approaching 1. This is only
an ordering among quantified country examples; Europe and Middle East are regional
figures, not country ranks. A comparable operational stationary GWh ranking is
unavailable and remains null. Existing dated ranking is preserved without timestamp
churn. Japan and Irish identity/metadata gaps were prioritized; no US bulk records.

## Reproducibility and checks

Existing `upsert_records` was used for additions and null-field enrichment.
The API correctly flagged replacement of nonempty `extensions_json`; the reviewed
explicit additive merge asserts every old namespace remains identical. All prior
created_at values, source entries and project rating conflicts were audited.
Only Kelwin-2 changed among prior canonical records. Every populated factual field
has explicit registered source attribution; source locators and original-byte
checksums are recorded. JSONL shards remain below 2 MB. No schema/package code change
or new parser was necessary, so no implementation-mirroring tests were added.

- Both validators: 1,328 projects and 331 equipment records pass.
- Full Python suite: **1,607 passed**, one optional `cdsapi` dependency skip.
- Focused BESS suites: **28 passed**; viewer DOM suite: **8 passed**.
- Ruff check/format, ty, repository hygiene and citation generation pass.
- Both offline examples and all six wheel/sdist outputs pass.
- Independent typed Zstandard Parquet builds match, including coverage/completeness
  manifests. Binary snapshots and raw source PDFs remain in ignored artifacts.
- Strict Sphinx build and local-link/asset audit passed for **397 HTML pages**.
- Final visual review corrected the 40 kW model to four MPPTs/eight strings;
  its snapshot was rebuilt twice and the catalogue/provenance audit passed again.
- Main and PR #68 remained unchanged immediately before publication; PV #69
  and workflow-only #47–49 changed paths do not overlap this batch.
  No assertion that the new remote commit CI already passed.

## Effort and next action

Started 10:45:34 Atlantic/Canary (UTC); research/data validation checkpoint
11:02:21 on 2 November 2026, **16.8 minutes elapsed**.
The equipment objective was met with 16 substantive exact models. Project yield
was below 50 because the large survey is anonymous, network inventory reuse/identity
is unresolved, and restricted RWE/fund pages were excluded. No thin rows, invented
phases or timestamps were added to inflate yield. The selected defensible OEM and
acquisition batches are exhausted; final validation/publication follows immediately.

Next: verify current DECC/EirGrid/ESB inventory rights and source version, reconcile
phase/site identities and MEC versus battery MW; inspect the SMA Altenso portfolio
with owner comparisons; obtain Japanese sources for Susono/Naie/Yufu. Retry triggers,
URLs, estimated yields and processed scopes are in the adjacent ranked backlog.

Final pre-publication checks completed 11:08:30 Atlantic/Canary (UTC),
**22.9 minutes actual elapsed effort**. Publication follows with an expected-head
lease and no force push; the PR stays open. This pass ends after exhausting the
selected source tables/acquisitions and completing validation, rather than waiting
for the maximum execution window.
