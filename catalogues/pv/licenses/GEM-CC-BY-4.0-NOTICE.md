# Global Solar Power Tracker attribution

Source: **Global Solar Power Tracker, Global Energy Monitor, February 2026 release**.
Copyright © Global Energy Monitor. Licensed under
[Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).
[Provider and methodology](https://globalenergymonitor.org/projects/global-solar-power-tracker/).
The exact provider-hosted workbook revision and SHA-256 are in `sources.json` under
`gem_202602_recovery_20261102`.

Modifications: utility-scale phase rows were grouped by GEM location ID, filtered
for explicit PV and reviewed source lineage, screened for existing identities,
and mapped to the catalogue schema. Native phase fields and units are retained.
Source-defined statuses are historical observations, not current verification.
National distributed-solar aggregates were not imported. A scalar MW total is
absent when a project's phases differ in status or rating or lack capacities.

Entire locations containing TZ/TransitionZero or WKSL/Wiki-Solar identifiers are
excluded from this import. TransitionZero entries have CC BY-NC 4.0 restrictions;
the workbook identifies Wiki-Solar's April 2023 data as proprietary. This notice
does not relicense those excluded records, and the full workbook is not redistributed.
Other source attributions remain in the native phase `Other IDs` fields. No GEM
endorsement of this transformed catalogue is implied.
