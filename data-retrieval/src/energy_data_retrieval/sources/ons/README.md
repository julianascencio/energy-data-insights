# Brazil: ONS generation and photovoltaic constrained-off detail

`ONSClient` discovers exact yearly/monthly Parquet resources in ONS's public
CKAN catalogue and downloads only the requested periods. No key is required.
Every HTTP request has a URL, retrieval time, byte count and SHA-256 in the
returned `GenerationResult.requests`. HTTPS hosts are restricted to `ONS_HOSTS`.

```python
from datetime import date
from energy_data_retrieval.sources.ons import ONS_HOSTS, ONSClient
from energy_data_retrieval.transport import HTTPClient

with HTTPClient(ONS_HOSTS) as http:
    client = ONSClient(http)
    hourly = client.generation(date(2024, 6, 1), date(2024, 6, 7), plant_ids=["CJU_SPPB"])
    solar = client.solar_curtailment(date(2024, 6, 1), date(2024, 6, 7), plant_ids=["BAFB11"])
```

The hourly product includes plants **and plant groups**. It is not a complete
inventory of individual units. ONS's small-plant Type III groups and MMGD contain
estimated/forecast data; these are excluded by default. `include_estimates=True`
retains them with `quality="estimated_or_forecast"`. Unknown operation categories
fail so that new categories cannot silently become measured generation.

Native `val_geracao` and `val_geracaoverificada` are **MWmed**, meaning average
power over the reporting interval. Normalized `value` is MW, not MWh; the native
columns and `source_unit="MWmed"` remain available. Hourly generation is available
from 2000, using annual exports through 2021 and monthly exports thereafter. PV
detail is a distinct half-hour product starting in April 2024. The connector
retains verified MW, irradiance and its validity flags, estimated MW, final
reference MW and the restriction flag. An estimated/actual difference is not
automatically labelled curtailment energy.

`din_instante` is a naive source reference label. By default the caller-visible
clock interpretation is `America/Sao_Paulo`, converted to UTC without shifting
the label or asserting an interval boundary. Historical ambiguous/nonexistent
DST labels raise an error. Use `source_timezone="Etc/GMT+3"` only when your export
is documented to use a fixed UTC−03 clock. The raw label remains in the frame.
Missing values remain missing; identical rows are deduplicated and conflicting
plant/time observations fail.

Defaults are 25 requests including catalogue discovery, one million rows per
native export and per returned selection, and the shared HTTP 64 MiB response
limit. Parquet is selected to avoid large CSV downloads; metadata row counts are
checked before decompression. Larger historical exports require explicit bound
adjustments. Missing periods/plant IDs and ambiguous catalogue resources fail.
`parse_generation_csv` supports bounded native semicolon CSV imports offline.

Official sources (attribution: Operador Nacional do Sistema Elétrico, ONS):

- [Hourly generation catalogue](https://dados.ons.org.br/dataset/geracao-usina-2)
- [Hourly data dictionary](https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/geracao_usina_2_ho/DicionarioDados_GeracaoPorUsina.json)
- [PV constrained-off detail catalogue](https://dados.ons.org.br/dataset/restricao_coff_fotovoltaica_detail)
- [PV detail dictionary](https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/restricao_coff_fotovoltaica_detail_tm/DicionarioDados_RestricaoContrainedoff_UsiFotovoltaica_Detail.json)

The catalogue specifies Creative Commons Attribution. The gallery contains small
real source selections, original CSV bytes and capture/hash manifests; it runs
without a network connection.
