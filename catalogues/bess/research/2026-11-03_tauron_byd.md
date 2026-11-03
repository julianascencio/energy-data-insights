# TAURON battery portfolio and BYD warranty depth

Started 3 November 2026 at 14:48:23 Atlantic/Canary (UTC), from PR #102 head
`6fa2cc4` and main `5063c416`. Both corrected remote CI workflows on the starting
head passed. Reviewed current workflow, dictionaries, source registers, manifests,
prior candidate ledgers and open PR titles/paths. Wind #101 and Data Center #100
advanced but their catalogue paths remain separate. Shared bibliography/viewer
changes are avoided. PR #44 and earlier launch counts remain historical.

## Decisions and implementation

The live TAURON investor page supplied a newer H1 2026 management report than the
annual-report backlog candidate. Read and visually checked all of Tables 8–9,
PDF pages 20–22: **20 candidates, 20 accepted new battery investments**. Four hybrid
battery subrows are separate from their PV ratings; Bytom standalone and hybrid
investments have distinct names/ratings. Proszówek and Proszówek II, and Stare
Bogaczowice I/II, remain explicitly distinguished. There is no aggregate parent
capacity row to double count. All 26 existing Polish identities were compared;
none is a TAURON site or a matching applicant. No automatic fuzzy merge was used.

The table supplies electrical power, implementing developer, expenditure through
30 June 2026, progress and completion targets. One-percent progress is retained
without assuming physical construction. Dąbie and Przewóz entered operation in
February 2026; month precision is preserved. Kuźnia Raciborska and Proszówek were
96% progressed at report preparation and retain dated construction evidence,
not assumed present-day operation. Two later owner searches found no unambiguous
commissioning confirmation for those sites.

A 20 October owner release adds **Jawor**, a ready-to-build acquisition at
28.27 MW / 120 MWh with 40 containers, February 2027 target, named grid operator,
110/20 kV station ratio and 2029–2045 capacity-market contract at 264.9 PLN/kW/year.
Station ratio is not promoted to project connection voltage. Acquisition does not
establish construction or operation, and exact equipment remains unknown.

A December 2025 owner release adds energy/location evidence to four of these new
records. Proszówek's earlier 8 MW conflicts with the later investment table's
9.5 MWe: both observations are retained, with the newer table as the dated canonical
rating and no derived duration. Its 16 MWh is not rescaled. The article's approximate
90 MWh aggregate conflicts with its named values summing 76 MWh; no aggregate
capacity is allocated. These are richer new records, not pre-existing enrichments.

Re-downloaded the original NFOŚiGW ranking and verified its SHA256 is unchanged.
Reviewed all 17 TAURON applicant rows: **16 exact site/beneficiary/power joins** add
application IDs, original titles, proposed investment costs and funding observations.
Their source-attributed CC BY-SA 4.0 terms are preserved. Proposed cost is separate
from actual expenditure to date, and recommendations are not signed awards.
Opole-Zawada remains held because it is absent from the owner battery tables.
The earlier 442 technology-unverified applications now have 16 supported mappings,
leaving **426**; earlier historical ledgers are not rewritten.

BYD's live download list already has ten BCU2.0 HVS/HVM configurations represented
in the catalogue, so no duplicate model rows were added. Read the complete ten-page
European warranty and visually checked the model and test tables on pages 1–3.
**Ten existing exact configurations gain substantive conditional warranty evidence**:
ten-year defect term, 60% retained usable energy, model-specific minimum throughput,
earliest-limit rule, temperature/current/voltage test conditions, start-date choices,
installation deadline, compatible-inverter condition and notification requirements.
Terms are limited to European purchases/installations and original buyers; no
worldwide or site-specific coverage is asserted. Original specifications and creation
dates remain unchanged. The listing/filename says V1.0 while every internal footer
says V1.2. That source-revision discrepancy is quarantined on all ten records rather
than silently resolving contract applicability. Test charge voltages remain test
conditions and never overwrite equipment operating limits.

The existing upsert API accepted new identities and surfaced populated JSON
collisions on evidence enrichments. Those replacements were explicitly reviewed;
no prior verified values were erased. No schema or importer code changed. Source
registers, factual JSONL, review ledger, pending references and reproducible typed
Zstandard Parquet manifests are committed; original bytes and binaries stay outside
Git. Copyright is retained for owner/OEM material; these are bounded factual
observations, not a claimed open bulk licence. No registration, payment, contact or
access-control bypass was used.

## Coverage and next work

Current totals: **1,883 projects / 39 countries / 284 sources**, and **679 equipment
records / 44 suppliers / 343 sources** (666 exact configurations, 13 families).
No new countries or OEMs; all six regions remain represented. Existing project
records are unchanged; ten existing equipment records are enriched. There are no
permanent whole-record rejections. One project rating, one source aggregate and ten
model source-revision ambiguities remain explicit; one additional funding candidate
is held. Four new bibliography references are queued, bringing this PR's scoped
queue to 90 while Wind overlaps the shared registry.

The dated market comparison remains the same-day
[IEA assessment](2026-11-03_poland_containers_markets.json): 2025 annual stationary
battery GW additions among quantified countries. Comparable worldwide operational
GWh and missing national ranks remain unavailable; no MW-to-MWh conversion or
regional-as-country ranking is made.

The complete 20-row owner tables, one acquisition release, four-project technical
release, 17-applicant subset and ten-model warranty partition are exhausted for
reviewed acceptance. The 21-project yield is below the planning range because this
is a bounded owner portfolio, not a national battery census. Model depth was met
through ten meaningful enrichments, not new cosmetic configurations. Next: exact
Energa tender phases, Opole-Zawada battery proof and TAURON commissioning/engineering
ratings. BYD's applicable revision requires authoritative document clarification.
Validation results and elapsed effort are recorded after the checks finish.

## Completed local validation

1,860 Python tests passed without skips; 28 final catalogue tests passed after
registry joins. Catalogue validation, preservation checks, two matching final
Parquet builds per catalogue, Ruff, formatting, ty, repository hygiene, existing
citation consistency, 13 viewer tests and both offline examples passed. Strict
Sphinx and the 449-page link/asset audit passed. No package code/dependency changed,
so distribution builds were not repeated; starting-head remote CI passed.

Validated at 15:01:14 Atlantic/Canary: 12.9 minutes actual elapsed effort
through local validation, followed by leased publication and remote-state checks.
The selected defensible batches are exhausted; no idle time was added.
