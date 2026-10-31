Example gallery
===============

Browse examples by task: learn a method, work with a data provider, or follow an
applied analysis, or explore the database. The same sections organize the repository's ``examples/`` folder.

The :doc:`worldwide connector coverage map <connectors/plot_generation_coverage>`
introduces all implemented generation, station, weather and climate sources.
Run its downloadable Python code offline to reproduce the country/system
inventory and the station-catalogue and grid-scope views.

.. grid:: 1 2 2 4
   :gutter: 3

   .. grid-item-card:: Methods
      :link: methods/index
      :link-type: doc

      Reusable calculations: daily profiles, climate-change yield assessment
      and KGPV classification.

   .. grid-item-card:: Connectors
      :link: connectors/index
      :link-type: doc

      Worldwide connector coverage, weather and generation: plant records,
      system totals, station catalogues and measured PV research arrays.

   .. grid-item-card:: Analysis
      :link: analysis/index
      :link-type: doc

      Applied studies: worldwide KGPV climate zones, soiling/snow risks and
      detailed maps for selected countries.

   .. grid-item-card:: Database
      :link: database/index
      :link-type: doc

      Interactive Parquet-backed explorer, equipment and project queries,
      database statistics, field completeness and country coverage.

Downloadable Python examples run during every documentation build without API
credentials or live downloads. Generation captures use attributed real public
observations with source URLs and checksums. ENTSO-E and KPX show offline request
plans; NIST and DKASC demonstrate native-export imports until a real file is
supplied. Other examples use clearly identified synthetic inputs,
NOAA climatology, NASA POWER or ERA5-Land data. Each example explains its units,
scope and limitations; a source observation does not establish validated plant
performance or complete national coverage.

Download the :download:`generation examples and their data together
<connectors/generation_examples.zip>` to run the examples from an extracted folder.
Install the repository's packages and docs dependencies first. See the
:doc:`worldwide generation guide </_generated/guides/worldwide-generation>`
for command-line usage and access requirements.
