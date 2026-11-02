# Scatec project coverage and Victron/SMA equipment

2 November 2026, Atlantic/Canary (UTC). Started 04:54:09. This iteration used
an isolated checkout of main `65931a16f949d3e5db1c014d8330914a971f3d80` after
confirming that the preceding BESS PR #60 was merged. Open PR #61 contains PV
records/research only; #47–49 update CI/Pages actions. Titles and changed paths
were inspected. BESS workflows, both dictionaries/schemas, sources, manifests,
recent ledgers, CONTRIBUTING and the compatible PV storage conventions were read.
No new parallel database, OEM entity table or schema was introduced.

## Accepted additions and enrichment

Seven new projects: Kenhardt, Mogobe and Haru in South Africa; Magat, Binga,
Binga 2 and Ambuklao in the Philippines. Obelisk in Egypt receives substantive
financing enrichment: lender identities, non-recourse financing, equity bridge,
sovereign guarantee and estimated EPC share, with the 2025 observation date.
The USD 590 million estimate is explicitly for the complete solar-plus-storage
hybrid; it is not stored as battery-only capex. Existing ownership and operating
observations remain unchanged.

The project batch contains battery MW/MWh, separate lifecycle evidence,
co-location, phase scope, owner/JV roles and useful commercial terms. Kenhardt's
225 MW battery is distinct from its 150 MW contracted hybrid delivery; its
456 battery units are source-reported, without an inferred model. Mogobe's
ZAR 3 billion and Haru's ZAR 2.2 billion are dated estimates, not final costs.
Haru's preferred-bidder award remains announced/backlog, not construction.
Forecast commercial-close dates are retained as forecasts. Intended equity
shares and contracted future service roles are labelled separately from current
ownership and physical operation.

Kenhardt represents the combined battery portion of three plants once. Magat
represents both battery phases once, with 24 MW and 16 MW phase metadata; no
phase energy is derived. Binga and Binga 2 are explicitly distinguished phases,
without an overlapping aggregate row. The associated Philippine hydropower
capacity is excluded. The schema has no co-located-hydro enum, so that relationship
is preserved in extensions instead of misclassifying it as solar or standalone.
No chemistry, exact commissioning day, coordinates or equipment assignment is
inferred. An operating-by announcement is not automatically an exact COD.

Sixteen exact battery inverter/charger records were added: thirteen Victron
MultiPlus-II 230 V models from two OEM tables and three SMA Sunny Island -13
models. Victron Energy and SMA Solar Technology AG are new catalogue suppliers.
These are PCS components with external batteries, not integrated battery systems.
Stored energy, battery chemistry, cycle life and system RTE therefore remain null.

Equipment fields include continuous active output, separate apparent power where
explicitly in VA, temperature derating, overload magnitude/time, DC limits,
charge-current limits, idle/AES/search consumption, enclosure, dimensions, mass,
altitude, communications, manufacturer standards claims and warranty conditions.
The four new Victron models have a row labelled apparent feed-in power but printed
in kW; no apparent MVA is accepted from that row. Their nominal DC voltage is also
left null rather than decoded from the model string. The distinct 48/10k/150-100
and 48/10000/140-100 codes are not cosmetic duplicates.

Maximum inverter conversion efficiency stays in a qualified extension, never
in the system round-trip-efficiency column. SMA's nominal five-year warranty and
registration-dependent ten-year extension remain separate. Its 12/2022 technical
edition is historical; the live OEM page states the 4.4M version is no longer
produced. The three PDF specification pages were visually checked, including
shared table cells, model order, units and footnotes.

## Conflicts, source access and yield

Eight equipment fields across seven accepted Victron records are quarantined:
three mass differences, one charge-current difference, two search-mode consumption
differences and two maximum-efficiency differences between the undated English
PDF and Spanish manual. Both values and sources are retained; neither source
silently wins. Some mass differences may be rounding, but the unqualified scalar
is withheld. No whole equipment record was rejected. No existing SolaX, Baltic,
Australia/Chile or other unresolved observation was changed.

Twenty-two named project candidates were reviewed across the selected inventories:
ten Scatec battery scopes produced seven additions, one enrichment and two unchanged
existing records. Eskom's twelve sites produced seven existing matches and five
continuing holds: Rietfontein, Witzenberg, Ashton, Cuprum and Kiwano. Country/fleet
aggregates and hydropower/solar-only rows were excluded, not counted as new projects.
All sixteen selected equipment identities were accepted; the nine standard Victron
models were also cross-checked against the manual, not counted twice.

CEA's September 2026 inventory was attempted first. The current listing remains
indexed, but direct retrieval returned 503. Eskom direct retrieval returned 403;
the earlier Africa ledger records an automated-collection restriction, so its
stale portfolio supplied no canonical facts. No forecast was promoted to operation.
Scatec's Q3 report was identified through its official issuer announcement; direct
retrieval returned 403 and web retrieval exceeded the 10 MiB limit. A secondary report
copy was used only for discovery. Its Dandara phase 1 50 MW and Mogobe connection-delay
claims are not imported without accessible primary report evidence.

The accessible primary owner HTML portfolios and linked regulatory releases are
the alternative source batch. Their facts are fully attributed, but source-byte
checksums are null: raw bytes were not obtained. All five accepted OEM documents/
pages have SHA256 hashes of downloaded bytes. The legal notices/terms of sale and
source-specific limitations were inspected. Public access is not represented as an
open bulk licence. Only selected factual metadata, evidence and research decisions
are committed; PDFs, HTML, images and binary snapshots remain outside Git.

An offline source-specific parser stages the four new Victron models from local
Poppler text and original PDF bytes. It checks model order, units, temperature
ratings and overload times, and leaves ambiguous apparent power null. Ten synthetic
tests cover malformed inputs and sidebar/page-break handling. Its four real-document
candidates were reconciled with the accepted rows. It stages candidates only.

The existing upsert API and validators were used. The Obelisk extension was explicitly
reviewed as an additive merge: every original nested value and created_at survives.
All other 1,296 baseline project records and all 239 baseline equipment records remain
unchanged in content. Incoming and canonical natural identities were checked;
no fuzzy merge or invented project-to-equipment link was made.

## Coverage and next work

Current branch totals are **1,304 projects / 31 countries / 123 primary sources** and
**255 equipment records / 35 suppliers / 91 primary sources**, comprising 242 exact
configurations/components and 13 families. No country is new. All six geographic
regions remain represented; these counts are catalogue coverage, not market capacity.

The existing dated IEA comparison was rechecked against the 29 May 2026 primary article.
Its comparable metric is 2025 annual stationary battery power additions in GW:
China, United States, Australia and Chile are ordered only among the quantified
country examples. Europe and Middle East remain separate regional figures.
Operational stationary energy in GWh remains unavailable on a comparable worldwide
basis; no GW-to-GWh conversion or exhaustive country ranking is asserted. See
`2026-11-02_dyness_baltic_markets.json`; unchanged evidence was not timestamp-churned.

The selected owner tables and equipment columns are exhausted. Project yield is
below the 50–200 planning objective because the national inventory was inaccessible,
Eskom ingestion is restricted, existing sites were reconciled and aggregates were
excluded. The 16-model batch meets the 10–30 equipment objective. The ranked backlog
prioritizes a recovered CEA report, the primary Scatec Q3 attachment for enrichment,
a corrected Victron edition, and then the unprocessed 120 V equipment partition.

## Validation

Research, reconciliation and final validation completed at 05:14:09 Atlantic/Canary
(UTC), 20.0 minutes after the 04:54:09 start, before publication. The selected
defensible source batches are exhausted; no idle time was added.

Both catalogue validators passed. Typed Zstandard Parquet snapshots were rebuilt
twice identically from the final records and source metadata. Full Python 3.13
suite: 1,587 passed, one optional `cdsapi` skip; 38 focused tests passed, including
ten new parser tests. Ruff lint/format and ty passed. Strict Sphinx and the local
link/asset check passed for 395 HTML pages. Four viewer DOM tests and both offline
BESS examples passed. All three package sdist/wheel builds and six archive checks
passed. Repository and citation checks passed. The initial Python 3.12 docs attempt
failed on the optional imagery dependency; the documented Python 3.13 imagery/docs
environment resolved it without changing unrelated code.

Pre-publication main and all four open PR heads remained unchanged; no GitHub
Actions workflow was in progress at the concurrency check. No BESS branch was
open, so publication uses a new scoped branch from current main.
Leave the resulting research PR open for review; these additions are not merged.
