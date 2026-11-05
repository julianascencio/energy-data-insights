# Victron warranty enrichment and African inventory screening

Started 5 November 2026 at 18:50:45 Atlantic/Canary (UTC). Continued open PR
[#172](https://github.com/julianascencio/energy-data-insights/pull/172) at
d1460ad2e3c175c74c7282ae6cb089a2e4ab1686, with main at 76179409.
All eleven open PR titles and changed paths were checked before edits. Only #172
covered BESS. Historical launch reports and prior accepted batches are unchanged.

## Accepted evidence

Forty existing exact Victron MultiPlus and MultiPlus-II inverter/charger
configurations receive missing warranty duration and conditions. The original
2025-(P) policy supports five years from first end-user purchase, capped at
66 months from the manufacturer invoice. Direct-customer versus conditional
end-user rights, seller claim route, exclusions, paid extension eligibility and
repair/replacement term remain explicit. The optional ten-year total is not
standard coverage, and eligibility of any actual purchased unit is unverified.
No technical rating, chemistry, lifecycle, identity, creation time or earlier
nested evidence was changed. Battery warranty exceptions were not applied to
inverter/chargers. The year comes from the filename, not a printed issue date.

The existing upsert API was used. Forty collisions concern additive nested
provenance; each existing namespace was preserved before accepting the patch.
No unresolved competing warranty value was present. All forty identities existed
on main: zero new models, forty substantive enrichments, zero model rejections
or quarantines. Exide and Ritar are two source-level rights holds, not counted
as accepted or rejected exact-model records.

## Project screening and yield

The scalable Scatec South African portfolio was attempted before individual
releases: all three BESS entries already have the capacity, roles and newer
lifecycle observations in the canonical catalogue. No duplicate or timestamp-only
update was made. REREC's two inventory tables plus project paragraphs identify
36 candidates (27 government, two university collaborations, seven KEMP).
The site's June 2026 terms restrict publication without written permission, so
none underwent canonical acceptance or import. Solar power was not relabelled
as BESS power. The old portfolio wording cannot establish current operation.
Kenya Power's independent annual-report index is the next actionable source;
its original asset tables and reuse terms remain unreviewed.

Thus 39 project candidates were screened, three already covered and 36 held at
source level; zero new or enriched projects and zero permanent row rejections.
No new country or supplier was added. Two additional OEM table sources were
held after terms review. Their unreviewed model counts are not inflated into
candidate totals. No alternate-host mirror was used to bypass these limits.

The new-project and new-technical-model planning targets were not reached.
This pass instead fills a substantive commercial metadata gap in 40 models.
The selected accessible warranty and Scatec batches are exhausted; the other
selected batches have concrete reuse blockers. Research/extraction/reconciliation
occupied approximately 10 minutes; validation and publication continued below.
No time was spent idling to reach a duration target.

## Coverage and reproducibility

Projects remain 2,147 across 48 countries and 408 sources. Equipment remains
1,172 records across 55 supplier labels (1,159 configurations and 13 families),
now backed by 483 sources. Warranty-term completeness increases from 206 to
246 records (17.58% to 20.99%). The existing regional coverage is retained.
The dated market comparison retains the same-day IEA source verification:
2025 utility-scale battery **power additions** in GW, selected China, US and
Australia; regional Europe is excluded from country ordering. Comparable
operational stationary battery GWh is unavailable, not derived from GW.

See the [review](2026-11-05_victron_warranty_review.json),
[audit](2026-11-05_victron_warranty_audit.json),
[coverage](2026-11-05_victron_warranty_coverage.json),
[manifests](2026-11-05_victron_warranty_manifests.json),
[captures](2026-11-05_victron_warranty_captures.json),
[ranked backlog](2026-11-05_victron_warranty_backlog.json) and
[market comparison](2026-11-05_victron_warranty_markets.json).
Original bytes and rebuilt typed Zstandard Parquet stay outside Git under the
established artifact mechanism. Accepted facts retain exact URL, publisher,
page/section, retrieval time and original SHA-256. No new parser or schema.

The final open-PR path recheck found shared bibliography changes in #171 and
#157. Provisional global bibliography edits were discarded to honor concurrent
scope; complete attribution remains in the BESS source register and evidence.
No shared importer, schema, code or bibliography changes are published.

Validation passed: 500 focused BESS tests; 25 viewer tests; both catalogue
validators; all field-source references; no-op/idempotent upsert and creation-time
preservation; two byte-identical typed Zstandard snapshots and Parquet readback;
Ruff lint/format; ty; repository hygiene/citations; offline OEM usage example;
strict Sphinx with gallery execution disabled and 666-page local link/asset validation. No new parser/schema/code means
no new synthetic parser tests or package-build pass claimed for this iteration.
Full published-head CI results and publication timing will be reported in the PR.

Local validation checkpoint: 2026-11-05 19:03:53 Atlantic/Canary (UTC),
approximately 14 minutes since start. About ten minutes covered discovery,
extraction and reconciliation; remaining time covered checks. Publication and
remote full-suite checks continue after this committed checkpoint.
