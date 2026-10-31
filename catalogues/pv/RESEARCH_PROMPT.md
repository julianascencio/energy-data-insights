# PV database research specification

Build and continuously enrich the public `julianascencio/energy-data-insights`
global PV asset catalogue. Cover OEM PV modules, PV inverters, trackers, combiner
boxes, and PV projects. Optimize verified coverage and useful metadata, not row
count. Use the current schemas, adapters, source register and tests in this repository.

## Scope and acceptance criteria

1. Maintain one canonical record per exact equipment model/configuration and one
   per project. Preserve aliases, source identifiers and phased assets without
   double counting. Review potential duplicate OEM names, punctuation/case variants,
   renamed facilities and nearby projects; never fuzzy-merge automatically.
2. Match established columns before adding new ones. Capture all available factual
   electrical, mechanical, thermal, optical, control/communication, environmental,
   certification and warranty metadata. For projects capture location and accuracy,
   lifecycle/status as-of date, owner/operator/developer/EPC, AC/DC capacity, dates,
   grid connection, equipment and counts, storage, area, expected generation, PPA
   and published costs with currency/year/basis. Omit private personal details.
3. Preserve units, test conditions, variants, uncertainty, explicit bounds and missing
   values. Do not derive active power from kVA, AC from DC, exact counts from approximate
   text, plant coordinates from a city center, or current operation from an old release.
   No invented technical specifications, dates, ownership or equipment assignments.
4. For every populated field retain its source mapping, with exact URL, publisher,
   title, document version/date where available, retrieval time, table/page/row locator
   and source checksum where bytes are downloaded. Record license/attribution and
   access limitations. Prefer OEM datasheets, regulators, system operators, government
   inventories and plant owners. Treat marketing gains as claims, not model parameters.
5. Use globally diverse sources and languages. Balance Africa, Asia, Europe, Latin
   America/Caribbean, North America and Oceania. Within each region prioritize missing
   countries and smaller manufacturers/projects as well as utility-scale leaders.
   Report actual country/model coverage; never call CEC equipment listings worldwide
   market coverage or a handful of projects a complete global project database.
6. Preserve created_at. Update updated_at only for substantive content/evidence
   changes. Track last_verified_at separately. Deduplicate identical findings.
   Keep conflicting values with evidence in a review file until resolved; do not
   silently overwrite. Empty fields do not erase verified data.
7. Store reviewable JSONL in Git; build Zstandard-compressed, typed Parquet snapshots
   using the package. Validate schema, ranges, IDs, links, dates and evidence; generate
   a coverage/completeness manifest, checksums and an offline example. No API keys,
   copyrighted full documents, binary data dumps or unverifiable harvested claims in Git.

## One scheduled research iteration

- Read main, this specification, `research/launch_report.md`, schema and source
  registry. Inspect open PRs before changing anything. Find a PR whose title starts
  `[PV database]` and whose scope/branch actually updates this catalogue. If it exists,
  work on its current head in an isolated checkout. Otherwise create a fresh
  `research/pv-database-<UTC date/time>` branch from current main when substantive
  additions are ready. Never reuse a closed/merged PR or overwrite another branch.
- Inspect the previous research log to avoid repeated sources and overlapping runs.
  Rotate six macroregions using the UTC hour modulo six, then select countries with
  the lowest verified project coverage. Also prioritize trackers and combiner boxes
  until their coverage is useful, and add OEM module/inverter specifications absent
  from CEC/SAM. The rotation is a prioritization rule, not a prohibition on useful
  evidence from another region.
- Do a bounded research pass, aiming for completion within 45 minutes. Seek both new
  records and missing fields in existing records. Prefer precise datasheet tables and
  downloadable official registries. Use conditional requests/checksums where possible;
  respect service limits/terms, retries and backoff. Never submit contact forms or
  fabricate registration details to obtain a gated datasheet.
- Check source freshness and license before any bulk ingestion. GEM includes PV,
  assumed-PV and CSP, phases and aggregates; only positively identified PV belongs
  here. TZ-tagged records have noncommercial restrictions. National records need
  plant/phase reconciliation. WRI GPPD is historical discovery material and generic
  `Solar` is insufficient to prove photovoltaic technology.
- Add immutable source entries and explicit evidence. Use the importer/upsert API.
  Check for natural-identity duplicates and equipment/project links before acceptance.
  Record blockers and conflicts under `catalogues/pv/research/` with UTC date and scope.
  Do not force a minimum row quota when evidence is insufficient.
- Run catalogue validation, focused pytest, repository Ruff/format/ty checks and
  build a fresh Parquet snapshot. If code or schema changes, run the wider relevant
  suite and docs. Fix failures introduced by this update. Keep binaries outside Git.
- Commit substantive accepted additions/metadata corrections and research evidence
  to that same open PR. Push without force; if its head moved, fetch, reconcile and
  revalidate. Create a new PR only if none remains open. Update its description with
  cumulative counts, countries, sources, meaningful changes, validation and limitations.
  Do not create empty PRs or commit timestamp-only churn.
- **Leave recurring research PRs open for review. Do not merge them automatically.**
  The initial launch PR alone was explicitly authorized for merge. Report the PR link,
  added/enriched/quarantined record counts, new countries/OEMs, checks and concrete
  blockers. If no substantive change, briefly say so and preserve useful blocked-source
  evidence without inventing progress.
