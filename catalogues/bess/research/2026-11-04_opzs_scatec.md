# Exact OPzS editions and Scatec portfolio — 4 November 2026

Started 08:48:13 Atlantic/Canary (UTC). Continued OPEN PR133 from
ba25144a4ca17478f8d5387ef4114f0b1922c60c in an isolated checkout. Read current main
c21dd1713067f15adc8b12954c3b7147906a770e, repository contribution instructions,
BESS workflow, both catalogues' schemas/dictionaries, source registers, recent
coverage/manifests and prior review/backlog. Reused PV upsert conventions. No
AGENTS file was present. PR44 and its Australia/Chile review are historical;
no earlier AEMO/CNE candidates were reimported. No subagents or schedule changes.

## Accepted changes and identity review

**Projects: two new, six substantively enriched; one new country, Romania.**
The owner portfolio's nine named construction/backlog battery projects were
reviewed: eight accepted changes and Haru unchanged because another rounded
interest observation alone is not substantive enrichment. Current totals are
**2,008 projects, 43 countries, 327 sources**. All six regions remain represented.

- Dandara phase1 gains the explicitly reported 50MW battery rating, separate from
  its existing100MWh and569MW solar. Dandara phase2 is a separate named backlog
  row:50MW battery,556MW co-located solar,100% reported economic interest. Phase2
  energy remains unknown: no subtraction from the combined200MWh is performed.
  The new phase links to the retained phase1 ID and excludes aggregate ratings.
- Buciumi is new, from Scatec's Romanian owner portfolio and the quarterly report.
  Its owner89MW/178MWh figures remain labelled observations, with scalar ratings
  withheld after differing independent lender discovery. The lender's terms limit
  reuse, so its technical figures, grid details, location and financing are **not
  copied into this database**. The discovery URL and reason for hold are retained.
  Backlog maps conservatively to announced, not permitted/construction/operation.
- Mogobe gains the dated Eskom connection-delay evidence and confirmation that COD
  had not commenced. Dandara1, Energy Valley, Binga, Binga2 and Ambuklao gain useful
  project-level economic-interest observations. The report defines these as shares
  of estimated economic return, not direct legal ownership. Existing owner roles,
  values, dates and nested observations remain intact; no equity/SPV substitution.
- The portfolio appendix is explicitly **as of publication**,30October2026, not
  automatically30September. No change to existing lifecycle dates solely to churn
  timestamps. No project-to-equipment assignments were invented.

**Equipment:16new exact LEOCH OPzS identities from24revisioned two-page sheets.**
Both global index tables and their entire linked PDF partitions were exhausted:
14standard-edition sheets and10telecom-path sheets, with eight overlapping marketed
codes. One canonical record per exact code; edition observations are nested, not
counted as extra configurations. All828prior equipment records remain unchanged.
Current totals: **844equipment,48suppliers,422sources**;831configurations and13families.
No new supplier this iteration. The previous13OPzS holds are now reviewed, plus
three global-index identities absent from the regional table. Earlier three12V
OPzV identity holds remain unresolved.

The new rows preserve C10Ah at20°C/1.80Vpercell;2Vnominal; short-circuit amperes;
maximum charge C-rate; separate charge/discharge/storage temperatures; standby and
cycle voltages with temperature coefficients; conditional self-discharge;20-year
manufacturer design-life claim at20°C; SAN container material; and edition-specific
physical dimensions, approximate mass, dry mass and terminal. None is an inferred
energy, active-power, continuous-current, cell-Ah, warranty or cycle-life scalar.
Finite-duration discharge tables are not promoted to continuous active power.

**Nine model records have field quarantines:** eight have standard-versus-telecom
terminal/approximate and dry mass differences; regional comparison additionally exposes the
6OPzS300 approximate-mass discrepancy. Both dated observations remain attributable.
The5OPzS250 publication string printsV20; it is preserved rather than repaired toV2.0.
PDF text layers contain residual template markers alongside concrete printed values.
A rendered representative page confirms layout and labels; only concrete adjacent
values are staged. Full PDFs and extracted text are outside Git.

There are **zero permanent whole-record rejections**. Five UJVN project candidates
are rights-held, and Buciumi's lender details remain separately held. Accepted
records with held fields are not counted as whole-record rejections.

## Project alternatives, rights and market comparison

Started with the queued downloadable UJVN multi-site owner portfolio and procurement
routes, rather than isolated news. Its copyright policy requires permission, as did
UERC in the prior pass. The owner table has five named candidates, including the
four earlier held identities; no owner/regulator factual records were imported and
no contact was made. Alternative AfDB Eskom March2026 portfolio/terms readers returned
HTTP402; this is an access result, not proof that a fee is required. NamPower's known
June2025 fact-sheet URL returned404; existing Omburu conflicts were preserved.

Scatec's original issuer-linked24.8MB quarterly PDF downloaded successfully after
reader rejection at its size limit. Its9named battery rows, adjacent explanations
and owner country tables provided the accepted project batch. Only bounded attributed
facts are committed; no blanket open bulk-reuse licence is asserted. Scatec privacy
policy and LEOCH sales/region terms were inspected. The LEOCH regional original HTML
returned406; fresh reader review was possible and the checksum is explicitly of
previously retained bytes, not a claimed successful new download.

A fresh original IEA HTML download confirms the selected-country2025 utility-scale
power-additions comparison:China55.10GW,US16.22GW,Australia4.32GW. Europe/MiddleEast
remain regional values, and average duration is not another country. This is a named,
dated comparable metric, **not an exhaustive operational stationary-energy GWh
ranking**. Article/chart inconsistencies and incomparable Indian inventory observations
remain in the market ledger; no MW/MWh conversion or unsupported global rank.

Project yield is below50–200 because the accessible owner partition has nine battery
identities, seven already canonical; two official alternatives were rights/access
blocked. Equipment objective was met with16substantive exact identities. Selected
24-sheet and9-project partitions are exhausted. The next highest-value work is
independently reusable Buciumi site/rating evidence, corrected OPzS physical variant
mapping, and central Indian procurement/VGF disclosures for the five held sites.
The adjacent ranked backlog records URLs, versions, terms, yields, offered fields,
partitions, results and retry conditions; this is not completion of global research.

## Implementation, validation and concurrency

The new offline source-specific OPzS parser/CLI fails closed on missing or mismatched
model/publication, changed voltage, capacity basis, mass units, temperature conditions,
duplicate fields and A-versus-C errors. Twelve synthetic regression tests passed.
Existing upsert/validation/build APIs used; no schema change. All previous scalar
facts, nested observations and creation timestamps are preserved. Incoming identities
are checked against the full canonical set and within the batch without fuzzy merge.

Current main was merged into this research branch locally with both parents retained.
The four shared-reference conflicts were resolved by a union that asserts equal
content for common IDs and preserves every entry from both parents; citation exports
were regenerated. This brings in the **already-merged** DataCenter encoding repair
and Wind changes, rather than independently editing those catalogues. Unrelated
catalogues are byte-identical to current main. Open PV134, DataCenter135 and Wind136
titles/changed paths were inspected; new BESS files do not overlap. New bibliography
entries remain queued for active Wind136 shared-reference work, with complete BESS
source metadata and field citations already committed. No active PR was merged.

Validation and actual elapsed effort are recorded in the adjacent validation ledger.
The first full-suite run found one stale citation-export test (2,211passes,5optional
skips); regeneration fixed the issue. The repaired full suite passed 2,212 tests with five optional-dependency skips. A final revalidation follows the subsequent main advance.
Both catalogue validators,289BESS tests,15viewer tests, all-prior-record preservation,
two byte-identical typed Zstandard snapshots per catalogue and offline examples passed.
No original binary document or snapshot is committed. Leave the PR OPEN for review;
publication uses a fresh head/main/PR check and expected-head non-force update.

At publication preparation, main advanced to `65c8cb6704a9b1cc1bf7529c19ad40eefa4b9144` after PV134, DataCenter135 and Wind136 were merged by others. These changes were incorporated without BESS overlap. The earlier bibliography deferral remains an auditable queue; its concurrency reason describes the extraction-time state. Final checks below refer to this reconciled tree.

Final reconciled validation at **09:13:47 Atlantic/Canary**, **25.57 minutes actual elapsed** from start: **2,259 passed, five optional-dependency skips**; strict Sphinx with gallery execution disabled passed, as did Ruff lint/format, explicit-venv type checking, hygiene, citations, 15 viewer tests, both actual offline examples, deterministic typed snapshots and all six package distributions with strict Twine. The initial incorrect project-example filename was corrected and rerun successfully. Publication follows this checkpoint; no full-gallery, installed-wheel or remote-CI pass is claimed.

The immediate publication check also found new OPEN Wind PR137: its 30 changed paths contain no BESS catalogue/importer files, but do include shared references/viewer files. The 30 new BESS bibliography entries therefore remain queued; the only shared edits in this PR reconcile previously existing parent references. Dependabot47–49 change workflows only. Main and the BESS target head remained unchanged at this check.
