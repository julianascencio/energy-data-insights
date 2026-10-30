Connectors
==========

Retrieve and interpret weather and real generation data with
``energy_data_retrieval``. The examples span the Americas, Europe, Asia,
Oceania and Africa, from plant meters and operational SCADA to technology
totals and instrumented PV research arrays. Each page explains its scope,
units, clock convention and access method.

Start with the :doc:`worldwide connector coverage map </auto_examples/connectors/plot_generation_coverage>`.
Its two offline figures place the generation providers, station catalogues and
gridded products in geographic context, with a complete inventory of the
repository's source modules and downloadable Python code. Country colors and
regional markers identify source scope; they do not define service territories
or promise data for every location. Station points are real catalogue metadata,
not retrieved weather observations.

Most generation examples replay attributed real captures with source URLs and
checksums. ENTSO-E and KPX show offline request plans with optional credentialed
retrieval; NIST and DKASC show working import workflows for user-downloaded
native exports. ERA5 demonstrates weather request planning. These setup examples
are labelled explicitly and do not invent generation observations.

Download the :download:`generation examples with their data
</auto_examples/connectors/generation_examples.zip>` to run them from an extracted folder.
See the :doc:`worldwide provider catalogue </_generated/guides/worldwide-generation>`
and :doc:`original generation guide </_generated/guides/generation-connectors>`
for Python/CLI usage, provider access and coverage limits.
