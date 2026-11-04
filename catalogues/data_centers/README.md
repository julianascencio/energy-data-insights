# Global Data Center Database

Two connected catalogues follow the existing PV/BESS architecture: reviewable
canonical JSONL under `records/projects` and `records/equipment`, a source registry,
field-level evidence, stable UUIDs and deterministic typed Parquet snapshots.
No network request occurs during validation, export or documentation builds.

The current continuation branch contains **183 project records in 36 countries**:
**66 facilities, three phases and 114 explicitly labelled campus aggregates**,
from 13 operators. It has **1,862 exact equipment records from 46 OEMs**.
Merged `main` at `9f36b0f3` contains **183 projects and 1,831 equipment records**.
These are catalogue counts, not a worldwide census or a count of operating buildings.
The research report and coverage manifest describe missing fields and scope.

```bash
uv run python -m energy_data_retrieval.data_center_catalogue validate
uv run python -m energy_data_retrieval.data_center_catalogue build --output artifacts/data-centers-v1
uv run python scripts/stage_data_center_portfolio.py captured.html --source-url https://www.nextdc.com/data-centres
uv run python scripts/stage_data_center_adc.py captured.html --source-url https://www.africadatacentres.com/nairobi/
uv run python scripts/stage_data_center_schneider.py extracted.txt --source-url https://www.se.com/uk/en/download/document/990-91317_EN/ --expected-count 23
uv run python scripts/stage_data_center_stulz.py extracted-layout.txt --source-url https://www.stulz.es/fileadmin/user_upload/Documents/STULZ__TechnicalData_CyberAir_3PRO_DX_ASR-ALR.pdf --expected-count 30
uv run python scripts/stage_data_center_stulz.py extracted-layout.txt --source-url https://www.stulz.es/fileadmin/user_upload/Documents/STULZ__TechnicalData_CyberAir_3PRO_DX_ASR-ALR.pdf --compressor modulating-ec --expected-count 20
uv run python scripts/stage_data_center_stulz.py extracted-layout.txt --source-url https://www.stulz.es/fileadmin/user_upload/Documents/STULZ__TechnicalData_CyberAir_3PRO_DX_ASR-ALR.pdf --compressor fixed-speed-r134a --expected-count 23
uv run python scripts/stage_data_center_meta.py captured.html --source-url https://datacenters.atmeta.com/all-locations/ --expected-count 33
uv run python scripts/stage_data_center_vertiv_powerups.py extracted.txt --source-url https://www.vertiv.com/49882a/globalassets/shared/vertiv-power-ups-industrial_data-sheet_en.pdf --expected-count 19
uv run python scripts/stage_data_center_carrier_19dv.py extracted-layout.txt --source-url https://brandportal.carrier.com/m/7aed1ae899ea9c0e/original/NA2316A_brochure_aquaedge_19DV_EN_carrier_bat04_bd.pdf --expected-count 28
uv run python scripts/stage_data_center_raxio.py captured.html --source-url https://www.raxiogroup.com/data-centres/angola/ --expected-code AO1
uv run python scripts/stage_data_center_cummins.py captured.html --source-url https://www.cummins.com/en-na/generators/products/qsk60 --expected-count 17
uv run python scripts/stage_data_center_inventory.py captured.html --source-url https://www.atnorth.com/nordic-data-centers/ --expected-count 13
uv run python scripts/build_data_center_atnorth_finland_permit_batch.py catalogues/data_centers/records/projects/2026-11-03-atnorth.jsonl catalogues/data_centers/records/projects/2026-11-03-atnorth.jsonl
uv run python scripts/build_data_center_atnorth_reconciliation_batch.py catalogues/data_centers/records/projects/2026-11-03-atnorth.jsonl catalogues/data_centers/records/projects/2026-11-03-atnorth.jsonl
uv run python scripts/stage_data_center_cdu.py extracted.csv --source-url https://www.motivaircorp.com/uploads/files/brochures/CDU%202026%20Motivair%20by%20SE.pdf --expected-count 8
uv run python scripts/stage_data_center_power_equipment.py extracted.csv --source-url https://www.eaton.com/dk/da-dk/catalog/medium-voltage-power-distribution-control-systems/dry-type-transformer.html --expected-count 16
uv run python scripts/stage_data_center_server_matrix.py extracted.csv --source-url https://www.delltechnologies.com/asset/en-us/products/servers/briefs-summaries/poweredge-server-gpu-matrix.pdf --expected-count 33
uv run python scripts/stage_data_center_lenovo_gpu.py captured.html --source-url https://lenovopress.lenovo.com/lp2265-thinksystem-gpu-comparison --expected-count 20
uv run python scripts/stage_data_center_supermicro.py captured.html staged.json --expected-count 13
uv run python scripts/stage_data_center_cooling.py extracted.csv --source-url https://info.support.huawei.com/Energy/info/en_US/dataCenter/docView/EDOC1100129236 --expected-count 6
uv run python scripts/build_data_center_envicool_batch.py staged-envicool.jsonl
uv run python scripts/build_data_center_toshiba_ups_batch.py staged-toshiba-ups.jsonl
uv run python scripts/build_data_center_mitsubishi_ups_batch.py staged-mitsubishi-ups.jsonl
uv run python scripts/build_data_center_fuji_ups_batch.py staged-fuji-ups.jsonl
uv run python scripts/build_data_center_daikin_chiller_batch.py staged-daikin-chillers.jsonl
uv run python scripts/build_data_center_kehua_ups_batch.py staged-kehua-ups.jsonl
uv run python scripts/build_data_center_kstar_transformer_ups_batch.py staged-kstar-ups.jsonl
uv run python scripts/build_data_center_borri_ups_batch.py staged-borri-ups.jsonl
uv run python scripts/build_data_center_baudouin_generator_batch.py staged-baudouin-generators.jsonl
uv run python scripts/build_data_center_makelsan_ups_batch.py staged-makelsan-ups.jsonl
uv run python scripts/build_data_center_siel_ups_batch.py staged-siel-ups.jsonl
uv run python scripts/build_data_center_tescom_ups_batch.py staged-tescom-ups.jsonl
uv run python scripts/build_data_center_energy_star_ups_batch.py captured-energy-star-ups.csv staged-energy-star-ups.jsonl
uv run python scripts/build_data_center_energy_star_ups_batch.py captured-energy-star-ups.csv staged-adi-ups.jsonl --partner-batch adi
uv run python scripts/build_data_center_energy_star_ups_batch.py captured-energy-star-ups.csv staged-ablerex-ups.jsonl --partner-batch ablerex
uv run python scripts/build_data_center_energy_star_ups_batch.py captured-energy-star-ups.csv staged-panduit-ups.jsonl --partner-batch panduit
uv run python scripts/build_data_center_energy_star_ups_batch.py captured-energy-star-ups.csv staged-appleton-ups.jsonl --partner-batch appleton
uv run python scripts/build_data_center_energy_star_ups_batch.py captured-energy-star-ups.csv staged-legrand-av-ups.jsonl --partner-batch legrand_av
uv run python scripts/build_data_center_energy_star_ups_batch.py captured-energy-star-ups.csv staged-delta-energy-star-ups.jsonl --partner-batch delta_energy_star
uv run python scripts/build_data_center_energy_star_ups_batch.py captured-energy-star-ups.csv staged-cyberpower-energy-star-ups.jsonl --partner-batch cyberpower_energy_star --shard-size 5
uv run python scripts/build_data_center_energy_star_ups_batch.py captured-energy-star-ups.csv staged-eaton-energy-star-ups.jsonl --partner-batch eaton_energy_star --shard-size 5
uv run python scripts/build_data_center_energy_star_ups_batch.py captured-energy-star-ups.csv staged-schneider-energy-star-ups.jsonl --partner-batch schneider_energy_star --shard-size 5
uv run python scripts/build_data_center_energy_star_ups_batch.py captured-energy-star-ups.csv staged-vertiv-energy-star-ups.jsonl --partner-batch vertiv_energy_star --shard-size 5
uv run python scripts/build_data_center_energy_star_ups_batch.py captured-energy-star-ups.csv staged-fuji-energy-star-ups.jsonl --partner-batch fuji_energy_star
uv run python scripts/build_data_center_energy_star_ups_batch.py captured-energy-star-ups.csv staged-ingram-v7-energy-star-ups.jsonl --partner-batch ingram_v7_energy_star
uv run python scripts/build_data_center_energy_star_ups_batch.py captured-energy-star-ups.csv staged-mitsubishi-energy-star-ups.jsonl --partner-batch mitsubishi_energy_star
uv run python scripts/build_data_center_energy_star_ups_batch.py captured-energy-star-ups.csv staged-n1c-energy-star-ups.jsonl --partner-batch n1c_energy_star
uv run python scripts/build_data_center_energy_star_ups_batch.py captured-energy-star-ups.csv staged-neuropower-energy-star-ups.jsonl --partner-batch neuropower_energy_star
uv run python scripts/build_data_center_energy_star_ups_batch.py captured-energy-star-ups.csv staged-power-logic-energy-star-ups.jsonl --partner-batch power_logic_energy_star
uv run python scripts/build_data_center_energy_star_ups_batch.py captured-energy-star-ups.csv staged-right-power-energy-star-ups.jsonl --partner-batch right_power_energy_star
uv run python scripts/build_data_center_energy_star_ups_batch.py captured-energy-star-ups.csv staged-upsonic-energy-star-ups.jsonl --partner-batch upsonic_energy_star
uv run python scripts/build_data_center_energy_star_server_batch.py captured-energy-star-servers.csv staged-cisco-energy-star-servers.jsonl --shard-size 5
uv run python scripts/build_data_center_energy_star_server_batch.py captured-energy-star-servers.csv staged-fujitsu-energy-star-servers.jsonl --partner-batch fujitsu --shard-size 5
uv run python scripts/build_data_center_energy_star_server_batch.py captured-energy-star-servers.csv staged-xfusion-energy-star-servers.jsonl --partner-batch xfusion --shard-size 5
```

IT MW, grid MW, facility MW, backup MW, battery MW/MWh, kW and kVA remain separate.
Each capacity has a boundary and rating basis. Campus and unresolved overlap
records are excluded from capacity sums, even when filters hide their children.
Planned, design-maximum and operating ratings are never combined. Unknown is null;
`+` ratings remain lower-bound observations. No IT capacity is inferred from area,
racks, investment or PUE. AI-ready claims do not establish GPU deployment.

Stable facility/campus/phase and organization IDs support future enrichments.
Exact equipment links require a disclosed deployment; none are asserted in this
batch. Existing stationary battery and BESS equipment records are referenced by
validated BESS IDs, not copied into a competing battery catalogue.

Read [the latest research report](research/2026-11-04-report.md),
[ranked continuation backlog](research/backlog.json),
[latest decision ledger](research/2026-11-04-decisions.jsonl),
[executed validation](research/2026-11-04T2215-validation.json), and
[usage and simulator guide](../../docs/data-center-catalogue.md).
The [project viewer](https://julianascencio.github.io/energy-data-insights/data-center-database-viewer.html?table=projects)
and [equipment viewer](https://julianascencio.github.io/energy-data-insights/data-center-database-viewer.html?table=equipment)
are generated by the docs build; links become public after merge and deployment.

Source access is not a blanket reuse licence. Original copyrighted pages/PDFs are
not redistributed. Registered byte hashes identify the reviewed captures; source
URLs, dates, revisions, locators and reuse notes travel with exports. Facts have
been normalized without reproducing marketing text, contact data, access details
or security procedures. Restricted NTT and PeeringDB bulk inventories are held out.
