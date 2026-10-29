Energy Data Insights
====================

**From source data to reproducible energy research.**

Retrieve weather, climate and generation data. Apply transparent PV methods.
Turn the results into repeatable studies and reports.

.. grid:: 1 1 3 3
   :gutter: 3

   .. grid-item-card:: Retrieve
      :link: _generated/packages/retrieval
      :link-type: doc

      Provider APIs, nearby stations, climate grids and download provenance.

   .. grid-item-card:: Model
      :link: _generated/packages/methods
      :link-type: doc

      PV performance, CCYA, KGPV classification and climate-driven degradation.

   .. grid-item-card:: Analyse
      :link: _generated/packages/analysis
      :link-type: doc

      Chile fleet studies, applied climate-yield cases and degradation maps.

Start with the :doc:`quickstart`, browse the :doc:`auto_examples/index`, or
look up a function in the :doc:`api`. All gallery calculations run locally on
explicitly synthetic inputs or offline request plans.

.. toctree::
   :maxdepth: 2
   :hidden:

   getting-started
   user-guide
   auto_examples/index
   api
   development
   _generated/guides/references

Scientific foundations
----------------------

The primary scientific reference is Julián Andrés Ascencio Vásquez (2021),
*Modelling and worldwide assessment of performance and aging of photovoltaic
modules and systems*, University of Ljubljana.
`Read the thesis record <https://www.dlib.si/details/URN:NBN:SI:DOC-TMG3QFI9>`_.

The :doc:`reference catalogue <_generated/guides/references>` connects the thesis,
individual papers, software and datasets to their implementations. Cite the
references actually used, along with the repository revision. Method adaptations,
calibration requirements and limits are documented explicitly.

.. note::

   Synthetic examples illustrate software behavior. They are not measured plant
   results, validated climate forecasts, or an exact reproduction of the thesis's
   Bolzano case study.

Related project: `OrbitalPV <https://julianascencio.github.io/orbital-pv/>`_.
This documentation uses Sphinx and the PyData theme, following the organization
of `pvlib python <https://pvlib-python.readthedocs.io/en/stable/>`_.
