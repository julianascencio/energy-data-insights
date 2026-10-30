# NASA POWER aerosol adapter

`NASAPowerClient.daily_aod(site, start, end)` retrieves unadjusted total AOD at
550 nm (`AOD_55`, dimensionless) from the daily point API. It explicitly requests
UTC, checks returned units and dates, and maps the provider's fill value to NaN.
Requests are bounded to 366 days from 2001 onward. The returned `AODChunk`
retains source labels and the shared HTTP client's request/checksum provenance.

The [NASA aerosol documentation](https://power.larc.nasa.gov/docs/methodology/data/sources_clds_aerosols/)
describes CERES SYN1deg/MATCH inputs. AOD is not ground-level particulate
concentration or measured deposition on a PV module. Use annual means for the
thesis soiling correlation; do not infer individual dust events from that fit.
See the [daily API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)
for access limits and credit NASA POWER/CERES for data use.
