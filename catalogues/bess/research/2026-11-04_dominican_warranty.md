# Dominican regulator and exact-model warranty review

Started 4 November 2026 at approximately 00:49 Atlantic/Canary (UTC). Continued open
PR #121 from ec971db889a909be09cff88d24a4fe4b5380d6c3 in an isolated worktree;
current main 7af547f900d676b4334226a64739aed2f4cb3f97. PR #44 is historical.
Read repository contribution rules, BESS workflow/dictionaries/schemas, current
sources/manifests and previous residential/owner reconciliation. Reused existing
PV upsert and typed catalogue APIs. Open PRs 119/120/122/124/125 were inspected
by titles and changed paths; no overlapping BESS/shared-reference writes observed.

## Project batch: four accepted identities

Attempted SIE's official national resolution inventory first, including current
archive and terms. The public archive is not an open bulk-reuse licence. Selected
individual resolutions received bounded factual review; no national scrape or
republication of legal documents. Original PDFs downloaded successfully and are
hash-pinned outside Git. The public reader rejected the large January files;
ordinary original downloads and local rendering were the alternative. OCR was
used only to locate pages; technical tables, decision text and dates were checked
visually. Personal contacts and signatories are not extracted into records.

- **Mirasol:**50.68MW proposed battery addition. Original and corrected resolutions
  form one identity. The correction restores an incomplete decision article but
  prints202.712MWh where its cover and written words say202.72MWh. Canonical
  energy remains null; both assertions survive. Environmental-licence component
  energy has a different aggregate scope and is not substituted. Proposed Fluence
  GSP5K/PE PCSM, AC coupling, collection-transformer voltage, dispatch cycles,
  licence and applicant are captured without asserting installation.
- **Santanasol:**31.68MW/126.72MWh, four hours. SIE verifies the concession-holder
  transfer from AES Andrés to AES Dominicana Renewable Energy; both roles and
  transfer evidence survive. PV phases remain separate from battery capacity.
  The138kV shared-site line/Pizarrete connection is labelled by scope.
- **Peravia Solar I:**44.35MW/177.4MWh, four hours. The battery is physically at
  Peravia Solar II's interconnection substation, also serving Solar I. One battery
  record, not two phases. Proposed equipment and dispatch/site metadata captured.
  The2025 footer conflicts with the2026 cover and signed date; preserved explicitly.
  Environmental container inventory is distinct from the resolution energy rating.
- **BESS-Haina:**80MW/160MWh installation permission dated8 September 2026, separate
  from 120MWh service allocation. Permission is not commercial operation. Capture
  includes EGE Haina,138kV connection, primary/secondary regulation, commissioning
  prerequisites, transformer-review constraint and conditional incentive horizon.
  A technical paragraph names **EL FURGON**; its LFP, cooling, grid-forming,
  voltage, duration and20-year-life claims are held, not assigned to Haina. The
  seven associated generators are a service portfolio, not seven more batteries.

Four reviewed project identities yield four new records, zero existing-project
edits, three accepted records with field holds, zero whole-record quarantine or
permanent rejection. The200MW tender and CNE20-plus project announcement are
aggregates, not counted as individual candidates. LAESA's SIE1202026 summary is
a deferred discovery, not an accepted or fully reviewed project.

## Equipment and substantive enrichment

Reviewed V1.41's complete 12-page OEM warranty against 31 existing BSLBATT identities.
Twelve exact Table 1.0 matches are enriched: two rack batteries, three PW wall
batteries, five MatchBox HVS stacks and two10-pack station strings. No new models
or suppliers. Preserve the existing specification ratings, created_at, older
conflicts and the superseded claim-only warranty wording in evidence history.

New metadata distinguishes two-year electronics/enclosure/BMS coverage from
conditional ten-year/6,000-cycle stationary performance coverage, output-throughput
limits, unallocated60–70% retention range, start-date alternatives, authorized
purchase/installation, OEM-affirmed registration, transfer and cost exclusions.
Contract-table energy remains a separate observation, not a replacement for rated
nominal/usable energy or a cycle-life marketing claim.

All 12 models carry the unresolved clause 2.3 versus Appendix A temperature conditions.
The300E and300PW rows each have two different energy/throughput entries under an
identical label: no scalar contract throughput is chosen for these two models.
The other 19 existing identities are deferred for this contract partition:12
non10-pack station configurations,100E3U exact applicability, four unlisted
PowerNest models and two cabinets governed by another contract. No family-wide
throughput extrapolation, registration submission or contact with the OEM.

The existing upsert API correctly returned 12 nested-evidence collisions. Each was
explicitly reviewed: append contract observations, preserve existing facts and
replace only the now-incomplete claim-only warranty qualifier. Preservation audit
checks unchanged prior extensions/conflicts and every technical rating. All other
existing records remain byte-equivalent as parsed objects.

## Coverage, yield and next work

Current proposed totals: **1,993 projects /42 countries /313 sources** and
**749 equipment /46 suppliers /367 sources**. Dominican Republic is the new country;
no new supplier. All six regions remain represented. The IEA page was freshly
retrieved and checked:2025 annual stationary battery power additions, GW, with
quantified-country examples China>US>Australia>Chile. This is a partial comparable
power-addition ranking, not a global operational-energy census. Operational GWh
ranking remains unavailable/incomparable; no conversion from GW.

The selected four-project/five-PDF regulator batch and exact-model warranty
partition are exhausted. Project yield is below the 50–200 planning objective:
scanned individual resolutions require identity, revision and status review, and
no licensed multi-record export was established. Twelve substantive model
warranty enrichments meet the 10–30 equipment planning range without thin new rows.
Remaining annexes and other archive entries are explicitly unprocessed, not a
claim that the national registry is exhausted. Next highest-value project source:
SIE1202026 LAESA followed by a reusable CNE concession export; equipment: corrected
300-series contract rows and Li-Pro/PowerLine/ECO exact tables. Recheck versions
and terms before resuming. Detailed URLs, partitions and retry conditions are in
the companion backlog; downloads/checksums and decisions are in the review JSON.

No schema or parser change was needed for this bounded manual source review.
Canonical JSONL and evidence are prepared for the scoped commit; typed Zstandard snapshots and source
bytes stay outside Git. Existing source-specific adapters were not modified.
Validation and actual elapsed effort are recorded below after completion.

## Completed validation and effort

Validated at 01:10 Atlantic/Canary on 4 November 2026, approximately 22.0 minutes from the 00:49 start. The selected source partitions were exhausted; no waiting to fill the time window. Publication follows these checks.

- 2,124 Python tests passed; 57 focused catalogue/reference tests and a final 28 catalogue tests passed.
- Catalogue validators, reviewed identities, preservation audit and two identical typed Zstandard snapshots passed. Documentation publication reproduces the final snapshot hashes.
- Ruff lint/format, repository typing, citation exports, hygiene and diff checks passed; 15 viewer tests and both offline examples passed.
- Strict Sphinx and the 518-page local-link/asset audit passed. Root disk exhaustion initially blocked documentation output; rebuilding in available temporary memory resolved it.
- Three wheels and three sdists built; strict Twine passed on all six. An initial invocation included a non-distribution .gitignore and was corrected. Installed-wheel smoke was not repeated for this data-only update; no remote CI outcome claimed.

Exact checks and initial-attempt limitations are in the validation JSON. The earlier full-suite results cited in historic logs remain historical.
