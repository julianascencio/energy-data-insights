# New Zealand EMI generation

Read the Electricity Authority's monthly `Generation_MD` CSV exports. These are
**metered grid injections mapped to generating plants**, with some shared
injection points apportioned by the publisher. They are not direct telemetry
from every generating unit. Plant, connection, network, fuel and technology codes
remain available in the normalized frame.

```python
from datetime import date
from energy_data_retrieval.sources.emi import EMI_HOSTS, EMIClient
from energy_data_retrieval.transport import HTTPClient

with HTTPClient(EMI_HOSTS) as http:
    result = EMIClient(http).generation(
        date(2024, 9, 28), date(2024, 9, 30), plants=["Kohira", "te_apiti"]
    )
```

Dates are inclusive in `Pacific/Auckland`. Each TP column is **half-hour energy
in kWh**. `timestamp` is its UTC start and `interval_end` its UTC end. Spring and
autumn clock changes have 46 and 50 periods respectively; the parser rejects
values in nonexistent periods. Nulls remain missing and negative values remain
negative. Multiply kWh by 0.001 for MWh; divide kWh by 500 for average MW.

`generation_urls` produces a credential-free monthly request plan.
`parse_generation_csv` accepts the same native UTF-8 format for local files.
Requests and output rows are bounded, and `GenerationResult.requests` records
the URL, retrieval time and response checksum. An absent requested plant raises
an error rather than returning a misleading zero profile.

The archive begins in August 1997 and can be revised. The gallery preserves a
small source subset and its acquisition/provenance manifest. Electricity
Authority material is generally **CC-BY 4.0**, subject to its stated exceptions.

- [Official generation dataset and field definitions](https://www.ea.govt.nz/data-and-insights/datasets/wholesale/generation/generation-output/)
- [EMI licensing and attribution](https://www.emi.ea.govt.nz/LegalInformation)
