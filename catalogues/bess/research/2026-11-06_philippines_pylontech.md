# Philippine project metadata and Pylontech low-voltage equipment

Started **6 November 2026, 01:21:16 Atlantic/Canary (UTC)**. Isolated checkout of
open PR #187 at `d305440e`; current main `4ef42de4`. Main, contribution guidance,
BESS/PV conventions, dictionaries, schemas, source registers, coverage and recent
research were reviewed. Open PRs #183–187 were checked by title and complete
changed paths. Only #187 owns the affected BESS paths. No shared schema edits,
subagents, contacts, login circumvention or schedule changes.

## Accepted work and identity reconciliation

**Projects: 17 historical registry rows reviewed; 15 existing projects enriched,
zero new projects, two previously unresolved rows held.** DOE/EVOSS December2024
Luzon, Visayas and Mindanao tables were rechecked. Their capacity/date observations
already exist and were not counted again. Previously absent dated operator,
combined owner/IPPA, site-address fragment, unit count and contract-code observations
were added. Exact prior registry mappings were reviewed; no fuzzy merge occurred.
The combined owner/IPPA column is not asserted to establish present ownership.
Registry units are not battery-container/module counts. Prior status, ratings,
phase scopes and conflicts remain unchanged. Kabankalan phase2 still needs scope
reconciliation; TMI's49MW diesel/battery hybrid figure is not battery-only capacity.

**Equipment: 21 exact configuration/component candidates reviewed; 19 accepted
new records, zero existing-model enrichments, two controller records held.**
Nine OEM-authored manuals supplied:

- Six Force L1 stacks with2–7 FL48074 modules and three FORCE-L2 stacks with
  2–4 FL4874M modules; two exact modules are separately documented.
- Pelio-L-5.12, US5000, US5000-B, UP2500, US2000, US3000, US3000C and Phantom-S.

These are actual table configurations, not an arbitrary combination of options.
US5000-B has a stated breaker and different weight; it is not a cosmetic alias.
Nine stack-to-module references resolve to exact canonical module IDs. Controller
names FC0048-100S and FC0048M-100S are preserved as component relationships, while
separate controller records await useful model-specific electrical specifications.
No equipment was assigned to projects. No OEM entity table was introduced.

The new rows retain energy basis, nominal/usable Wh where stated, exact voltage
limits, standard/recommended/normal/maximum/peak current classes and durations,
physical observations, charge versus discharge temperature ranges, communications,
IP scope, storage/altitude bounds and qualified cycle/design-life claims. The
Force96% efficiency statement has no established round-trip boundary. L1 maximum
discharge duration is unstated; L2 specifies15seconds. System kWh is the printed
rounded value, not recalculated from module count. Module-only records do not
inherit system-only IP/current claims. No active power, usable-energy calculation,
duration, warranty, cell supplier or independently verified certification inferred.
UP2500's raster cover/introduction/table were rendered: nominal2840Wh differs from
usable2550Wh; the integration page's2.55kWh is not substituted for nominal energy.

Printed revision controls: Force-L2 says2.2 despite filename2.3; US3000 says2.1
despite filename2.2. Original bytes and SHA256 are retained outside Git. Exact
versions, row/page locators, publisher versus distributor and field source maps
are in the source register and records. Historical manuals do not prove current
commercial availability. Existing created_at values and every prior fact/source
entry were preserved; updated_at changes only accompany substantive enrichment.

## Sources, terms, market priorities and lower project yield

A scalable official inventory was attempted first. Current DOE March2026 routes,
the June2026 project index and a CMS PDF were unavailable (502/403 or unavailable
reader route). EVOSS historical PDFs remain readable through the public reader;
original downloads returned403. Reader-export SHA256 is explicitly not an original
PDF checksum. IEMOP's reuse prohibition was freshly reconfirmed; no facts imported,
no consent requested, and its downloaded page/text removed. Existing DOE sources
remain immutable; the new capture ledger records this retrieval separately.

Pylontech's Japan/US current download listings were empty; the China product page
was uninformative. Victron's compatibility page and the public distributor index
led to Pylontech-authored manuals. Copyright/host policy was reviewed: this is
bounded factual specification extraction, not an assertion of open bulk rights.
No copyrighted manual, image, instructions or distributor-created descriptions are
committed. Government historical rows receive bounded manual review and attribution;
EVOSS's website copyright is not labelled an open licence. No paid/gated material.

IEA's29May2026 commentary was freshly checked. Its comparable selected-country
metric is **2025 utility-scale battery power additions**: China about55GW, US over16GW,
Australia about4.2GW. Europe4.6GW is a region, not a country. Comparable operational
stationary energy in GWh is unavailable there; no MW/MWh conversion is fabricated.
This pass rotates from Australia to Philippine metadata and Chinese OEM depth.
Existing representation of Africa, Asia, Europe, Latin America/Caribbean, North
America and Oceania is preserved. No new country or supplier label this iteration.

The15-project yield is below the50–200 planning objective because the fresh large
inventory routes are unavailable, IEMOP reuse is restricted, and the historical
17-row partition already exists except for two unresolved scopes. Useful enrichment
was selected over duplicate or thin projects. The19-model result meets the10–30
planning range. The selected nine manuals and three historical battery sections
are exhausted; no idle time or padding was used. The ranked backlog specifies
URLs, versions, licence/access assessment, offered fields, result, partition,
retry condition and next action. Highest project opportunity: a new accessible
DOE existing/committed inventory. Next equipment partition: current exact
US2000C/D manuals or substantive specifications for the two held controllers.

## Validation and current totals

Existing upsert API was used. Fifteen additive JSON collisions were reviewed with
explicit old-field preservation. No new whole-record quarantines or permanent
rejections. Source/identity references,9component links, no-op substantive replay,
old source entries and old created_at checks pass. One historical sources array
normalizes order on replay; set membership/facts and timestamps remain unchanged.
Two independent typed Zstandard Parquet builds are byte-identical for each
catalogue; all binary outputs stay outside Git under the established mechanism.

Current totals: **2,207 projects /48countries /413sources** and **1,239 equipment
records /56supplier labels /544sources** (1,226configurations,13families).
Cumulative PR relative to main: **58new projects,20pre-existing project enrichments,
47new equipment records,17pre-existing equipment enrichments**. This includes prior
PR work; the present increment is19new equipment records and15project enrichments.
Nothing in this increment is merged.

Local checks: **564 focused BESS tests**, **34viewer tests**, repository-wide
Ruff/format/ty, hygiene/citations and both offline catalogue examples passed.
The nine new synthetic parser tests reject changed revision, model identity,
units, configuration columns/order and invalid voltage bounds, and preserve merged
current scope and unstated peak duration. Full local Python/package suite was not
rerun; published-head hosted CI supplies those wider checks. Strict documentation,
publication and hosted CI results are recorded in the validation ledger/PR.

Research/extraction/reconciliation and overlapping local validation used about
**16minutes** through01:37. The selected defensible partitions are exhausted;
publication and wider CI follow. Final elapsed effort belongs to the PR's final
verification entry rather than an estimated completion time. Prior launch and
research reports are unchanged.
