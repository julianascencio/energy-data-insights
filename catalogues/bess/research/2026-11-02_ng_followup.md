# NG battery depth and Uzbekistan source reconciliation — 2 November 2026

This pass continues open PR 81 at 9184061d072baae708cba7e648d4df9514df12f2,
based on main 38587c2d990f22dc862824cf370c5356b80fab44. Open PV PR 82 changes
PV catalogue paths only; dependency PRs 47–49 change workflows. No shared code,
schema or PV records changed. Earlier Australia/Chile ledgers and held phases
remain untouched. Prior scratch was removed; an isolated fresh clone restored
repository state. Initial clone latency and a proxy authentication failure did
not block the eventual standard Git clone.

## Accepted work

Four exact configurations added: Victron Lithium NG 25.6 V/100 Ah, 200 Ah,
300 Ah and 51.2 V/100 Ah. All four actual table model columns are exhausted;
HTML colspan is presentation, not an extra model. Added reported nominal energy,
voltage, pack Ah, charge/discharge continuous and 10-second pulse limits,
conditional cycle claims, internal resistance, temperature limits, IP65,
dimensions, estimated mass and external BMS requirements. Estimated mass stays
qualified in extensions. No power inferred from current, no cell-Ah substitution,
no AC-to-AC efficiency inference, no family expansion or project equipment assignment.

Twelve existing Smart/12.8 V NG models enriched with charge-voltage windows and
float voltage; eight Smart models also gain recommended charge voltage. The
shared Smart row explicitly lists 12/24 V alternatives, mapped by each model's
nominal voltage; these are charger settings, not general operating-voltage limits.
All prior nested facts and created_at values preserved. New rows use the existing
upsert API; populated nested extensions use explicit reviewed additive edits,
because generic upsert intentionally refuses replacing populated JSON.

Equipment: 16 reviewed -> 4 new, 12 enriched, 0 held/rejected, 0 new conflicts.
Projects: five named candidates -> 0 accepted, 5 deferred, 0 permanent rejections.
No new country or supplier. Totals: 1,707 projects / 34 countries / 203 sources;
455 equipment records / 39 suppliers / 203 sources (442 configurations, 13 families).
Six-region project coverage retained.

## Source terms and project workstream

Attempted EBRD's project portfolio before individual releases. Celest, Sazagan-1,
Guzar and Artemisya disclosures offer useful metadata, but EBRD terms section 4.1
limit redistribution/derivative reuse; no bulk extraction or canonical import.
Artemisya financing facilities are not separate physical projects. Sazagan's live
page also contains different current/historical energy observations requiring
chronology reconciliation. Future approval dates do not establish construction.

Alternatives: AMEA's Celest owner page was accessible, but its legal disclaimer
requires consent for reuse; not ingested. ADB's Guzar news is accessible, while
project-data and linked RRP endpoints returned 403. ADB project-data terms permit
reuse with attribution, but this was not assumed to cover the separate news page.
No access-control bypass or contact. Masdar's Nur-Bukhara page contains both an
inauguration statement and under-construction label; battery-specific operation
is not established. The backlog records exact URLs and retry conditions.

Victron legal notice and linked terms of sale were inspected. OEM copyright is
retained; bounded technical facts with attribution, not an asserted bulk licence.
Four downloaded manual pages are checksum-verified; two unchanged pages reuse existing source IDs and two new page SHA256s are registered; source bytes remain in
ignored artifacts/ng. The source register locates section 8.1 and exact row/model
columns. No manuals, images, or binary snapshots are committed.

IEA's 29 May 2026 comparison was freshly reopened. The dated market file keeps
2025 annual stationary power additions separate from operational energy:
China >63 GW, US 19 GW, Australia nearly 8 GW, Chile approaching 1 GW, among
quantified examples only. A comparable global operational GWh ranking remains
unavailable; regional totals are not country ranks.

## Yield and next action

New-model yield is four because these two remaining NG tables contain four
actual configurations. Useful charging enrichment covers twelve existing models.
Project yield is zero after portfolio/owner/lender alternatives because of
explicit reuse restrictions, blocked reusable endpoints and unresolved chronology.
This is not a claim that worldwide research is exhausted. Next priority: ADB's
public Uzbekistan IATI project-data partition or a later successful Guzar PDS
request, followed by exact standalone BMS/PCS datasheets. Recheck freshness and
identity; do not repeat restricted AMEA/EBRD collection or manufacture variants.

## Validation and elapsed effort

Full Python suite: 1,647 passed, one optional cdsapi skip. Catalogue validation,
prior-field preservation audit, deterministic repeated typed Zstandard Parquet,
Ruff lint/format, ty, repository hygiene, citations, eight viewer tests, offline
OEM example, three package builds and six Twine checks passed. Documentation
and installed-wheel checks are recorded below when complete. Data-only changes;
no parser/schema code requiring new synthetic tests.

Started 21:52:39 Atlantic/Canary (UTC); research and implementation through
21:57, with validation/publication continuing. Selected four manual tables fully
reviewed; no idle time used to extend the pass.

Installed-wheel checks and the first strict Sphinx build passed. Fourteen focused
OEM tests passed after removing duplicate source registrations. Final incremental
strict documentation/link checks follow the source consolidation.

Final incremental strict Sphinx build passed; all local links/assets across 405
HTML pages passed. Both offline examples and both catalogue builds passed.
Final source consolidation retains 203 OEM sources, avoiding two identical-source
registrations. Selected checks complete at approximately 22:01 UTC: about eight
minutes elapsed, including source recovery, research, implementation and validation;
publication follows immediately. Four new models is below the new-model planning
range, but sixteen exact models received substantive verified specifications.
