El Mirlo / Rengo 3D continuation — pinned terrain and declared assumptions

The adjacent rengo_modules directory supplies the original imagery, detection
configuration and same-image visual audit. This scene covers its southern
inspection block, not the complete solar farm. Candidate identities and table
groups are retained; the 2,055 candidates are not a verified asset inventory.

el_mirlo_copernicus.tif is an unresampled native 48 x 47 pixel crop of the
Copernicus GLO-30 tile S35/W071. Its roughly 30 m sampling cannot establish
module heights, foundations, ground clearance or small obstacles. The source
is a digital surface model including vegetation/buildings, not bare-earth DTM.
TanDEM-X acquisition is mainly 2011–2015 (gap-fill sources can be older);
the capture timestamp is a download date, not a survey date.
Horizontal CRS: EPSG:4326. Heights: metres, EGM2008 orthometric reference.
No vertical datum conversion is applied.

terrain_provenance.json preserves the original tile URL, native metadata,
download receipt and SHA256 hashes. scene_config.json pins both these inputs
and the counting study, plus the assumed 20 degree tilt, local-north facing
azimuth and 0.8 m minimum sampled terrain clearance. These are illustrative
scenario values, not recovered measurements of El Mirlo. One plane per table
preserves alignment. Horizontal footprints stay fixed as the tilt changes.

Source and terms:
https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM
https://registry.opendata.aws/copernicus-dem/

produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence
and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA;
all rights reserved

Reproduce offline: examples/analysis/plot_rengo_site_3d.py
Reusable methods and other-site recipe: docs/pv-site-3d.md
Explicit live recapture: scripts/prepare_rengo_3d.py (not needed for reproduction).
