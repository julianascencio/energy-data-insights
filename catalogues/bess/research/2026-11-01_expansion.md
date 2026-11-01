# BESS inventory expansion — 1 November 2026

**1,113 records across 27 countries; 41 primary sources.** This batch adds 1,076
records to the 37-record launch: 918 EIA plants, 149 REPD records and nine curated
projects. Five existing rows receive additional evidence. U.S. registry rows are sharded by state to keep each reviewable source file
below the repository size limit. The source-access date
is 1 November 2026; most underlying observations are older.

## What was accepted

| Research stream | Candidates | Added rows | Treatment |
| --- | ---: | ---: | --- |
| EIA-860 2025 | 931 battery plants | 918 | 13 possible Edwards & Sanborn subdivisions nested under the existing project |
| REPD July 2026 (Q2) | 178 operational Battery entries | 149 | 2 matched existing rows; 27 held for proximity/phase review |
| Owner / lender / issuer research | 9 | 9 | Australia (2), Egypt (1), Uzbekistan (1), Ireland (2), Hungary (1), Estonia (2) |

The EIA storage worksheet contains 981 OP / BA / Batteries units. Two are coded
as electrochemical capacitors and excluded. The remaining 979 battery units
span 931 plant IDs. Non-OP battery units at those plants remain in phase metadata
but do not contribute to ratings. Plants with both operating and non-OP battery
units are marked partly operational. Nameplate MW is AC per the archived survey
instructions; nameplate MWh is nominal. Survey status refers to 31 December 2025.

REPD contains 178 operational Battery records after trimming labels (including
one trailing-space status). MWh is not available. The release was published on
3 August 2026. Operational dates, application references, native grid coordinates,
reapplication IDs and the ambiguous applicant/operator label remain in metadata.
The published subset is not all UK operating storage and excludes the planning
pipeline. Nearby entries within 500 native coordinate units and unresolved named
phases are held for investigation, not asserted to be duplicates.

The machine-readable [review ledger](2026-11-01_inventory_review.json) records
accepted external IDs and all 42 withheld/matched candidates. Checksums in
[sources.json](../sources.json) pin the downloaded files. The offline staging CLI
reproduces the candidates; it deliberately does not perform automatic upserts.

## Reconciliation decisions

- **Edwards & Sanborn:** thirteen EIA plant IDs report 1,065.8 MW / 2,613.8 MWh
  in operating units, compared with the retained EPC whole-project 3,287 MWh.
  Coverage and date equivalence are not proven. Keep battery MW null and the EPC
  MWh rating; nest the EIA observations and flag the scope question. Do not add
  these thirteen rows alongside the commercial aggregate. The 1,300 MW site
  connection is still separate from battery output.
- **Salisbury:** preserve the owner's 50 MW and retain REPD's 49.5 MW as an
  unresolved alternative. No AC/DC explanation is invented.
- **Ferrybridge / Monk Fryston / Fiddler's Ferry:** match REPD references to the
  existing SSE records; retain the owner's ratings, scope and dated statuses.
- **Western Downs:** publish operating Stages 1 and 2 once, 540 MW / 1,080 MWh.
  The 305 MW / 1,220 MWh Stage 3 remains construction metadata outside the totals.
- **Aghada:** combine the separately described 19/38 and 150/300 facilities into
  one explicitly scoped 169 MW / 338 MWh site record. No extra phase rows.
- **Dunamenti:** publish the new 40 MW / 80 MWh facility. The 2022 4 MW / 8 MWh
  demonstrator is separately described but excluded from these ratings.
- **Abydos:** 300 MWh battery commissioning is reported ahead of scheduled COD;
  retain commissioning status and unknown battery MW. The 500 MW solar rating
  and November 2024 solar commissioning date do not become BESS attributes.
- **Riverside:** use the issuer's 334 MW / 501 MWh full commercial-operation
  confirmation. The notice was received on 11 February 2026; that is not asserted
  as the exact COD. The 200 MW solar plant remains separate.
- **Poolbeg / Estonia:** operation, grid connection and inauguration are distinct
  events. Preserve source wording in notes or extensions instead of inventing
  exact CODs. Kiisa and Aruküla are two independent parks; no 400 MWh fleet row.

## Coverage and limits

| Country (ISO alpha-3) | Records |
| --- | ---: |
| AUS | 6 |
| BRA | 1 |
| CAN | 1 |
| CHL | 2 |
| CHN | 1 |
| DEU | 2 |
| EGY | 1 |
| ESP | 1 |
| EST | 2 |
| FIN | 2 |
| FRA | 1 |
| GBR | 153 |
| HUN | 1 |
| IND | 1 |
| IRL | 2 |
| JPN | 1 |
| LTU | 4 |
| NLD | 1 |
| NZL | 3 |
| PHL | 1 |
| PRT | 1 |
| SAU | 2 |
| SGP | 1 |
| SWE | 1 |
| USA | 919 |
| UZB | 1 |
| ZAF | 1 |

| Dated status observation | Records |
| --- | ---: |
| commissioning | 1 |
| operational | 1106 |
| partially_operational | 3 |
| under_construction | 2 |
| unknown | 1 |

These counts describe this catalogue. The U.S. and UK dominate because reusable
inventories were available; this is not a global market-share estimate. EIA plant
IDs and curated commercial projects have different identity granularity. Source
reporting dates, rating bases and capacity scopes remain visible and must be
harmonized before comparative totals. `last_verified_at` means access to evidence,
not independent engineering verification or confirmation of today's availability.

U.S. plant coordinates are survey-reported. No UK coordinate conversion, geocoding,
inferred duration, efficiency, LFP chemistry, exact COD or guessed supplier is
introduced. `source_backed` means traced to a source, not free from source error.
Unresolved discrepancies are marked `needs_review`.

Next research priorities: resolve the 27 held UK entries using planning and owner
records; reconcile the Edwards & Sanborn registry boundary; add audited AEMO,
Chile CEN and Chinese project inventories; expand Asia, Africa and Latin America.
No new recurring research job or automatic data overwrite is configured.
