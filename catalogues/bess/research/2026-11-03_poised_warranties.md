# POISED commissioned inventory and exact TESVOLT warranty enrichment

Started 3 November 2026 at 20:49:10 Atlantic/Canary (UTC). This pass follows merged
PR108 from current main `2598b1431fc85aff95f589518e6cb8f5c4e572c1` in an isolated checkout.
The November1 checkpoint is historical. BESS schemas, dictionaries, source registers,
workflow, recent research and completeness manifests retain their established conventions.
No open compatible BESS PR existed. Wind111 changes shared bibliography files; three
new references are queued locally rather than overwriting concurrent work.

## Results and evidence

Reviewed every one of 45 named installations in ADB's 2024 POISED publication,
Table2.1, printed pages9–10 / PDF23–24. Both rendered pages were visually checked.
The complete table sums to 6,152kWh, matching its control total. Added 38 projects
with battery energy, co-located solar DC peak capacity, atoll/island, lithium-ion
chemistry and historical commissioned lifecycle evidence. July2022 is normalized
to reporting month-end; it is not exact COD or evidence of operation in2026.
Neither diesel power nor solar power is assigned as battery MW.

Seven candidates remain held: Addu City, Villingili, Dhihdhoo, Holhudhoo, Manadhoo,
Velidhoo and Milandhoo. They overlap later ARISE/ASSURE sites; explicit asset retention,
replacement and phase evidence is required before adding or merging them. No fuzzy
merge is performed. Baa Goidhoo and Shaviyani Goidhoo are distinct reviewed locations.
Atoll aggregates in Table2.2 and the Table2.1 total are not project records.
No existing project changes, permanent rejections or canonical project conflicts.

The original Finance phase2a document was attempted first but returned an HTML
error; the reader had no extractable text. Its 13-island lead remains a backlog
partition, not 13 verified candidates. The ministry-hosted ADB original provided
an accessible alternative. The book is CC BY3.0 IGO with a third-party exception;
Table2.1 credits the Maldives ministry. Only bounded attributed factual observations
are committed; original documents and renders remain outside Git under `/tmp/bess2049`.
Exact URLs, checksums, dates, locators and candidate decisions are in the review ledger.

Enriched all 11 exact configurations from the preceding pass using three original
manufacturer guarantees: eight TAYTAN configurations, FORTON/12-30 and two TS-I HV E
configurations. The E-Series source already exists and was matched by downloaded
SHA-256, avoiding a duplicate source. Model eligibility, sales dates and territorial
scope remain explicit. No universal warranty-years scalar is inferred.

TAYTAN gains its exact model-row discharged-throughput threshold, 65% retention,
10-year product /12-year conditional capacity terms, -17 to50C warranty conditions,
CCCV capacity test and installation/connectivity requirements. Its preliminary
operating envelope remains distinct from warranty eligibility. FORTON gains 60%
retention, 5-year system /12-year capacity terms and conditional15-year extension,
CP/temperature cycle tables, daily limits and test conditions. Its erroneous Table1
cross-reference is retained as a source caveat. Two E-Series models gain the10-year
performance /5-year system distinction,70% retention, temperature/C-rate cycle limits,
commissioning/logging requirements and DC capacity test boundary. No new models,
manufacturer assignments or canonical equipment field conflicts.

Proposed totals: **1,985 projects /40 countries /300 sources**; **718 equipment
records /45 suppliers /359 sources** (705 configurations,13 families). No new country
or supplier; all six world regions remain represented. Existing records' created_at
values and all non-null facts are preserved. Only11 substantive equipment changes
advance updated_at/last_verified_at. Existing upsert API collisions were reviewed
explicitly as evidence augmentation. No schema, shared importer or package code changed.

## Market priorities and remaining work

Reuse the same-day primary IEA comparison in `2026-11-03_poland_containers_markets.json`:
2025 annual stationary battery power additions, GW, among quantified country examples
China >United States >Australia >Chile. This is not an exhaustive operational GWh
ranking; missing/incomparable markets stay unranked. No MW-to-MWh conversion is made.
The underserved island inventory was selected from the previous actionable backlog.

The complete45-row batch is exhausted; seven identity holds explain the38-project
yield below the50-project planning objective. Eleven substantive warranty enrichments
were preferred to hypothetical new equipment combinations. Next resolve the seven
legacy installations, obtain the phase2a completion inventory, then rotate to an
African or Latin-American official owner portfolio. The ranked backlog includes
source versions, access/reuse assessment, partitions and retry conditions.

Validation and actual elapsed time are recorded in the companion validation JSON.
Both catalogues passed validation, and two independent typed Zstandard Parquet builds
per catalogue produced identical hashes and completeness manifests. Binaries stay
outside Git and regenerate through the established documentation artifact mechanism.
Historical launch reports remain unchanged. The research PR stays OPEN; no merge or
publication deployment is authorized by this run.
