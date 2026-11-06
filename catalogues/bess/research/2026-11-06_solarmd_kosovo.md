# Solar MD equipment depth, Kosovo sites and South African services — 6 November 2026

This continuation began at **02:49:13 Atlantic/Canary (UTC)** on open PR187 head
`67c5290d1999bea5ea154844d7d33e9452511999`, against main
`4ef42de474f69b5cdca5824410c06db0d851b434`. PR44 is historical. The live successor
PR187 and other open PR titles and changed paths were checked before edits.
An isolated checkout was used; no subagents, shared schemas, viewer changes or merge.
The existing BESS and OEM catalogues, source registers, dictionaries, research
workflow, coverage and recent logs were read together with compatible PV conventions.
Historical reports and existing quarantine decisions remain intact.

## Accepted increment and decisions

| Entity | Candidates reviewed | New | Existing enriched | Held/deferred |
| --- | ---: | ---: | ---: | ---: |
| Projects | 8 | 2 | 5 | 1 additional Komati claim set |
| Equipment configurations/components | 40 | 20 | 0 | 20 |

The combined Kosovo340MWh programme is excluded as aggregate context, not counted
as a ninth physical candidate or third accepted asset. No equipment candidate is
silently merged, no new whole-model quarantine is introduced, and no supplier entity
is added. Solar MD was already present. Kosovo adds **XKX**, explicitly documented
as a user-assigned code rather than an officially assigned ISO3166-1alpha3 code.

The scalable project attempt reviews the entire five-project South African BESIPPPP
Bid Window3 government list before isolated project research. Haru, Erfdeel, Vanilla,
Retreat and Bloemhoek already exist. They gain four **required** reserve services:
instantaneous, regulating, ten-minute and supplemental. The dated procurement
requirement does not establish delivered services, commissioning or present operation.
All prior capacities, lifecycle observations, ownership, conflicts and creation dates
are preserved; five extension collisions were explicitly reviewed as additive namespaces.

MCA-Kosovo and the Ministry's1October2026 procurement announcements, the Ferizaj
public-hearing notice and the Prime Minister's14October speech establish two distinct
sites: **Istog125MW/250MWh** and **Ferizaj45MW/90MWh at Sojevë**. They remain announced,
with bid evaluation observed on1October. Expected2027construction is a forecast.
ESC and KOSTT are planned owners/operators in qualified extensions, while MCA-Kosovo
is the implementing agency. No chemistry, equipment, coordinates, grid voltage,
permit approval or current operation is inferred. Compact-wide financing is not
battery capex. The unrelated Calistoga USA substring match was manually rejected.

The Solar MD exact technical tables provide:

- Thirteen distinct **SS70xx-05** stacks, SS7008-05 through SS7027-05 as explicitly
  enumerated in the source, with5–17SS6160modules,80–272kWh and40–136kWDC at0.5C.
- Exact **SS6160** and **SS216** modules with voltage/current limits, dimensions,
  mass, interfaces and explicit LFP/cell-supplier evidence.
- **BMS-EX** and **BMU-H17-01** controllers with supply/input envelopes, qualified
  relay/fuse/isolator ratings, communications and auxiliary-power information.
- Three individually marketed outdoor PCS bundles: **100kW/208kWh**, **125kW/272kWh**
  and **50kW/112kWh powered by SMA**. Their product labels and configurations are
  retained without inventing standalone SKUs or exact PCS model numbers.

The thirteen stack identities match exact rows in the warranty schedule: performance
coverage ends at the **earlier of12years or the model-specific throughput**, with
minimum60%initial-capacity retention. Delivery start, installation/data/maintenance
conditions, exclusions, DC claim-test conditions and the separate5year latent-defect
limit remain qualified. The sales PDF's printed revision is v1.0,13October2023;
its June2025URL is not a document revision date.

Charging-only efficiency is not round-trip efficiency. Outdoor battery-only RTE,
PCS conversion efficiency, battery voltage and PCS voltage remain separate. Recommended
DoD is not a cycle-test condition. PCS-only warranty is not whole-system warranty.
Common fully-loaded cabinet mass and unlabelled dimension-axis order are withheld
from normalized configuration fields. Controller relay ratings are not dielectric
withstand ratings; fuse/isolator currents are not operating currents. Sixteen
system-to-SS6160 links and one controller compatibility link validate; no component
is assigned to a project without evidence.

Twenty equipment candidates remain deferred: three variable SS216 cabinets, one
standalone outdoor energy range, six container option/range columns and ten older
unsuffixed SS70xx warranty identities lacking corresponding technical sheets.
They are not Cartesian product variants or inferred replacements for the -05generation.

## Access, evidence and market prioritization

Official government, programme and OEM sources were inspected for version, technology,
sample and access conditions before extraction. The source registers retain exact URLs,
publishers, dates, retrieval timestamps, document/page/column locators and checksums
for downloaded originals. Twelve source-byte checksums were revalidated. Original PDFs,
HTML, images and binary snapshots remain outside Git; factual JSONL and evidence
metadata are committed. The PM speech was readable through the public web reader;
direct retrieval returned403, so no original-byte checksum or access bypass is claimed.

Solar MD retains copyright and its sales terms grant no implied intellectual-property
licence. This is bounded factual specification extraction, not an open-licence claim
or redistribution of complete documents/table layouts/instructions. South African
[government terms](https://www.gov.za/terms-and-conditions-use-0) permit non-commercial
information/reference copying; commercial use requires permission. Attribution remains
to the Ministry's30May2025release, with the source-specific restriction visible.
MCA-Kosovo privacy terms do not provide a reuse licence, nor is its material assumed
to be US-government public domain. Only bounded project facts are retained.

World Bank Komati restructuring was examined as an alternative, but its600MWh and
financing observations were **not ingested**: current reproduction terms require
permission absent an applicable explicit licence, which was not established for that
PDF. Existing Komati stays unchanged. The blocked batch triggered Kosovo alternatives.
No forms, contacts, payment, registrations or control bypasses occurred.

IEA's29May2026 commentary was freshly rechecked. Its comparable selected-country
metric is **2025 utility-scale battery power additions**: China about55GW, US over16GW,
Australia about4.2GW. Europe4.6GW is a region, not another country rank. Comparable
operational stationary battery energy capacity in GWh is unavailable in this source;
no conversion from GW is made. All six world regions remain represented while this
increment deepens African equipment/project metadata and adds underserved Kosovo.

## Implementation, validation and follow-up

The new offline SS70xx-05 parser and CLI accept a locally extracted, reviewed table.
They reject changed revisions, headings, units, model suffixes/order, missing columns,
invalid module counts, dimensions and voltage bounds. Thirteen synthetic cases avoid
redistributing source tables. A replay of the actual local extraction reproduces all
thirteen accepted stack identities, energies, powers and module quantities.
The established upsert API, canonical natural identities and source-preservation rules
are used. Replaying current rows preserves updated_at; empty fields erase no facts.

Current totals are **2,210 projects /49countries and territories /419sources** and
**1,274 equipment records /57supplier labels /554sources** (1,261configurations and
13families). Cumulative PR-versus-main counts are **61new projects,28pre-existing
project enrichments,82new equipment records and17pre-existing equipment enrichments**.
These are accepted working-branch changes, not merged content.

Local checks pass: **588 focused BESS tests**, including13new parser cases; **34viewer
tests**; repository Ruff, format, ty, hygiene and citation checks; both offline examples;
reference, identity, preservation, checksum, relationship and no-op replay audits.
Both typed Zstandard snapshots rebuild twice byte-identically through the existing
package. Coverage and manifests are regenerated. The full local suite was attempted
but stopped during collection in the unrelated worldwide PV example when psutil could
not find host PID5. Full Python/package and strict full-gallery documentation checks
are delegated to normal published-head CI; no pending check is called a pass.

Research/extraction/reconciliation and overlapping validation used approximately
25minutes through03:14 Atlantic/Canary; publication and hosted checks follow.
The actual final elapsed time and published-head CI outcome are recorded in PR187.
The20equipment additions meet the10–30planning range. Seven useful project changes
fall below50–200 because all five official award-list identities already exist, the
Komati alternative fails its reuse gate and the Kosovo partition contains only two
sites. The selected defensible source partitions are exhausted, with no count padding.

Highest next project partition: official Kosovo environmental decisions/award notices
for the two sites, then fresh licensed South African parliamentary lifecycle evidence.
Highest next equipment partition: the older Solar MD SS70xx manual, reconciled against
the ten unsuffixed warranty identities; container ranges require exact configurations.
Recheck freshness and rights before continuing. Prior Chile/AEMO/DOE/IEMOP/Fullriver,
US2000C and SS4083 conflicts and holds are unchanged.

Reviewable ledgers:
[decisions](2026-11-06_solarmd_kosovo_review.json),
[ranked backlog](2026-11-06_solarmd_kosovo_backlog.json),
[captures](2026-11-06_solarmd_kosovo_captures.json),
[relationships](2026-11-06_solarmd_kosovo_relationships.json),
[market comparison](2026-11-06_solarmd_kosovo_markets.json),
[coverage](2026-11-06_solarmd_kosovo_coverage.json),
[manifests](2026-11-06_solarmd_kosovo_manifests.json),
[cumulative counts](2026-11-06_solarmd_kosovo_cumulative.json),
[validation](2026-11-06_solarmd_kosovo_validation.json) and
[concurrency](2026-11-06_solarmd_kosovo_concurrency.json).


## Publication and hosted verification

Data/code commit `22ecdd2f2fb87134a3d3f360289cd176e778dd88` was published at
03:15 Atlantic/Canary. All28published blob hashes and tree
`665e9acedbaea1929530cf80e6f5a0efe65cf1bf` match the reviewed index; the fetched
checkout is clean. Main and PR heads were unchanged at the expected-head non-force
update. The PR remains open and unmerged.

At03:22, [Python CI](https://github.com/julianascencio/energy-data-insights/actions/runs/42155450097)
passes **3,182tests on Python3.13** and **3,178passed /4skipped on Python3.12**, plus
lint/types/format, distribution metadata, installed wheels and examples.
[Documentation CI](https://github.com/julianascencio/energy-data-insights/actions/runs/42155450173)
passes strict full-gallery execution, database/viewer assets and **717HTML-page**
internal-link validation. PR Pages deployment is correctly skipped.

Actual elapsed effort to the verified data/code result: **approximately33minutes**,
comprising about25minutes of research, extraction, reconciliation and overlapping
local validation, followed by publication and hosted validation. The selected source
partitions are exhausted. This follow-up records validation evidence and adds no
canonical data or timestamp-only record changes. Final documentation-head status
is reported in the PR verification without attributing these data-head results to
another commit.
