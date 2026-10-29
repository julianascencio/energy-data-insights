"""Climate Change Yield Assessment (CCYA), Ascencio Vásquez (2021), §7.5.

Monthly climate-to-yield calibration, separate irradiance/temperature/power
effects, and cumulative comparisons with measured annual yields. See
``docs/ccya.md`` for the thesis equation map and explicit implementation choices.
No data acquisition, calendar conversion, or degradation-rate inference occurs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike

from energy_methods._arrays import BoolArray, FloatArray, aligned, immutable, vector

REFERENCE_IDS = (
    "ascencio_vasquez_2021_thesis",
    "skoplaki_palyvos_2009_temperature",
    "polo_2020_site_adaptation",
)
YIELD_COMPONENTS = ("irradiance", "irradiance_temperature", "irradiance_power", "combined")


@dataclass(frozen=True, slots=True)
class LinearSiteAdaptation:
    """OLS map from modelled monthly means to measured monthly means (§7.5.1)."""

    slope: float
    intercept: float
    training_min: float
    training_max: float
    training_rows: int

    def predict(self, values: ArrayLike) -> FloatArray:
        """Apply the frozen map; extrapolation is allowed and separately flagged."""
        return self.slope * vector(values, "values") + self.intercept

    def support(self, values: ArrayLike) -> BoolArray:
        """Identify values inside the calibration range, not independent validity."""
        x = vector(values, "values")
        return np.isfinite(x) & (x >= self.training_min) & (x <= self.training_max)


def fit_site_adaptation(modelled: ArrayLike, measured: ArrayLike) -> LinearSiteAdaptation:
    """Fit y = a*x+b to supplied, already aligned monthly pairs.

    All pairs must be finite. Constant predictors or nonpositive slopes fail;
    no missing-data imputation or silent fallback to identity is performed.
    """
    x, y = aligned(modelled, measured)
    if len(x) < 3 or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("Site adaptation requires at least three finite monthly pairs")
    centered = x - x.mean()
    denominator = float(centered @ centered)
    if denominator <= np.finfo(float).eps * max(1.0, float(x @ x)):
        raise ValueError("Site adaptation predictor has insufficient variation")
    slope = float(centered @ (y - y.mean()) / denominator)
    intercept = float(y.mean() - slope * x.mean())
    if not np.isfinite([slope, intercept]).all() or slope <= 0:
        raise ValueError("Site adaptation requires a finite positive slope")
    return LinearSiteAdaptation(slope, intercept, float(x.min()), float(x.max()), len(x))


@dataclass(frozen=True, slots=True)
class CCYAConfig:
    """Thermal defaults from thesis p. 161; rates are fractions, not percentages."""

    gamma_per_c: float = -0.0045
    ross_c_m2_w: float = 0.03
    rolling_years: int = 10
    min_calibration_years: int = 2

    def __post_init__(self) -> None:
        if not np.isfinite([self.gamma_per_c, self.ross_c_m2_w]).all():
            raise ValueError("Thermal parameters must be finite")
        if not -0.02 <= self.gamma_per_c <= 0 or not 0 <= self.ross_c_m2_w <= 0.2:
            raise ValueError("Thermal parameters are outside the supported PV domain")
        for name, value, minimum in (
            ("rolling_years", self.rolling_years, 1),
            ("min_calibration_years", self.min_calibration_years, 2),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
                raise ValueError(f"{name} must be an integer >= {minimum}")


DEFAULT_CONFIG = CCYAConfig()


def _monthly(frame: pd.DataFrame, *, measured: bool = False) -> pd.DataFrame:
    """Validate full monthly years without coercing calendars or dropping rows."""
    columns = ["ghi_wm2", "temperature_c", "days"]
    if measured:
        columns.append("dc_yield_kwh_kwp")
    if not isinstance(frame.index, pd.PeriodIndex) or frame.index.freqstr != "M":
        raise ValueError("Use a monthly PeriodIndex (freq='M'); months are calendar labels")
    index = frame.index
    if frame.empty or index.hasnans or index.has_duplicates or not index.is_monotonic_increasing:
        raise ValueError("Monthly input must be nonempty, finite, unique and increasing")
    expected = pd.period_range(f"{index[0].year}-01", f"{index[-1].year}-12", freq="M")
    if not index.equals(expected):
        raise ValueError("Monthly input must contain consecutive complete January-December years")
    if not frame.columns.is_unique or not set(columns).issubset(frame.columns):
        raise ValueError(f"Monthly input requires unique columns including {columns}")
    result = frame.loc[:, columns].astype(float).copy()
    if not np.isfinite(result.to_numpy()).all():
        raise ValueError(
            "Monthly input contains missing or infinite values; qualify coverage first"
        )
    if (result["ghi_wm2"] < 0).any():
        raise ValueError("Monthly GHI must be nonnegative in W/m² (all-hours mean)")
    if (result["temperature_c"] <= -273.15).any():
        raise ValueError("Temperature must be in degrees Celsius above absolute zero")
    days = result["days"].to_numpy()
    if ((days < 28) | (days > 31) | (days != np.floor(days))).any():
        raise ValueError("days must contain native-calendar integer month lengths, 28 through 31")
    # Explicit days support Gregorian, noleap, all_leap and 360_day climate data.
    # Do not accept an arbitrary mixture of calendars within a year.
    for _, group in result.groupby(index.year):
        d = group["days"].to_numpy()
        standard = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
        leap = standard.copy()
        leap[1] = 29
        if not any(np.array_equal(d, option) for option in (standard, leap, np.full(12, 30))):
            raise ValueError("days do not describe a supported complete calendar year")
    if measured and (result["dc_yield_kwh_kwp"] < 0).any():
        raise ValueError("Measured monthly DC specific yield must be nonnegative in kWh/kWp")
    return result


@dataclass(frozen=True, slots=True)
class CCYAResult:
    """Monthly decomposition and annual/cumulative metrics for one scenario/member."""

    monthly: pd.DataFrame
    annual: pd.DataFrame
    metadata: dict[str, object]


@dataclass(frozen=True, slots=True)
class CCYAModel:
    """Frozen monthly response calibrated only on the supplied historical overlap."""

    config: CCYAConfig
    ghi_adaptation: LinearSiteAdaptation
    temperature_adaptation: LinearSiteAdaptation
    daily_yield_per_ghi: FloatArray
    reference_module_temperature_c: FloatArray
    historical_annual_yields: FloatArray
    monthly_ghi_min: FloatArray
    monthly_ghi_max: FloatArray
    calibration_start: str
    calibration_end: str

    def to_dict(self) -> dict[str, object]:
        """Export coefficients, calibration bounds, units and attribution as JSON data."""
        return {
            "method": "climate_change_yield_assessment",
            "implementation_version": 1,
            "reference_ids": list(REFERENCE_IDS),
            "thesis_sections": "7.5.1-7.5.3; equations 7.1-7.4, 3.6 and 3.8",
            "config": asdict(self.config),
            "ghi_adaptation": asdict(self.ghi_adaptation),
            "temperature_adaptation": asdict(self.temperature_adaptation),
            "daily_yield_per_ghi": self.daily_yield_per_ghi.tolist(),
            "reference_module_temperature_c": self.reference_module_temperature_c.tolist(),
            "historical_annual_yields_kwh_kwp": self.historical_annual_yields.tolist(),
            "monthly_ghi_min_wm2": self.monthly_ghi_min.tolist(),
            "monthly_ghi_max_wm2": self.monthly_ghi_max.tolist(),
            "calibration_start": self.calibration_start,
            "calibration_end": self.calibration_end,
            "yield_mapping": "month_of_year_centroid_ratio_to_raw_model_ghi",
            "temperature_multiplier": "1 + gamma * (adapted_module_T - historical_month_module_T)",
            "p_values": "empirical_nonexceedance_quantiles_0.10_0.50_0.90",
            "calendar": "explicit_native_days_per_month; no_timestamp_conversion",
        }

    def project(
        self,
        climate: pd.DataFrame,
        *,
        scenario: str,
        degradation_per_year: float = 0.0,
        age_at_start_years: float = 0.0,
        power_factors: pd.Series | None = None,
    ) -> CCYAResult:
        """Assess complete future years for one site/model/member/scenario.

        Inputs: monthly all-hours mean GHI (W/m²), ambient temperature (°C),
        native-calendar days. Linear power retention is 1-rate*age, with age
        sampled at each operating year's start. Alternatively pass an explicitly
        aligned monthly power-retention series for a nonlinear degradation path.
        No scenario probabilities, stochastic simulation or extrapolation cap
        are implied. Nonphysical negative predictions raise, rather than clip.
        """
        frame = _monthly(climate)
        if not scenario.strip():
            raise ValueError("A nonempty scenario/model/member identifier is required")
        if not np.isfinite([degradation_per_year, age_at_start_years]).all():
            raise ValueError("Degradation rate and age must be finite")
        if not 0 <= degradation_per_year <= 1 or age_at_start_years < 0:
            raise ValueError("Use a loss fraction per year in [0, 1] and nonnegative age")
        index = frame.index
        assert isinstance(index, pd.PeriodIndex)
        if index[0] <= pd.Period(self.calibration_end, freq="M"):
            raise ValueError("Projection must start after the calibration period")
        months = index.month.to_numpy() - 1
        raw_ghi = frame["ghi_wm2"].to_numpy()
        ghi = self.ghi_adaptation.predict(raw_ghi)
        temperature = self.temperature_adaptation.predict(frame["temperature_c"].to_numpy())
        if (ghi < 0).any() or (temperature <= -273.15).any():
            raise ValueError("Site adaptation produced nonphysical weather outside its domain")
        module_temperature = temperature + self.config.ross_c_m2_w * ghi
        temperature_factor = 1 + self.config.gamma_per_c * (
            module_temperature - self.reference_module_temperature_c[months]
        )
        if not np.isfinite(temperature_factor).all() or (temperature_factor <= 0).any():
            raise ValueError("Temperature multiplier is nonpositive or nonfinite")
        if power_factors is None:
            ages = index.year.to_numpy() - index[0].year + age_at_start_years
            power = 1 - degradation_per_year * ages
        else:
            if degradation_per_year != 0 or age_at_start_years != 0:
                raise ValueError("Supply either power_factors or linear degradation settings")
            if not power_factors.index.equals(index):
                raise ValueError("power_factors must have exactly the projection monthly index")
            power = power_factors.to_numpy(dtype=float)
        if not np.isfinite(power).all() or ((power < 0) | (power > 1)).any():
            raise ValueError("Power-retention factors must be finite and in [0, 1]")
        invariant = self.daily_yield_per_ghi[months] * raw_ghi * frame["days"].to_numpy()
        monthly = pd.DataFrame(
            {
                "days": frame["days"],
                "adapted_ghi_wm2": ghi,
                "adapted_temperature_c": temperature,
                "module_temperature_c": module_temperature,
                "temperature_factor": temperature_factor,
                "power_factor": power,
                "irradiance_kwh_kwp": invariant,
                "irradiance_temperature_kwh_kwp": invariant * temperature_factor,
                "irradiance_power_kwh_kwp": invariant * power,
                "combined_kwh_kwp": invariant * temperature_factor * power,
                "outside_calibration_support": (
                    (raw_ghi < self.monthly_ghi_min[months])
                    | (raw_ghi > self.monthly_ghi_max[months])
                    | ~self.ghi_adaptation.support(raw_ghi)
                    | ~self.temperature_adaptation.support(frame["temperature_c"].to_numpy())
                ),
            },
            index=index,
        )
        numeric = monthly.select_dtypes(include="number").to_numpy()
        if not np.isfinite(numeric).all():
            raise ValueError("Projection overflowed the supported numerical domain")
        annual = _annual_metrics(monthly, self.historical_annual_yields, self.config.rolling_years)
        return CCYAResult(
            monthly,
            annual,
            {
                "scenario": scenario,
                "model": self.to_dict(),
                "degradation_per_year": degradation_per_year if power_factors is None else None,
                "age_at_start_years": age_at_start_years if power_factors is None else None,
                "power_model": "linear_start_of_year"
                if power_factors is None
                else "supplied_monthly",
                "projection_start": str(index[0]),
                "projection_end": str(index[-1]),
                "extrapolated_months": int(monthly["outside_calibration_support"].sum()),
                "uncertainty": "historical_interannual_quantiles_only; no_scenario_probabilities",
            },
        )


def fit_ccya(
    measured: pd.DataFrame,
    historical_climate: pd.DataFrame,
    *,
    config: CCYAConfig = DEFAULT_CONFIG,
) -> CCYAModel:
    """Calibrate CCYA on an exact, explicit historical overlap of full years.

    Both inputs require a monthly PeriodIndex and columns ghi_wm2,
    temperature_c, days. Measured data also need monthly total
    dc_yield_kwh_kwp, normalized with qualified DC STC capacity. Inputs must
    already be coverage-qualified; missing months/values fail. Model calendars
    may differ from the observed calendar, because fitting uses mean daily yield.

    The invariant response scales each calendar month's centroid daily yield
    proportionally to raw modelled GHI. This is an explicit implementation
    choice for the seasonal relationship illustrated in thesis Figure 7.13.
    """
    observations = _monthly(measured, measured=True)
    climate = _monthly(historical_climate)
    if not observations.index.equals(climate.index):
        raise ValueError("Select the same explicit historical overlap in both monthly tables")
    if len(climate) < 12 * config.min_calibration_years:
        raise ValueError("Insufficient complete calibration years")
    index = climate.index
    assert isinstance(index, pd.PeriodIndex)
    ghi_fit = fit_site_adaptation(climate["ghi_wm2"], observations["ghi_wm2"])
    temp_fit = fit_site_adaptation(climate["temperature_c"], observations["temperature_c"])
    model_groups = climate.groupby(index.month)
    ghi_centers = model_groups["ghi_wm2"].mean().to_numpy()
    if (ghi_centers <= 0).any():
        raise ValueError("Every calendar month needs a positive modelled GHI centroid")
    daily_yield = observations["dc_yield_kwh_kwp"] / observations["days"]
    yield_centers = daily_yield.groupby(index.month).mean().to_numpy()
    # Normalize against the same fitted weather maps used in projection. Using
    # measured centroids here would count seasonal OLS residual bias as future
    # warming/cooling, even when the model's climate has not changed.
    reference_temperature = temp_fit.predict(
        model_groups["temperature_c"].mean().to_numpy()
    ) + config.ross_c_m2_w * ghi_fit.predict(ghi_centers)
    annual_yields = observations["dc_yield_kwh_kwp"].groupby(index.year).sum().to_numpy()
    if (annual_yields <= 0).any():
        raise ValueError("Every measured annual yield must be positive for gain/loss comparisons")
    return CCYAModel(
        config,
        ghi_fit,
        temp_fit,
        immutable(yield_centers / ghi_centers),
        immutable(reference_temperature),
        immutable(annual_yields),
        immutable(model_groups["ghi_wm2"].min().to_numpy()),
        immutable(model_groups["ghi_wm2"].max().to_numpy()),
        str(index[0]),
        str(index[-1]),
    )


def _annual_metrics(monthly: pd.DataFrame, historical: FloatArray, window: int) -> pd.DataFrame:
    """Discrete full-year accounting for thesis equations 7.1 through 7.4."""
    index = monthly.index
    assert isinstance(index, pd.PeriodIndex)
    grouped = monthly.groupby(index.year)
    annual = grouped[[f"{name}_kwh_kwp" for name in YIELD_COMPONENTS]].sum()
    annual.index.name = "year"
    annual["operating_year"] = np.arange(1, len(annual) + 1)
    annual["outside_calibration_support_months"] = grouped["outside_calibration_support"].sum()
    baselines = dict(
        zip(("p10", "p50", "p90"), np.quantile(historical, [0.1, 0.5, 0.9]), strict=True)
    )
    for label, baseline in baselines.items():
        annual[f"measured_{label}_kwh_kwp"] = baseline
    for component in YIELD_COMPONENTS:
        values = annual[f"{component}_kwh_kwp"]
        annual[f"{component}_rolling_mean_kwh_kwp"] = values.rolling(
            window, min_periods=window
        ).mean()
        annual[f"{component}_rolling_gain_pct"] = 100 * (
            annual[f"{component}_rolling_mean_kwh_kwp"] / historical.mean() - 1
        )
        cumulative = values.cumsum()
        annual[f"{component}_cumulative_kwh_kwp"] = cumulative
        for label, baseline in baselines.items():
            ratio = cumulative / (baseline * annual["operating_year"])
            annual[f"{component}_cumulative_ratio_{label}_pct"] = 100 * ratio
            annual[f"{component}_cumulative_gain_{label}_pct"] = 100 * (ratio - 1)
    return annual
