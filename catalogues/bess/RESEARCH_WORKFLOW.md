# BESS research workflow

Each research iteration should produce verified additions or corrections, with a
small durable checkpoint explaining what was searched and what remains uncertain.
The catalogue contains projects and registry-defined plants; it is not a census
or a live availability feed. Do not interpret record counts as installed capacity.

1. Read the current main branch, open BESS research PR, schema, source registry
   and latest research/reconciliation ledgers. Reuse a matching open research PR;
   otherwise create a new branch from main. Never discard another task's work.
2. Rotate countries and evidence gaps. After the November 1 Australia/Chile batch,
   prioritize China, India, continental Europe, Africa, Latin America outside
   Chile, and non-NEM Australia. U.S./UK registry coverage dominates the current
   sample. Older facts missing from the catalogue are useful as well as news.
3. Prefer primary regulators, system operators, owners, OEMs and EPCs. Search in
   local languages when useful. Check recent status updates as well as technical
   sources. Register exact URLs, access method, retrieval/publication dates,
   source terms and downloaded inventory checksums. Raw downloads stay outside Git.
4. For TAB TOPzS PDF pages 10–11, `scripts/stage_bess_tab_topzs.py` stages
   eight exact cell models. Preserve the printed `6 TOPzS750` identity and reviewed
   web spacing alias; C10 uses 20°C, C100 uses 25°C, and C20 temperature is unstated.
   Fault current is in A, not kA or operating current. Live-table wet/dry mass
   order is reversed from the PDF. Two additional OPzS live-only cells were
   reviewed separately; do not copy brochure life/voltage/temperature onto them.
   For TAB UPS PDF pages 8–9, `scripts/stage_bess_tab_ups.py` stages
   the 15-model table. C10 Ah belongs to the cell/monobloc; timed W/cell
   observations are not continuous unit power. Preserve rate-specific final voltage
   and reference temperature, dry/wet mass, and the printed compensation-unit hold.
   For TAB OGi PDF page 6, `scripts/stage_bess_tab_ogi.py` stages the
   reviewed 25-model partition. Preserve kA fault current, 2 V cell versus
   6/12 V monobloc Ah, and PDF dry/wet versus website wet/dry mass order.
   Page 7 supplies operating conditions; do not normalize its questionable
   temperature-compensation unit or choose between conflicting web/PDF capacities.
   Website-only models were separately reviewed on 5 November.
   `scripts/stage_bess_tab_ogi_web.py --cells cells.json --output staged.json`
   accepts a local JSON array of `td/th` text in DOM order, retaining empty cells.
   The malformed live HTML must not be grouped by `tr`. Check all 41 identities,
   rate/end-voltage headers and wet/dry mass order; 25 previously imported models
   are reconciliation-only, not new rows. Fourteen extra rows omit the shortest
   rate capacity and nominal voltage; the live page states no capacity temperature.
   Do not transfer brochure-only conditions to these website-only models.
   For TAB stationary OPzS PDF tables, `scripts/stage_bess_tab_opzs.py`
   stages the 22-cell or six-block partition (`--partition blocks`). It rejects
   changed units/mass order, duplicates and partial tables. Cell Ah and block Ah,
   short-circuit versus operating current, and cell/block design-life footnotes
   must remain distinct; no MWh is inferred. Website-only models need separate review.
   Stage national inventory candidates with `scripts/stage_bess_inventory.py`.
   For the seven-column BSLBATT S205/S314 station sheets,
   `scripts/stage_bess_bslbatt.py` stages local `pdftotext -layout` output and
   checks model order, units, merged-cell scope and voltage envelopes. The row
   labelled `Rate Power(kWh)` is energy, never active power. S205 maximum-current
   assertions require manual reconciliation with its separate 0.5C claim.
   Component dimensions are not complete-system dimensions; neither optional
   equipment nor index filenames establish installed configuration or revision dates.
   For the reviewed PIB Indian Table-II format, use `scripts/stage_bess_pib.py`
   on downloaded HTML; it stages candidates only and does not import identities.
   For public NEMSA mini-grid applications, `scripts/stage_bess_nemsa.py` stages
   allowlisted site/battery observations without personal contacts or unit repairs;
   an inspection request is not an operating certificate.
   For the reviewed Victron 120 V and 2 kVA 230 V HTML manuals,
   `scripts/stage_bess_victron_html.py` preserves exact model headers, explicit
   merged-cell scope and separate W/VA rows. It stages facts only; compare
   undated editions and retain conflicting auxiliary/standard observations.
   For the ODRÉ French register, use `scripts/stage_bess_odre.py` on downloaded
   API JSON with the explicit reporting date. Exclude aggregates, confidential
   names and inconsistent battery classifications; review multiple EICs at one
   location before treating them as distinct projects or phases. Tiny reported
   kWh values are quarantined, never silently rescaled. Preserve industrial-service
   dates separately from contractual COD and annual energy separately from storage.
   For Rolls flooded model pages, `scripts/stage_bess_rolls.py` stages exact named
   HTML tables, rate-dependent monobloc Ah and charge limits. No inferred MWh,
   cell-capacity substitution or charging-unit repairs; review source revisions.
   For the reviewed Crown SB-CRP-G0720 table, use `scripts/stage_bess_crown.py`
   on local `pdftotext -layout` output. Keep C20/C100 Ah and kWh observations
   separate; the ambiguous DoD footnote does not authorize usable-energy inference.
   Review metric/imperial discrepancies before promoting physical dimensions.
   For exact Rolls AGM-S reader tables, `scripts/stage_bess_rolls_agm.py`
   stages local extracted text. Its hash is not an original-HTML checksum.
   Missing current stays null; inconsistent Ah/current rows require review.
   `--reviewed-r2` additionally accepts reviewed 2 V, one-cell AGM tables with
   undated revision labels; blank series stays unknown and other layouts fail.
   For the historical EA September2024 pipeline, `scripts/stage_bess_nz_pipeline.py`
   stages explicit chemical batteries without treating committed status as operation.
   Its `--format transpower-2026` adapter preserves connection/parent IDs and anonymous
   rows for review only; it does not grant reuse rights or infer physical status.
   For Chinese Sinexcel two-page PCS sheets, `scripts/stage_bess_sinexcel.py` checks
   exact model headers and columns in local `pdftotext -layout` output. AC kVA and
   maximum DC kW remain distinct; conversion efficiency is not round-trip efficiency.
   For Flower Q2 2026, `scripts/stage_bess_flower.py` stages local
   `pdftotext -layout` output, checks the reporting period, status sections and
   separate MW/MWh control totals. Review every named row against the ownership
   chart and later releases. Marieboda remains held for possible multi-site scope;
   the adapter never turns portfolio rows or future COD targets into accepted projects.
   `scripts/stage_bess_ceb.py` stages the reviewed26May2022 Mauritius table
   from local text, checks both MW/MWh totals and keeps the Amaury expansion
   separate. The table does not establish lifecycle: preserve unknown status
   unless independently supported by a reusable dated primary source.
   For the 12 December 2025 NFOŚiGW ranking, `scripts/stage_bess_nfosigw.py`
   stages the local 24-page PDF using optional pdfplumber. The programme is
   technology-neutral: a funding applicant named BESS is not battery evidence.
   Review exact project titles, grant/loan pairs, named sites and signed-contract
   evidence; recommendations are not awards, and awards are not construction.
   For PGE notice 719197-2026 version 01, `scripts/stage_bess_ted_pge.py`
   stages the original public TED XML. It checks the notice revision, four lots,
   22 distinct named sites, battery CPV and delivery-period units. It excludes
   personal contacts and lot-level geography. Review each site against existing
   identities; Budzyń remains held. Procurement deadlines are not COD, and
   missing annex ratings stay unknown. Changed revisions require fresh review.
   For the 9 December 2021 Maldives ARISE screening report,
   `scripts/stage_bess_arise.py` stages local `pdftotext -layout` output from
   page 15. It checks units, date and all 18 named grid identities. Preserve the
   two Addu grids and the single Isdhoo-Kallaidhoo-Dhanbidhoo grid. Its 32.7 MWh
   row sum differs from the approximate 37 MWh cover and later 40 MWh tender;
   never scale rows to fit a portfolio total. These are historical design
   estimates, not current as-built ratings. Keep ARISE distinct from ASSURE.
   `scripts/stage_bess_ngcp.py` stages the reviewed March and September 2026
   NGCP service bulletins from local layout text. BSS means black start service,
   not battery technology. Contract cases and certification do not establish COD,
   ownership or capacity; preserve phase names and dated firm-capacity warnings.
   Use `--september-2026` only with bulletin 2026-51; unknown rows fail closed.
   `scripts/stage_bess_effekta.py` stages the 18 exact BTL overview models. C20 Ah
   belongs to a monobloc, not a cell; do not derive energy or match differing model
   suffixes automatically. Individual-sheet and overview rating bases stay separate.
   `scripts/stage_bess_effekta_individual.py` stages reviewed English BT/front-terminal
   sheet facts from local layout text. Supply the printed model heading and archive
   URL explicitly; filenames do not define identities. Preserve approximate mass,
   height labels, C-rate versus amperes and short-circuit versus peak current.
   Charging tables, rate conditions and overview discrepancies require manual review.
   `scripts/stage_bess_leoch_opzs.py` stages reviewed two-page 2 V OPzS sheets
   from local layout text. It requires the exact printed heading and publication
   number, preserves C10 at 20°C/1.80 V per cell, and separates dry/approximate
   mass, short-circuit amperes and maximum charge C-rate. The same marketed code
   appears in standard and telecom URL editions: do not create duplicate identities
   or select a terminal/mass winner without configuration evidence. Residual template
   tokens in the text layer are not numerical specifications. Staging never imports.
   `scripts/stage_bess_inventory.py repd --repd-status "Under Construction"`
   selects that explicit lifecycle partition; the default remains Operational.
   Recheck the release hash, exact application IDs, nearby sites, names and phases.
   REPD construction flags are dated registry observations, not live availability.
   `scripts/stage_bess_kehua.py` reads exact model tabs from local OEM HTML.
   It fails on changed panel counts/labels/units and requires reviewed model order.
   Preserve full-load versus operating DC ranges, rated kW versus maximum kVA,
   temperature conditions, conversion efficiency versus RTE and NEMA versus IP.
   Do not claim PDF-only specifications when the linked download service fails.
   Resolve external IDs, aliases, physical location, phases and commercial-project
   scope against existing rows and the ledgers before accepting candidates.
   AEMO survey sites 3100/3101/3102 already belong to the single MREH record.
5. Use the existing typed schema and explicit field provenance. Preserve stable
   IDs and creation times. Leave unsupported fields null. Battery MW, grid MW,
   solar MW, annual GWh and stored MWh are different quantities. Keep electrical
   and energy rating bases explicit. Do not derive discharge hours as a reported
   fact, guess a supplier's role, or turn a forecast date into COD.
6. Retain conflicting observations and qualify the chosen scope. Do not overwrite
   curated ratings simply because a registry is newer. Administrative construction
   status is not evidence of physical progress; commissioning is not commercial
   operation. Inauguration and commercial-operation authorization are distinct
   milestones. Keep unresolved candidates in the review ledger.
7. Keep canonical UTF-8 JSONL shards below 2 MB; rebuild Parquet and derived browser
   data offline. Update documentation counts and research notes, and add sources
   to the reference registry. Run citation regeneration, catalogue validation and
   relevant tests. For adapter or publication changes, run repository checks and
   strict documentation/viewer validation as required by CONTRIBUTING.md.
8. Publish an evidence-backed PR update with a leased branch update. Report new
   and enriched counts, countries, unresolved gaps, checks and the PR link. Do not
   auto-merge without user authorization. Keep the PV research task independent.

If no reliable additions are found, report that accurately and record a concise
checkpoint when it will prevent repeated work. Do not create empty commits or
invent records to satisfy a target count. If a source becomes unavailable, retain
its previous observation and record the access failure rather than asserting a
new verification.

The offline `bess_oem_catalogue.kehua_panels.parse_panels` adapter stages reviewed
skid, cabinet and PCS panels with explicit expected model order and field labels.
Retain channel currents, component-specific enclosure classes, adjustable transformer
ratios and unspecified efficiency boundaries in native observations. Embedded public
index routes can resolve canonical HTML URLs; unavailable PDFs confer no specifications.

For the EA 29 September 2026 status overview, `scripts/stage_bess_nz_status.py`
stages six local HTML rows and checks the release, headers, units and unique names.
Retain owner slash labels and commissioning months verbatim. Commissioning month,
registry effective date and exact commercial-operation date are different facts;
older table statuses must not replace later owner evidence. Rotohiko's November
registry date and December overview month remain unresolved.

The Kehua panel parser also accepts a reviewed field set per model, for native
label-spacing differences. Numeric bounds such as `<100ms` remain bounds; embedded
markup still fails. PV MPPT limits must not populate battery DC limits, optional
battery ranges must not become fixed energy, and EMS auxiliary supply must not
become system power. Elum controller maximum controlled BESS capacity is a control
limit, not energy installed in the controller. Optional enclosure IP and WIP
metadata require explicit qualifiers; the MC-XL solar-row MWh label is unresolved.

For Portugal's C21-i08 final grant report v1.1 (8 April 2025),
`scripts/stage_bess_portugal_grants.py` reads local layout text and requires all
41 final ranks on PDF pages 27–28. It stages application IDs and Decimal funding
observations, preserving cumulative arithmetic discrepancies. An award ID is not
a physical project identity. Reuse rights and site reconciliation are prerequisites
for import; preliminary-table MVA limits and minimum hours cannot yield BESS MW/MWh.

`scripts/stage_bess_elum.py` reads the exact three-column ES Compact / ES / ES+
controller table. Changed columns, duplicate rows and unsupported units fail closed.
Common merged cells require visual review. Controlled plant capacity, optional IP
kits and control-loop timing retain their own boundaries; none is battery hardware
capacity or unconditional performance. The Taiwan review distinguishes Xia Xing's
two actual chemistry-specific systems from subsequent simulation scenarios.

For Ingeteam revisions 300002287_C, 300001994/F and 300002273_A,
`scripts/stage_bess_ingeteam.py` stages local PDF layout text with `--series M`,
`C` or `350`. Named M600/M630/M660/M690 module configurations and C600–C840
columns remain distinct. The eleven 350TL AC-voltage operating points remain
one model. Preserve kVA, charge versus discharge, 30/40/50°C conditions,
grid-tied versus off-grid DC limits and converter efficiency boundaries.
Common cells, optional accessories and footnotes require visual review.
Changed revisions, headings, units or column counts fail before staging.

For the final Portuguese C21-i18/2026 table after tie-breaking, use
`scripts/stage_bess_portugal_grants.py --final-2026`. It requires 45 unique
application IDs and the EUR80,250,000 funding control total. Zero funding
remains zero; the GGS charging column has no published unit in this table
and must not become MW. Applicant/company IDs are not physical-site identities.
The adapter stages locally only; site reconciliation and reuse review remain
prerequisites for canonical ingestion. This is a different cohort from 2025.

## EU Innovation Fund and Studer offline staging (4 November 2026)

`python scripts/stage_bess_innovation_fund.py INPUT.html --output candidates.json` stages grant inventory rows without treating grant status as plant lifecycle. Review technology and physical site identity before using the existing upsert API. Shared factsheet URLs are flagged for manual identity review. The 49 reviewed candidate decisions are in `research/2026-11-04_eu_studer_review.json`.

`python scripts/stage_bess_studer.py INPUT.html --series xts --output candidates.json` accepts xtm/xth/xts original public product HTML. It requires exact model headings, consistent mobile/desktop tables, units and footnotes. VA stays apparent power; optional ecf 01 operating points stay within the original model. No network access or canonical writes occur in either adapter.

For Studer AJ product pages, `scripts/stage_bess_studer_aj.py --series 275-400`
(and `500-700`, `1000-1300`, `2100-2400`) stages local original HTML. It checks
exact models, responsive tables, units and conditional footnotes. These are
unidirectional stationary battery inverters, not bidirectional PCS. VA stays
apparent power, maximum inverter efficiency stays separate from RTE, and optional
solar-regulator standby conditions do not define extra model records. Review
source terms and lifecycle before upsert; the six smaller models are discontinued.

For BOE open-data daily indices, `scripts/stage_bess_boe.py --date YYYYMMDD`
selects all battery-title mentions across the day's issues and sections. Original
XML needs an `Accept: application/xml` request header. The offline adapter checks
response/date, identifiers and URLs; `inspect_notice` checks original SHA-256 and
returns numbered paragraphs for review. A title can denote non-stationary cells,
a multi-site procurement or an amendment to an existing hybrid: never auto-import.
One notice can cover distinct named projects, so retain project-qualified external
identities and the shared notice in evidence. Administrative permits do not imply
physical construction. Preserve gross/usable and container-arithmetic conflicts.

`scripts/stage_bess_neata.py --series lfp48` (or `ess`) stages exact original
Neata HTML tables. Model/header/units changes fail closed. Pack Ah is not cell Ah;
current is not inferred watts, unnamed dimension-axis order stays native, and
system efficiency is not automatically round-trip efficiency. Cycle and warranty
claims without conditions remain qualified observations. Retain external
communications separately from interfaces and reserved fire equipment from
installed equipment. No project/model assignment follows from common branding.

The offline `bess_oem_catalogue.neata_ups.parse_sc_partitions` stages the complete
SC48/SC51/SC76 voltage partitions from original Neata UPS HTML. Changed exact
model lists, units or 60-second peak notation fail closed. Pack capacity and
battery-type labels can disagree: retain both, without deriving energy. Approximate
mass is not exact mass, parenthesized charge voltages have an unspecified meaning,
and generic NC/TC chemistry or lifecycle claims do not establish SC specifications.
Higher-voltage partitions reuse some model codes and need independent identity review.

`bess_oem_catalogue.neata_ups.parse_high_sc` stages the remaining thirteen
SC102/192/204/240 models and checks the shared prior partition. Preserve the
SC102 type-label/voltage-column discrepancy and 27/30Ah discrepancies; do not
infer energy. Plain kW maximum-discharge observations have no stated continuous
duration. Repeated NC/TC codes are outside this adapter's reviewed identity scope.

`neata_ups.parse_low_voltage_cabinets` stages twelve reviewed unique NC/TC models
at 204.8/240/256 V. It rejects repeated selected codes anywhere in the table,
changed units and unknown timing syntax. NC40/TC100Y remain outside scope because
codes repeat at other configurations. NC35's exact printed `60mi` is preserved
as ambiguous text, never silently corrected to minutes. Maximum and timed
power ratings are separate observations; neither defines stored energy.

`neata_ups.parse_mid_voltage_cabinets` stages fourteen unique NC/TC models at
384/409.6 V. NC56 remains excluded because its code repeats at two configurations.
The TC48Y/TC48 labels give 30 Ah but capacity columns give 27 Ah; preserve both
in conflicts and withhold a resolved pack-capacity scalar. Timed discharge
ratings do not establish stored energy or indefinite continuous power.

`neata_ups.parse_upper_voltage_cabinets` stages thirteen unique NC/TC models at
480/512 V. Full-table repeated codes TC100Y and NC40 remain excluded. TC60Y/TC60
have conflicting 30 Ah type labels and 27 Ah capacity columns; keep both native
observations and withhold resolved capacity. Maximum power and timed discharge
ratings remain separate, with no inferred stored energy or continuous power.

`neata_ups.parse_final_voltage_cabinets` stages the final 23 unique cabinets at
614.4/716.8/768 V. Repeated NC56 remains outside accepted identities. TC72/TC84/TC90
retain conflicting 30 Ah labels and 27 Ah columns. NC42/TC84 omit the power-unit
suffix under a generic W header: retain native text without resolving a power
scalar. Do not infer energy or repair unusual timed ratings.

For Microcare manuals INV-1-5kW-LION-2018-4-V10R5/6 and the reviewed
2021-1-V21R1 editions, `scripts/stage_bess_microcare.py` stages local
`pdftotext -layout` text. Exact model columns, revision, units and voltage
envelopes must match. The three manuals yield18 observations but17 identities:
5kW48V appears twice and must be reconciled before upsert. Preserve8kW
manual/datasheet current and standby disagreements and10/15kW AC-current
disagreements. Grid-assisted200% throughput is not battery inverter rated power;
peak efficiency is not RTE, L in LxWxD is not automatically height, and warranty
eligibility depends on manufacture date. Never create unlisted voltage variants.

### TAB OPzV partition

`scripts/stage_bess_tab_opzv.py --text LOCAL_LAYOUT_TEXT --output NEW_JSON` stages the 14-model brochure page 12 partition offline. Obtain text with `pdftotext -layout` after reviewing source terms and checksum. It rejects changed revision marks, units, heights, rate basis and identities. Staging is not acceptance: compare the live OEM table before the existing upsert API. The 5 November review found differing measured Ah, fault current, masses and resistance; keep both observations in quarantine. Nominal Ah is not measured C10 Ah, H2 includes terminals, and neither fault current nor charge-rate formulas establish active power. See [review ledger](research/2026-11-05_opzv_latvia_review.json).

For Fullriver DC Series, `scripts/stage_bess_fullriver.py` stages exact selected
HTML cards, requiring one metric and one imperial panel. Pass reviewed model
headings with `--models`; suffix variants are not equivalent. The brochure tables
on PDF pages 2 and 3 are raster and require visual transcription; they repeat
identities but disagree on DC150-12 capacity/reserves and DC85-12 height. Preserve
56A versus75A reserve conditions, Ah per battery unit, cranking temperatures and
removable-post qualifiers. Undated web/PDF physical differences remain holds; do
not infer energy, cell count or a newest revision. Mobility-only PowerVault packs
are excluded without stationary evidence.

Fullriver individual-sheet electrical tables use `fullriver.parse_datasheet` on
local layout text. Keep per-battery Ah separate from cell Ah; retain the explicit
SoC, temperature and per-cell endpoint. Raster sheets require visual review.
Undated sheet/brochure conflicts remain observations, not silently chosen ratings.

For ADB TCS220320-2, `scripts/stage_bess_adb_pacific.py` stages only Table3.3's
four Cook Islands rows from local layout text. It rejects changed identities,
units, report date and missing chemistry/SoC qualifications. Year of installation
and completion differ; old and new energy observations remain quarantined.
`scripts/stage_bess_fullriver_conditions.py --model EXACT` stages native temperature
classes and bank charging columns. `--include-small-unit` adds reviewed small-battery
rate/mechanical tables. Unknown C3/C2/C1 stays absent; anomalous printed values
require review. Preserve case/terminal height and undated web/PDF discrepancies.

For DCCEEW's 12 October 2026 community-battery table,
`scripts/stage_bess_dcceew_community.py` accepts a local attributed reader-text
export, including optional line prefixes. It validates the seven regional tables
and 57 displayed applicant/location rows. The narrative says 58 locations; do not
invent the absent row. Direct HTML returned 503 during this pass, so the evidence
ledger fingerprints the reader export without claiming an original-HTML hash.
One programme location may aggregate several batteries. Review each natural
identity against the canonical catalogue before upsert. Grant applicants are not
automatically owners, grant amounts are not capex, and “In progress” does not
establish construction. Keep operational-From dates separate from commercial COD.
Refresh the source date before continuing; the adapter rejects changed partitions.

`scripts/stage_bess_fullriver_conditions.py --include-terminal-case` additionally
stages exact-sheet terminal types and ABS case material claims. UL94-HB is retained
as the manufacturer's material-rating claim, not independently verified product
certification. The generic torque table uses highlighted applicable values and is
not parsed as a model-specific torque. A suffix in an index URL does not establish
an exact model when the printed sheet uses a base name or a raster heading.

For Pylontech Force-L1 v2.3 / Force-L2 v2.2 manuals,
`scripts/stage_bess_pylontech_force.py` stages the exact six/three system columns
from local `pdftotext -layout` output. It checks printed revision, module and
controller identity, column counts, module order and voltage bounds. Preserve
standard/normal/peak current classes and the unstated L1 discharge-peak duration.
The L2 filename says v2.3 but its cover says v2.2. System kWh is printed/rounded,
not a multiplication of module kWh. Separate module records must not inherit
system IP/current/efficiency. Review the mechanical and module tables separately.

## Force-H1-V2 offline table staging

After independently checking source rights, printed identity and revision, export
PDF pages11–12 using `pdfplumber`: combine `pdf.pages[10].extract_tables()[0]`
and `pdf.pages[11].extract_tables()[0]` into a two-table JSON array outside Git.
The optional PDF extraction dependency is not needed by the package parser.

```bash
uv run python scripts/stage_bess_pylontech_hv.py tables.json --revision '22P1FH1018 / 5PMPA08-00135' --output staged.json
```

The adapter validates model/component identities, units, single-string column order,
voltage bounds and numeric scope. It does not expand optional parallel arrangements,
fetch URLs, assign project components or mutate canonical records. Mechanical and
module tables, chemistry/compliance claims and printed revision still need visual
review. Use the existing upsert API after reviewed natural-identity reconciliation.
