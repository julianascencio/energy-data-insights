# Flower portfolio, Sinexcel guidebook and BlueNova exact equipment

Research began **3 November 2026, 10:47:25 Atlantic/Canary (UTC)**. End time and
actual elapsed effort are recorded in the companion review ledger after validation.
This iteration continues OPEN PR102 at `c7edcb0d1cc0432304056c1e2d0b755238c11ad3`.
Main at discovery was `5063c41694b17b1a3fc856ea9527a32211278203`. PR44 and its
successors are merged historical work, not a new foundation to duplicate.

## Accepted changes and scope

- **13 new projects**: eight Swedish and five German named battery sites.
  No existing project records changed; no new countries.
- **21 new exact equipment configurations**: ten Sinexcel PCS/integrated
  configurations and eleven BlueNova products (ten DC cabinets, one controller).
  **BlueNova is a new supplier**, separately identified as brand/system supplier;
  no cell manufacturer or project installation is inferred.
- **Two existing Sinexcel models substantively enriched** with conflicting
  guidebook revision observations. Creation dates and original source-scoped
  electrical/mechanical ratings are preserved. The upsert API first quarantined
  the conflicting proposed edits; an explicit reviewed evidence-only update adds
  the alternatives to `conflicts_json` without silently selecting a revision.
- Proposed catalogue totals: **1,809 projects / 37 countries / 268 sources** and
  **645 equipment records / 44 suppliers / 306 sources** (632 exact configurations,
  13 families). All six world regions remain represented. This is incomplete
  research coverage, not an operating-capacity census.

Flower's complete Q2 owner inventory is the scalable project source for this pass.
The offline adapter checks reporting period, sections, exact units, duplicate names
and control totals: ten source rows reconcile to 209.6 MW and 496.7 MWh. Nine rows
are accepted. Marieboda's 3.3 MW row may represent two acquired assets mentioned
in the narrative; it is held rather than added as one physical project. Four more
named sites come from dated owner disclosures: Hanhals, Bergedorf, Borken and Berga.
The other five Chint portfolio sites remain unnamed in the reviewed release and
are held. No 112 MW portfolio aggregate or residual-capacity project is created.

Lifecycle observations remain dated. Q2 operating/construction status is as of
30 June, not a current November assertion or inferred COD. Borken/Berga have
permitted/ready-to-build status as of July and separately dated October acquisition
closings; an acquisition is not construction or operation. Bergedorf's September
construction and end-2028 target remain distinct. The October ownership chain,
SEK217.5 million share acquisition consideration and bond ISIN are preserved;
that price is **not capex**. Hanhals records Flower's optimizer role, not ownership.
Kungälv's 15 MW versus 14.8 MW observations remain quarantined with canonical MW
null; a rounding/rating explanation is not assumed. Energy remains available.

Sinexcel's 2025 guide has 20 exact model columns: ten new, two existing with useful
revision-conflict evidence, seven already covered without substantive changes,
and one held suffix (`PWS1-450M-H-L-CN`). Separate125P and135M sheets corroborate
four accepted columns. Captured power boundaries, nominal energy/LFP for the
SES cabinet, cell/pack configuration, voltage/current, overload conditions,
mechanical dimensions, mass bounds, IP, cooling, temperature/altitude derating,
communications and conversion-efficiency boundaries. Four new PCS records retain
feature-page `>99%` versus table `99%` conversion-efficiency conflicts. Neither is
RTE. AC kVA does not become active kW. The existing1250/1725models retain unresolved
voltage, branch/current and rack/mass alternatives from guide page19.

BlueNova's eight current314Ah air-cooled sheets and two liquid-cooled sheets were
reviewed individually. Exact energy, voltage, module counts, cell test conditions,
thermal limits, fire systems, dimensions/tolerances, mass qualifiers and controls
are retained. “AC” in these model names means **air cooled**. The PCS compatibility
plots are not installed PCS power ratings. The225k sheet's parallel-energy claim
and418k sheet's `<1000VDC` feature statement versus higher voltage table remain
quarantined; the latter's canonical voltage scalars are null. Unusual standards
labels are transcribed as manufacturer claims, not independently verified
certifications; UN38.3/MSDS are not recast as product certification. The BMAC manual
explicitly identifies **version D**, revision4.1 dated28October2024. BMAC-E and
HV-BMAC labels remain held, not automatically aliased. Its supply-voltage limits
refer to the controller, not compatible battery voltage. No contact form or
registration was used.

## Evidence, access and reproducibility

Original PDFs/HTML and SHA256 hashes are retained outside Git. Committed records
contain selected factual observations and page/row/section mappings, not source
PDFs, figures or copied narratives. Sources register publisher, exact URL, known
publication/revision and actual UTC retrieval time. No open bulk licence is
asserted for Flower, Sinexcel or BlueNova. Copyright notices and current source
pages were inspected before the selected bounded factual review. BlueNova's
current sale terms retain IP in goods/services; the public facts here do not
redistribute the underlying documents or grant a reuse licence. An older indexed
sale-terms URL and BMAC listing returned404; the current linked sale-terms PDF and
exact manual were obtained normally. Search cached text was not treated as
successful original-byte access.

The new Flower source-specific adapter operates only on local text, stages
candidates and never merges identities. Run:

```bash
pdftotext -layout Flower-Second-Quarter-2026.pdf flower-q2.txt
uv run python scripts/stage_bess_flower.py flower-q2.txt --output flower-candidates.jsonl
```

The reviewed source table is fully exhausted, including the held row. Synthetic
parser tests cover changed period, missing status section, units, duplicate names,
nonpositive capacity and failed/missing totals. Exact equipment facts are manually
reviewed columns submitted through the existing upsert API; materially different
layouts are not forced into the earlier Sinexcel parser. All1796prior projects and
622of624prior equipment rows remain byte-for-byte equal as decoded JSON; the two
reviewed evidence enrichments preserve every other field and creation time.
Typed Zstandard snapshots are built twice through the established packages and
compared. Manifests record coverage/completeness and immutable input/output hashes.

The dated market comparison rechecks IEA's2025 annual stationary battery **GW
additions**, ranking only the quantified country examples. A comparable worldwide
operational stationary **GWh** ranking remains unavailable; no conversion or false
country ordering is introduced. Africa/Asia/Europe/Latin America/North America/
Oceania coverage is preserved, with this iteration deepening underrepresented
Sweden/Germany projects and South African equipment.

## Yield, concurrency and next work

The equipment objective is met with21new exact records and2substantive quality
enrichments. Project yield is below50 because the selected complete owner table
has only ten named rows, one is scope-ambiguous, and five other portfolio sites
lack individual identities. Four release-supported sites increase accepted
project yield to13. No sparse residual rows, cosmetic suffix variants, fabricated
parallel configurations or timestamp churn are added. Selected owner and OEM
partitions are exhausted; the pass proceeds directly to validation/publication
without waiting to satisfy a duration.

Open Wind101 owns shared bibliography paths and advanced during this run; DC100
and PV103 own other catalogue/viewer work. Those overlapping files are untouched.
Twenty-one new reference entries are queued in this run's scoped pending-reference
file alongside the16from the preceding increment. Catalogue citations are complete;
shared bibliography integration remains pending until Wind101 settles. This is
an explicit concurrency limitation, not a claim that integration passed.

Next: verify the current Irish EirGrid/ESBN battery inventory version and reuse
terms, reconcile named grid IDs and distinguish MEC from battery MW; obtain the
latest Eskom named-site lifecycle report; review BlueNova's five exact AIO sheets.
Resolve Marieboda/Kungälv, Sinexcel revision/suffix and BlueNova conflicting claims
before choosing scalars or new identities. The dated ranked backlog carries forward
prior NZ permit and Transpower reuse holds without falsely refreshing them.

## Executed validation

Validation completed 2026-11-03T11:10:18.516117+00:00 (Atlantic/Canary equals UTC on this date),
22.89 minutes after research began. Publication follows immediately.

- Full Python suite: **1,840 passed**, one optional `cdsapi` skip.
- Eight focused parser tests and complete original-table replay passed.
- Both catalogue validators, preservation audit and two independent Zstandard
  builds passed; manifests include completeness and file hashes.
- Ruff, formatting and ty passed. Type checking initially selected the wrong
  interpreter; rerunning with the intended virtualenv exposed one row-inference
  issue, fixed with an explicit list type. No dependency/schema change.
- Thirteen viewer Node tests, both offline BESS examples, strict Sphinx and
  the **445-page** local link/asset audit passed.
- All three package wheels/sdists built; strict Twine and installed-wheel
  public entry-point checks passed. No fresh interactive browser or optional
  imagery wheel check claimed.
- Current shared citation consistency passed, with new bibliography entries
  explicitly still queued. Final repository/whitespace checks rerun before commit.

Main and PR102head were unchanged at the final reconciliation checkpoint;
Wind101, DC100 and PV103 had advanced on nonoverlapping paths. Publish with a
non-forced expected-head update, never overwrite their work. Keep the recurring
research PR **OPEN and UNMERGED**.

Publication prepared at 2026-11-03T11:12:05.576988+00:00; **24.68 minutes**
of elapsed work through preparation. Selected partitions exhausted; remaining
publication time is branch/tree verification and PR metadata, not additional research.
