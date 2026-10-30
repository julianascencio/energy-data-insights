# CHELSACanaryClim

`CanaryClimClient.download_month` retrieves public v1.0 temperature (`tas`) or
precipitation (`pr`) COGs for months 1–12 and baseline 1979–2013. Use an
`HTTPClient` restricted to `CANARY_CLIM_HOSTS`, with a 160 MB response cap.
Shared transport provides atomic downloads, integrity checks and cache manifests.
An expected SHA-256 can pin each file to reviewed bytes.

The 2025 COG release is CC0. Readers must mask encoded nodata before applying
embedded scale/offset; temperature is K and precipitation kg/m²/month. The
current roughly 5 m pixel spacing does not establish 5 m climate accuracy;
the published study compared 100 m fields. The analysis package owns regional
KGPV classification; retrieval does not import scientific methods.

Sources: https://doi.org/10.16904/envidat.692 and https://doi.org/10.1111/ddi.13757.
