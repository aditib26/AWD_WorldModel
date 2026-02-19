from typing import Tuple, Dict, Any

try:
    from .farm_state import FarmState
except ImportError:
    from farm_state import FarmState


class AWDDecisionEngine:
    """Core AWD decision logic: feasibility, safety, action"""
    
    @staticmethod
    def check_feasibility(state: FarmState) -> Tuple[bool, str]:
        """Check if AWD is feasible given current conditions"""
        
        if state.soil.bunded_lowland is False:
            return False, "AWD requires a bunded paddy field that can hold water. Your field is not suitable for AWD."
        
        if state.weather.forecast_rain_next_7d_mm and state.weather.forecast_rain_next_7d_mm > 50:
            return False, f"High rainfall expected ({state.weather.forecast_rain_next_7d_mm}mm in next 7 days). AWD is not recommended during heavy monsoon."
        
        if state.soil.percolation_class == "high" or state.soil.texture_class == "sandy":
            return False, "Sandy/high percolation soils lose water too quickly for safe AWD. Consider continuous flooding."
        
        return True, "Field conditions are suitable for AWD practice."
    
    @staticmethod
    def check_safety(state: FarmState) -> Tuple[bool, str]:
        """Check if continuing AWD is safe for the crop"""
        
        stage = state.crop.growth_stage
        water_depth = state.water.water_table_cm_below_surface
        
        if stage == "flowering":
            if water_depth is not None and water_depth > 10:
                return False, "⚠️ CRITICAL: Flowering stage is highly sensitive to water stress. Water table should not go below 10cm. Irrigate immediately!"
        
        if stage == "grain_filling":
            if water_depth is not None and water_depth > 12:
                return False, "⚠️ Water stress during grain filling can reduce yield. Irrigate now."
        
        if state.observations.stress_symptoms_flag:
            return False, "⚠️ Crop is showing stress symptoms (leaf rolling, wilting). Stop drying and irrigate."
        
        if state.observations.cracking_level == "severe":
            return False, "Severe soil cracking detected. Risk of root damage. Irrigate immediately."
        
        if water_depth is not None and water_depth > 20:
            return False, "Water table too deep (>20cm). Excessive drying can harm roots and reduce yield. Irrigate now."
        
        return True, "Current drying level is safe for the crop stage."
    
    @staticmethod
    def recommend_action(state: FarmState) -> str:
        """Recommend specific irrigation action based on state"""
        
        depth = state.water.water_table_cm_below_surface
        stage = state.crop.growth_stage
        
        if depth is None:
            if state.water.standing_water_cm and state.water.standing_water_cm > 0:
                return "Standing water present. Continue monitoring as water level drops."
            return "Unable to provide recommendation without water level information."
        
        if stage == "flowering":
            if depth < 5:
                return "Water level good. Continue monitoring daily during flowering."
            elif depth <= 10:
                return "🔔 Prepare to irrigate within 1-2 days. Flowering stage needs careful monitoring."
            else:
                return "🚨 Irrigate NOW to 5cm standing water. Flowering is critical."
        
        if depth < 10:
            days_to_wait = int((15 - depth) / 2)
            return f"Continue drying. Check again in {days_to_wait} days or when water table reaches 15cm below surface."
        
        elif 10 <= depth < 15:
            return "🔔 Prepare for irrigation. Check water level daily. Irrigate when it reaches 15cm below surface."
        
        elif depth >= 15:
            standing_water_target = "5cm" if stage in ["tillering", "vegetative"] else "3cm"
            return f"🚨 Irrigate NOW. Refill to {standing_water_target} standing water. This completes one AWD cycle."
        
        return "Monitor water level daily and irrigate at 15cm depth."
    
    @staticmethod
    def get_full_advice(state: FarmState) -> Dict[str, Any]:
        """Complete AWD advisory with all checks"""
        
        feasible, feasibility_msg = AWDDecisionEngine.check_feasibility(state)
        if not feasible:
            return {
                "status": "not_feasible",
                "message": feasibility_msg,
                "recommendation": "Consider continuous shallow flooding instead of AWD.",
                "confidence": "high"
            }
        
        safe, safety_msg = AWDDecisionEngine.check_safety(state)
        if not safe:
            return {
                "status": "unsafe",
                "message": safety_msg,
                "recommendation": "Irrigate immediately to prevent yield loss.",
                "confidence": "high"
            }
        
        action = AWDDecisionEngine.recommend_action(state)
        
        return {
            "status": "ok",
            "message": safety_msg,
            "recommendation": action,
            "confidence": "high" if state.water.water_table_cm_below_surface is not None else "medium"
        }
    
    @staticmethod
    def estimate_water_savings(state: FarmState, cycles: int = 3) -> Dict[str, Any]:
        """Estimate water savings from AWD"""
        
        baseline_water_mm = 1200
        awd_reduction_pct = 0.25
        
        area_ha = state.farm.area_ha or 1.0
        
        water_saved_mm = baseline_water_mm * awd_reduction_pct
        water_saved_m3 = water_saved_mm * area_ha * 10
        
        return {
            "baseline_water_mm": baseline_water_mm,
            "awd_water_mm": baseline_water_mm - water_saved_mm,
            "water_saved_mm": water_saved_mm,
            "water_saved_m3": water_saved_m3,
            "water_saved_percent": awd_reduction_pct * 100,
            "expected_cycles": cycles
        }
    
    @staticmethod
    def estimate_emission_reduction(state: FarmState) -> Dict[str, Any]:
        """Estimate methane emission reduction from AWD"""
        
        area_ha = state.farm.area_ha or 1.0
        
        baseline_ch4_kg_per_ha = 200
        awd_reduction_pct = 0.48
        
        ch4_reduced_kg = baseline_ch4_kg_per_ha * awd_reduction_pct * area_ha
        co2_equivalent_kg = ch4_reduced_kg * 28
        
        return {
            "baseline_ch4_kg": baseline_ch4_kg_per_ha * area_ha,
            "awd_ch4_kg": baseline_ch4_kg_per_ha * (1 - awd_reduction_pct) * area_ha,
            "ch4_reduced_kg": ch4_reduced_kg,
            "co2_equivalent_kg": co2_equivalent_kg,
            "reduction_percent": awd_reduction_pct * 100
        }

    @staticmethod
    def predict_drying_rate(state: FarmState) -> Dict[str, Any]:
        """
        Predict how many days until the field needs irrigation (reaches -15cm)
        based on soil physics and weather.
        """
        # 1. Determine Percolation Rate (mm/day)
        # Clay holds water well (low percolation), Sandy drains fast (high)
        percolation_map = {
            "clay": 2.0,    # mm/day
            "loam": 5.0,
            "sandy": 12.0,
            "unknown": 4.0
        }
        
        # Normalize texture class key
        texture = (state.soil.texture_class or "unknown").lower()
        if "clay" in texture: texture = "clay"
        elif "sand" in texture: texture = "sandy"
        elif "loam" in texture: texture = "loam"
        else: texture = "unknown"
        
        percolation_rate = percolation_map.get(texture, 4.0)
        
        # 2. Determine Evapotranspiration (ET) (mm/day)
        # Hotter weather = faster drying
        avg_temp = state.weather.temp_avg or 30.0
        if avg_temp > 32:
            et_rate = 7.0  # Hot
        elif avg_temp < 25:
            et_rate = 4.0  # Cool
        else:
            et_rate = 5.5  # Moderate
            
        # 3. Total Daily Drawdown (cm/day)
        # (Percolation + ET) / 10 to convert mm -> cm
        daily_drawdown_cm = (percolation_rate + et_rate) / 10.0
        
        # 4. Calculate Days to Target (-15cm)
        current_level = state.water.water_table_cm_below_surface
        
        # If we have standing water (positive cm), treat as negative depth relative to surface for calculation
        # e.g. 5cm standing = -5cm depth. Target is +15cm depth.
        # But our state uses:
        # water_table_cm_below_surface (positive = below ground)
        # standing_water_cm (positive = above ground)
        
        if state.water.standing_water_cm and state.water.standing_water_cm > 0:
            current_effective_depth = -state.water.standing_water_cm
        elif current_level is not None:
            current_effective_depth = current_level
        else:
            return {"status": "unknown", "message": "Need water level to predict drying time."}
            
        target_depth = 15.0 # cm below surface
        
        if current_effective_depth >= target_depth:
            return {
                "status": "ready",
                "days_remaining": 0,
                "message": "Field is already dry enough. Irrigate now!"
            }
            
        cm_to_dry = target_depth - current_effective_depth
        days_remaining = cm_to_dry / daily_drawdown_cm
        
        return {
            "status": "predicting",
            "days_remaining": round(days_remaining, 1),
            "daily_drawdown_cm": round(daily_drawdown_cm, 2),
            "drying_rate_cm_per_day": round(daily_drawdown_cm, 2),
            "percolation_rate_mm": percolation_rate,
            "et_rate_mm": et_rate,
            "message": f"Based on your {texture} soil and weather, water drops about {daily_drawdown_cm} cm/day.",
            "reasoning": f"Based on your {texture} soil and weather, water drops about {daily_drawdown_cm} cm/day."
        }
