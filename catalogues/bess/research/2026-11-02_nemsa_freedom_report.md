# Nigerian mini-grids and exact Freedom Won models — 2 November 2026

Started **14:45:57 Atlantic/Canary (UTC)**. Main was `12f9c8c3`, after PR #72
merged externally at 13:19:39. Current instructions, BESS workflow/OEM research
specification, typed schemas/dictionaries, source registers, manifests and prior
research/identity ledgers were reviewed. Open PR titles and paths were checked:
#73 concerns PV; #47–49 concern workflows. There was no open BESS research PR.
Historical Australia/Chile and launch reports, including held phases, are preserved.

## Accepted data and limits

This iteration adds **nine Nigerian projects** and **10 exact Freedom Won models**,
and substantively enriches **four existing equipment records**. No existing project
changes, no new country and no new OEM. Current totals: **1,350 projects, 34 countries,
180 project sources; 363 equipment records, 38 suppliers, 131 equipment sources**
(350 configurations, 13 families). All six geographical regions remain represented;
these are database coverage counts, not installed-capacity or completeness claims.

Projects: Fadama Bauna North, Kalong, Ibaragun, Mebiowa Okposi, Eriwe, Fagbo,
Gurin, Emereoke and Gamakai. Ten NEMSA application entries describe nine sites.
Mebiowa entries 1442720 and 1446317 share the site, coordinates, owner and REA lot;
both registry IDs are retained on one record. The earlier storage field contains
chemistry text, not a competing numeric capacity. Emereoke is manually reconciled
to the prior held Emeroke portfolio lead using Renewvia's applicant company,
Eastern Obolo location and the owner page. Its operational status comes from the
owner's operating portfolio as accessed. Other application-only statuses remain
unknown; inspection requests and installation dates are not COD or certification.

Records add source-qualified chemistry, exact applicant-reported battery models,
ownership where the form names a company/agency, administrative area, PV co-location,
installation/application chronology, coupling, raw GPS and registry IDs. No GPS
is asserted as WGS84 without datum evidence. Generator kVA and PV/MPPT ratings are
not converted to battery MW. No equipment-table references are invented from a
project applicant's model string. Emereoke's individual applicant in the owner field
is not treated as legal ownership; no personal contact, address or tax fields are
committed. The public forms are applicant declarations hosted by the regulator,
not independently verified OEM performance specifications.

**Four project energy fields are quarantined**, with both observations and row
locators retained in `conflicts_json`; the identities and other defensible facts
are accepted with `needs_review`. Kalong reports 172.8 versus 1440 kWh; Fagbo 160
versus 15 kWh; Gurin 153600 versus 153.6 kWh; Gamakai 244.8 versus 1020 kWh. These
may involve unit or subsection scope errors, but no automatic correction is made.
Gurin's manufacturer role mismatch is separately retained and the normalized
manufacturer withheld. There are **zero whole-record rejections** and **zero OEM
conflict quarantines**. Three further discovery leads are deferred: Uyo, Toto and
Lokpaukwu; they are not included in accepted counts.

Equipment comprises four LiTE 2 Home 52V Model A models, two LiTE 2 Business HV
models, three legacy LiTE Home HV models, and one eTower 2 single-module configuration.
These are distinct voltage/generation identities; five additional eTower stack
columns are not inflated into separate models. Specifications include nominal DC
energy, DoD alternatives, continuous and maximum discharge/charge ratings, voltage,
current duty limits, short-circuit current, dimensions/mass, controls, enclosure,
and warranty/life conditions. Chemistry is only populated for explicitly LFP eTower 2.
Its IEC62619 claim is in progress, not certification; recommended ambient limits
are not asserted as absolute operating limits. The printed 4.5 kWh at 90% DoD is
preserved with a basis caveat rather than recomputed from 5.12 kWh. No inferred RTE,
active power from kVA, or calculated discharge duration is added.

Four existing LiTE Home 52V Model A records gain short-circuit ratings, DC lead
counts/cross-sections/length, enclosure material and BMS breaker/reset information
from their existing exact datasheet, freshly reread. Their creation dates and all
prior specifications remain unchanged. The upsert API staged all new identities;
its four extension collisions were explicitly reviewed as additions of new keys,
not silent numeric overwrites. Independent old-row/field/timestamp audits passed.

## Source batches, access and market priority

The scalable-source attempt began with the prior REA 2022 inventory lead; its
current PDF URL returned 404. Publicly indexed NEMSA applications offered an
alternative national regulatory source. A representative sample and copyright
footer were inspected before bounded extraction. No open bulk licence is asserted.
Ten selected public application pages were downloaded and SHA256 checked outside
Git. Original pages, attachments, personal fields and binary dumps are not committed.
Two Freedom Won range links returned verification pages; no controls were bypassed.
Four accepted OEM PDFs returned HTTP403 on direct download, but primary-document
text was readable through the search service. Their original-byte checksums remain
null, not hashes of error pages. OEM download index, ownership notices and June
2025 trade terms were reviewed; terms do not establish an open bulk-reuse licence.

IEA's 29 May 2026 commentary was reopened on this pass. The established comparable
metric remains **2025 annual stationary battery power additions, GW**: China just
over 63, USA 19, Australia nearly 8, Chile approaching 1. This is a partial country
order among quantified examples, not an exhaustive global ranking. Europe's 6.2
and Middle East's >3 GW are regional totals, not country ranks. Comparable worldwide
operational stationary energy GWh remains unavailable; no GW-to-GWh conversion.
See the preserved `2026-11-02_pylon_saft_markets.json`. This pass deepens underserved
Africa and a regional OEM while retaining existing worldwide coverage.

## Implementation and next batch

A reusable **offline NEMSA staging adapter and CLI** now extract allowlisted site
and battery fields, preserve unparsed unit conflicts, keep exact entry IDs and
checksum the input. Company-address State fields do not overwrite site State.
Personal contact/owner-name fields are excluded. Identical page copies collapse;
conflicting copies, source-layout drift and wrong URL namespaces fail closed.
It never crawls, fuzzy-merges, imports or asserts operation. Nine synthetic tests
cover these boundaries; all ten downloaded applications were staged successfully.
Canonical additions use the existing importer/upsert API and typed schema.

The accepted source batch is exhausted: ten application entries → nine projects,
with four energy quarantines; ten exact models → ten additions; four existing
models → four substantive enrichments. Uyo/Toto/Lokpaukwu are discovery follow-ups,
not rejected records. Two additional OEM range documents are access-blocked.
Project yield is below the 50–200 planning range because unlicensed bulk reuse was
not assumed, each application required identity/unit review, and four selected
sites had explicit capacity inconsistencies. The model batch meets the 10–30 range.
No idle time was added to meet a duration target.

The ranked backlog records each URL, entity/country, revision/application date,
access/reuse assessment, fields, result, processed partition, retry condition and
next action. Highest-value next steps: Uyo's primary ESS schedule; Toto's 971/972
kWh revision difference; Lokpaukwu 1/2 identity; corrected NEMSA battery schedules
for four energy quarantines; an official replacement REA inventory; then the two
blocked OEM sheets. Recheck freshness and reuse terms before another partition.

## Validation and publication

Full Python suite: **1,616 passed**, one optional `cdsapi` dependency skip. Focused
BESS catalogue/analysis suites: **30 passed**; new adapter: **9 passed**. Both
catalogue validators, duplicate/reference/provenance checks and repeatable typed
Zstandard Parquet builds passed. Binary snapshots remain outside Git; reviewable
coverage/completeness manifests are committed. Further publication checks and
actual elapsed effort are recorded at the end of this log.

All remaining local checks passed: Ruff check/format, ty, repository hygiene,
citation consistency, eight viewer DOM tests, both offline database examples,
the staging CLI example and six wheel/sdist package artifacts. The built retrieval
wheel includes the new adapter. Strict Sphinx documentation build succeeded and
the completed documentation link audit passed for 399 HTML pages. The first link
checker invocation omitted its required output-directory argument; the corrected
command passed. No remote CI success is asserted.

Publication preparation checkpoint: **15:04:49 Atlantic/Canary (UTC)**,
**18.9 minutes actual elapsed effort**. The selected finite source batches
are complete; access and unit/scope blockers for the next batch are recorded above.
No time was spent idling to reach a duration target. The final remote check found main advanced to `2ead6413` after PV PR #73
merged externally. Its changed paths remain wholly under `catalogues/pv/`.
The BESS branch is rebased and revalidated on that main before publication.
Workflow PRs #47–49 have no overlapping files. The new BESS PR is left open.

Revalidation on main `2ead6413` completed at **15:08:24 Atlantic/Canary**
(**22.5 minutes elapsed**): full suite again 1,616 passed / one optional skip;
Ruff, formatting, ty, repository and citation checks passed; both BESS Parquet
manifests are unchanged. Strict docs and the completed 399-page link audit passed.
The target research branch did not already exist remotely. No other work was overwritten.
