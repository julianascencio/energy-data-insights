# New Zealand evidence and exact BESS controllers — 4 November 2026

Started **11:45:37 Atlantic/Canary (UTC)**. Continued open PR133 from Git-verified
`4520feadf23c270a64aeda136bd093a3b8f70065`, in an isolated checkout. Main remained
`7004215c89e6d4482a391577d321605860ae0f9a` through the publication preparation check.
Repository instructions, research workflow, dictionaries, schemas, sources, current
manifests and recent logs were reviewed. The Australia/Chile checkpoint and previous
Kehua/REPD batches are historical; no completed candidates are reimported or recounted.
Open BESS133, Wind137, Data Centers139, Kazakhstan140, HVAC141 and PV142 were checked
by title and changed paths, including a second check before publication. No overlapping
BESS write or foundation dependency was found. No subagents or PR merges were used.

## Accepted records and evidence

| Entity | New | Substantively enriched | Field quarantines | Other decisions |
| --- | ---: | ---: | ---: | --- |
| Projects | 0 | 6 | 1 | Two owner-source leads withheld for terms; prior inventory holds retained |
| Equipment | 17 | 0 | 1 | One generic-model identity hold; two peripheral accessories excluded |

Current totals are **2,058 projects / 43 countries / 335 sources** and **887 equipment
records / 50 suppliers / 439 sources**. Equipment includes 874 exact configurations
and 13 explicitly configurable families. Elum Energy is a new supplier; no new project
country. All six geographic regions remain represented. These are catalogue counts,
not a global installed-capacity census. The cumulative PR versus current main adds
62 projects and enriches39, adds115 equipment configurations and enriches8.

The Electricity Authority's **29 September 2026** six-row BESS status table was
retrieved as original HTML, checksum recorded, and covered by its CC BY4.0 notice.
All six identities already exist: Rotohiko, Ruakākā, Glenbrook-Ohurua1 and2, and Huntly
stages1 and2. This is a complete bounded regulator table, not a complete national
inventory. Five missing owner fields and six reported-duration fields are filled;
source-native connection, ownership and commissioning observations are retained.
The Rotohiko WEL Network/NewPower slash label stays native rather than becoming two
invented legal entities. Commissioning months for three facilities do not become
exact commercial-operation dates. Rotohiko's December2023 overview month differs
from the existing23November2023 registry date; both remain in explicit quarantine.
The September Huntly commissioning observation cannot replace newer October operation.
All existing statuses, capacities, dates, names, IDs and phases are preserved.

Four selected Kehua pages supply **12 exact models**: three iStoragE1 inverters,
five iStoragE3 inverters, three BTS switching/transformer cabinets and KM-ECU-30.
The fresh public index resolves canonical HTML routes. Each printed model and native
panel is reviewed against both the canonical set and the incoming batch. No product
family is expanded into fictitious intermediate models. Generic “PCS Cabinet” lacks
an exact configuration identity and stays held; KC762A/KC761B connectivity peripherals
are excluded from this selected BMS/EMS scope.

Inverter rated AC output, voltage, PV MPPT range and channel current limits are
separately scoped. Optional B5-S1/B5-S2 energy ranges do not become fixed battery
energy or installed module counts. PV voltage is not battery DC voltage. BTS cabinet
load/storage-side ratings, grid apparent capacity, switching bound, protocols,
temperature, altitude derating, physical dimensions and mass stay distinct. Native
transformer kW text is not silently repaired to kVA. Controller supply voltage/current
are auxiliaries, not BESS discharge power; the controller's ports and unit limit are
captured. Unspecified efficiency boundaries are not RTE. No chemistry is guessed.

Elum's public Academy page links directly to a two-page **ePowerControl MC** datasheet;
no gated form or registration was submitted. All five printed configurations are
reviewed: MC-XS, MC-S, MC-M, MC-L and MC-XL. The PDF text and rendered specification
page were checked together to resolve the merged cells. Captured fields include
explicit device/BESS/genset/meter/grid-connection limits, serial/LAN/USB interfaces,
Modbus protocols, temperature/humidity, auxiliary AC supply and50W maximum consumption,
control-loop timing with conditions, storage and export options. MC-XL explicitly
includes a DL10000 datalogger. Controlled BESS capacity is not stored energy in the
controller. IP66 applies to an optional wall-mount kit, not every configuration.
Standards are manufacturer claims, not independently certified performance.

The Elum filename says2025, while PDF metadata says “WIP Mars2026” and printed pages
have no revision date. These five records are conservatively **preliminary**, with
that discrepancy retained, rather than asserting final/current commercial availability.
MC-XL's solar-limit row contains50MWh: the incompatible unit is quarantined without
repair to MWp. Physical observations remain native because dimension axes and controller/
casing/screen mass boundaries are incomplete. No optional configuration variants are
invented. Elum is the named product supplier; no cell manufacturer or project assignment
is inferred.

## Scalable-source attempt, access and ranking

Transpower's landing page still identifies8October2026 as the latest pipeline.
Its reproduction terms remain restrictive, so the previously staged41forward and
four completed BESS observations remain held and are not counted as new candidates.
The existing offline adapter is retained. The EA current pipeline landing page is
readable, but its Sigma dashboard did not provide a downloaded named export in this
pass. Its definition of committed means FID, not physical construction. This is the
highest-yield next project source, subject to export access and content-specific rights.

Meridian's Ruakākā and Bunnythorpe owner pages were examined as alternatives; the
website terms restrict redistribution, so their additional facts are not imported.
The proposed Meridian Bunnythorpe development must remain distinct from two existing
Harmony Bunnythorpe proposals. An independent reusable council decision is the next
route. Saft was discovery-only: reader502/terms timeout did not produce accepted facts.

OEM copyright is retained. The bounded selected factual specifications carry exact
URLs, retrieval times, SHA256 and page/model/row locators. No open bulk licence is
claimed. Elum's sales/service terms and privacy page, and Kehua's footer/privacy page,
were inspected. Source PDFs/HTML, rendering and extracted text remain outside Git.
Prior blocked Kehua PDFs were not retried before the24-hour backoff. No contact,
payment, control bypass, messaging or automation change occurred.

The IEA29May2026 commentary and CC BY4.0 attribution were reopened. The adjacent
market file retains the prior comparable **2025 annual utility-scale GW-additions**
chart ranking: China, United States, Australia among the named country columns.
Regional Europe/Middle East values are not country rankings. No comparable worldwide
operational stationary-energy GWh series was established; absent countries are unranked,
and the previous chart/narrative discrepancies remain visible. No GW-to-GWh inference.

## Implementation, preservation and checks

The new offline `nz_status` reader and `stage_bess_nz_status.py` check the exact release,
headers, units, six rows, duplicate names and lifecycle vocabulary. Seven synthetic
checks preserve raw owner/month semantics and reject changed dates, headers, units,
identities, statuses and invalid capacities. The existing Kehua panel reader now accepts
explicit per-model field sets and numeric less-than bounds while still rejecting markup;
five additional synthetic checks cover these boundaries. Both parsers stage observations
only. Existing upsert APIs perform accepted additions/null-field enrichment; reviewed
nested additions preserve old observations. No schema or shared-core changes.

Both catalogues validate. Preservation confirms **2,052 prior projects and all870 prior
equipment records unchanged**, with all previous facts, nested conflict/extension keys,
source lists, field provenance and creation timestamps retained on the six enrichments.
Two independent final typed Zstandard builds per catalogue are byte-identical; their
completeness/coverage manifests are adjacent, and snapshots remain outside Git.

**2,291 full Python tests passed, five optional-dependency skips;321 focused BESS tests
and15 viewer tests passed.** Ruff lint/format, explicit isolated-environment type checks,
repository hygiene, citation consistency, both offline catalogue examples and diff checks
passed. One overlong regex line was split and lint/focused checks rerun. Strict Sphinx
with gallery execution disabled passed;548 HTML pages have valid local links/assets.
Three wheels and three sdists built and passed all six strict Twine checks. Fresh remote
CI, full online gallery execution and independent OEM certification are not claimed.
Six new bibliographic entries are queued because Wind/HVAC still touch shared references;
complete source and field evidence is already in the catalogues.

## Effort, yield and continuation

Validation completed at **12:01:36 Atlantic/Canary**, **16.00 minutes** after starting;
publication is a separate expected-head update after final concurrency checks. The
selected six-row regulator table, four accepted Kehua pages and five-column Elum sheet
are exhausted. The17-model depth objective is met. Project yield is below50 because
all six licensed table identities already exist and the larger Transpower inventory
has unresolved reuse constraints; duplicate or thin project rows would add no value.
The pass finishes before45minutes because the defensible selected batches are complete,
not to save extraction effort or wait out a duration. Next: an explicitly downloadable
EA named pipeline export, independent Rotohiko commissioning clarification, then the
public Elum ES/ES+ training-page datasheet and final MC revision. Keep PR133 OPEN.
