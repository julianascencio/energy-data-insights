# Community-battery coverage and exact Fullriver specifications

Started 6 November 2026, 00:49:02 Atlantic/Canary (UTC). Isolated checkout of
open PR #187 at `122ba6a4`; main `4ef42de4`. Titles and complete changed paths
of open PRs #183–187 were inspected. PV, wind, data-centre and hydro changes do
not overlap. Contribution instructions, catalogue workflows, dictionaries,
schemas, sources, coverage and recent logs were reviewed. No schema changes.

## Accepted project batch

DCCEEW's national table, updated 12 October 2026, yields **57 new programme-location
records** across seven Australian states/territories. **45 are reported operational**;
**12 say “In progress”**, retained as unknown lifecycle with the native wording.
The programme narrative says 58 locations; only 57 are displayed. That discrepancy
is logged without inventing a missing row. ARENA's recipient-only lists are excluded.

The records contain exact applicants and localities, states, energy in MWh converted
from labelled kWh, grant observations and dated operational-From wording. A location
may aggregate several batteries; no constituent rows are also imported. Applicants
remain grant applicants, not assumed owners/operators. Grant money is not capex;
“$” is preserved without guessing an unstated currency or price year. No inferred
MW, chemistry, duration, cell supplier, equipment, coordinates or commercial COD.
The dated table is not a live availability feed.

All 56 existing Australian canonical identities were compared with the incoming
57 natural identities and the incoming batch itself; none matched. Dapto's 2025
community-battery location is not merged with the earlier West Dapto network-support
battery discovered in MPower's portfolio. No fuzzy merges were performed.

The table and copyright notice are public through the web reader; direct original
HTTP downloads returned 503. The government table is CC BY 4.0, with no indicated
third-party restriction. The retained reader-export checksum is explicitly not an
original-HTML checksum. No access control was bypassed. The new offline parser
validates columns, units, dates, seven regional counts, duplicate identities and
complete partition boundaries. It stages candidates only.

## Equipment and enrichment

Eight final DC index headings were reviewed. Four exact models are new:
DC200-6, DC200-6B, DC220-12 and DC240-12. Each has exact-sheet electrical,
mechanical, charging and temperature evidence plus metric/imperial OEM cards.
DC200-6's PDF filename contains “A”, but the printed heading and live card both
say DC200-6; the printed identity is retained. Its first page was visually checked.
Four DC210/DC260 LT/APW headings remain held: base-name/raster sheets do not
establish exact suffix identities. They are not fabricated configurations.

Fourteen existing DC models receive newly extracted terminal types and ABS case
material/UL94-HB claims. Each exact sheet was freshly downloaded and its hash
matched the registered original. DC70-12's button-terminal claim was visually
checked. UL94-HB remains a manufacturer material-rating claim, not verified
certification. The generic torque table requires visual highlighting and is not
converted into model-specific torque. Prior rating/dimension conflicts are unchanged.

The new offline terminal/case parser rejects changed headings, missing/duplicate
rows and unreviewed claims. Additions and enrichments use the existing upsert API.
Fourteen nested-JSON collisions were reviewed as additive namespaces; old values,
source entries and created_at were preserved. No-op replays remain unchanged.

## Other source attempts and limits

MPower's eight-case portfolio supplied three explicit BESS headings: Rarotonga was
already processed; UQ Gatton and historical Endeavour West Dapto are held. Five
other headings were not classified as batteries. UQ's owner page explicitly restricts
systematic retrieval/storage and nonpersonal reuse; original bytes/text were removed
and no owner technical facts imported. An ASX historical West Dapto release is marked
personal use only; no facts accepted from it. A planning-report alternative needs terms
and phase review. This pass continued with the licensed DCCEEW batch instead.
Prior MFEM reuse restrictions, ADB retry cooldown, Chile phase holds and AEMO MREH
identity/rating decisions remain unchanged.

Current totals are **2,207 projects / 48 countries / 413 sources**, and **1,220 equipment
records / 56 supplier labels / 535 sources** (1,207 configurations and 13 families).
No new countries or suppliers. All six world regions remain represented. Australia
was selected for undercovered community-scale aggregations, not another NEM survey
pass. The freshly checked IEA ranking uses 2025 utility-scale power additions:
China about 55 GW, US over 16 GW, Australia about 4.2 GW among explicitly quantified
countries. This is neither an exhaustive world ranking nor operational energy in GWh;
a comparable energy ranking is unavailable from that source.

## Validation and next partition

The selected 57-row national partition and eight-heading OEM partition are exhausted.
Accepted yield is 57 new projects, four new models and 14 substantively enriched models.
Two project candidates and four equipment identities are held; one project was already
processed. No rejected canonical rows or new whole-record quarantines. The missing
58th location is a source-completeness issue, not a reviewed candidate.

Both catalogues validate. Typed Zstandard snapshots are rebuilt twice outside Git
and are byte-identical. Reference integrity, preservation of prior facts/sources and
created_at, incoming/canonical identities and idempotent upsert are checked. The
validation ledger records actual commands/results; published-head full CI is recorded
in the PR. Next: clarify DCCEEW's missing location and 12 in-progress rows, reconcile
Fullriver terminal variants, and rotate to a non-Oceania licensed owner inventory.
The dated backlog records URLs, terms, partitions, retry conditions and expected yield.
This does not claim that worldwide research is exhausted.

Commit-preparation checkpoint: 01:10:02 Atlantic/Canary, **21.0 minutes actual elapsed** from discovery through extraction, reconciliation and local validation. Strict Sphinx and 711-page local link/asset checks passed after recovering disk space by deleting older reproducible HTML builds. Full hosted CI and final publication elapsed time are recorded in the PR description; no local full-suite/package success is claimed.
