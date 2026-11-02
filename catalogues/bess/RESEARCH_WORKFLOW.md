# BESS research workflow

Each research iteration should produce verified additions or corrections, with a
small durable checkpoint explaining what was searched and what remains uncertain.
The catalogue contains projects and registry-defined plants; it is not a census
or a live availability feed. Do not interpret record counts as installed capacity.

1. Read the current main branch, open BESS research PR, schema, source registry
   and latest research/reconciliation ledgers. Reuse a matching open research PR;
   otherwise create a new branch from main. Never discard another task's work.
2. Rotate countries and evidence gaps. After the November 1 Australia/Chile batch,
   prioritize China, India, continental Europe, Africa, Latin America outside
   Chile, and non-NEM Australia. U.S./UK registry coverage dominates the current
   sample. Older facts missing from the catalogue are useful as well as news.
3. Prefer primary regulators, system operators, owners, OEMs and EPCs. Search in
   local languages when useful. Check recent status updates as well as technical
   sources. Register exact URLs, access method, retrieval/publication dates,
   source terms and downloaded inventory checksums. Raw downloads stay outside Git.
4. Stage national inventory candidates with `scripts/stage_bess_inventory.py`.
   For the reviewed PIB Indian Table-II format, use `scripts/stage_bess_pib.py`
   on downloaded HTML; it stages candidates only and does not import identities.
   For public NEMSA mini-grid applications, `scripts/stage_bess_nemsa.py` stages
   allowlisted site/battery observations without personal contacts or unit repairs;
   an inspection request is not an operating certificate.
   For the reviewed Victron 120 V and 2 kVA 230 V HTML manuals,
   `scripts/stage_bess_victron_html.py` preserves exact model headers, explicit
   merged-cell scope and separate W/VA rows. It stages facts only; compare
   undated editions and retain conflicting auxiliary/standard observations.
   For the ODRÉ French register, use `scripts/stage_bess_odre.py` on downloaded
   API JSON with the explicit reporting date. Exclude aggregates, confidential
   names and inconsistent battery classifications; review multiple EICs at one
   location before treating them as distinct projects or phases. Tiny reported
   kWh values are quarantined, never silently rescaled. Preserve industrial-service
   dates separately from contractual COD and annual energy separately from storage.
   For Rolls flooded model pages, `scripts/stage_bess_rolls.py` stages exact named
   HTML tables, rate-dependent monobloc Ah and charge limits. No inferred MWh,
   cell-capacity substitution or charging-unit repairs; review source revisions.
   Resolve external IDs, aliases, physical location, phases and commercial-project
   scope against existing rows and the ledgers before accepting candidates.
   AEMO survey sites 3100/3101/3102 already belong to the single MREH record.
5. Use the existing typed schema and explicit field provenance. Preserve stable
   IDs and creation times. Leave unsupported fields null. Battery MW, grid MW,
   solar MW, annual GWh and stored MWh are different quantities. Keep electrical
   and energy rating bases explicit. Do not derive discharge hours as a reported
   fact, guess a supplier's role, or turn a forecast date into COD.
6. Retain conflicting observations and qualify the chosen scope. Do not overwrite
   curated ratings simply because a registry is newer. Administrative construction
   status is not evidence of physical progress; commissioning is not commercial
   operation. Inauguration and commercial-operation authorization are distinct
   milestones. Keep unresolved candidates in the review ledger.
7. Keep canonical UTF-8 JSONL shards below 2 MB; rebuild Parquet and derived browser
   data offline. Update documentation counts and research notes, and add sources
   to the reference registry. Run citation regeneration, catalogue validation and
   relevant tests. For adapter or publication changes, run repository checks and
   strict documentation/viewer validation as required by CONTRIBUTING.md.
8. Publish an evidence-backed PR update with a leased branch update. Report new
   and enriched counts, countries, unresolved gaps, checks and the PR link. Do not
   auto-merge without user authorization. Keep the PV research task independent.

If no reliable additions are found, report that accurately and record a concise
checkpoint when it will prevent repeated work. Do not create empty commits or
invent records to satisfy a target count. If a source becomes unavailable, retain
its previous observation and record the access failure rather than asserting a
new verification.
