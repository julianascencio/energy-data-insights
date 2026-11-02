# 2 November 2026: exact MultiPlus models and African project enrichment

## Outcome

This pass continues open PR #74 from `ab99d448cbb9ad3a4ec515811daaba7e6bb1c657`,
with main at `2ead641336d6cf6417017f1de94792433060b85b`. PR #44 is historical
and merged. Open PR titles and changed paths were checked; #47–49 touch workflows
only. No PV data, shared schemas or earlier adapters were changed. The existing
Victron PDF-layout adapter is retained alongside the new HTML-table stager.

Accepted **2 new Nigerian projects, 4 substantively enriched existing projects
(3 Nigeria, 1 Kenya), and 18 exact Victron configurations**. Equipment enrichment
count is zero. Ten new-project candidates were reviewed: two accepted and eight
deferred; four additional existing identities were enriched. Five NEMSA
applications were staged/reviewed, plus an owner commissioning announcement and
two primary financing releases. All 18 explicitly named OEM configurations were
accepted; 3 retain disputed optional fields. No whole-record rejection or fuzzy
merge was used. There are **2 project records with newly quarantined capacity
observations**: Toto's installed-energy inconsistency and Kalobeyei's future
expansion targets. Eriwe's questionable charging-voltage text is retained as raw,
not accepted as a charging limit.

The resulting snapshot has **1,352 projects / 34 countries / 188 sources**, and
**381 equipment records / 38 suppliers / 135 sources** (368 exact configurations,
13 families). Nigeria, Kenya and Victron were already represented. Coverage of
Africa, Asia, Europe, Latin America/Caribbean, North America and Oceania remains;
this is a sampled research database, not a complete world inventory.

## Source batches and identity decisions

- NEMSA Uyo entry 1542032: 6.096 MWh battery summary, 2.938 MWp co-located PV,
  REA ownership and applicant-reported Huawei LUNA2000-2.0MWH-2H1. The 344 KW
  text under a kWh label is malformed, not an alternative energy measurement.
  No BESS MW, chemistry, installed container count or operation was inferred.
- NEMSA Toto entry 1467329: Samsung SDI ME3, lithium-ion, PowerGen ownership,
  installation chronology and interconnected solar configuration. The summary
  says 971 kWh while five bank rows each say 194.4 kWh: their explicit sum is
  972 kWh. Energy remains null. A separate PowerGen announcement establishes
  completed commissioning by its publication, without supplying an exact COD.
- Existing Fadama Bauna North, Eriwe and Ibaragun gain battery/cell/charging
  voltage observations and topology qualifiers. Ibaragun's 51.2 V may describe
  one module rather than the full DC bus. No inferred series count or battery
  discharge power was introduced. Previously verified facts remain unchanged.
- Existing Kalobeyei Settlement gains financing and counterparty metadata:
  USD 4.475 million senior secured loan, up to USD 4.2 million RBF grant with
  USD 1.26 million structured as a forgivable loan within that grant, and
  connection-verification conditions. These are financing amounts, not capex.
  Same developer, location and existing 541 kW PV rating identify the expansion.
  Its 2023 6 MWh and 2025 5 MWh targets remain separate observations; neither
  replaces the built 1.1 MWh, changes operating status or creates an additive site.
- Victron raster datasheet: all 15 named 230 V models (12/24/48 V DC across
  500/800/1200/1600/2000 VA) were visually checked. Three 12 V 120 V AC models
  use their separate HTML manual. W and VA remain independent. Captured facts
  include continuous and peak output, temperature derating, charging currents,
  voltage ranges, idle/search consumption, maximum inverter efficiency and its
  boundary, dimensions, mass, enclosure protection and controls. No battery
  energy, chemistry, system RTE, warranty or exact project assignment is inferred.
- The 2 kVA manual disagrees with the datasheet on enclosure material and
  automotive-standard edition for all three models, and on idle/search power
  for the 24 V and 48 V models. Disputed scalars are withheld; both observations
  are retained. Manufacturer-listed safety standards are not verified certificates.

## Scalable coverage and access limits

The national NEMSA source was attempted before individual owner releases, using
the existing offline allowlisted adapter. Uyo and Toto were advanced from the
prior backlog. The Uyo ESS attachment and Toto inspection PDF returned 404;
no error-page hashes were registered as source documents. Direct PowerGen access
returned 406, but primary indexed text was accessible; its checksum remains null.
Eleven of this pass's twelve registered sources have original-byte SHA256 hashes.
Downloaded bytes and generated binary snapshots stay in ignored artifacts.

A second inventory lead, the DTU/DANIDA October 2018 Kenya Miniwind study,
was inspected at its rights statement and representative Annex 1 private-site
rows. Its explicit private-study/research and no-further-distribution/commercial
reuse terms do not supply an open bulk-reuse licence. No inventory bulk import
was made. Renewvia's primary portfolio and releases were then examined as an
alternative. Ngurunit and Ringiti remain held pending explicit primary battery
facts; Balep, Bendeghe-Afi, Ekong Anaku and Opu are solar-hybrid-only in the
reviewed release. Kakuma III's JV release does not establish specific battery
hardware, and the UBA contract does not identify individual BESS sites.

The IEA 29 May 2026 primary commentary was reopened. Its comparable metric is
**2025 stationary battery power additions, GW**, not operational energy GWh.
Among quantified countries: China >63, US 19, Australia nearly 8, Chile nearly 1.
Europe 6.2 and Middle East >3 are regional comparisons, not country ranks.
A comparable worldwide operational-GWh table remains unavailable. This pass
prioritized underserved African metadata and a different equipment level (PCS)
rather than reimporting the dominant US/UK project sample.

The project yield is below the 50–200 planning range because the reviewed national
pages require manual identity/unit checks and the alternative inventory has
restrictive reuse terms. The 18-model equipment objective was met. The selected
finite OEM columns and defensible project batch were exhausted; remaining leads
require new primary evidence or clarified access, not more speculative rows.

## Implementation and validation

The new offline `stage_bess_victron_html.py` stages six model columns from the two
reviewed manuals. Explicit HTML spans control shared values; changed identities,
ambiguous spans, missing W/VA rows and duplicate labels fail closed. It does not
crawl, auto-import or resolve conflicts. Ten synthetic scope/unit/identity tests
were added; the two real source documents were staged and six active/apparent
ratings independently compared with accepted records. Existing importer/upsert
APIs and field provenance were used. Explicit reviewed extension augmentations
preserve old facts and creation timestamps.

Both typed Zstandard Parquet builds were repeated with matching manifests, with
coverage and completeness committed as JSON. JSONL remains canonical; binary
snapshots are outside Git under the established artifact workflow. Reference
exports and live documentation counts were regenerated; historical reports and
all earlier Australia/Chile and Nigerian holds were preserved.

Validation completed:

- Full Python suite: **1,626 passed**, one optional `cdsapi` dependency skip.
- Focused catalogue/usage/new-parser suites after final data enrichment: 40 passed;
  new and existing Victron parser suites: 30 passed (10 new cases).
- Catalogue CLIs, duplicate identities, field/source references, old timestamps,
  additive enrichment, raw checksums and six staged W/VA comparisons passed.
- Ruff check/format, ty, repository hygiene, citation exports, both offline examples,
  eight viewer DOM tests and six wheel/sdist package artifacts passed.
- Strict documentation build passed; completed link/asset audit: **401 HTML pages**.

Actual elapsed effort through final validation/publication preparation: **24.7
minutes**, from 15:56:06 to 16:20:49 on 2 November 2026
(Atlantic/Canary, UTC+0 on this date). Research/reconciliation and validation
partly overlapped. Finished the selected defensible batches before the 45-minute
window; no waiting to satisfy a duration. Publication is a leased fast-forward to
the same open PR, not a merge. Remote CI for the new commit is not claimed here.

## Next actionable work

1. Lokpaukwu NEMSA entry 1474922: refresh the application and site plan to resolve
   Lokpaukwu 1 versus 2 before creating a site or phase.
2. Obtain a corrected Toto bank schedule and explicit Kalobeyei expansion scope
   or as-built battery schedule. Preserve all existing capacity observations.
3. Find owner/GIZ/EnDev technical evidence for Ngurunit and Ringiti; do not reuse
   secondary 144/96 kWh reports as unsupported specifications.
4. Resolve Victron 2 kVA edition differences, then rotate to another OEM/product
   level rather than repeating these 18 configurations.

See the sibling review, ranked backlog, audit and both catalogue manifests for
exact URLs, bytes, IDs, candidates and per-field limitations.

Final concurrency recheck: PV PR #75 opened during this run at `9657176f`.
Its changed paths are confined to `catalogues/pv/` and `docs/pv-catalogue.md`;
there is no overlap with this BESS commit. Main and PR #74 head remained unchanged.
