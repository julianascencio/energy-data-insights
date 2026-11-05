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
4. Stage national inventory candidates with `scripts/stage_bess_inventory.py`.
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
