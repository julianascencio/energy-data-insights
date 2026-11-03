# PGE inventory, Mauritius lifecycle evidence and TESVOLT configurations

## Scope and reviewed state

Started 3 November 2026 at 17:50:28 Atlantic/Canary (UTC). Continued open PR #102
from `5b52248c3bd9e248c225125ee179e211f74b0c85`, with main at
`5063c41694b17b1a3fc856ea9527a32211278203`. The November 1 PR #44 checkpoint is
historical, not the starting dataset. Existing Australia/Chile reconciliations,
Atacama/Solar Ray holds, Polish phases and OEM rating/warranty conflicts remain.
Read current instructions, both BESS schemas/dictionaries/source registers,
workflow, coverage manifests and recent research; reused the PV upsert API.
Worked in an isolated checkout without subagents or changes to shared schemas.

## Accepted changes

| Entity / source batch | Candidates reviewed | New | Enriched | Held |
| --- | ---: | ---: | ---: | ---: |
| PGE original TED notice, four lots | 22 | 21 | 0 | 1 |
| Mauritius ministry reports, eight site identities | 8 | 1 | 7 | 0 |
| TESVOLT, selected exact battery configurations | 12 | 12 | 0 | 0 |
| Socomec order codes, discovery and terms assessment | 29 | 0 | 0 | 29 |

The Socomec candidates were not individually extracted for specifications after
the terms check. One existing Freedom Won model was also rechecked as an access
alternative, but a 403 and incompatible indexed revisions yielded no accepted
changes. Zero permanent record rejections and zero new canonical field conflicts.
The Budzyń identity hold and the 29 terms holds are in research, not canonical rows.

Current proposed coverage is **1,908 projects / 39 countries / 293 sources** and
**707 equipment records / 45 suppliers / 352 sources**. Equipment comprises
694 exact configurations and 13 family records. TESVOLT is a new manufacturer;
no new project country. Africa, Asia, Europe, Latin America/Caribbean, North
America and Oceania remain represented. Counts are catalogue coverage, not
installed capacity or an exhaustive market census.

Against current main the cumulative PR adds **119 projects and 95 equipment
records**, and changes **five existing-main projects and 12 existing-main
equipment records**. This pass's seven enriched Mauritius records were introduced
earlier in this PR and therefore do not increase existing-main enrichment counts.

## Scalable project coverage and reconciliation

Retrieved the original public XML for [TED notice 719197-2026](https://ted.europa.eu/en/notice/719197-2026/xml),
version 01, published 19 October 2026. TED's documented public download route provided
the inventory even though the PGE technical-annex portal returned a CAPTCHA.
Reviewed all four lots and 22 named storage sites, the battery CPV classification,
procurement organizations, delivery conditions and original bid deadline before
extraction. The [TED legal notice](https://ted.europa.eu/en/legal-notice) permits
notice reuse unless otherwise stated; no contact-person information is exported.

Accepted 21 sites after comparison with existing Polish names, aliases, funding
identities and the incoming batch. Łuków I/II remain explicitly distinguished;
no aggregate lot/facility records are added. Budzyń remains held against existing
record `2561ff09-e29f-5ab4-badd-c41d6c061b61`: the funding applicant is Farma
Fotowoltaiczna Budzyń, whereas this buyer is PGE INWEST 21. Neither a shared
locality nor different organizations prove that the physical installations are
the same or different. Obtain parcel/site evidence before merging or adding it.

Each accepted site gains notice/lot/site identifiers, aliases, named-site labels,
dated announced status and buyer/service-provider roles. The original delivery
requirement is the earlier of 28 months after contract effectiveness and 30 June 2029;
the original bid deadline is 16 November 2026 at 12:00+01:00. These are procurement
requirements, not COD, an award, or evidence of physical construction. Site
MW/MWh, chemistry, equipment and coordinates remain unknown. Lot-level NUTS
geography is not assigned to individual sites. Buyer and service-provider roles
do not become unsupported owner/operator/EPC relationships.

The new offline `stage_bess_ted_pge.py` adapter checks the reviewed notice ID,
revision/date, tender ID, ordered lot set, site counts, battery CPV and 28-month
unit. It rejects duplicate names, changed layouts/revisions and XML entity/DTD
declarations. It stages candidates only. Nine synthetic tests exercise identity,
scope, unit and privacy boundaries; no downloaded XML is committed.

## Mauritius enrichment

Three original Ministry of Energy and Public Utilities annual reports provide
older but useful primary evidence. Relevant pages were visually inspected:
2018–2019 PDF23/printed21; 2019–2020 PDF20/printed19; 2022–2023 PDF30/printed29.
The State copyright terms allow accurately attributed factual use; third-party
images/text and the original reports are not redistributed.

- Amaury 2 MW and Henrietta gain installation observations by 30 June 2019. Amaury's
  25 October 2018 inauguration is stored separately from commercial operation.
- Jin Fei, La Tour Koenig, Wooton and Anahita gain explicit lithium-ion programme
  evidence, renewable-integration application and November 2019 installation
  contract history. The early 2021 target is historical, not a COD.
- Amaury 20 MW expansion gains explicit lithium-ion evidence and July 2022 contract
  history. Its later operational observation is preserved.
- Pointe Monnier, Rodrigues, is one new 1.5 MW project with October 2019 contract
  award evidence for design, manufacture, installation and commissioning.
  The original 2020 Q3 and revised early 2021 targets are not operation evidence.
  Energy, chemistry, supplier and present lifecycle remain unknown.

The current CEB portfolio URL returned404 both directly and through the reader;
cached snippets were not accepted as a current source. Earlier UNDP reuse holds
remain. All seven enriched records retain creation timestamps, prior evidence,
ratings and lifecycle fields. The audit checks every prior factual key.

## Exact equipment depth

Reviewed three original TESVOLT tables and their printed revision labels:

- D.01: seven TS HV 50/4-20 through 50/10-20 battery cabinets, with individually
  mapped 32–80kWh energy, voltage ranges, currents, dimensions and mass.
- F.01: two TS HV 70 configurations, 14/16 modules in two racks,67/76kWh.
- Printed H.01, filename I.01: TS 25 five-module, TS 40 eight-module and TS 50
  ten-module complete battery configurations,24/38.4/48kWh. Both revision
  observations are preserved; the filename does not silently override the footer.

Records include explicitly stated NMC chemistry and Samsung SDI cell supplier,
electrical limits, standby consumption, cooling/environmental limits, enclosure,
dimensions/mass, cycle conditions and qualified guarantee claims where scoped
to the exact configuration. Cell/module standards stay separate from product
claims; a listed standard does not assert an independently authenticated certificate.
The up-to-98% battery efficiency is not explicitly round-trip efficiency and stays
an extension observation. Datasheet guarantee periods remain qualified; design
life and cycle expectations are not converted into warranty promises.

For TS 48 V, the upper module table's voltage, cycle and guarantee observations
remain module-scoped rather than being promoted to cabinet-level specifications.
The complete-system matrix supplies cabinet energy, Ah/current, dimensions,
weight, standby and IP20. No active kW is derived from kVA, voltage/current or
C-rate. External SMA inverters are excluded from these battery-only configurations;
no battery equipment is assigned to any project without evidence. Optional
cabinet/inverter cross-products and scalable family combinations were not used
to multiply record counts.

TESVOLT's legal notice permits individual use of public downloads; this bounded
manual factual extraction is not treated as an open bulk-reuse licence. PDFs
remain outside Git. Socomec's section 5 restriction on specification disclosure
prevented accepting 29 discovered SUNSYS order codes; the alternative TESVOLT
batch supplied 12 substantive accepted configurations.

## Market priority, effort and continuation

Use the same-day [market assessment](2026-11-03_poland_containers_markets.json):
IEA 2025 annual stationary battery power additions, utility-scale plus behind-the-
meter, in GW. Among quantified country examples: China just over 63 GW, United
States 19 GW, Australia nearly 8 GW, Chile approaching 1 GW. This is not an exhaustive
world rank. Europe 6.2 GW and Middle East over 3 GW are regional observations, not
country ranks. Comparable worldwide operational stationary energy in GWh remains
unavailable; no power-to-energy conversion is made. This pass follows a pending
scalable Polish inventory while deepening underrepresented Mauritius and a
regional German OEM rather than importing another US bulk partition.

The selected source batches are exhausted: all 22 PGE sites, eight Mauritius
identities across three reports and 12 exact OEM configurations. The project
objective of 50–200 was not met because the inventory contains only 22 sites,
one has unresolved identity, annex ratings are gated, and the current CEB page
is unavailable. The equipment working objective was met without variant inflation.
No time was spent waiting merely to extend the run.

The ranked [backlog](2026-11-03_pge_tesvolt_backlog.json) records URLs, terms,
versions, yield estimates, processed partitions, retries and next actions.
Highest new regional inventory lead: Maldives URA's Energy Supply and Demand
Study 2018–2022. Inspect its licence and island-level battery fields before
accepting anything; annual energy is not stored energy. Next enrichment partition:
public PGE technical annex/site ratings and Budzyń parcel/corporate reconciliation.
Freshness checks are required before continuing any partition.

## Evidence, validation and publication

Seven new source-register entries carry exact URLs, publishers, revision/date
qualifications, retrieval timestamps, byte checksums and page/table/lot locators.
The [review ledger](2026-11-03_pge_tesvolt_review.json) maps each accepted/held
candidate and downloaded source. Unknown publication years remain null in the
seven pending bibliography entries. No empty value erases a verified fact.

Canonical JSONL uses the existing upsert API and validators. Two independent
typed Zstandard Parquet builds per catalogue produced identical manifests;
the committed [manifest](2026-11-03_pge_tesvolt_manifest.json) includes row and
field completeness counts. Binary snapshots and original source bytes stay
outside Git; the established docs/CI artifact process rebuilds distributable views.

Validation passed: 1,869 Python tests (zero skips), 37 final focused catalogue/adapter tests, Ruff lint/format, ty, repository hygiene and citation consistency. All 13 viewer tests and both offline catalogue examples passed. Strict Sphinx completed and the link/asset audit passed for 451 HTML pages. All three wheels and source distributions built with `--no-sources`; strict Twine validation and isolated installed-wheel/CLI checks passed. The actual XML CLI output exactly matched all 22 reviewed candidates. No remote CI result is implied by local checks.

Research/extraction/reconciliation ran from 17:50:28 to approximately 18:08 UTC; validation, review and publication preparation followed. At 18:14 UTC the elapsed effort was approximately 24 minutes. The selected defensible batches were exhausted and the equipment objective was met; publication follows the final concurrency check rather than waiting to fill 45 minutes.

Main, PR #102 and other open PR paths were rechecked. PV advanced and a new
Timestral PR #104 appeared; neither overlaps this batch. Wind/Timestral overlap
the shared reference registry, so seven additional bibliography entries are
queued in the BESS research directory (108 pending cumulatively), with all field
evidence already in the catalogue. Shared schema/importer/viewer files remain
untouched. See the [concurrency ledger](2026-11-03_pge_tesvolt_concurrency.json).
Publication uses an expected-head, non-forced update; the PR remains open.
