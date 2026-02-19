"""Deterministic water balance simulator"""

from typing import Dict, Any
from .schemas import WorldState, WeatherSummary
from .config import BUND_HEIGHT_CM, DEFAULT_PARAMS, KC_BY_STAGE


class HydrologyCoreSimulator:
    """Deterministic daily water balance physics"""
    
    def __init__(self, params: Dict[str, float] = None):
        self.params = {**DEFAULT_PARAMS, **(params or {})}
    
    def step(
        self,
        state: WorldState,
        action: str,
        weather: WeatherSummary,
        params: Dict[str, float] = None
    ) -> WorldState:
        """One day forward simulation"""
        
        new_state = state.model_copy(deep=True)
        effective_params = {**self.params, **(params or {})}
        
        # Extract parameters
        percolation_rate = effective_params.get("percolation_mm_per_day", 5.0)
        infiltration_rate = effective_params.get("infiltration_mm_per_day", 10.0)
        runoff_factor = effective_params.get("runoff_factor", 0.2)
        effective_rain_factor = effective_params.get("effective_rain_factor", 0.8)
        
        # Get crop coefficient
        kc = KC_BY_STAGE.get(new_state.growth_stage or "unknown", 1.1)
        
        # Get bund height
        bund_height_cm = BUND_HEIGHT_CM[new_state.bund_height_class]
        
        # Action effects
        irrigation_mm = 0
        if action == "IRRIGATE":
            # Get refill target from params or use default
            target_cm = params.get("refill_target_cm", 4.0) if params else 4.0
            # Irrigate to bring ponded water to target
            needed_cm = max(0, target_cm - new_state.ponded_water_cm)
            irrigation_mm = needed_cm * 10  # cm to mm
        
        if action == "DRAIN":
            # Remove all ponded water
            new_state.ponded_water_cm = 0
        
        # Rain inputs
        rain_mm = weather.rain_last_24h_mm
        effective_rain_mm = rain_mm * effective_rain_factor
        runoff_mm = rain_mm * runoff_factor
        
        # ET calculation
        et0_mm = weather.et0_next_24h_mm or 5.0
        et_mm = et0_mm * kc
        
        # Infiltration (from ponded to root zone)
        current_ponded_mm = new_state.ponded_water_cm * 10
        infiltration_mm = min(current_ponded_mm, infiltration_rate)
        
        # Update ponded water (all in mm)
        ponded_mm = current_ponded_mm
        ponded_mm += irrigation_mm
        ponded_mm += effective_rain_mm
        ponded_mm -= runoff_mm
        
        # ET only from ponded water if present
        if ponded_mm > 0:
            et_from_ponded = min(ponded_mm, et_mm)
            ponded_mm -= et_from_ponded
            et_mm -= et_from_ponded  # Remaining ET comes from root zone
        
        ponded_mm -= infiltration_mm
        
        # Cap ponded water at bund height
        ponded_mm = max(0, min(ponded_mm, bund_height_cm * 10))
        new_state.ponded_water_cm = ponded_mm / 10
        
        # Update water table depth (simplified model)
        if new_state.water_table_depth_cm is not None:
            # Drying components
            drying_mm = et_mm + percolation_rate
            
            # Wetting components
            wetting_mm = infiltration_mm + (effective_rain_mm * 0.5)
            
            # Net change
            depth_change_mm = drying_mm - wetting_mm
            
            new_state.water_table_depth_cm += depth_change_mm / 10
            new_state.water_table_depth_cm = max(0, min(new_state.water_table_depth_cm, 60.0))
            
            # Update soil deficit index based on water table depth
            # 0 = saturated, 1 = very dry
            if new_state.water_table_depth_cm < 5:
                new_state.soil_deficit_index = 0.0
            elif new_state.water_table_depth_cm < 15:
                new_state.soil_deficit_index = (new_state.water_table_depth_cm - 5) / 10
            else:
                new_state.soil_deficit_index = min(1.0, 1.0 + (new_state.water_table_depth_cm - 15) / 30)
        
        # Update soil cracks based on water table depth
        if new_state.water_table_depth_cm is not None:
            if new_state.water_table_depth_cm < 10:
                new_state.soil_cracks = "none"
            elif new_state.water_table_depth_cm < 15:
                new_state.soil_cracks = "small"
            elif new_state.water_table_depth_cm < 20:
                new_state.soil_cracks = "visible"
            else:
                new_state.soil_cracks = "deep"
        
        return new_state
    
    def simulate_trajectory(
        self,
        initial_state: WorldState,
        actions: list,
        weather_forecast: list,
        params: Dict[str, float] = None
    ) -> list:
        """Simulate multiple days forward"""
        
        trajectory = [initial_state]
        current_state = initial_state
        
        for i, (action, weather) in enumerate(zip(actions, weather_forecast)):
            current_state = self.step(current_state, action, weather, params)
            trajectory.append(current_state)
        
        return trajectory
    
    def get_soil_params_by_type(self, soil_type: str) -> Dict[str, float]:
        """Get soil-specific hydraulic parameters"""
        
        soil_params = {
            "alluvial": {
                "percolation_mm_per_day": 4.0,
                "infiltration_mm_per_day": 12.0
            },
            "clay": {
                "percolation_mm_per_day": 2.0,
                "infiltration_mm_per_day": 6.0
            },
            "sandy": {
                "percolation_mm_per_day": 10.0,
                "infiltration_mm_per_day": 20.0
            },
            "acid_sulfate": {
                "percolation_mm_per_day": 3.0,
                "infiltration_mm_per_day": 8.0
            },
            "unknown": {
                "percolation_mm_per_day": 5.0,
                "infiltration_mm_per_day": 10.0
            }
        }
        
        return soil_params.get(soil_type, soil_params["unknown"])
