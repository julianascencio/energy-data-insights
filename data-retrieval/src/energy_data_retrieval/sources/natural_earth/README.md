# Natural Earth country shapefiles

`NaturalEarthClient.download_countries(directory, scale="10m")` acquires the
public-domain Admin 0 countries archive and retains its `.shp`, `.shx`, `.dbf`,
`.prj` and optional `.cpg`/version members. A manifest records source URL,
retrieval time, map scale, release version and hashes. Pass `expected_sha256`
to require the exact previously acquired archive.

The HTTP transport bounds compressed bytes; expanded selected files are limited
to 50 MB. Only exact flat member names are read, with duplicate/missing members
rejected. Cached downloads are verified before reuse. No credentials are needed.

`10m`, `50m`, `110m` mean 1:10/50/110 million map scales, not metre accuracy.
Natural Earth uses de facto boundaries and its own country/territory units.
The methods package handles selection, CRS transformation, masking and exports.
See [Natural Earth](https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-0-countries/)
and its [public-domain terms](https://www.naturalearthdata.com/about/terms-of-use/).
