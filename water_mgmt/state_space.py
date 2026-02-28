"""
Formal State Space definition for the AWD World Model.

Defines every state variable with:
  - type, valid range, units
  - observation method (how we learn this variable's value)
  - decay behaviour (does confidence drop over time?)
  - whether the variable is observable, latent, or derived
"""

from dataclasses import dataclass, field
from typing import Optional, List, Literal, Dict, Any
from datetime import timedelta


# ---------------------------------------------------------------------------
# State Variable Metadata
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StateVariableMeta:
    """Metadata for one variable in the world-model state space."""
    name: str
    category: Literal["crop", "field", "water", "weather", "constraint", "management"]
    dtype: Literal["float", "int", "bool", "categorical"]
    unit: Optional[str]
    min_val: Optional[float]
    max_val: Optional[float]
    valid_values: Optional[List[str]]  # for categorical variables
    observability: Literal["direct", "indirect", "derived", "latent"]
    observation_methods: List[str]
    decay_hours: Optional[float]  # hours until confidence halves; None = no decay
    description: str


# ---------------------------------------------------------------------------
# Complete State Space Registry
# ---------------------------------------------------------------------------

STATE_SPACE: Dict[str, StateVariableMeta] = {}


def _register(v: StateVariableMeta):
    STATE_SPACE[v.name] = v
    return v


# ---- Crop variables ----
_register(StateVariableMeta(
    name="das",
    category="crop", dtype="int", unit="days",
    min_val=0, max_val=200, valid_values=None,
    observability="derived",
    observation_methods=["profile_sowing_date"],
    decay_hours=None,
    description="Days after sowing / transplanting"
))

_register(StateVariableMeta(
    name="growth_stage",
    category="crop", dtype="categorical", unit=None,
    min_val=None, max_val=None,
    valid_values=["seedling", "tillering", "panicle_initiation",
                  "heading", "grain_filling", "maturity", "unknown"],
    observability="derived",
    observation_methods=["das_lookup", "farmer_report"],
    decay_hours=None,
    description="Current phenological growth stage"
))

_register(StateVariableMeta(
    name="expected_harvest_date",
    category="crop", dtype="categorical", unit="date",
    min_val=None, max_val=None, valid_values=None,
    observability="derived",
    observation_methods=["variety_duration_estimate"],
    decay_hours=None,
    description="Estimated harvest date"
))

# ---- Field variables ----
_register(StateVariableMeta(
    name="soil_type",
    category="field", dtype="categorical", unit=None,
    min_val=None, max_val=None,
    valid_values=["alluvial", "acid_sulfate", "clay", "sandy", "unknown"],
    observability="direct",
    observation_methods=["farmer_profile", "farmer_chat"],
    decay_hours=None,
    description="Soil type classification"
))

_register(StateVariableMeta(
    name="bund_height_class",
    category="field", dtype="categorical", unit=None,
    min_val=None, max_val=None,
    valid_values=["low", "medium", "high", "unknown"],
    observability="direct",
    observation_methods=["farmer_profile"],
    decay_hours=None,
    description="Bund height classification"
))

_register(StateVariableMeta(
    name="leveled",
    category="field", dtype="bool", unit=None,
    min_val=None, max_val=None, valid_values=None,
    observability="direct",
    observation_methods=["farmer_profile"],
    decay_hours=None,
    description="Whether field is level"
))

# ---- Water variables ----
_register(StateVariableMeta(
    name="ponded_water_cm",
    category="water", dtype="float", unit="cm",
    min_val=0.0, max_val=30.0, valid_values=None,
    observability="direct",
    observation_methods=["bucket_observation", "farmer_chat", "checkin"],
    decay_hours=24.0,
    description="Depth of standing water above soil surface"
))

_register(StateVariableMeta(
    name="water_table_depth_cm",
    category="water", dtype="float", unit="cm",
    min_val=0.0, max_val=60.0, valid_values=None,
    observability="direct",
    observation_methods=["awd_tube_reading", "farmer_chat", "checkin"],
    decay_hours=12.0,
    description="Depth of water table below soil surface (AWD tube reading)"
))

_register(StateVariableMeta(
    name="soil_deficit_index",
    category="water", dtype="float", unit="ratio",
    min_val=0.0, max_val=1.0, valid_values=None,
    observability="latent",
    observation_methods=["hydrology_model"],
    decay_hours=None,
    description="Soil moisture deficit index (0=saturated, 1=wilting point)"
))

_register(StateVariableMeta(
    name="soil_cracks",
    category="water", dtype="categorical", unit=None,
    min_val=None, max_val=None,
    valid_values=["none", "small", "visible", "deep", "unknown"],
    observability="direct",
    observation_methods=["farmer_chat", "checkin", "photo"],
    decay_hours=48.0,
    description="Severity of soil surface cracking"
))

# ---- Weather variables ----
_register(StateVariableMeta(
    name="rain_last_24h_mm",
    category="weather", dtype="float", unit="mm",
    min_val=0.0, max_val=500.0, valid_values=None,
    observability="direct",
    observation_methods=["weather_api", "farmer_report"],
    decay_hours=24.0,
    description="Rainfall in last 24 hours"
))

_register(StateVariableMeta(
    name="rain_next_72h_mm",
    category="weather", dtype="float", unit="mm",
    min_val=0.0, max_val=500.0, valid_values=None,
    observability="indirect",
    observation_methods=["weather_api_forecast"],
    decay_hours=6.0,
    description="Forecasted rainfall in next 72 hours"
))

_register(StateVariableMeta(
    name="et0_next_24h_mm",
    category="weather", dtype="float", unit="mm",
    min_val=0.0, max_val=15.0, valid_values=None,
    observability="derived",
    observation_methods=["weather_api_estimate", "hargreaves_equation"],
    decay_hours=12.0,
    description="Reference evapotranspiration estimate for next 24h"
))

_register(StateVariableMeta(
    name="temperature_next_24h_c",
    category="weather", dtype="float", unit="°C",
    min_val=0.0, max_val=50.0, valid_values=None,
    observability="indirect",
    observation_methods=["weather_api_forecast"],
    decay_hours=6.0,
    description="Forecasted average temperature for next 24h"
))

# ---- Constraint variables ----
_register(StateVariableMeta(
    name="irrigation_access",
    category="constraint", dtype="bool", unit=None,
    min_val=None, max_val=None, valid_values=None,
    observability="direct",
    observation_methods=["farmer_profile", "farmer_chat"],
    decay_hours=None,
    description="Whether farmer has access to irrigation"
))

_register(StateVariableMeta(
    name="drainage_access",
    category="constraint", dtype="bool", unit=None,
    min_val=None, max_val=None, valid_values=None,
    observability="direct",
    observation_methods=["farmer_profile", "farmer_chat"],
    decay_hours=None,
    description="Whether farmer has access to drainage"
))

_register(StateVariableMeta(
    name="can_irrigate_today",
    category="constraint", dtype="bool", unit=None,
    min_val=None, max_val=None, valid_values=None,
    observability="direct",
    observation_methods=["farmer_chat"],
    decay_hours=24.0,
    description="Whether irrigation is possible today"
))

# ---- Management variables ----
_register(StateVariableMeta(
    name="regime",
    category="management", dtype="categorical", unit=None,
    min_val=None, max_val=None,
    valid_values=["AWD", "CONTINUOUS", "RAINFED", "AUTO"],
    observability="direct",
    observation_methods=["farmer_profile", "farmer_chat"],
    decay_hours=None,
    description="Water management regime"
))

_register(StateVariableMeta(
    name="mode",
    category="management", dtype="categorical", unit=None,
    min_val=None, max_val=None,
    valid_values=["handbook_only", "handbook_plus", "general_only"],
    observability="direct",
    observation_methods=["system_default"],
    decay_hours=None,
    description="Rule engine operating mode"
))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_variable_meta(name: str) -> Optional[StateVariableMeta]:
    """Look up metadata for a state variable."""
    return STATE_SPACE.get(name)


def get_variables_by_category(category: str) -> List[StateVariableMeta]:
    """Get all state variables in a category."""
    return [v for v in STATE_SPACE.values() if v.category == category]


def get_observable_variables() -> List[StateVariableMeta]:
    """Get variables that can be directly observed."""
    return [v for v in STATE_SPACE.values() if v.observability == "direct"]


def get_decaying_variables() -> List[StateVariableMeta]:
    """Get variables whose confidence decays over time."""
    return [v for v in STATE_SPACE.values() if v.decay_hours is not None]


def validate_value(name: str, value: Any) -> bool:
    """Check whether a value is within the valid range for a state variable."""
    meta = STATE_SPACE.get(name)
    if meta is None:
        return True  # unknown variable, pass through

    if value is None:
        return True

    if meta.dtype == "categorical" and meta.valid_values:
        return value in meta.valid_values

    if meta.dtype in ("float", "int"):
        try:
            v = float(value)
        except (TypeError, ValueError):
            return False
        if meta.min_val is not None and v < meta.min_val:
            return False
        if meta.max_val is not None and v > meta.max_val:
            return False

    return True


def state_space_summary() -> Dict[str, Any]:
    """Return a JSON-serialisable summary of the full state space."""
    out = {}
    for name, meta in STATE_SPACE.items():
        entry = {
            "category": meta.category,
            "type": meta.dtype,
            "unit": meta.unit,
            "observability": meta.observability,
            "observation_methods": meta.observation_methods,
            "description": meta.description,
        }
        if meta.min_val is not None:
            entry["min"] = meta.min_val
        if meta.max_val is not None:
            entry["max"] = meta.max_val
        if meta.valid_values:
            entry["valid_values"] = meta.valid_values
        if meta.decay_hours is not None:
            entry["decay_hours"] = meta.decay_hours
        out[name] = entry
    return out
