# Legacy Solar MD configurations and Kosovo design evidence — 6 November 2026

Started **03:55:10 Atlantic/Canary (UTC)** from live open PR187 head
`240b81421c052aab970eb029843aebf6ea967b6e`, with main unchanged at
`4ef42de474f69b5cdca5824410c06db0d851b434`. Current catalogues, schemas,
dictionaries, source registers, manifests, workflow and previous logs were read;
PR183–187 titles and complete changed paths were inspected. Only187 overlaps BESS.
An isolated checkout was created. Clean obsolete own checkouts were removed to
recover disk space; source originals were preserved. No subagents or merge.

## Accepted records

**Eleven exact equipment candidates yield eleven new records**: ten unsuffixed
SS7000 stacks (SS7011, SS7013, SS7014, SS7016, SS7017, SS7019, SS7020, SS7021,
SS7023, SS7024) and SS6143. No existing equipment record is changed. These resolve
ten identities deferred in the previous pass and are distinct from the newer
SS6160-based -05 generation. Module quantities8–17, nominal energy114.4–243.1kWh,
voltage envelopes and nominal voltage come from the exact row table, not inferred
variants. The200A current rating has unspecified operating classification; it is
not normalized as continuous/peak charge/discharge current and no stack power is
calculated. Ten stack/module references validate against the SS6143 record.

SS6143 explicitly supplies CATL/LFP chemistry,14.3kWh nominal and13kWh usable at0.3C,
10kW nominal DC power,51.2V nominal,41.6–57.6V operating envelope,115kg and
364×700×234mm W/D/H, CANBUS/RS485,0–50C, and at least6000cycles at25C. DoD and
EOL retention are unstated. Charging99% is not RTE. Module-only conditions are not
copied to complete stacks. Manufacturer and cell-supplier roles remain distinct.

All ten stack model names AND energy ratings match warranty schedule rows1–10.
Their throughput limits are500,563,626,688,750,813,876,939,1000,1064MWh respectively.
The earlier of12years or throughput,60%retention, delivery start, separate latent
defect term, claim-test conditions and exclusions remain qualified by section9.
These are exact matches, not -05 extrapolations. The newly downloaded terms match
the prior original checksum; existing source metadata is preserved.

**Two project candidates yield two existing-site enrichments, zero new projects.**
MCA-Kosovo's19January2026 article records2.34ha and a Ferizaj-municipality-to-KOSTT
land transfer, with a historical February2029 completion expectation. Its15October
article identifies Bellopojë village for Istog and ESCorp's13March2024 establishment
and sole government shareholder. These are qualified observations; no operator role
is recast as presently operational, and land transfer does not establish a permit.

The official two-site summit portfolio is printed **24September2024**, despite its
August2025upload path. Pages12–13 propose lithium-ion technology, underground cables,
and KOSTT Ferizaj / Peja3 substations with400/110kV levels. Those are substation levels,
not inferred BESS terminal voltages. Its May2026award and August2028COD targets are
historical plans; October2026 bid evaluation and the later Ferizaj target remain
separate. No actual chemistry, contract award, current COD, status or capacity is
silently overwritten. Compact financing is not site capex.

No new whole-record quarantine or permanent rejection; no new country or OEM.
Two additive extension updates were reviewed per project ingestion step; prior
namespaces, facts, sources, conflicts and created_at remain unchanged. These two
projects were added earlier in this PR, so they do not increase cumulative enrichment
counts for records already on main.

## Source selection, rights and backlog

The official MMPHI environmental announcement inventory was attempted first for
project coverage. Its first visible October2026 page and targeted Albanian searches
did not expose the two target battery EIAs; unrelated PV reports are not battery
project evidence. This is **not exhaustion of the whole registry**. Published
September2026 pagination and exact document retrieval remain next actions. The
independent MCA two-site portfolio and two official articles supplied accepted
metadata instead. The portfolio's two rows are fully processed.

The Solar MD resource index and original manual/terms were refreshed. Manual Rev1.0
is dated26April2024 and applies to BMU H17; URL directory date does not replace the
printed revision. Specification pages8–9 were visually reviewed. Five original
files are checksummed and retained outside Git. Only bounded factual observations
and locators are committed, not full documents, artwork, instructions or table layouts.
OEM section11 retains intellectual property; no implied open bulk licence is claimed.
MCA pages retain copyright; privacy policy is not a reuse licence or a US-government
public-domain designation. No contacts, forms, payment or access bypass.

Fresh IEA comparison retains the named metric **2025 utility-scale battery power
additions**: China about55GW, US over16GW, Australia about4.2GW. Europe4.6GW is a
region. Comparable operational stationary energy GWh ranking is unavailable from
that commentary, with no GW-to-GWh conversion. Africa and underserved European
metadata deepen; all six regions remain represented.

Current totals: **2,210 projects /49countries and territories /422sources**;
**1,285 equipment records /57supplier labels /555sources**, including1,272exact
configurations and13families. Cumulative versus main:61new projects,28pre-existing
project enrichments,93new equipment records,17pre-existing equipment enrichments.

The equipment yield meets the10–30 planning range. Two project enrichments are below
50–200 because the target inventory partition exposed no exact BESS report and the
alternative owner portfolio has two sites, both already represented. Eleven exact
manual records and all ten applicable warranty rows are exhausted. Optional containers
and variable cabinets remain deferred; old DOE/AEMO/Chile/US2000C/SS4083 holds remain.
Next: September Kosovo EIA/award evidence and exact container/controller specifications;
never expand options into artificial configurations.

## Implementation and validation

`parse_legacy_ss7000` and `scripts/stage_bess_solarmd_legacy.py` stage local page9
JSON only. Eight synthetic tests guard edition, exact identities, module counts,
units, numeric values and voltage bounds. No network fetch, canonical mutation,
power or warranty inference occurs in the parser. Existing upsert APIs handle
canonical records; additive extension collisions are explicitly reviewed.

Local checks:596focused BESS tests,33viewer tests, Ruff/format/ty, repository hygiene
and citations, both offline catalogue examples, source checksum and exact-table
replay, reference/identity/preservation/no-op checks. Both typed Zstandard snapshots
rebuild twice byte-identically outside Git, with updated completeness/manifests.
Full local suite/docs are not claimed; the known host-process collection limitation
and disk pressure favor published-head full Python/package and strict-gallery CI.
Actual hosted results and final elapsed effort are recorded in the PR description.

Research, extraction, reconciliation and overlapping checks used approximately
9minutes through04:04 Atlantic/Canary; publication and full CI follow. Selected
manual and two-site portfolio partitions are complete; no duration padding.

Evidence ledgers: [review](2026-11-06_solarmd_legacy_review.json),
[backlog](2026-11-06_solarmd_legacy_backlog.json),
[captures](2026-11-06_solarmd_legacy_captures.json),
[relationships](2026-11-06_solarmd_legacy_relationships.json),
[markets](2026-11-06_solarmd_legacy_markets.json),
[coverage](2026-11-06_solarmd_legacy_coverage.json),
[manifests](2026-11-06_solarmd_legacy_manifests.json),
[cumulative counts](2026-11-06_solarmd_legacy_cumulative.json).
