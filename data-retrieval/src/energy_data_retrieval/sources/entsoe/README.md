# ENTSO-E actual generation

The connector reads the official Transparency Platform REST endpoint
`https://web-api.tp.entsoe.eu/api` and returns **reported actual generation**:

| Method | Product | Coverage | Native quantity |
| --- | --- | --- | --- |
| `generation_by_type(area, start, end, psr_type=None)` | A75 / A16 | Generation by production type in the chosen EIC area | Interval-average net power, MW |
| `generation_by_unit(area, start, end, psr_type=None, unit_id=None)` | A73 / A16 | Published individual generation units | Interval-average net power, MW |

An account with enabled API access and a personal token is required. Store the
token in `ENTSOE_API_TOKEN`; never put it in source files or notebooks. The shared
HTTP transport redacts credential-bearing logs, omits secrets from provenance and
does not cache authenticated responses in its public cache.

```python
from datetime import UTC, datetime
from energy_data_retrieval.sources.entsoe import ENTSOE_HOSTS, ENTSOEClient
from energy_data_retrieval.transport import HTTPClient

with HTTPClient(ENTSOE_HOSTS) as http:
    result = ENTSOEClient.from_environment(http).generation_by_type(
        "10YES-REE------0",  # Spain; choose an EIC appropriate to the required area.
        datetime(2025, 9, 1, tzinfo=UTC),
        datetime(2025, 9, 8, tzinfo=UTC),
        psr_type="B16",  # Solar.
    )
generation = result.data.query("flow == 'generation'")
```

## Interpretation and bounds

- Boundaries must be aware datetimes aligned to whole minutes; the end is
  exclusive. UTC interval starts and ends are returned, with `duration_hours`.
  Only whole native intervals within the requested range are retained. Select
  boundaries aligned to the provider's market-time-unit resolution for full
  coverage; no fractional interval is relabelled as a complete measurement.
- A75 is queried in conservative 31-day chunks and A73 in one-day chunks.
  Both the number of requests and expanded row count are bounded. Timeouts,
  response sizes, rate limiting and retries use `HTTPConfig`.
- A01 missing positions remain missing. A03 variable blocks are expanded only
  inside the originating Period. A point without a quantity starts an explicitly
  missing block; no previous value leaks into it or into a later Period.
- `inBiddingZone_Domain.mRID` means generation; `outBiddingZone_Domain.mRID`
  means consumption. `flow` preserves this distinction even for pumped storage.
  Published signs are retained and no automatic netting is performed.
- Source `MAW` is normalized to `MW`; it is **power**, not MWh. Multiplying a
  complete interval by its duration gives energy for that interval. Missing power
  is never converted to zero. Do not sum MW across time as if it were energy.
- Provider estimates may be included in aggregated actual-generation series.
  A73 primarily covers generation units at or above the publication threshold;
  do not interpret its plant list as every installation in a country.
- Equal duplicate observations are removed; conflicting duplicates, overlapping
  intervals, unexpected units/products, invalid XML and cancelled series fail
  explicitly. A documented no-matching-data acknowledgement returns an empty
  typed frame. Other error acknowledgements raise `RetrievalError` without
  echoing request URLs or provider text containing tokens.
- EIC area selection is explicit. Country, control-area and bidding-zone codes
  are not interchangeable. No country-name guessing or implicit cross-area
  aggregation is applied.
- XML text responses are supported. ZIP/multipart exports are not supported and
  fail explicitly. No live authenticated request was validated for this change;
  the parser and request contract are tested with labelled synthetic fixtures.

The gallery's `plot_generation_entsoe.py` builds an offline request-plan chart by
default. It is clearly labelled as a plan and includes an opt-in authenticated
workflow to fetch and plot real generation; no sample values are claimed as
measurements.

## Official references

- [REST endpoint](https://transparencyplatform.zendesk.com/hc/en-us/articles/15696677194644-Request-Endpoint)
- [API parameters and current Postman documentation](https://transparencyplatform.zendesk.com/hc/en-us/articles/15696716612372-Request-Parameters)
- [API access and security token](https://transparencyplatform.zendesk.com/hc/en-us/articles/12845911031188-How-to-get-security-token)
- [EIC area list](https://transparencyplatform.zendesk.com/hc/en-us/articles/15885757676308-Area-List-with-Energy-Identification-Code-EIC)
- [Query response, UTC and acknowledgements](https://transparencyplatform.zendesk.com/hc/en-us/articles/15727773247124-Query-Response)
- [A01 and A03 curve semantics](https://transparencyplatform.zendesk.com/hc/en-us/articles/30262342482961-CurveType-A01-vs-CurveType-A03)
- [Official generation XML examples](https://gitlab.entsoe.eu/transparency/xml-examples/-/tree/main/Generation)
- [Detailed Data Descriptions, actual generation](https://www.entsoe.eu/fileadmin/user_upload/_library/resources/Transparency/02_MoP%20Ref02%20-%20DDD_V2R5.pdf)

Provider schemas, coverage, publication revisions and reuse terms remain governed
by ENTSO-E and the reporting organisations. Retrieve a fresh copy for operational
decisions and validate data completeness for the selected area and period.
