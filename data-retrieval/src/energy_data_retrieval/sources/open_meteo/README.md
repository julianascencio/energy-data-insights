# Open-Meteo weather adapter

`OpenMeteoClient` explicitly chooses ERA5 or IFS, nearest native cells and no
elevation downscaling. It normalizes hourly source values to UTC interval starts;
temperature and wind are means of instantaneous endpoints, and GHI is the
preceding-hour mean at interval end. `WeatherChunk` retains request provenance
and selected source-cell coordinates.

For degradation studies, `OpenMeteoClient(..., include_degradation=True)` also
requests ambient relative humidity and calculated terrestrial (TOA) irradiance.
It produces `relative_humidity_percent` from endpoint means and `toa_wm2` from
the preceding-hour mean. Missing values stay missing and units are validated.
Finite negative source radiation remains in the retrieved record for audit;
the applied degradation analysis marks negative TOA unavailable before modelling.
The default client keeps its existing weather columns.

The [historical API documentation](https://open-meteo.com/en/docs/historical-weather-api)
defines source variables and access terms. The public endpoint is for
non-commercial use and has request limits. Data attribution includes Open-Meteo
(CC BY 4.0) and the underlying Copernicus ERA5 provider. Calculated TOA is an
Open-Meteo solar-geometry product, not a separately retrieved ERA5 radiation field.
