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

## Physical ground snow depth

`OpenMeteoSnowClient` in `open_meteo.snow` separately requests **ERA5-Land**
hourly `snow_depth`, nearest cells, UTC and no elevation downscaling. It checks
complete hourly timestamps and physical metre units, then converts to
`snow_depth_cm`. Samples are instantaneous hourly depths, without the endpoint
averaging used for other weather variables. Null values stay missing.

This field is physical ground snow depth, distinct from native ERA5's
water-equivalent `sd`. Open-Meteo warns that snow depth can be overestimated.
Cite Open-Meteo and Muñoz-Sabater et al. (2021) for ERA5-Land; the request
manifest records the selected model and source-cell coordinates.
