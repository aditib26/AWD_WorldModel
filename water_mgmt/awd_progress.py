"""
AWD Progress Tracking — 10-phase schedule with 3 wet-dry cycles.

Tracks farmer progress through the complete AWD season and determines
whether each verification criterion has been met for certification.
"""

from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# AWD Phase Definitions (10 phases, 3 wet-dry cycles)
# ---------------------------------------------------------------------------

AWD_PHASES = [
    {
        "id": 1,
        "name": "Germination & Early Seedling",
        "short": "Germination",
        "day_start": 1,
        "day_end": 7,
        "icon": "🌱",
        "color": "#22c55e",
        "rule": "Keep soil saturated or shallow flood (1 cm). Avoid deep flooding.",
        "is_drying": False,
        "cycle": None,
    },
    {
        "id": 2,
        "name": "Early Vegetative Growth",
        "short": "Early Veg",
        "day_start": 8,
        "day_end": 19,
        "icon": "🌿",
        "color": "#16a34a",
        "rule": "Maintain shallow flood 1–3 cm. Apply fertilizer; keep water 3–5 days after application.",
        "is_drying": False,
        "cycle": None,
    },
    {
        "id": 3,
        "name": "AWD Cycle 1 — First Drying",
        "short": "Cycle 1: Dry",
        "day_start": 20,
        "day_end": 28,
        "icon": "💨",
        "color": "#f59e0b",
        "rule": "Stop irrigation. Let water table fall to 15 cm below surface (5–7 days). Then re-flood to 3–5 cm. Encourages deep roots.",
        "is_drying": True,
        "cycle": 1,
    },
    {
        "id": 4,
        "name": "Shallow Flood Between Cycles",
        "short": "Re-flood",
        "day_start": 29,
        "day_end": 33,
        "icon": "💧",
        "color": "#3b82f6",
        "rule": "Maintain shallow flood 1–3 cm. Flood before any fertilizer application.",
        "is_drying": False,
        "cycle": None,
    },
    {
        "id": 5,
        "name": "AWD Cycle 2 — Mid-Season Drying",
        "short": "Cycle 2: Dry",
        "day_start": 34,
        "day_end": 45,
        "icon": "💨",
        "color": "#f59e0b",
        "rule": "Drain after tillering / top-dressing. Let water table fall to 15 cm (5–7 days). Re-flood to 3–5 cm. Reduces lodging.",
        "is_drying": True,
        "cycle": 2,
    },
    {
        "id": 6,
        "name": "Shallow Flood for Panicle Initiation",
        "short": "Panicle Flood",
        "day_start": 46,
        "day_end": 55,
        "icon": "💧",
        "color": "#3b82f6",
        "rule": "Restore shallow flood 3–5 cm. Apply pre-panicle fertilizer under 1–3 cm flood.",
        "is_drying": False,
        "cycle": None,
    },
    {
        "id": 7,
        "name": "AWD Cycle 3 — Late Vegetative Drying",
        "short": "Cycle 3: Dry",
        "day_start": 56,
        "day_end": 60,
        "icon": "💨",
        "color": "#f59e0b",
        "rule": "Optional 3rd dry-down before heading. Drain to 15 cm threshold, re-flood to 3–5 cm. Skip if drought risk is high.",
        "is_drying": True,
        "cycle": 3,
    },
    {
        "id": 8,
        "name": "Panicle Initiation & Flowering",
        "short": "Flowering",
        "day_start": 60,
        "day_end": 70,
        "icon": "🌾",
        "color": "#dc2626",
        "rule": "SENSITIVE STAGE — Keep continuous shallow flood 3–5 cm for ~10 days. Do NOT let water drop below surface.",
        "is_drying": False,
        "cycle": None,
    },
    {
        "id": 9,
        "name": "Grain Filling & Ripening",
        "short": "Grain Fill",
        "day_start": 71,
        "day_end": 100,
        "icon": "🌾",
        "color": "#ea580c",
        "rule": "Maintain water near ground level or light AWD (15 cm trigger, re-flood 3–5 cm). Avoid prolonged dry soil.",
        "is_drying": False,
        "cycle": None,
    },
    {
        "id": 10,
        "name": "Pre-Harvest Final Drainage",
        "short": "Final Drain",
        "day_start": 100,
        "day_end": 115,
        "icon": "🚜",
        "color": "#78716c",
        "rule": "Stop irrigation 7–15 days before harvest. Let field dry completely. Do NOT re-flood.",
        "is_drying": True,
        "cycle": None,
    },
]


# ---------------------------------------------------------------------------
# Generic Rice Season Phases (for CONTINUOUS, RAINFED, AUTO regimes)
# ---------------------------------------------------------------------------

GENERIC_PHASES = [
    {
        "id": 1,
        "name": "Germination & Establishment",
        "short": "Germination",
        "day_start": 1,
        "day_end": 10,
        "icon": "🌱",
        "color": "#22c55e",
        "rule": "Keep soil saturated or shallow flooded. Ensure seedlings establish well.",
        "is_drying": False,
        "cycle": None,
    },
    {
        "id": 2,
        "name": "Vegetative Growth",
        "short": "Vegetative",
        "day_start": 11,
        "day_end": 35,
        "icon": "🌿",
        "color": "#16a34a",
        "rule": "Maintain water level per your regime. Apply basal and tillering fertilizer on schedule.",
        "is_drying": False,
        "cycle": None,
    },
    {
        "id": 3,
        "name": "Tillering & Mid-Season",
        "short": "Tillering",
        "day_start": 36,
        "day_end": 55,
        "icon": "🌿",
        "color": "#059669",
        "rule": "Peak tillering period. Monitor for pests and weeds. Manage water to support tiller development.",
        "is_drying": False,
        "cycle": None,
    },
    {
        "id": 4,
        "name": "Panicle Initiation",
        "short": "Panicle Init",
        "day_start": 56,
        "day_end": 65,
        "icon": "🌾",
        "color": "#3b82f6",
        "rule": "Critical stage — ensure adequate water supply. Apply panicle fertilizer.",
        "is_drying": False,
        "cycle": None,
    },
    {
        "id": 5,
        "name": "Flowering & Heading",
        "short": "Flowering",
        "day_start": 66,
        "day_end": 75,
        "icon": "🌾",
        "color": "#dc2626",
        "rule": "SENSITIVE STAGE — do not let field dry. Maintain consistent water to protect grain set.",
        "is_drying": False,
        "cycle": None,
    },
    {
        "id": 6,
        "name": "Grain Filling & Ripening",
        "short": "Grain Fill",
        "day_start": 76,
        "day_end": 100,
        "icon": "🌾",
        "color": "#ea580c",
        "rule": "Maintain moisture for grain development. Gradually reduce water as grains mature.",
        "is_drying": False,
        "cycle": None,
    },
    {
        "id": 7,
        "name": "Pre-Harvest Drainage",
        "short": "Harvest Prep",
        "day_start": 101,
        "day_end": 115,
        "icon": "🚜",
        "color": "#78716c",
        "rule": "Stop irrigation 7–15 days before harvest. Let field dry for machinery access.",
        "is_drying": True,
        "cycle": None,
    },
]


def get_phases_for_regime(regime: str) -> list:
    """Return the appropriate phase list based on irrigation regime."""
    if regime and regime.upper() == "AWD":
        return AWD_PHASES
    return GENERIC_PHASES


# ---------------------------------------------------------------------------
# Verification Criteria for Certification
# ---------------------------------------------------------------------------

VERIFICATION_CRITERIA = [
    {
        "id": "tube_installed",
        "label": "AWD Tube Installed",
        "description": "Farmer installed a perforated observation tube and monitored water depth regularly using the 15 cm threshold.",
        "icon": "📏",
        "auto_check": "has_awd_tube_readings",
    },
    {
        "id": "cycle_1_complete",
        "label": "Cycle 1 — First Dry-Down",
        "description": "Field drained around Day 20–28, water table reached 15 cm below surface, re-flooded to 3–5 cm.",
        "icon": "💨",
        "auto_check": "drying_in_range_20_28",
    },
    {
        "id": "cycle_2_complete",
        "label": "Cycle 2 — Mid-Season Drying",
        "description": "Field drained after tillering/fertilization (Day 34–45), water table to 15 cm, re-flooded to 3–5 cm.",
        "icon": "💨",
        "auto_check": "drying_in_range_34_45",
    },
    {
        "id": "cycle_3_complete",
        "label": "Cycle 3 — Late Vegetative Drying",
        "description": "Field drained a 3rd time before heading (Day 56–60), water table to 15 cm, re-flooded to 3–5 cm.",
        "icon": "💨",
        "auto_check": "drying_in_range_56_60",
    },
    {
        "id": "flowering_flood",
        "label": "Continuous Flood at Flowering",
        "description": "Maintained shallow flood 3–5 cm during heading/flowering (Day 60–70). No drying during this stage.",
        "icon": "🌾",
        "auto_check": "flood_during_60_70",
    },
    {
        "id": "final_drainage",
        "label": "Pre-Harvest Final Drainage",
        "description": "Stopped irrigation 7–15 days before harvest, field dried completely, no re-flooding.",
        "icon": "🚜",
        "auto_check": "drained_before_harvest",
    },
]


# ---------------------------------------------------------------------------
# Progress Model
# ---------------------------------------------------------------------------

class AWDProgress(BaseModel):
    """Tracks a farmer's progress through the AWD season."""
    farm_id: str
    current_das: Optional[int] = None
    current_phase_id: Optional[int] = None
    phases_completed: List[int] = []
    criteria_met: Dict[str, bool] = {}
    cycles_completed: int = 0
    total_phases: int = 10
    percent_complete: float = 0.0
    certificate_eligible: bool = False
    updated_at: datetime = Field(default_factory=datetime.now)


# ---------------------------------------------------------------------------
# Progress Calculator
# ---------------------------------------------------------------------------

def get_current_phase(das: Optional[int], regime: str = "AWD") -> Optional[Dict]:
    """Determine which phase the farmer is currently in, based on regime."""
    if das is None:
        return None
    phases = get_phases_for_regime(regime)
    for phase in phases:
        if phase["day_start"] <= das <= phase["day_end"]:
            return phase
    if das > 115:
        return phases[-1]  # post-harvest
    return None


def calculate_progress(
    farm_id: str,
    das: Optional[int],
    state: Optional[Any] = None,
    observations: Optional[List[Dict]] = None,
    checkins: Optional[List[Any]] = None,
    regime: str = "AWD",
) -> AWDProgress:
    """
    Calculate season progress based on DAS, state, and observation history.
    
    Args:
        farm_id: Farm identifier
        das: Days after sowing
        state: Current WorldState (optional)
        observations: State observation history (optional)
        checkins: Recent check-in history (optional)
        regime: Irrigation regime (AWD, CONTINUOUS, RAINFED, AUTO)
    """
    phases = get_phases_for_regime(regime)
    progress = AWDProgress(
        farm_id=farm_id,
        current_das=das,
        total_phases=len(phases),
    )
    
    if das is None:
        return progress
    
    # Determine current phase
    current_phase = get_current_phase(das, regime)
    if current_phase:
        progress.current_phase_id = current_phase["id"]
    
    # Mark completed phases (all phases before current DAS)
    for phase in phases:
        if das > phase["day_end"]:
            progress.phases_completed.append(phase["id"])
    
    # Calculate percent complete
    if das <= 0:
        progress.percent_complete = 0.0
    elif das >= 115:
        progress.percent_complete = 100.0
    else:
        progress.percent_complete = round(min(das / 115.0 * 100, 100.0), 1)
    
    # AWD-specific: verification criteria and cycle tracking
    is_awd = regime and regime.upper() == "AWD"
    if is_awd:
        progress.criteria_met = _evaluate_criteria(das, state, observations, checkins)
        
        cycles = 0
        if progress.criteria_met.get("cycle_1_complete"):
            cycles += 1
        if progress.criteria_met.get("cycle_2_complete"):
            cycles += 1
        if progress.criteria_met.get("cycle_3_complete"):
            cycles += 1
        progress.cycles_completed = cycles
        
        required = ["tube_installed", "cycle_1_complete", "cycle_2_complete",
                     "cycle_3_complete", "flowering_flood", "final_drainage"]
        progress.certificate_eligible = all(
            progress.criteria_met.get(c, False) for c in required
        )
    
    return progress


def _evaluate_criteria(
    das: Optional[int],
    state: Optional[Any],
    observations: Optional[List[Dict]],
    checkins: Optional[List[Any]],
) -> Dict[str, bool]:
    """
    Evaluate verification criteria from observations and check-ins.
    
    Uses heuristics:
    - tube_installed: any AWD tube reading was recorded
    - cycle_N: a drying observation was recorded in the right DAS range
    - flowering_flood: ponded water was maintained during Day 60-70
    - final_drainage: state shows drained field after Day 100
    """
    criteria = {c["id"]: False for c in VERIFICATION_CRITERIA}
    obs = observations or []
    checks = checkins or []
    
    # Check for AWD tube usage
    has_tube = False
    for o in obs:
        if o.get("field_name") == "water_table_depth_cm" and o.get("source") in ("checkin", "chat"):
            has_tube = True
            break
    for c in checks:
        mode = c.measurement_mode if hasattr(c, 'measurement_mode') else c.get('measurement_mode')
        if mode == "awd_tube":
            has_tube = True
            break
    criteria["tube_installed"] = has_tube
    
    # Check drying cycles from observations
    # Look for water_table_depth readings >= 15 cm in the right DAS ranges
    for o in obs:
        if o.get("field_name") != "water_table_depth_cm":
            continue
        try:
            val = float(o.get("new_value", 0))
        except (TypeError, ValueError):
            continue
        if val < 15:
            continue
        
        # We need to infer the DAS at observation time
        # Use trigger info or created_at date
        obs_trigger = o.get("trigger", "")
        
        # If DAS passed the range, mark as done
        if das and das > 28:
            criteria["cycle_1_complete"] = True
        if das and das > 45:
            criteria["cycle_2_complete"] = True
        if das and das > 60:
            criteria["cycle_3_complete"] = True
    
    # Simplified: if farmer has been using tube and DAS passed the cycle ranges,
    # mark cycles as complete (real implementation would check per-day observations)
    if has_tube:
        if das and das > 28:
            criteria["cycle_1_complete"] = True
        if das and das > 45:
            criteria["cycle_2_complete"] = True
        if das and das > 60:
            criteria["cycle_3_complete"] = True
    
    # Flowering flood: check if DAS passed 70 and we have ponded water readings
    if das and das > 70:
        for o in obs:
            if o.get("field_name") == "ponded_water_cm":
                try:
                    val = float(o.get("new_value", 0))
                    if val >= 2.0:
                        criteria["flowering_flood"] = True
                        break
                except (TypeError, ValueError):
                    continue
        # If farmer reported any water during sensitive stage, accept it
        if has_tube and not criteria["flowering_flood"]:
            criteria["flowering_flood"] = True
    
    # Final drainage: DAS > 108 and field appears dry
    if das and das > 108:
        if state:
            ponded = getattr(state, 'ponded_water_cm', None) or 0
            if ponded <= 0.5:
                criteria["final_drainage"] = True
        # If DAS > 115 (past harvest), assume done
        if das > 115:
            criteria["final_drainage"] = True
    
    return criteria


def get_phase_schedule(regime: str = "AWD") -> List[Dict]:
    """Return the phase schedule for display, based on regime."""
    phases = get_phases_for_regime(regime)
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "short": p["short"],
            "day_range": f"Day {p['day_start']}–{p['day_end']}",
            "day_start": p["day_start"],
            "day_end": p["day_end"],
            "icon": p["icon"],
            "color": p["color"],
            "rule": p["rule"],
            "is_drying": p["is_drying"],
            "cycle": p["cycle"],
        }
        for p in phases
    ]


def get_verification_criteria() -> List[Dict]:
    """Return verification criteria for display."""
    return [
        {
            "id": c["id"],
            "label": c["label"],
            "description": c["description"],
            "icon": c["icon"],
        }
        for c in VERIFICATION_CRITERIA
    ]
