# UK construction inventory, owner enrichment and Kehua PCS — 4 November 2026

Started **09:18:36 Atlantic/Canary (UTC)**. Continued OPEN PR133 from
`0c6a49340bb9fa059ab530e042134a66228e3f68` in a new isolated checkout. Current main
was `65c8cb6704a9b1cc1bf7529c19ad40eefa4b9144`. Read repository contribution
instructions, BESS workflow/specification, both schemas/dictionaries, source
registers, coverage manifests and recent logs. No AGENTS file was present.
The previous Australia/Chile/Belgium and OPzS/Scatec passes are historical baselines;
none of their candidates is recounted. Existing PV importer/upsert conventions
are reused. No subagents, contacts, registrations, purchases or schedule changes.

## Accepted records and scope

**Projects:50 new,2 substantively enriched; equipment:13 new exact models.**
Current totals are **2,058 projects/43 countries/333 sources** and
**857 equipment/49 suppliers/427 sources** (844 configurations,13 families).
Kehua is a new supplier; no new project country. All six regions remain represented.
These record counts are not global installed-capacity coverage.

The selected REPD partition contains122 battery applications marked Under
Construction:50accepted new standalone identities,2exact-ID matches already
canonical,26identity/phase holds,38co-location-scope holds,5depth holds and1freshness/rights hold.
All122 have individual decisions in the review ledger. No permanent record
rejections. Blackhillock has a total-energy field quarantine after owner review.
Existing conflicts, including the Atacama/Solar Ray and OEM physical-edition holds,
remain untouched. The70held new candidates are not accepted or merged records.

The fresh July2026 CSV is byte-identical to the existing registered source.
The publisher still lists3August2026 as its latest release. An old record-update
or forecast date does not become current operation. Construction status denotes
that dated registry observation, not observed live physical progress or a new COD.
No automatic promotion of planning, energisation or funding status occurred.

The full canonical set and incoming partition were screened by exact registry IDs,
reviewed names, application references, authorities, addresses and original grid
coordinates. A1,500m screen flags review; it never merges identities. Near-site
clusters at Eccles, Capenhurst, Welkin Road, Uskmouth and Monk Fryston are held.
Mannington's name overlap, Brindley extension and CoalburnII's phase/aggregate
scope are also held. Separate application IDs alone do not establish separate
physical projects. The accepted list retains explicit standalone battery power,
planning reference, applicant label, address, county/region and source-native
planning milestones. Applicant/operator strings are not legal-owner assignments;
OS grid coordinates are not asserted as WGS84 or silently geocoded. Battery MWh,
chemistry, durations, equipment and cost remain unknown unless independently sourced.

Three SSE owner pages add useful evidence. Existing Monk Fryston and Fiddler's
Ferry gain explicitly labelled lead-contractor observations and coarse construction
milestones; Monk Fryston also gains its named substation and transmission-connection
observation. These are not unsupported EPC/manufacturer assignments. New Derrymeen's
registry identity gains200MWh, SSE development, Kirby construction/integration/BoP
role, Sungrow technology-supplier observation and a late2027 construction forecast.
No exact COD, grid voltage, equipment model or cell supplier is invented. Previous
facts, nested observations and created_at values are preserved.

Kehua's five complete HTML specification panels yield13 exact PCS identities:
three B-HUD, two C-HUD, two global HM-X2, three US HM-X2 and three legacy A models.
Each panel is tied to its exact tab, with no data copied across a model family.
Ten models have explicit rated ACkW; three legacy models only maximum kVA, with
active power unknown. Conditions include40°C/45°C where printed. Full-load DC
voltage ranges stay nested and are not promoted to absolute operating limits;
legacy500–900V operating range remains distinct from1000V absolute maximum.
DC/AC currents, AC wiring/frequency, enclosure ratings and conversion-efficiency
claims remain model-specific. NEMA4X is not assigned an IP equivalent. Maximum
PCS efficiency is not RTE. No energy, chemistry, warranty, cycle life or project
assignment is inferred. Original HTML has no printed revision; unknown stays null.

A final owner-source sample resolves Blackhillock beyond the stale registry status.
Phase1 entered commercial operation on3March2025 and is explicitly200MW/400MWh;
phase2 is underway. The one canonical project is partially_operational, with300MW
clearly scoped to the complete two-phase build-out. Its owner now reports700MWh
versus600MWh in the dated launch release. Both observations are quarantined and
whole-project energy remains null; no phase2 energy is derived by subtraction.
Phase-specific dates/ratings and the owner-reported Wärtsilä Quantum label remain
nested without a fabricated exact-model assignment or duplicate phase record.

Coalburn1 is withheld from the accepted count after a newer lifecycle discovery.
CIP's terms explicitly prohibit republication without prior permission, so neither
its technical details nor a replacement operating status is imported. An independently
reusable Alcemi release is the next route. This leaves50new projects, not51.

## Source selection, rights and yield

First attempted underrepresented Portugal's official2026 funding ranking and2024
programme report, searching the Portuguese programme names and detailed annexes.
Repeated applicant rows lack reliable physical-site identities; one power column
has an unclear unit. Public funding is not construction or operation. The public
footer reserves rights and no clear bulk-reuse grant was found. No applicant-only
project row or ambiguous power value was imported. The ranked backlog retains
an owner/permit crosswalk for the funded operations, after reuse review.

Ireland's fresh ESB Networks Q3 tables and EirGrid contracted report offered a
scalable alternative, but their explicit reproduction/public-use restrictions
prevented ingestion. Nine DSO contracted battery candidates were identified at
source level; no restricted technical details entered the catalogue. This triggered
the openly licensed UK alternative rather than ending the pass or defaulting to US.

REPD uses OGLv3, confirmed on the fresh GOV.UK publication page. The National Archives
licence endpoint returned403; the existing source registration and attribution are
retained, with this access result recorded. The source CSV's exact checksum matches.
SSE and Kehua retain copyright: only bounded attributed facts from the selected
pages are committed, not full pages, marketing prose, layouts or an asserted open
bulk licence. Their footer/privacy pages were inspected. The attempted SSE/legal
route404 is not treated as a successful terms read.

Kehua's public download-list request returned HTTP200 with application code500.
Search and direct OEM pages provided the fallback. Thus no PDF-only physical,
certification, protocol or warranty details are claimed. Two newer indexed family
routes remain unresolved after attempted title-based URLs returned404; this does
not prove their canonical publisher links are broken. No contacts/forms or access
controls were used. Original bytes and hashes remain outside Git; the committed
metadata names exact URLs, retrieval timestamps and panel/row locators.

Both working objectives were met. The selected122-row registry partition, six
owner pages and five complete13-model tables are exhausted at the current review
boundary. Remaining70 project holds and PDF depth need additional independent
sources, not padding. No claim of exhaustive worldwide research is made.

The market ledger freshly rechecks IEA's29May2026 comparison:2025 annual utility-scale
battery power additions in selected countries, not operational energy inGWh.
China55.10GW,US16.22GW andAustralia4.32GW are the selected-country chart values;
regional values are not country ranks and the earlier article/chart discrepancies
remain explicit. A comprehensive comparable operational-GWh ranking is unavailable
from this source. No MW/MWh conversion or regional-to-country substitution.

## Implementation, reproducibility and concurrency

The REPD adapter now accepts an explicit Under Construction partition while keeping
Operational as its default. Stable IDs do not change across lifecycle partitions.
An offline Kehua parser/CLI checks expected model order, panel cardinality, duplicate
fields, exact layouts and units. Fourteen new synthetic tests cover partition
selection, lifecycle identity, changed units/layouts, kVA versus kW, full-load voltage
and temperature-bound model panels. No schema or shared importer change.

Existing upsert APIs insert accepted rows; reviewed additive edits preserve prior
scalars, extension keys and creation timestamps. The preservation audit confirms
2,006 prior projects and all844 prior equipment records unchanged. Snapshots and
field-completeness manifests are rebuilt using the established package, with a
second byte-identical build. Raw documents/binary snapshots are outside Git.

Live PR133, Wind137, PV138 and new Data Center139 were inspected by title and all changed paths.
Wind137 has30 paths, PV138 has155 and Data Center139 has12; none overlaps BESS writes. Wind still modifies
shared references/viewer files, so eleven new bibliography entries are queued with
complete catalogue field citations. Earlier queues remain intact. Dependabot47–49
change workflows only. Main/head are rechecked immediately before publication;
no force push, PR merge or overwrite of concurrent work is authorized.

Validation details and actual elapsed effort are in the adjacent validation ledger.
The first new CSV test exposed pandas string-versus-numeric native-coordinate
representation; its assertion now compares the canonical fields while preserving
native source types. No production conversion was added to force an artificial
match. All checks below describe this iteration only, not historical test results.

Validation completed at **09:48:34 Atlantic/Canary**, after **29.97 minutes** of active research, reconciliation and checks. Publication follows the final concurrency check; the PR remains open. The selected bounded source batches are exhausted, while the recorded holds require new evidence.
