# 2 November 2026: French registry coverage, Rolls models and Lithops enrichment

## Outcome and live repository state

Started at **16:50:05 Atlantic/Canary (UTC+0)** on 2 November 2026, from main
`f379469be29427b5265d0347cf883d7efdd2957a`. PR #44 and the later BESS PR #74
are merged; they were not reused. Open PR #47–49 titles and all changed paths
were inspected: workflow-only changes. Main still matched this base at the
publication preparation check. Prior PV additions on main are preserved. This
pass creates a new scoped BESS research branch and leaves its PR open.

Accepted **113 new French battery installations, one enriched existing Namibian
project and 16 exact Rolls models**. No equipment enrichments or new country;
Rolls Battery is a new supplier, distinct from Rolls-Royce. Current totals:
**1,465 projects / 34 countries / 194 sources**; **397 equipment records /
39 suppliers / 152 sources**, comprising 384 documented configurations and
13 families. France has 116 project records. All six world regions remain
represented; these counts describe the sampled catalogue, not market capacity.

The French candidate ledger contains **220 unique detailed candidates: 113
accepted and 107 held**. A further 578 downloaded rows were used only to screen
identities and remain unreviewed for acceptance. Held-reason counts overlap:
66 same-commune groups, 39 confidential names, four hybrid/multiantenna scope
cases and two possible overlaps with curated projects. No whole-record permanent
rejection, automatic fuzzy merge or retirement inference was made. Five accepted
French records have anomalous energy fields withheld. Lithops retains one new
planning conflict, giving six project records with new field quarantines. One
Rolls model has an unaccepted charging-voltage claim. All 16 selected model pages
were accepted, with no whole-model hold. Separate discovery leads (12 NGEN,
four METLEN Italy and 19 EnerSys table models) were deferred on terms/scope grounds;
they are not counted as accepted or as detailed French candidates.

## Project evidence and reconciliation

The ODRÉ national register was attempted as the scalable official source before
isolated announcements. Its 31 August 2026 snapshot was processed on 20 October
2026. Metadata, Etalab Open Licence v2.0, technology classifications, a sample,
field glossary and the EIC renumbering notice were inspected before extraction.
The explicit battery-only filter uses `Stockage non hydraulique`, `Batterie`,
`BATTE` and at least 1,000 kW. Eight bounded API pages contain 798 unique EICs.
First 200 rows plus the complete 22-row RTE subset overlap by two, yielding 220
reviewed candidates. All eight pages support conservative same-commune identity
screening; only the reviewed partitions contribute records. Source freshness
was checked again after processing and title, processed date, revision, count
and licence were unchanged. The backlog preserves queries, page hashes and cursor.

Each accepted row is one explicitly named, single-installation EIC. Names remain
registry labels, without inferring ownership. Added fields include installed MW,
stockable MWh, charging and connection capacities, grid operator/substation,
published voltage, department/region/commune, operating status as of the snapshot,
and source version/industrial-service dates. Locations are delivery-point areas,
not surveyed coordinates. AC/DC and gross/usable bases remain unspecified; annual
energy is never substituted for storage. Industrial-service dates remain separate
from contractual commercial operation. The canonical 60-field schema is unchanged.

Saucats BARBAS01 was explicitly reconciled through RTE's January 2026 notice:
former EIC `17W000001600745Y`, current `17W000001637626Q`; both are preserved.
The five implausibly small energy entries (Chervey, Jonzac, Montendre, Marennes,
Fontenilles) retain reported kWh and evidence in conflicts, with no factor-of-1,000
repair. Dunkerque FORTELET, Orbec and same-commune multiple EIC groups remain held
until site/phase evidence establishes independent assets. All prior Australia,
Chile and other held records remain unchanged.

GOPA's owner-engineer page enriches **Lithops BESS** with 220 kV grid connection,
reported two-hour duration, 95% required availability, 80% required RTE with
unspecified measurement boundary, and the March 2026–February 2031 advisory
service period/partner. Procurement requirements are not measured performance.
The owner-source 19-year/November 2028 and engineer 15-year/Q3 2028 planning
horizons are retained separately. No status promotion or new phase is inferred.
The Namibian environmental registry returned 503; the owner portfolio's future
BESS-ready PV item is not an installed battery project.

## Exact equipment and access review

Rolls' current catalogue explicitly lists renewable-energy applications for all
16 selected physical models: S12 24/27/31/185, S6 GC2/GC2-HC/145/305/L16-EX/L16/
L16-HC, 12CS11P, 4CS17P and 6CS17P/21P/25P. Each exact HTML specification page
was parsed and checked independently. Model-specific revisions, 4/6/12 V and
cell quantities, four to nine discharge-rate Ah/current pairs, published charge
currents and voltage conditions, float/self-discharge, terminal/thread, materials,
plates/electrolyte reserve, dimensions including terminals and qualified sample
mass are retained. These are flooded lead-acid monoblocs for stationary systems;
they are not integrated BESS. No project equipment assignments were invented.

Capacity Ah is monobloc capacity at the stated discharge rate, not cell capacity.
No energy is inferred by multiplying voltage and Ah. No active power, efficiency,
warranty years, cycle count or temperature range is extrapolated. Sample mass
remains qualified; dimensions retain the OEM axis order. The 12CS11P page's
14.7–15 V/cell charging text is retained as a disputed observation, not silently
changed to V per battery. Marketing-page guidance encourages referencing current
OEM specifications; this does not confer an open bulk licence. Only bounded
factual records and evidence metadata are committed, not full HTML or brochures.

Alternative owner/OEM batches were examined before switching to defensible
sources. NGEN terms restrict redistribution; its Jesenice ratings also conflict.
METLEN/Dolomiti terms are restrictive, and the official San Severo permit differs
from the portfolio duration claim. EnerSys SBS terms restrict noncommercial use.
No gated form, contact request, purchase or control bypass was attempted. Exact
URLs, dates, offered fields and retry conditions are in the ranked backlog.

## Market priorities

The primary IEA commentary dated 29 May 2026 was reopened (CC BY 4.0). The named
comparable metric is **2025 stationary battery power additions in GW**: China
>63, United States 19, Australia nearly 8 and Chile nearly 1, among the countries
quantified. Europe 6.2 and Middle East >3 are regional comparators, not country
ranks. A comparable global operational stationary-energy GWh ranking was not
available and is not fabricated. This pass deepens underrepresented French
coverage, African grid metadata and a smaller Canadian manufacturer; the dated
market file records these distinctions.

## Implementation, validation and continuation

Two reproducible offline stagers were added: `scripts/stage_bess_odre.py` for
API bytes with an explicit reporting date, and `scripts/stage_bess_rolls.py` for
one exact model page with its expected identity and source URL. They do not crawl
or auto-import. Invalid/duplicate identities, malformed units and unrecognized
table structure fail closed. The existing importer/upsert API accepted the batch;
reviewed additive JSON extensions preserve all prior facts and creation dates.
The EIC alias addition is an explicit reviewed resolution, not a fuzzy merge.
Twenty-one meaningful parser/identity cases cover the new code.

Both typed Zstandard Parquet snapshots were built twice with matching manifests;
coverage/completeness manifests are committed. Raw source bytes, 23 verified
checksums and Parquet binaries remain in ignored artifacts under the established
artifact mechanism. The review ledger links each accepted/held EIC to source,
row and reason; exact model records map every populated field to primary evidence.
No schema, PV data or historical launch report was changed.

Checks actually run: full Python suite **1,647 passed, one optional cdsapi skip**;
focused catalogue/parser suite **49 passed**; Ruff lint/format and ty passed;
repository hygiene and citation export consistency passed; both offline usage
examples and eight viewer DOM tests passed; all three packages built (six
wheel/sdist artifacts). Strict Sphinx build (`-W --keep-going`) and link validation passed
(405 HTML pages). Both new documented CLI staging examples also passed. Catalogue validation, prior-fact preservation, source-byte hashes,
exact-model rate tables and current/previous EIC identities passed audit.

The 113-project and 16-model yields meet the planning objectives. This finishes
the selected first-200-plus-RTE batch and all 16 selected model pages; it does not
claim the remaining French inventory is exhausted. The next highest-value task
is refreshed offsets 200–399, skipping all reviewed EICs, followed by adjudicating
same-commune groups using owner/planning evidence. Remaining Rolls 2 V/8 V models
are a separate exact-configuration review. Unresolved terms/scope candidates
remain in the backlog rather than being used to inflate the accepted count.

## Elapsed effort and publication checkpoint

Work began at 16:50:05 and reached final publication preparation at
17:15:18 Atlantic/Canary (UTC+0), **25.2 minutes elapsed**.
Approximately 14 minutes covered discovery/extraction/initial reconciliation;
the remainder covered EIC identity resolution, manifests, tests, documentation,
package installation checks and publication preparation. The selected finite
source batch is fully reviewed; finishing within the available window does not
claim unprocessed French partitions are complete. All three installed wheels
and their public CLI entry points passed in a clean environment; six package
artifacts also passed Twine metadata checks. Main and open-PR paths were rechecked
without a conflicting catalogue writer or target-head advance.

Only accepted factual rows, evidence/held-candidate ledgers, source-specific code,
tests and derived text manifests are prepared for the new scoped PR. Nothing
from this iteration is merged by this run. Historical launch reports are retained.
