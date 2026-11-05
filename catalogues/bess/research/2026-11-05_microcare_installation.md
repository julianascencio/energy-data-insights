# Microcare installation limits and Rodrigues procurement reconciliation

5 November 2026, started 12:48:39 Atlantic/Canary. Continued open PR #168 from
404fbf579d7bd8c437c83f129e1d2a49f9039c05 in an isolated worktree. PR #168 was merged externally during validation; this batch was carried without
conflict onto new branch research/bess-database-20261105T125800Z from current main
76179409. The merged BESS code/data exactly match the reviewed starting head. Reviewed open PR titles and changed paths, including new PV #169
and data-center #170; no overlapping BESS writes. Existing schema, dictionaries,
source register, workflow, prior review/coverage and PV conventions were retained.

## Accepted changes

Two new project records from CEB tender CPB/22/2025, issued 11 August 2025:
Pointe Monnier expansion, 1 MW / 2 MWh, and Grenade, two 0.5 MW / 1 MWh units
represented as one 1 MW / 2 MWh site. The document explicitly reconnects the
existing 1.5 MW / 1.5 MWh Pointe Monnier plant, resolving the separate identity of
the tender expansion. No aggregate tender record or duplicate unit rows were added.
The old PSIP aggregate was not automatically mapped to this procurement.

Added tender IDs, lithium-ion chemistry without inferred subtype, 22 kV connection
requirements, continuous PCC power boundary, peak shaving/frequency/renewables
applications, CEB ownership and twelve-month completion condition. Coordinates
remain native observations because datum and accuracy are unspecified. Tender
requirements are not awarded/as-built equipment or proof of operation. No existing
project fact is overwritten. Tamarind Falls remains held.

Seventeen exact Microcare configurations enriched with ambient limits of 0–40°C,
indoor/dry/ventilated placement, required battery supply, AC-output parallel
restriction, separation from non-sealed batteries and external breaker conditions.
Clearance is 200 mm for smaller models and 300 mm for 10/15 kW, at top/left/right.
The latter manual specifies external input breakers; the smaller manuals specify
input and output breakers. No full-power temperature guarantee, IP rating, humidity
bound or derating curve is inferred. Each model points to its applicable manual
and exact PDF pages. All prior scalar/nested facts, conflicts, evidence and
created_at survive reviewed additive upsert; replay is idempotent.

## Evidence and limits

CEB portfolio/phase reconciliation was pursued before isolated announcements.
The official tender copy hosted by TCIL was downloaded successfully and checksummed;
a web-reader follow-up timed out, so original bytes were used. The 1–5 kW manual
was freshly downloaded and matches its registered checksum. The 5–8 kW refresh
returned 503; no repeated retry, with the already verified same-day original
retained as historical edition evidence. The 10–15 kW download succeeded. Original
bytes and derived snapshots remain outside Git. Copyright is retained; this is
bounded factual extraction, not document redistribution or an assumed open licence.

Four monitoring/accessory product candidates were discovered but deferred pending
exact model/datasheet reconciliation. No thin product-family rows were added.
The earlier dated IEA market comparison remains applicable: selected-country 2025
utility-scale power additions, not comparable operational stationary energy GWh.
No new universal GWh ranking is claimed.

## Counts and checks

This pass: 2 new projects, 0 project enrichments; 0 new equipment, 17 equipment
enrichments; no new quarantined canonical rows or permanent rejections. Four
monitoring candidates are deferred. Totals: 2,136 projects / 47 countries / 394
project sources; 1,064 equipment / 54 supplier labels / 476 equipment sources.
No new countries/OEMs; all six geographic regions remain covered.

Catalogue validation, existing upsert preservation/replay and two independent typed
Zstandard snapshot builds passed. Thirty-five focused catalogue/parser tests pass;
offline OEM example and repository-wide Ruff/format pass. No schema/parser code
changed. Full local suite is not rerun: prior same-day full-suite psutil failures
were reproduced on unchanged main, while the starting PR head passed remote CI.
Final head CI is reported separately in the PR description.

The selected three manual safety/installation sections and two-site tender scope
are exhausted. Project yield is below the bulk objective because this procurement
contains only two identifiable sites; no unnamed programmes or duplicated phases
were counted. Next: CEB award evidence and the four exact monitoring datasheets;
retain the CEA backoff. Detailed source cursors and retry conditions are in the
companion backlog. Earlier historical ledgers are unchanged.

Elapsed through implementation/validation preparation: 6.7 minutes. Final upload and remote CI time is recorded in the PR description.

Post-main-refresh checks: 35 focused tests, viewer tests, repository-wide Ruff/format and ty passed. Strict gallery-disabled documentation build was run; final remote gallery validation is reported on the PR. No parser/schema changes or new parser tests in this data-only pass.

Elapsed through publication preparation: 9.5 minutes at 12:58:06 Atlantic/Canary.

Strict local documentation build completed successfully. Link checking was initially invoked before asset publication completed; final post-build link check passed.
