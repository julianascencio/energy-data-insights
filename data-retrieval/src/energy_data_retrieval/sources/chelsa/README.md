# CHELSA v2.1 native climatology windows

`CHELSAClient.download_window(directory, variable, month, bounds)` explicitly
acquires `tas` or `pr`, January–December, baseline 1981–2010. Bounds are
west/south/east/north in EPSG:4326. The public provider path is fixed; callers
cannot inject arbitrary URLs. Use a verified `httpx.Client` with finite timeouts.

The source must be a one-band uint16, 30-arcsecond raster with the expected CF
variable, units and version tags. Integral crop windows preserve native values,
scale, offset and centres. Nodata remains encoded: downstream readers mask
65535 before converting K to Celsius or precipitation kg/m²/month to mm/month.

The Python range reader supports verified TLS, exact 206/Content-Range/ETag
checks, If-Match, a bounded LRU cache, transfer limits and finite retries.
It rejects whole-body HTTP fallbacks. Up to ten million native cells can be
requested. Pass `expected_etag` and `expected_pixels_sha256` to reproduce reviewed
source versions and raw crop pixels; ETags are not cryptographic checksums.
Cached files require their companion manifest and SHA-256 integrity match.
Acquisition is explicit; imports and the documentation build do not download.

Source: CHELSA v2.1 climatologies, CC0 1.0, DOI
https://doi.org/10.16904/envidat.228; scientific description
https://doi.org/10.1038/sdata.2017.122. Climate support is about 1 km, not the finer
grid of an analysis that samples these cells. The analysis package owns KGPV
classification, boundary selection and plotting.
