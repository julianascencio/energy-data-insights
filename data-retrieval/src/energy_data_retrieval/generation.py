"""Shared result envelope for public generation observations.

Providers retain their physical units, measurement scope and timestamp semantics
in the returned frame and its metadata. This envelope never converts a power
snapshot into energy or treats an estimate as a measured observation.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from energy_data_retrieval.transport import RequestRecord


@dataclass(frozen=True, slots=True)
class GenerationResult:
    """Provider observations and provenance for every acquired response."""

    frame: pd.DataFrame
    requests: tuple[RequestRecord, ...]
