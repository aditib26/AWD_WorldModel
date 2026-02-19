from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple

try:
    from .farm_state import FarmState
    from .decision_logic import AWDDecisionEngine
except ImportError:
    from farm_state import FarmState
    from decision_logic import AWDDecisionEngine


Urgency = Literal["low", "medium", "high"]
WaterManagementMode = Literal["awd", "continuous_flooding", "rainfed"]


def _estimate_daily_drawdown_cm(state: FarmState) -> float:
    percolation_map = {
        "clay": 2.0,
        "loam": 5.0,
        "sandy": 12.0,
        "unknown": 4.0,
    }

    texture = (state.soil.texture_class or "unknown").lower()
    if "clay" in texture:
        texture = "clay"
    elif "sand" in texture:
        texture = "sandy"
    elif "loam" in texture:
        texture = "loam"
    else:
        texture = "unknown"

    percolation_rate = percolation_map.get(texture, 4.0)

    avg_temp = state.weather.temp_avg or 30.0
    if avg_temp > 32:
        et_rate = 7.0
    elif avg_temp < 25:
        et_rate = 4.0
    else:
        et_rate = 5.5

    return (percolation_rate + et_rate) / 10.0


class WaterManagementStrategy:
    mode: WaterManagementMode

    def check_feasibility(self, farm_state: FarmState) -> Dict[str, Any]:
        raise NotImplementedError

    def check_safety(self, farm_state: FarmState) -> Dict[str, Any]:
        raise NotImplementedError

    def recommend_action(self, farm_state: FarmState, weather: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        raise NotImplementedError

    def predict(self, farm_state: FarmState, weather: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        raise NotImplementedError


class AWDStrategy(WaterManagementStrategy):
    mode: WaterManagementMode = "awd"

    def check_feasibility(self, farm_state: FarmState) -> Dict[str, Any]:
        feasible, msg = AWDDecisionEngine.check_feasibility(farm_state)
        return {"feasible": feasible, "reasons": [msg]}

    def check_safety(self, farm_state: FarmState) -> Dict[str, Any]:
        safe, msg = AWDDecisionEngine.check_safety(farm_state)
        urgency: Urgency = "low" if safe else "high"
        return {"safe": safe, "warnings": [] if safe else [msg], "urgency": urgency}

    def recommend_action(self, farm_state: FarmState, weather: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        advice = AWDDecisionEngine.get_full_advice(farm_state)

        urgency: Urgency = "low"
        if advice.get("status") in {"unsafe"}:
            urgency = "high"
        elif "🔔" in (advice.get("recommendation") or ""):
            urgency = "medium"
        elif "🚨" in (advice.get("recommendation") or ""):
            urgency = "high"

        return {
            "action": advice.get("recommendation", ""),
            "reasoning": advice.get("message", ""),
            "urgency": urgency,
            "recommended_targets": {},
        }

    def predict(self, farm_state: FarmState, weather: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return AWDDecisionEngine.predict_drying_rate(farm_state)


class ContinuousFloodingStrategy(WaterManagementStrategy):
    mode: WaterManagementMode = "continuous_flooding"

    TARGET_MIN_CM = 3.0
    TARGET_MAX_CM = 7.0
    TARGET_IDEAL_CM = 5.0
    HEAVY_RAIN_7D_MM = 50.0

    def check_feasibility(self, farm_state: FarmState) -> Dict[str, Any]:
        if farm_state.soil.bunded_lowland is False:
            return {
                "feasible": False,
                "reasons": [
                    "Continuous flooding generally requires a bunded field that can hold shallow standing water."
                ],
            }

        return {"feasible": True, "reasons": ["Continuous flooding is generally feasible in your field."]}

    def check_safety(self, farm_state: FarmState) -> Dict[str, Any]:
        warnings: List[str] = []
        urgency: Urgency = "low"

        stage = (farm_state.crop.growth_stage or "").lower()
        standing = farm_state.water.standing_water_cm
        rain_7d = farm_state.weather.forecast_rain_next_7d_mm

        safe = True

        if standing is not None:
            if stage == "flowering" and standing < 1:
                safe = False
                urgency = "high"
                warnings.append(
                    "Standing water is very low during flowering. Continuous flooding usually needs shallow water to avoid stress."
                )
            elif standing < self.TARGET_MIN_CM:
                urgency = "medium"
                warnings.append("Standing water is below the typical target band (3–7 cm).")

            if standing > 15:
                urgency = "medium" if urgency != "high" else urgency
                warnings.append(
                    "Standing water is very deep. Deep water can increase lodging risk and may affect crop health."
                )

            if rain_7d is not None and rain_7d >= self.HEAVY_RAIN_7D_MM and standing > self.TARGET_MAX_CM:
                urgency = "medium" if urgency != "high" else urgency
                warnings.append(
                    "Heavy rainfall is expected soon and standing water is already high. Prepare for overflow / drainage."
                )

        else:
            depth_below = farm_state.water.water_table_cm_below_surface
            if depth_below is not None and depth_below >= 10:
                urgency = "medium"
                warnings.append(
                    "No standing-water measurement provided. Water table is quite deep below surface; flooding may not be maintained."
                )

        return {"safe": safe, "warnings": warnings, "urgency": urgency}

    def recommend_action(self, farm_state: FarmState, weather: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        stage = (farm_state.crop.growth_stage or "").lower()
        standing = farm_state.water.standing_water_cm
        depth_below = farm_state.water.water_table_cm_below_surface
        rain_7d = farm_state.weather.forecast_rain_next_7d_mm

        if stage == "maturity":
            return {
                "action": "Consider gradual drainage as you approach harvest.",
                "reasoning": "Fields are often drained near maturity to support harvest operations.",
                "urgency": "low",
                "recommended_targets": {},
            }

        if standing is not None:
            if standing < self.TARGET_MIN_CM:
                return {
                    "action": f"Add water to raise standing water to ~{self.TARGET_IDEAL_CM:.0f} cm (target band {self.TARGET_MIN_CM:.0f}–{self.TARGET_MAX_CM:.0f} cm).",
                    "reasoning": "Continuous flooding aims to maintain shallow standing water; low water increases stress risk.",
                    "urgency": "high" if stage == "flowering" else "medium",
                    "recommended_targets": {"standing_water_cm_target": self.TARGET_IDEAL_CM},
                }

            if standing > self.TARGET_MAX_CM and rain_7d is not None and rain_7d >= self.HEAVY_RAIN_7D_MM:
                return {
                    "action": "Prepare drainage / overflow outlets to avoid deep water after expected heavy rain.",
                    "reasoning": "Deep water plus heavy rainfall can cause overflow and crop damage.",
                    "urgency": "medium",
                    "recommended_targets": {"standing_water_cm_target": self.TARGET_IDEAL_CM},
                }

            return {
                "action": "Maintain current water level and monitor.",
                "reasoning": f"Standing water is within the typical target band ({self.TARGET_MIN_CM:.0f}–{self.TARGET_MAX_CM:.0f} cm).",
                "urgency": "low",
                "recommended_targets": {"standing_water_cm_target": self.TARGET_IDEAL_CM},
            }

        if depth_below is not None:
            return {
                "action": f"If you are practicing continuous flooding, add water until you see ~{self.TARGET_IDEAL_CM:.0f} cm standing water.",
                "reasoning": "You provided water-table depth but not standing-water depth. Continuous flooding guidance is strongest with standing-water measurements.",
                "urgency": "medium",
                "recommended_targets": {"standing_water_cm_target": self.TARGET_IDEAL_CM},
            }

        return {
            "action": "Share your standing water depth (cm) or water table depth to get a recommendation.",
            "reasoning": "Continuous flooding decisions depend on current water depth.",
            "urgency": "low",
            "recommended_targets": {},
        }

    def predict(self, farm_state: FarmState, weather: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        standing = farm_state.water.standing_water_cm
        if standing is None:
            return {
                "status": "unknown",
                "message": "Need standing water (cm) to predict when you may fall below the target band.",
            }

        daily_drawdown_cm = _estimate_daily_drawdown_cm(farm_state)

        if standing <= self.TARGET_MIN_CM:
            return {
                "status": "ready",
                "days_remaining": 0,
                "message": "Standing water is already at/below the minimum target. Add water to maintain flooding.",
                "drying_rate_cm_per_day": round(daily_drawdown_cm, 2),
            }

        cm_to_min = standing - self.TARGET_MIN_CM
        days_remaining = cm_to_min / max(daily_drawdown_cm, 0.1)

        return {
            "status": "predicting",
            "days_remaining": round(days_remaining, 1),
            "daily_drawdown_cm": round(daily_drawdown_cm, 2),
            "drying_rate_cm_per_day": round(daily_drawdown_cm, 2),
            "message": f"At current conditions, standing water may drop below {self.TARGET_MIN_CM:.0f} cm in about {days_remaining:.1f} days.",
            "reasoning": "Estimated from soil texture and temperature.",
        }


class RainfedStrategy(WaterManagementStrategy):
    mode: WaterManagementMode = "rainfed"

    LOW_RAIN_7D_MM = 10.0
    HIGH_RAIN_7D_MM = 80.0

    def check_feasibility(self, farm_state: FarmState) -> Dict[str, Any]:
        return {
            "feasible": True,
            "reasons": [
                "Rainfed management focuses on rainfall timing and risk management rather than scheduled irrigation."
            ],
        }

    def check_safety(self, farm_state: FarmState) -> Dict[str, Any]:
        warnings: List[str] = []
        urgency: Urgency = "low"

        stage = (farm_state.crop.growth_stage or "").lower()
        rain_7d = farm_state.weather.forecast_rain_next_7d_mm

        safe = True

        if rain_7d is not None:
            if rain_7d < self.LOW_RAIN_7D_MM and stage in {"panicle_initiation", "flowering"}:
                safe = False
                urgency = "high"
                warnings.append(
                    "Very low rain expected during a water-sensitive stage. High drought stress risk."
                )
            elif rain_7d < self.LOW_RAIN_7D_MM:
                urgency = "medium"
                warnings.append("Very low rain expected over the next 7 days. Watch for drought stress.")

            if rain_7d >= self.HIGH_RAIN_7D_MM:
                urgency = "medium" if urgency != "high" else urgency
                warnings.append("Very high rain expected over the next 7 days. Flooding risk may increase.")

        return {"safe": safe, "warnings": warnings, "urgency": urgency}

    def recommend_action(self, farm_state: FarmState, weather: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        stage = (farm_state.crop.growth_stage or "").lower()
        rain_7d = farm_state.weather.forecast_rain_next_7d_mm
        irrigation_access = getattr(farm_state.farm, "irrigation_access", None)

        if rain_7d is None:
            return {
                "action": "Monitor rainfall and field moisture closely.",
                "reasoning": "Rain forecast is not available yet; rainfed guidance depends on expected rainfall.",
                "urgency": "low",
                "recommended_targets": {},
            }

        if rain_7d < self.LOW_RAIN_7D_MM and stage in {"panicle_initiation", "flowering"}:
            if irrigation_access is True:
                return {
                    "action": "Consider supplemental irrigation if possible, and conserve soil moisture (mulch, reduce cracking).",
                    "reasoning": "Low rainfall is expected during a critical stage; yield risk is higher.",
                    "urgency": "high",
                    "recommended_targets": {},
                }

            return {
                "action": "Conserve moisture (mulch/weed control), monitor for stress, and seek any emergency water options if available.",
                "reasoning": "Low rainfall is expected during a critical stage. Without irrigation access, focus on conserving moisture and early warning.",
                "urgency": "high",
                "recommended_targets": {},
            }

        if rain_7d >= self.HIGH_RAIN_7D_MM:
            return {
                "action": "Prepare drainage and protect field bunds; monitor waterlogging after heavy rain.",
                "reasoning": "High rainfall forecast increases flooding and lodging risk.",
                "urgency": "medium",
                "recommended_targets": {},
            }

        if rain_7d < self.LOW_RAIN_7D_MM:
            if irrigation_access is True:
                return {
                    "action": "Monitor closely; consider light supplemental irrigation if stress appears.",
                    "reasoning": "Rainfall is expected to be low; respond early if stress symptoms appear.",
                    "urgency": "medium",
                    "recommended_targets": {},
                }

            return {
                "action": "Monitor closely and conserve moisture (mulch/weed control).",
                "reasoning": "Rainfall is expected to be low; focus on moisture conservation.",
                "urgency": "medium",
                "recommended_targets": {},
            }

        return {
            "action": "Monitor field conditions; no urgent water action needed based on forecast.",
            "reasoning": "Rainfall forecast looks adequate in the near term.",
            "urgency": "low",
            "recommended_targets": {},
        }

    def predict(self, farm_state: FarmState, weather: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        stage = (farm_state.crop.growth_stage or "").lower()
        rain_7d = farm_state.weather.forecast_rain_next_7d_mm

        if rain_7d is None:
            return {"status": "unknown", "message": "Need rainfall forecast to estimate rainfed risk."}

        drought_risk = 0
        if rain_7d < self.LOW_RAIN_7D_MM:
            drought_risk = 80
        elif rain_7d < 20:
            drought_risk = 50
        else:
            drought_risk = 20

        if stage in {"panicle_initiation", "flowering"}:
            drought_risk = min(100, drought_risk + 20)
        elif stage in {"grain_filling"}:
            drought_risk = min(100, drought_risk + 10)

        flood_risk = 0
        if rain_7d >= self.HIGH_RAIN_7D_MM:
            flood_risk = 80
        elif rain_7d >= 50:
            flood_risk = 50
        else:
            flood_risk = 20

        stress_risk_score = max(drought_risk, flood_risk)

        return {
            "status": "ok",
            "rain_forecast_7d_mm": rain_7d,
            "drought_risk_score": drought_risk,
            "flood_risk_score": flood_risk,
            "water_stress_risk_score": stress_risk_score,
            "message": "Rainfed risk estimated from 7-day rain forecast and crop stage.",
        }


def get_strategy(mode: Optional[str]) -> WaterManagementStrategy:
    normalized = (mode or "awd").strip().lower()

    if normalized == "continuous_flooding":
        return ContinuousFloodingStrategy()
    if normalized == "rainfed":
        return RainfedStrategy()

    return AWDStrategy()


class MultiTechniqueDecisionEngine:
    def _get_mode(self, state: FarmState) -> str:
        management = getattr(state, "management", None)
        mode = getattr(management, "mode", None)
        return (mode or "awd")

    def _get_strategy_for_state(self, state: FarmState) -> WaterManagementStrategy:
        return get_strategy(self._get_mode(state))

    def check_feasibility(self, state: FarmState) -> Tuple[bool, str]:
        strategy = self._get_strategy_for_state(state)
        result = strategy.check_feasibility(state)
        feasible = bool(result.get("feasible"))
        reasons = result.get("reasons") or []
        if reasons:
            return feasible, str(reasons[0])
        return feasible, "Feasible." if feasible else "Not feasible."

    def check_safety(self, state: FarmState) -> Tuple[bool, str]:
        strategy = self._get_strategy_for_state(state)
        result = strategy.check_safety(state)
        safe = bool(result.get("safe"))
        warnings = result.get("warnings") or []
        if warnings:
            return safe, str(warnings[0])
        return safe, "Current conditions look safe."

    def get_full_advice(self, state: FarmState) -> Dict[str, Any]:
        strategy = self._get_strategy_for_state(state)
        mode = self._get_mode(state)

        feasibility = strategy.check_feasibility(state)
        if not feasibility.get("feasible"):
            reasons = feasibility.get("reasons") or []
            msg = " ".join([str(r) for r in reasons if r]) or "Technique is not feasible for the current field conditions."
            recommendation = "Consider switching techniques or improving field infrastructure (bunds/drainage)."
            if mode == "awd":
                recommendation = "Consider continuous shallow flooding instead of AWD."

            return {
                "status": "not_feasible",
                "message": msg,
                "recommendation": recommendation,
                "confidence": "high",
                "mode": mode,
            }

        safety = strategy.check_safety(state)
        safety_warnings = safety.get("warnings") or []
        safe = bool(safety.get("safe"))

        rec = strategy.recommend_action(state)
        action = rec.get("action") or ""
        reasoning = rec.get("reasoning") or ""

        if not safe:
            msg = " ".join([str(w) for w in safety_warnings if w]) or "Unsafe conditions detected."
            if reasoning:
                msg = f"{msg} {reasoning}".strip()
            return {
                "status": "unsafe",
                "message": msg,
                "recommendation": action,
                "confidence": "high",
                "mode": mode,
                "urgency": safety.get("urgency", "high"),
            }

        msg = reasoning or (str(safety_warnings[0]) if safety_warnings else "Current conditions look safe.")
        return {
            "status": "ok",
            "message": msg,
            "recommendation": action,
            "confidence": "high",
            "mode": mode,
            "urgency": rec.get("urgency", "low"),
        }

    def predict_drying_rate(self, state: FarmState) -> Dict[str, Any]:
        strategy = self._get_strategy_for_state(state)
        result = strategy.predict(state)
        if isinstance(result, dict) and "mode" not in result:
            result = {**result, "mode": self._get_mode(state)}
        return result

    def estimate_water_savings(self, state: FarmState, cycles: int = 3) -> Dict[str, Any]:
        mode = self._get_mode(state)
        if mode != "awd":
            return {
                "baseline_water_mm": None,
                "awd_water_mm": None,
                "water_saved_mm": None,
                "water_saved_m3": None,
                "water_saved_percent": 0.0,
                "expected_cycles": cycles,
            }
        return AWDDecisionEngine.estimate_water_savings(state, cycles=cycles)

    def estimate_emission_reduction(self, state: FarmState) -> Dict[str, Any]:
        mode = self._get_mode(state)
        if mode != "awd":
            return {
                "baseline_ch4_kg": None,
                "awd_ch4_kg": None,
                "ch4_reduced_kg": None,
                "co2_equivalent_kg": None,
                "reduction_percent": 0.0,
            }
        return AWDDecisionEngine.estimate_emission_reduction(state)
