# Nordic owner portfolios, Samoa procurement and Crown exact configurations

Research began 3 November 2026 at 05:53 Atlantic/Canary (UTC on this date).
Continues open PR90 at `f6ad2aec9f46a87a4afe3f559d8cdccae714c08a`, based on
main `15e9d60b84b0e741979437fd8d7172f0d7e30824`. The November1 PR44 checkpoint
is historical; its Australia/Chile identities and held phases were not reimported.
Current main, workflow, dictionaries, source registers, manifests and recent
research/backlogs were read. PR89 Wind, PR91 PV and PR92 Data Center changed
paths were checked; no competing BESS work was found. Shared reference exports
are additive, and other catalogue data/schema/importers remain untouched.

## Accepted data and reconciliation

This iteration adds **20 projects**, enriches **two existing projects**, and adds
**31 exact Crown Battery configurations**. Proposed totals are **1,758 projects,
37 countries, 226 sources; 567 equipment records, 42 suppliers, 242 sources**.
Country additions are Sweden15, Finland4 and Samoa1; no new countries.
Crown Battery is a new supplier. All six geographic regions remain represented.
Counts describe reviewed records, not a global census or installed capacity.

- Reconciled all14 BW ESS/Ingrid Swedish sites against the current named operating
  portfolio, eight-site February2024 announcement and the engineer's portfolio
  presentation. Visually checked PDF page5 (printed slide6). Fourteen site MW
  values are sourced individually; the211MWh fleet total is not divided among
  sites and no aggregate facility row is created.
- Retained11MW for Vaggeryd and Västerås from the announcement, with12MW slide
  observations quarantined. Slide labels sum213MW despite its211MW heading.
  No assumption that this is an expansion, rounding or grid/export distinction.
- Added Pedersöre45MW/90MWh and Vaggeryd100MW/200MWh as separate Ingrid/Mirova
  developments. Ready-to-build and a signed offtake are not operation or physical
  construction. Mirova's EUR65million is a two-project investment, not per-site
  capex. The100MW Vaggeryd development is distinct from the11MW BW ESS site.
- Added Haapajärvi125MW/250MWh from NEPower: EPC scope,110/33kV connection,
  construction and mid2027 forecast. Preserved the September heading date and
  November publication date. Added Valkeakoski30MW/36MWh using independent Merus
  commissioning/EPC evidence, with supplier-qualified grid-forming claims.
- Added Mertaniemi38MW/43MWh with actual market-use date15May2025, nominal energy,
  approximate power qualifier, JV participants, developers and EUR15million
  supplier delivery value separated from whole-project capex.
- Added Fiaga's public SAMEPC12/2026 tender for25MW/50MWh battery plus25MWpPV,
  bidding deadline and20-year post-COD contract. It is announced procurement,
  distinct from the2018 Fiaga PSEP battery. No NDA-controlled documents accessed.
- Enriched the existing Yllikkälä phases using Destia: construction history,
  participants,20containers,110kV connection, actual2025 operation year, site
  area, transformer voltage/apparent power and remote operation. Destia's56.6MW
  differs from owner56.4MW; retain owner rating and quarantine the other assertion.
  Nidec's equipment supply does not establish cell manufacture. The first phase's
  construction participants are not promoted to unsupported EPC contract roles.
- Processed all31 Crown SB-CRP-G0720 table rows:19monoblocs, six power modules and
  six FreedomBloc configurations. Exact models, voltage, C20/C100Ah, dimensions,
  mass, terminals and source revision are retained. These are historical2020
  specifications, not current availability claims. No Ah-to-MWh inference.
- All31 reported kWh pairs remain qualified observations outside canonical energy:
  the source's50%DoD/1.94Vpc footnote does not establish a clear usable boundary.
  Also withheld6CRV400height and12CRV100mass because metric/imperial observations
  differ by over1%. Both observations remain reviewable; no unit repair.

The three project rating conflicts,31 equipment energy holds and two physical
field conflicts are **field-level**, not rejected records. There are zero permanent
record rejections. Creation timestamps and all pre-existing verified scalar facts
are preserved; only two pre-existing project rows changed. No project-equipment
assignments were invented.

## Sources, limitations and why project yield is below50

Twenty-two canonical project candidates yielded20new and2enriched records.
The selected14-site owner portfolio and31-row equipment table were exhausted.
The equipment working objective was met. Project yield was limited by reuse
restrictions and unresolved independent site evidence, rather than padded with
anonymous assets or aggregate rows. The review JSON separates additional
source-specific held candidates and overlapping observations from accepted IDs.

Scalable sources were attempted before isolated releases. Eskom's12-site owner
inventory had seven existing sites and five already held under restrictive terms.
JRC's European inventory was sampled: Eskilstuna explicitly uses Wood Mackenzie
content, so the EU site's default CC BY does not establish third-party dataset
reuse rights. No bulk JRC extraction was performed. Locus's public client renders
anonymized labels; no hidden names or nonpublic data were queried. Its13-site
Ingrid portfolio remains a named-source reconciliation backlog.

Exide's two tables offered21exact models but its legal notice restricts product
information reuse to personal/private purposes; all21remain held. Apolima's
technical specification restricts use to project evaluation/implementation.
JICA's three planned site observations remain held under its nonpersonal reuse
policy. Axpo's three candidate sites and Alpiq's direct material have public-use
restrictions; two Alpiq Finnish projects were independently sourced from their
EPC/supplier, while La Corne-en-Vexin remains deferred. No people were contacted.

Accepted publications are bounded factual observations, not an assertion of open
bulk licensing. Downloaded original bytes are outside Git with SHA-256, URLs,
retrieval timestamps, titles and page/section locators in the source register and
review ledger. Copyrighted documents/artwork are not committed. The source
backlog records version, access/terms, fields, yield, partitions, retry condition
and next action for each examined source.

The IEA comparison was freshly rechecked:2025 stationary battery **power additions**
rank the quantified country examples China(just over63GW), United States(19GW),
Australia(nearly8GW), Chile(approaching1GW). Europe6.2GW is a region, not a country.
This is not an exhaustive market ranking. Comparable operational stationary
**GWh** remain unavailable and are explicitly null; no power-to-energy conversion.
See the dated markets JSON for attribution and scope.

## Reproduction and validation

The new offline adapter consumes `pdftotext -layout` output of the reviewed Crown
edition, preserves source observations and fails on changed edition, malformed
rows or duplicated exact models. It stages candidates only. Existing canonical
upsert/validation APIs perform acceptance after manual identity review.

```bash
pdftotext -layout /outside-git/Renewable-Energy-Batteries.pdf /tmp/crown.txt
uv run python scripts/stage_bess_crown.py /tmp/crown.txt --output /tmp/crown-candidates.json
uv run pytest data-retrieval/tests/test_bess_crown.py
uv run python -m energy_data_retrieval.bess_catalogue validate
uv run python -m energy_data_retrieval.bess_oem_catalogue validate
```

Independent typed Zstandard Parquet builds and coverage manifests are recorded in
`2026-11-03_nordic_crown_manifest.json`; preservation and candidate ledgers accompany
this log. Binary snapshots use the existing ignored artifact/build mechanism,
not Git. Validation and elapsed-time results are appended after completion.

Next highest-value work: verify Mäntyharju's commissioning and Tymbark's exact
site identity from the already identified public Merus releases, then reconcile
named sites in the13-project Ingrid/Locus portfolio. Resolve Swedish11/12MW
ratings and Crown energy/unit ambiguities from newer exact source editions.

## Completed local checks and effort

Final local validation checkpoint: 2026-11-03 06:12 Atlantic/Canary.
Measured research, implementation and local validation effort: 19.4 minutes;
publication transport follows this checkpoint. Finished the selected14-site and
31-model tables early rather than idling to fill45minutes. Other sources are
explicitly held or queued; no claim that worldwide research is exhausted.

Full Python suite: **1,754 passed, one optional cdsapi skip**. Final focused
parser/catalogue suite:36passed. Viewer:11passed. Both offline examples, catalogue
validation, independent typed Zstandard snapshots, Ruff/format, ty, citation and
repository checks passed. Six distributions built and passed strict Twine checks;
all three installed wheels passed outside-workspace smoke tests. Strict Sphinx
and all422HTML-page local links/assets passed. The first full run caught citation
exports pending regeneration; the final full run passed. A later cost-reporting
wording correction was rebuilt, revalidated and checked by the focused suite.
No schema or dependency changes. Remote CI for the new commit is not assumed.
