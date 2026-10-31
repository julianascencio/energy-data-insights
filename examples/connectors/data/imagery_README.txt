Real native satellite crops, captured 2026-10-31.

These data are not covered by the repository's code licence.

imagery_tenerife_*: Contains modified Copernicus Sentinel data (2026),
processed by ESA; distributed by Element 84 Earth Search. Native crops from
Sentinel-2 Collection 1 L2A. Retain attribution and the source terms:
https://dataspace.copernicus.eu/terms-and-conditions

imagery_altadena_*: © Maxar/Vantor Open Data Program. CC BY-NC 4.0 at the
program/event level: https://creativecommons.org/licenses/by-nc/4.0/
Cropped native WorldView-3 pixels; no resampling or sharpening applied here.
The original acquisition collection's generic proprietary declaration is also
preserved in the STAC sidecars; this package grants no commercial image rights.
https://xpress-docs.maxar.com/OpenData/OpenData_intro.htm

Retain each TIFF together with its .tif.meta.json. The sidecars contain full
STAC, source URLs, acquisition/retrieval dates, native grids, calibration,
nodata, processing declarations and SHA-256. imagery_searches.json records
search scope and matching candidates. imagery_provenance.json gives sample
attribution and measured native spacing. A finer RGB display grid does not
imply finer sensor detail. Valid pixels are not necessarily cloud/shadow free.

Reproduce with scripts/prepare_satellite_imagery_samples.py using Python 3.13
and the optional imagery workspace group (pinned Orbital PV alongside this package). The example runs offline through the actual
Orbital PV verified loader. Its panchromatic percentile stretch is display-only.
