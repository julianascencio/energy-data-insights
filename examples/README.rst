Example gallery
===============

Browse examples by task: learn a method, work with a data provider, or follow an
applied analysis. The same sections organize the repository's ``examples/`` folder.

.. grid:: 1 1 3 3
   :gutter: 3

   .. grid-item-card:: Methods
      :link: methods/index
      :link-type: doc

      Reusable calculations: daily profiles, climate-change yield assessment
      and KGPV classification.

   .. grid-item-card:: Connectors
      :link: connectors/index
      :link-type: doc

      Provider workflows: ERA5, AEMO, U.S. EIA, Spain REE and Europe ENTSO-E.

   .. grid-item-card:: Analysis
      :link: analysis/index
      :link-type: doc

      Applied studies: worldwide KGPV climate zones and soiling/snow risk maps.

Downloadable Python examples run during every documentation build without API
credentials or live downloads. The AEMO, EIA and REE generation examples use
attributed real public observations with source URLs and checksums. The ENTSO-E
example shows an offline request plan and an explicit opt-in workflow for
credentialed downloads. Other examples use clearly identified synthetic inputs,
NOAA climatology, NASA POWER or ERA5-Land data. Each example explains its units,
scope and limitations; a source observation does not establish validated plant
performance or complete national coverage.

Download the :download:`generation examples and their data together
<connectors/generation_examples.zip>` to run all four examples from an extracted folder.
Install the repository's packages and docs dependencies first. See the
:doc:`generation connector guide </_generated/guides/generation-connectors>`
for command-line usage and access requirements.
