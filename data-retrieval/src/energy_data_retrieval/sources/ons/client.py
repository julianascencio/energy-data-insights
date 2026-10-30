"""Brazil ONS plant generation and per-plant photovoltaic constrained-off data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from energy_data_retrieval.generation import GenerationResult
from energy_data_retrieval.transport import (
    HTTPClient,
    RequestRecord,
    RetrievalError,
    array_value,
    object_value,
)

ONS_HOSTS = frozenset({"dados.ons.org.br", "ons-aws-prod-opendata.s3.amazonaws.com"})
CATALOGUE_ENDPOINT = "https://dados.ons.org.br/api/3/action/package_show"
REFERENCE_IDS = ("ons_hourly_generation", "ons_pv_curtailment")
_PRODUCTS = {
    "generation": ("geracao-usina-2", "Geracao_Usina_2-", "geracao_usina_2_ho"),
    "solar_curtailment": (
        "restricao_coff_fotovoltaica_detail",
        "Restricoes_coff_fotovoltaica_Detail-",
        "restricao_coff_fotovoltaica_detail_tm",
    ),
}


def _limit(value: int, name: str, upper: int) -> None:
    if type(value) is not int or not 1 <= value <= upper:
        raise ValueError(f"{name} must be an integer in 1..{upper}")


def _normalize(
    native: pd.DataFrame,
    *,
    product: str,
    source_timezone: str,
    include_estimates: bool,
    maximum_rows: int,
) -> pd.DataFrame:
    if product not in _PRODUCTS:
        raise ValueError("ONS product must be generation or solar_curtailment")
    if len(native) > maximum_rows:
        raise RetrievalError("ONS native file exceeds maximum_rows")
    value_column = "val_geracao" if product == "generation" else "val_geracaoverificada"
    mode_column = "cod_modalidadeoperacao" if product == "generation" else "nom_modalidadeoperacao"
    required = {"din_instante", "id_ons", "nom_usina", "id_subsistema", value_column, mode_column}
    if product == "generation":
        required.add("nom_tipousina")
    if required - set(native):
        raise RetrievalError("ONS native data are missing required generation columns")
    frame = native.copy()
    for column in ("din_instante", "id_ons", "nom_usina", mode_column):
        if frame[column].isna().any() or frame[column].astype(str).str.strip().eq("").any():
            raise RetrievalError(f"ONS omitted {column}")
    try:
        local = pd.to_datetime(frame["din_instante"], format="%Y-%m-%d %H:%M:%S", errors="raise")
        stamps = local.dt.tz_localize(source_timezone, ambiguous="raise", nonexistent="raise")
    except (ValueError, TypeError, KeyError) as exc:
        raise RetrievalError("ONS invalid, ambiguous or nonexistent source timestamp") from exc
    except Exception as exc:
        # Timezone libraries expose distinct exception types for DST folds/gaps.
        raise RetrievalError("ONS invalid, ambiguous or nonexistent source timestamp") from exc
    minutes = 60 if product == "generation" else 30
    if ((local.dt.minute % minutes != 0) | (local.dt.second != 0)).any():
        raise RetrievalError("ONS timestamp is not aligned with the product interval")
    for column in [name for name in native if isinstance(name, str) and name.startswith("val_")]:
        raw = frame[column].astype("string").str.strip().replace("", pd.NA)
        try:
            numbers = pd.to_numeric(raw, errors="raise").astype(float)
        except (ValueError, TypeError):
            raise RetrievalError(f"ONS nonnumeric {column}") from None
        if np.isinf(numbers).any():
            raise RetrievalError(f"ONS non-finite {column}")
        frame[column] = numbers
    mode = frame[mode_column].astype(str).str.upper()
    estimated = mode.str.contains("PEQUENAS USINAS|TIPO III", regex=True)
    known = mode.isin({"TIPO I", "TIPO II-A", "TIPO II-B", "TIPO II-C", "CONJUNTO DE USINAS"})
    if (~(known | estimated)).any():
        raise RetrievalError("ONS unknown operation category; actual/estimated status is uncertain")
    frame["timestamp"] = stamps.dt.tz_convert("UTC")
    frame["source"] = "ons"
    frame["area"] = frame["id_subsistema"]
    frame["unit_id"] = frame["id_ons"]
    frame["technology"] = frame["nom_tipousina"] if product == "generation" else "FOTOVOLTAICA"
    frame["value"] = frame[value_column]
    frame["unit"] = "MW"
    frame["source_unit"] = "MWmed"
    frame["aggregation"] = "hourly_mean" if minutes == 60 else "half_hour_mean"
    frame["quality"] = np.where(estimated, "estimated_or_forecast", "verified")
    excluded = int(estimated.sum()) if not include_estimates else 0
    if not include_estimates:
        frame = frame.loc[~estimated].copy()
    frame = frame.drop_duplicates()
    if frame.duplicated(["timestamp", "unit_id"]).any():
        raise RetrievalError(
            "ONS conflicting plant/time observations; do not sum duplicate entities"
        )
    frame = frame.sort_values(["timestamp", "unit_id"]).reset_index(drop=True)
    frame.attrs.update(
        product=product,
        source_timezone=source_timezone,
        timestamp_semantics=(
            "Source din_instante label converted to UTC without shifting; "
            "interval boundaries not inferred"
        ),
        reference_ids=list(REFERENCE_IDS),
        excluded_estimated_rows=excluded,
        scope="Plants and plant groups; not a complete inventory of individual generators",
        missing_policy="Source null/blank remains missing; no interpolation or zero filling",
        curtailment_policy=(
            "Verified, estimated and final-reference MW retained separately; no inferred loss"
        ),
    )
    return frame


def parse_generation_csv(
    payload: str,
    *,
    product: str = "generation",
    source_timezone: str = "America/Sao_Paulo",
    include_estimates: bool = False,
    maximum_rows: int = 1_000_000,
) -> pd.DataFrame:
    """Parse native semicolon CSV while retaining every native column.

    Timestamps are native reference labels in the supplied source timezone. The
    default interprets them as Brazilian civil time, with ambiguous historical DST labels
    rejected. Callers with evidence for a fixed clock may specify ``Etc/GMT+3``.
    Type III and small-plant/MMGD estimates are excluded by default. PV detail
    keeps irradiance flags, estimated MW, actual MW and reference MW separate.
    """
    _limit(maximum_rows, "maximum_rows", 10_000_000)
    try:
        native = pd.read_csv(
            StringIO(payload),
            sep=";",
            dtype="string",
            keep_default_na=False,
            nrows=maximum_rows + 1,
        )
    except (ValueError, pd.errors.ParserError):
        raise RetrievalError("ONS returned malformed CSV") from None
    return _normalize(
        native,
        product=product,
        source_timezone=source_timezone,
        include_estimates=include_estimates,
        maximum_rows=maximum_rows,
    )


@dataclass(slots=True)
class ONSClient:
    """Discover exact public monthly/yearly exports through ONS's CKAN catalogue."""

    http: HTTPClient
    maximum_requests: int = 25
    maximum_rows: int = 1_000_000

    def __post_init__(self) -> None:
        _limit(self.maximum_requests, "maximum_requests", 1000)
        _limit(self.maximum_rows, "maximum_rows", 10_000_000)

    def generation(
        self,
        start: date,
        end: date,
        *,
        plant_ids: list[str] | None = None,
        source_timezone: str = "America/Sao_Paulo",
        include_estimates: bool = False,
    ) -> GenerationResult:
        """Retrieve inclusive local dates from hourly verified-generation exports."""
        return self._retrieve(
            start, end, "generation", plant_ids, source_timezone, include_estimates
        )

    def solar_curtailment(
        self,
        start: date,
        end: date,
        *,
        plant_ids: list[str] | None = None,
        source_timezone: str = "America/Sao_Paulo",
    ) -> GenerationResult:
        """Retrieve half-hour PV detail, retaining actual/reference values and flags."""
        return self._retrieve(start, end, "solar_curtailment", plant_ids, source_timezone, False)

    def _retrieve(
        self,
        start: date,
        end: date,
        product: str,
        plant_ids: list[str] | None,
        source_timezone: str,
        include_estimates: bool,
    ) -> GenerationResult:
        minimum = date(2000, 1, 1) if product == "generation" else date(2024, 4, 1)
        if (
            type(start) is not date
            or type(end) is not date
            or not minimum <= start <= end < date(9999, 1, 1)
        ):
            raise ValueError(f"ONS requires inclusive dates from {minimum}")
        if plant_ids is not None and (
            not plant_ids or any(not isinstance(x, str) or not x for x in plant_ids)
        ):
            raise ValueError("plant_ids must contain nonempty ONS identifiers")
        periods = pd.period_range(start, end, freq="M")
        keys = list(
            dict.fromkeys(
                str(p.year) if product == "generation" and p.year <= 2021 else str(p)
                for p in periods
            )
        )
        if len(keys) + 1 > self.maximum_requests:
            raise ValueError("ONS query exceeds maximum_requests including catalogue lookup")
        dataset, prefix, directory = _PRODUCTS[product]
        catalogue = self.http.get_json(CATALOGUE_ENDPOINT, {"id": dataset})
        root = object_value(catalogue.value)
        if root.get("success") is not True:
            raise RetrievalError("ONS catalogue returned an error")
        resources = array_value(object_value(root.get("result")).get("resources"))
        selected: dict[str, str] = {}
        for item in resources:
            resource = object_value(item)
            name = resource.get("name")
            if (
                not isinstance(name, str)
                or not name.startswith(prefix)
                or resource.get("format") != "PARQUET"
            ):
                continue
            key = name.removeprefix(prefix)
            if key not in keys:
                continue
            url = resource.get("url")
            if not isinstance(url, str):
                raise RetrievalError("ONS catalogue resource has no URL")
            parsed = urlsplit(url)
            if (
                parsed.scheme != "https"
                or parsed.hostname != "ons-aws-prod-opendata.s3.amazonaws.com"
                or not parsed.path.startswith(f"/dataset/{directory}/")
                or parsed.query
                or parsed.fragment
            ):
                raise RetrievalError("ONS catalogue supplied an unapproved export URL")
            if key in selected and selected[key] != url:
                raise RetrievalError("ONS catalogue has ambiguous exports for a period")
            selected[key] = url
        if set(keys) - selected.keys():
            raise RetrievalError("ONS catalogue has no Parquet export for a requested period")
        frames: list[pd.DataFrame] = []
        records: list[RequestRecord] = [catalogue.record]
        total = 0
        with TemporaryDirectory(prefix="energy-ons-") as temporary:
            for index, key in enumerate(keys):
                path = Path(temporary) / f"part-{index}.parquet"
                records.append(self.http.download_file(selected[key], path))
                try:
                    if pq.read_metadata(path).num_rows > self.maximum_rows:
                        raise RetrievalError("ONS export exceeds maximum_rows before decompression")
                    native = pd.read_parquet(path)
                except (OSError, ValueError) as exc:
                    raise RetrievalError("ONS returned invalid Parquet") from exc
                frame = _normalize(
                    native,
                    product=product,
                    source_timezone=source_timezone,
                    include_estimates=include_estimates,
                    maximum_rows=self.maximum_rows,
                )
                dates = frame["timestamp"].dt.tz_convert(source_timezone).dt.date
                frame = frame.loc[(dates >= start) & (dates <= end)].copy()
                if plant_ids is not None:
                    frame = frame.loc[frame["unit_id"].isin(plant_ids)].copy()
                total += len(frame)
                if total > self.maximum_rows:
                    raise RetrievalError("ONS selection exceeds maximum_rows")
                frames.append(frame)
        result = pd.concat(frames, ignore_index=True)
        result.attrs.update(frames[0].attrs)
        result.attrs["excluded_estimated_rows"] = sum(
            frame.attrs["excluded_estimated_rows"] for frame in frames
        )
        if plant_ids is not None and set(plant_ids) - set(result["unit_id"]):
            raise RetrievalError("ONS requested plant_ids absent from selected actual observations")
        if result.duplicated(["timestamp", "unit_id"]).any():
            raise RetrievalError("ONS exports overlap in plant/time observations")
        return GenerationResult(result, tuple(records))
