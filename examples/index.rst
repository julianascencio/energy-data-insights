Example gallery
===============

Choose a main section, then a topic. Each topic opens a focused collection of
examples with plots, explanations and downloadable code.

.. grid:: 1 1 2 2
   :gutter: 3
   :class-container: gallery-navigation

   .. grid-item-card:: Methods
      :link: methods/index
      :link-type: doc

      Learn the reusable calculations before applying them to a study.

   .. grid-item-card:: Data & connectors
      :link: connectors/index
      :link-type: doc

      Find a data source, understand its coverage and reproduce an offline retrieval example.

   .. grid-item-card:: Analysis & case studies
      :link: analysis/index
      :link-type: doc

      Combine inputs and methods into maps, forecasts, inspections and uncertainty studies.

   .. grid-item-card:: Databases
      :link: database/index
      :link-type: doc

      Explore attributed project and equipment records, coverage and completeness.

Start with the :doc:`source coverage overview <connectors/topic_source_coverage>`
if you are choosing a data provider, or
:doc:`generation forecasting <analysis/topic_forecasting>` to compare prediction models.

Running an example
------------------

Examples run during the documentation build without API credentials or live
provider downloads. Each example states whether it uses captured observations,
synthetic inputs or an offline request plan. Follow its setup instructions and
use its complete data bundle when provided. See the :doc:`quickstart </quickstart>`
for package installation.

.. toctree::
   :hidden:
   :maxdepth: 2

   methods/index
   connectors/index
   analysis/index
   database/index

