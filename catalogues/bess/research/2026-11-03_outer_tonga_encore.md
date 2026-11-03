# Outer Tonga and exact Encore models — 3 November 2026

Started 02:51 UTC (also Atlantic/Canary). Research/extraction/reconciliation completed
02:57 UTC; validation and publication followed. This bounded pass exhausted the
selected eleven exact OEM sheets and completed the two held national-portfolio
identities. It finished earlier than the planning window rather than padding time.

## Accepted changes

- Two projects: Eua TREP-03 Lot 1 at Ohonua and Vavau TREP-03 Lot 1 at Kameli.
  Government commissioning releases identify the physical projects and contractor;
  the utility's contract table explicitly reports operation. March 2023 ceremonies
  are not asserted commercial-operation dates. The undated utility status is
  marked with its access-date basis, not presented as live telemetry.
- Eua power and energy remain quarantined: 1.003 MW/1.856 MWh in the commissioning
  release versus 1 MW/1.85 MWh in the NDC review. Precision/boundary reconciliation
  remains open. Vavau has reported 1 MW/2 MWh, boundaries unspecified.
- Seven exact equipment additions: HPS50/100/150/250/500 and Encore 12K/15K.
  All seven appear in the OEM's end-of-life download section and are historical
  documents, not current availability claims. Optional PV controllers remain
  ranges; no Cartesian configuration expansion. Split HPS250/500 enclosures and
  maximum-weight descriptions remain in extensions, not misleading single-box dimensions.
- Four existing single-phase Encore models enriched with EPS current/voltage,
  current/voltage THD limits and overvoltage categories. Existing values and
  creation dates preserved. Source hashes filled from fresh downloads.
- No new countries or suppliers; no project enrichments, permanent rejections or
  equipment quarantines. Prior quarantines remain untouched.

Proposed totals: **1,715 projects / 35 countries / 211 sources; 518 equipment
records / 39 suppliers / 231 sources**. Six-region coverage retained. These are
branch totals, not merged totals (main 76d0c1a: 1,710 projects, 465 equipment).

## Research depth and limits

Revisited the four-installation national battery paragraph of Tonga's 2025 NDC
review, the utility TREP-03 Lot 1 portfolio and contract table, both PM-office
commissioning articles, and four Infratec portfolio pages (Eua/Vavau, outer Tonga,
Tuvalu, southern Cook Islands). The two Tongatapu records were already covered.
Five further Tonga island sites, the Tuvalu Fisheries battery and a four-island
Cook portfolio remain discovery candidates: per-site ratings, identity and scope
need additional work. No combined portfolio battery capacity was assigned to
individual sites. This is not a national bulk import or a worldwide completeness claim.

Direct PM-office/ADB pages returned 403 and utility access timed out. Full primary
article/table content was available through the search index; that access method
is explicit in sources, and unavailable original-byte checksums remain null.
The national PDF was read through the web reader. Contractor portfolios provided
alternatives, not automatic acceptance. No source's public access is claimed to
be an open bulk licence. Only selected factual data is committed; OEM PDF bytes
remain outside Git with checksums in the source register and review ledger.

All eleven Encore exact sheets downloaded and checked: seven new, four existing
substantively enriched. No thin duplicates or timestamp-only records accepted.
The project objective fell short because this selected four-site national cohort
had only two remaining identities; other island portfolios require site evidence.
The equipment work covered eleven new/enriched models. Next sources are ranked
in the accompanying backlog rather than rediscovered next run.

The IEA 29 May 2026 comparison was reopened: 2025 stationary power additions in
GW give quantified country examples China >63, US 19, Australia nearly 8, Chile
approaching 1. This is not an operational energy GWh ranking. A comparable global
operational-GWh table is still unavailable; regional numbers are not country ranks.

## Validation

- Full suite: 1,666 passed, one optional cdsapi skip (before final status-evidence
  refinement); final focused catalogue checks: 28 passed.
- Both canonical catalogues validated; two independently rebuilt Zstandard Parquet
  snapshots/manifests match. Preservation audit: 1,713 projects unchanged;
  507 of 511 previous equipment records unchanged; four reviewed enrichments.
- Ruff lint/format, ty with the correct project interpreter, repository hygiene,
  citations, eight viewer tests and both offline catalogue examples passed.
- An initial ty invocation selected the wrong environment; corrected invocation
  passed. An initial documentation build observed the in-progress source timestamp
  edit and failed; final build is recorded below after correcting verification dates.
- No code/schema change or reusable importer required: selected exact tables were
  individually reviewed and existing upsert/validation/snapshot APIs reused.

PR #86 remains open and unmerged. No force push or merge authorized.

Final strict Sphinx build succeeded; all 409 HTML pages passed local links/assets
validation. Validation completed 03:00 UTC: approximately 6 minutes for research
and reconciliation and 3 minutes for validation, with publication following.
No packaging/code changes; package builds were not repeated. Remote CI is
reported separately after publication, never inferred from these local checks.
