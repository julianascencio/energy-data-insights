# India IATI and exact HW15 inverter components — 2 November 2026

Started 23:51 Atlantic/Canary (UTC), from main 76d0c1a after merged BESS PR83.
Open PRs 84/85/47/48/49 were checked by title and changed paths: none change
BESS catalogues. Isolated worktree; no foundation duplication, merge or force push.
Read workflow, dictionaries, source registers, last coverage manifests and IATI/BMS
report/backlog. Existing APIs and all prior canonical rows are preserved.

## Research decisions

Three complete ADB country files (572 activities) were processed through the
existing offline IATI adapter: India 406 / Kazakhstan 37 / Mongolia 129.
Five keyword candidates: one accepted Indian physical battery project, three
Indian electric-bus financing entries excluded as nonstationary, one Mongolian
activity held. The latter describes national targets and placeholder outcomes;
100 MW is not an accepted asset rating. No financing dates were promoted to COD.
ReNew Peak Power has a separately reported 173 MW / 415 MWh battery portion,
Andhra Pradesh, 435 MW AC solar and 250.8 MW wind, SECI offtake and a named
implementing entity. The contractual 27 October 2026 commissioning requirement
is a forecast only. Physical status remains unknown. Existing Indian names,
registry identities and aliases were reviewed; no ReNew counterpart found.
No existing project had a defensible substantive enrichment from these files.

One current Victron 230 V HW15 technical table explicitly enumerates 18 models:
12/24/48 V variants for six model ratings. Exact column and voltage subrow
mapping reviewed for active W, separate 40 C power, DC range/shutdown,
AC tolerance/frequency, maximum conversion efficiency, idle watts, cooling,
IP21, temperature limits, derating, mass and dimensions. These are unidirectional
battery inverter components, not complete storage or bidirectional PCS. Model
numbers are never substituted for W ratings. Socket options do not create rows.
No chemistry, capacity, warranty or project association inferred. Existing
manufacturer/model/variant identities and incoming IDs checked; no matches.
Three Sungrow PCS candidates were examined but held because current website
terms restrict commercial content reuse without permission. No restriction bypass.

Accepted: projects +1, equipment +18; existing enrichments 0/0, new canonical
quarantines 0/0, permanent canonical rejections 0/0. Candidate exclusions: three
bus financing activities. Holds: one project and three equipment models.
Proposed totals: 1,711 projects / 34 countries / 205 sources; 483 equipment /
39 suppliers / 212 sources (470 configurations, 13 families). No new country or
supplier; six-region coverage preserved. Counts are not installed market capacity.

## Rights and reproducibility

ADB Project Data terms were rechecked: reuse with attribution and downstream
acknowledgment, no ADB endorsement. All XML bytes/checksums preserved outside Git.
Victron legal notice and linked Terms & Conditions of Sale checked: no bulk
open-data licence claimed; bounded factual specifications only, no copied manual
prose/artwork. Sungrow terms dated 5 December 2025 held at
https://www.sungrowpower.com/en/terms-of-use; private manual bytes not redistributed.
Source-register hashes and exact activity/table/model locators retained. Existing
upsert API used, all prior records unchanged, no schema or parser changes.
The IEA 29 May 2026 country comparison was freshly reopened: named metric remains
2025 stationary GW additions, not a complete operational GWh ranking. Retain the
dated market file's limitations; do not invent missing country rankings.

Project yield is low because only one of five keyword-matched financing activities
in three full inventories was sufficiently identified and in scope. Equipment
target met; the selected 18-model table is exhausted. Additional independent
Sungrow source examined and held. Next source/partition and retry conditions are
in the dated backlog. No claim that worldwide research is complete.

## Validation and elapsed effort

146 focused BESS tests passed. Both catalogue builds validated successfully.
Citation registration initially lacked required metadata; repaired before validation.
Additional final checks and actual elapsed effort are recorded below.

Final checks completed around 00:01 Atlantic/Canary on 3 November: about ten
minutes elapsed from start (research/implementation approximately five minutes,
validation/publication preparation approximately five). No intentional idle time;
selected full inventories and the 18-model OEM table exhausted, with independent
alternatives and remaining source limitations documented above.

Full suite: 1,666 passed, one optional cdsapi skip. Ruff, format (601 files), ty,
repository hygiene, citations and diff checks passed. Both offline examples and
eight viewer tests passed. Two independent builds of each catalogue produced
byte-identical typed Zstandard Parquet; coverage manifests committed. Strict
Sphinx and local links/assets across 409 HTML pages passed. Initial Sphinx
attempt lacked optional Orbital PV; installing the locked imagery group resolved
it, with no source change. No package or remote CI success claimed. Main remained
76d0c1a at final prepublication check; new branch did not already exist.
