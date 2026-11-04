# Kenya source screening and Pylontech component/service evidence

Started 4 November 2026, 03:50:03 Atlantic/Canary (UTC). PR #130 merged at
03:41:52; this isolated checkout starts at main 6b38f9a. Open PRs #131 and #132
were checked by title and all changed paths. Neither changes BESS or shared
bibliography files. Older launch reports remain historical.

## Accepted changes

One new project: Saigeri Solar Park BESS, Kenya, 160 MWh battery portion of a
40 MW AC / 60 MW DC solar design. The consultant's dated 8 October 2026 page
supports the 132 kV LILO at Kimuka, hybrid-site transformers and open-for-bid
stage. It does not establish battery MW, construction, operation, chemistry,
installed equipment or ownership. Eco Cloud is retained as technical consultant,
not silently assigned developer, EPC or owner roles. No photograph geolocation.

Two exact Pylontech components added: FH9637M battery module and
FC0500M-40S-V2 BMS control module. The original Force-H2-V2 manual specifies
module energy, cell arrangement, chemistry, voltage, mass, dimensions and thermal
limits, plus controller dimensions, service/communication ports and radio limits.
Cycle and design-life claims retain unknown test conditions; no warranty inferred.
Radio dBm and a separate combiner current are not converted into BESS ratings.

Eight existing records enriched: six exact Force-H3 single strings, FH10050 and
FC1000. Newly reviewed manual sections add long-term storage temperature/humidity,
SOC and recharge intervals, lowest-SOH expansion limits, SOC commissioning,
CAN/RS485 baud rates and termination, and maintenance intervals. Scope is explicit:
battery storage rules are not assigned to the controller; system commissioning
is not assigned as a standalone battery-module interface specification. Earlier
absolute storage-temperature discrepancies remain unchanged. A recommended
long-term storage range is not a correction of those absolute limits.

No existing numeric ratings, nested facts, conflicts or creation timestamps were
removed. No schema/parser change. Existing upsert validation was used; nested
extension collisions were explicitly reviewed before preserving both observations.

## Candidate decisions and source batches

Eight project candidates reviewed, one accepted, seven deferred. The complete
visible KETRACO planned-project table was attempted before isolated project pages:
11 rows, including one combined BESS/STATCOM/substation entry. That entry cannot
safely be split into battery projects or assigned its site-wide voltage. KenGen's
four named locations remain held because 100 MW / 100 MWh is a portfolio total
and its terms restrict redistribution. InvestKenya's Narok/Suswa pair remains
held because the 200 MWh statement is ambiguous across sites and USD 520 million
is portfolio cost. No capacity is allocated by proportion or duplicated per site.
Original InvestKenya HTML succeeded after the search reader timed out.

Thirteen equipment candidates reviewed: two new, eight enriched, three deferred.
H2-V2's three exact stack columns cannot yet be reconciled with existing H2
configurations and their later datasheet; no duplicate variants were manufactured.
The newer H3 V1.1 manual was freshly downloaded and its bytes match the registered
source. The older V1.0 linked by Victron was checked for revision only and was not
used to overwrite V1.1. Dynamic OEM download pages supplied no readable table;
public OEM/manual links were the alternative.

The project planning target was not reached: the inventory was transmission-heavy,
portfolio allocation ambiguous, and one owner's reuse terms restrictive. Ten exact
models/components received useful additions or enrichment; this is not ten new
models. Selected component tables and H3 service/storage sections are exhausted.
The backlog ranks unresolved site allocations and H2-V2 identity reconciliation.
No whole-record permanent rejections or new canonical field quarantines.

## Coverage, evidence and publication

Proposed totals: **1,997 projects / 42 countries / 318 sources** and **774 equipment
records / 46 suppliers / 372 sources** (761 configurations, 13 families). No new
countries or OEMs; all six regions retain coverage. These are catalogue counts,
not operational capacity estimates. The dated market ledger retains IEA's comparable
2025 utility-scale GW-additions examples, with a fresh byte check. Operational GWh
ranking remains unavailable; Europe and Australia/New Zealand scope discrepancies
are retained, not converted or combined.

Original permitted source bytes and checksums remain outside Git. Field evidence,
locators and source terms are committed; no full manuals or binary snapshots.
The previous two bibliography queues are now integrated (eight references), along
with the two new sources. Historical queue files remain unchanged; the review
ledger lists the integrated IDs. Citation exports regenerated consistently.

Root storage and shared memory were full at discovery. Only this task's old,
reproducible documentation builds and already-published prior checkout were removed;
source bytes and prior evidence logs retained. Validation commands and actual
elapsed effort are recorded in the companion validation file. Leave the resulting
PR open and unmerged. No remote CI success is assumed.

Validation concluded at 03:59:32 Atlantic/Canary after 9.49 minutes.
57 focused and 15 viewer tests passed. The full suite passed 2,143 tests with
15 setup errors from the unchanged Data Center encoding defect addressed in
open PR #131. Strict documentation is blocked by that same inherited file.
BESS validation, preservation, deterministic snapshots, lint/format, ty, citation
and repository checks and both offline examples passed. All three wheels/sdists
and strict Twine passed after moving the build cache off the full root volume.
No completed documentation-link or remote-CI success is claimed.
