Energy Data Insights
====================

.. raw:: html

   <div style="text-align:center; margin: 1.5rem 0 2rem 0;">
     <a href="https://asvaconsulting.com">
       <img
         src="https://asvaconsulting.com/wp-content/uploads/2022/05/ASVA-1-1-scaled.jpg"
         alt="ASVA Consulting"
         style="max-width:280px; width:100%; height:auto;"
       >
     </a>
     <p style="margin-top:0.75rem;">
       <strong>Created by ASVA Consulting</strong><br>
       <a href="https://asvaconsulting.com">asvaconsulting.com</a><br>
       <a href="mailto:contacto@asvaconsulting.com">contacto@asvaconsulting.com</a>
     </p>
   </div>

**From source data to reproducible energy research.**

Created by **ASVA Consulting**, Energy Data Insights provides Python tools to
retrieve weather, climate and generation data, apply transparent PV methods,
and turn the results into repeatable studies and reports.

The project was inspired by a doctoral thesis, with the first studies and
methods based on that research. It has since grown to include new methods,
connectors, databases and applications beyond the thesis, each with its own
sources and documented implementation choices.

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
clearly identified synthetic inputs, attributed data fixtures or offline request plans.

.. toctree::
   :maxdepth: 2
   :hidden:

   getting-started
   user-guide
   auto_examples/index
   api
   development
   _generated/guides/references
   _generated/guides/court-barton-pv-claim-audit

Scientific foundations
----------------------

Most of the code, documentation and examples in this repository are **AI-generated
under developer direction**. The scientific methods are based on **real, specifically
identified literature selected by the repository's developers**, who define the
research scope, choose the sources and guide the implementation. Responsibility
for review, testing and scientific validation remains with the developers and
contributors.

As the project evolves, errors or omissions may remain in the code or documentation.
Please check assumptions and results for your intended use; corrections and issue
reports are welcome.

The project's original inspiration is Julián Andrés Ascencio Vásquez (2021),
*Modelling and worldwide assessment of performance and aging of photovoltaic
modules and systems*, University of Ljubljana.
`Read the thesis record <https://www.dlib.si/details/URN:NBN:SI:DOC-TMG3QFI9>`_.

The :doc:`reference catalogue <_generated/guides/references>` connects the thesis,
individual papers, software and datasets to their implementations. Cite the
references actually used, along with the repository revision, and cite the
thesis for work derived from it. Later additions have their own scientific
foundations. Method adaptations, calibration requirements and limits are
documented explicitly. Methods use descriptive names such as **acceptance band**;
author names are retained in citations and attribution.

.. note::

   Synthetic examples illustrate software behavior. They are not measured plant
   results, validated climate forecasts, or an exact reproduction of the thesis's
   Bolzano case study.

Related project: `OrbitalPV <https://julianascencio.github.io/orbital-pv/>`_.
This documentation uses Sphinx and the PyData theme, following the organization
of `pvlib python <https://pvlib-python.readthedocs.io/en/stable/>`_.

License
-------

Copyright (c) 2026 ASVA Consulting TFE SL. Original software is source-available
for noncommercial use only. Internal business use, paid services, and commercial
products require separate written permission. Third-party materials keep their
own terms. Read the `full license <https://github.com/julianascencio/energy-data-insights/blob/main/LICENSE>`_
and `licensing scope <https://github.com/julianascencio/energy-data-insights/blob/main/LICENSING.md>`_.
