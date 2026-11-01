# ODRE national electricity production and storage register

Source producers: **RTE, Enedis, EDF SEI and ELD**, via Open Data Réseaux Énergies.
Original data: [national installation register](https://odre.opendatasoft.com/explore/dataset/registre-national-installation-production-stockage-electricite-agrege/).
Snapshot: **31 August 2026**. Publisher's last-modified metadata: **13 October 2026**;
API processing: **20 October 2026**. Retrieved **1 November 2026**.

Reuse is under [Licence Ouverte / Open Licence v2.0, Etalab, April 2017](https://www.etalab.gouv.fr/wp-content/uploads/2017/04/ETALAB-Licence-Ouverte-v2.0.pdf).
The licence permits commercial and noncommercial reuse with attribution of the
producer and update date. This catalogue is an independent transformed selection;
it is not endorsed or certified by those producers. The data are supplied as-is.

Transformations: explicit PHOTV selection; reviewed individual installation IDs;
maximum installed kW divided by 1,000 into AC/DC-unspecified MW; native dates parsed
to ISO dates. Aggregates, anonymized entries and unresolved project/phase identities
are excluded from accepted records. Network administrative geography is not a
surveyed plant position. Registry status remains dated to the snapshot. No private
contact details or natural-person operator names are copied. Source URLs, exact
export queries, downloaded checksums and evidence locators are in `sources.json`
and the dated research ledger. Original downloaded files are not distributed.
