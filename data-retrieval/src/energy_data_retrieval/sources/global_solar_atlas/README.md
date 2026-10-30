# Global Solar Atlas

`GlobalSolarAtlasClient.download_spain_ghi` acquires the pinned **2019 Spain
archive**, then extracts only annual `GHI.tif` and its XML/PDF metadata. It is
not a general country downloader or the current live solar-map service.
Configure `HTTPClient` with `GSA_HOSTS`, `SolarAtlasTransport` and a 110 MB cap.
The transport permits the canonical API URL and its single, exact provider S3
object redirect. Signed query strings are not persisted in request manifests.

The archive is SHA-256/size pinned; extraction checks duplicate/missing members
and expanded size. The GHI raster is annual kWh/m², baseline **1994–2018**, at
9 arcseconds (nominal 250 m). No conversion from daily to annual is required.

Data: Global Solar Atlas 2.0, developed and operated by Solargis s.r.o. on behalf
of the World Bank Group, utilizing Solargis data with ESMAP funding.
Source: https://globalsolaratlas.info. CC BY 4.0 with additional provider terms;
preserve the extracted full XML license and attribution with derived outputs.
