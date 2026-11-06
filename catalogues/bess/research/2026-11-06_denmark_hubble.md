# Denmark/Baltic projects and exact Hubble equipment — 6 November 2026

Started **04:54:49 Atlantic/Canary (UTC)**. This iteration adds **eight projects and
four exact equipment configurations**, and substantively enriches **18 existing
Hubble models**. Denmark is new; Lithuania and Latvia deepen. No new supplier.
This is accepted catalogue work, not merged content from this iteration.

## Current state and concurrency

The checkpoint PR44 was historical. At discovery the compatible open PR187 head
was `223ea922baa60291efec649d50d5d03737ce9c10`, with main
`4ef42de474f69b5cdca5824410c06db0d851b434`. Repository instructions, both BESS
catalogues, schemas/dictionaries, workflow/source registers, current coverage,
recent logs/backlogs and compatible PV conventions were reviewed. No AGENTS file
was found. PR183–187 titles and changed paths were inspected; other work concerned
PV, wind, datacentres and hydropower, including shared viewer paths we did not edit.

The prepublication check found PR187 merged at **05:07:15**, with new main
`036429f93354749517d91ac62b18390ec7bccddc` and no open PRs. This batch is therefore
reconciled onto current main and published on a new research branch. We did not
merge PR187, reuse its closed branch, force-push or alter shared schemas/viewers.
Earlier PR totals are now historical merged additions, not this batch's yield.

## Candidate decisions and evidence

Eleven named project candidates reviewed: **eight new, zero existing enriched,
three held**, zero new whole-record quarantines/permanent rejections. Seven named
operating sites come from European Energy's dated portfolio; the eighth is
Telšiai, explicitly under construction. Separate sources add battery capacity,
hybrid boundaries, lifecycle, development/EPC roles and optimisation/balancing
contracts. No fleet-total row, project equipment assignment or inferred duration.

- Agersted and Stouby: separate battery MW/MWh, linked PV and EPC/integrator roles.
- Kvosted: 200 MWh, LFP and December2025 operation versus February2026 inauguration.
  The August portfolio's 2026 wording remains a chronology conflict, not exact COD.
- Måde: battery ratings and the dated Twig balancing/optimisation agreement.
- Kragerup: later operational evidence; earlier planned power/expansion stays in
  history. Its unknown operating MW/MWh remains null.
- Anykščiai and Saldus: battery capacities and Capalo AI optimisation/trading roles.
  Conflicting solar MW/MWp figures remain unresolved. The Saldus stake-sale
  agreement does not establish closing/current owners; hybrid price is not BESS capex.
- Telšiai: approximate power and energy with construction status, no invented COD.

Energistyrelsen's public data index was attempted before isolated owner articles;
its examined links exposed wind data, not a battery asset export. India's examined
PIB table contains ten state/UT aggregates, not named project identities. Neither
source supplies safe bulk project additions. Eurowind's test-project portfolio was
blocked by restrictive redistribution terms. The independent GreenLab host release
is queued for phase/lifecycle reconciliation. Skuodas lacks precise battery scope.
These are reviewed partitions, not a claim that all official registries are exhausted.

NIB's Kvosted release was initially staged, then its terms sections2/5 were found
to restrict redistribution/derivative use. **All NIB-only financing, ownership,
power and administrative-location claims and its canonical source entry were
removed before publication.** Independent European Energy facts remain. No full
source bytes, prose, images, private contacts or document layouts are committed.

Equipment: **23 exact-model candidates reviewed → four new,18 enriched, one
older-generation candidate deferred**. Three current OEM sheets supply Cube
50kW/143kWh V1.1,80kW/160kWh V1.1,105kW/241kWh V5 and125kW/261kWh V1.
This is one record per published configuration, not optional PV combinations.
Captures energy/voltage/current boundaries, distinct AC charge/discharge ratings,
module/cell counts, temperature/derating, cooling, mechanical observations,
interfaces/protocols, qualified cycle conditions and manufacturer compliance claims.
Unlabelled dimensions, approximate/max weight and unknown efficiency boundaries
retain qualifications. The80 variant's kVA/kW discrepancy and PV-rating mismatch,
and125 variant's IP54/IP55 conflict, remain unresolved rather than chosen scalars.

Seven exact/family-specific warranty PDFs enrich18 existing AM/BLADE/HV models.
Ten-year cell coverage is separate from two/five-year electronics coverage.
Earlier-of years/cycles, strict battery-temperature limits, purchase-invoice start,
registration/monitoring, remedy and storage conditions remain explicit. HV100Ah
three/five-year monitoring fallback contradictions affect11 accepted records.
Warranty cycle limits do not replace design/test life or imply guaranteed retention.
Cube V2 warranty applicability is held rather than assumed from rack terms.
The older105kW/215kWh catalogue is deferred pending revision/generation evidence.

Thus **three project and13 equipment records carry new scoped conflicts**, while
other supported fields remain accepted. Existing conflicts and Chile/AEMO/DOE/
Fullriver/US2000C/SS4083 holds are preserved. No automatic fuzzy merge was used;
natural names, aliases, countries and exact model/variant identities were reviewed
against canonical records and the batch. Existing upsert API was used;18 additive
extension collisions were explicitly reconciled without deleting old namespaces.

## Coverage, rights and reproducibility

Current totals: **2,218 projects /50 countries and territories /430 sources**;
**1,289 equipment records /57 suppliers /565 sources**, comprising1,276 exact
configurations and13 explicit families. Africa, Asia, Europe, Latin America/
Caribbean, North America and Oceania remain represented; this pass does not
pretend to add projects in every region. It uses18 accepted primary documents:
eight European Energy articles and ten Hubble PDFs. Original checksummed bytes
are retained outside Git, including access-policy/discovery captures and the
excluded NIB release. Copyright remains; bounded factual extraction is not a
claim of an open bulk licence. Privacy policies are not reuse licences.

The fresh IEA comparison ranks selected individually quantified countries by
**2025 utility-scale battery power additions (GW)**: China around55, United States
over16, Australia around4.2. Europe around4.6 is a regional comparator, excluded
from country rank. Comparable operational stationary energy stock in GWh is not
available in that source, so no GWh ranking or power-to-energy conversion is made.
This comparison guides priorities, not catalogue completeness or market share.

The reusable local warranty parser rejects unreviewed headings, incomplete terms,
ambiguous cycle counts and missing conditions. It stages observations only, never
fetches, assigns warranties, writes catalogue rows or overwrites an existing output.
Eleven synthetic tests exercise these failure modes. All seven original text
partitions replay successfully. Model applicability and remaining conditions still
require manual review; there is no inference of equipment installed at projects.

Validation:607 focused BESS tests;11 parser tests rerun after lint fixes;33 viewer
DOM tests; repository-wide Ruff/format/type checks; repository hygiene and citation
consistency; both offline usage examples; both catalogue validators; exact-ID and
field-source/reference checks; preserved created_at, prior facts/source entries;
no-op upsert timestamp stability. Typed Zstandard snapshots rebuilt twice byte-
identically outside Git, with manifest and field-completeness results committed.
The first rebuild correctly refused to overwrite an immutable snapshot; the final
changed source set was rebuilt into new directories. Full local pytest/gallery is
not claimed; the host has a previously observed PID collection limitation. Hosted
full tests/package/strict documentation results will be recorded in the new PR.

Research/extraction/reconciliation and overlapping checks used approximately
20 minutes before final branch reconciliation/publication. Final elapsed effort
and hosted results belong in the PR's completion note. The eight-project yield is
below the inventory target because examined official sources did not expose a
usable named BESS inventory, two source sites restrict reuse, and thin/ambiguous
candidates were held. Equipment work covers22 exact records, within the10–30
planning range including substantive enrichment. The selected seven-site portfolio,
additional named construction site, three current Cube tables and seven warranty
partitions are exhausted; no count or duration padding. Next actionable partition:
GreenLab44MWh phase/current status, then exact Cube warranty applicability and a
battery-specific official Danish register. Recheck source freshness and terms.

Machine-readable companions: [review](2026-11-06_denmark_hubble_review.json),
[ranked backlog](2026-11-06_denmark_hubble_backlog.json),
[captures](2026-11-06_denmark_hubble_captures.json),
[markets](2026-11-06_denmark_hubble_markets.json),
[coverage](2026-11-06_denmark_hubble_coverage.json),
[manifests](2026-11-06_denmark_hubble_manifests.json), and
[cumulative comparison](2026-11-06_denmark_hubble_cumulative.json),
[concurrency](2026-11-06_denmark_hubble_concurrency.json), and
[validation](2026-11-06_denmark_hubble_validation.json).
