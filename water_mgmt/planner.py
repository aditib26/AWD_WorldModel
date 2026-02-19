"""MPC-lite planning engine"""

from typing import List, Dict, Any, Tuple
from datetime import date
from .schemas import WorldState, WeatherSummary, AdviceResponse, RationaleBullet, CounterfactualOutcome
from .hydrology import HydrologyCoreSimulator
from .resolver import PolicyResolver
from .config import PLANNING_HORIZON_DAYS, COST_WEIGHTS


class WaterManagementPlanner:
    """MPC-lite planning over short horizon"""
    
    def __init__(
        self,
        hydrology: HydrologyCoreSimulator,
        resolver: PolicyResolver,
        horizon_days: int = PLANNING_HORIZON_DAYS
    ):
        self.hydrology = hydrology
        self.resolver = resolver
        self.horizon = horizon_days
    
    def plan(
        self,
        state: WorldState,
        weather_forecast: List[WeatherSummary]
    ) -> AdviceResponse:
        """Select best action via simulation"""
        
        # Ensure we have enough forecast data
        if len(weather_forecast) < self.horizon:
            # Pad with last available forecast
            last_weather = weather_forecast[-1] if weather_forecast else WeatherSummary()
            weather_forecast = weather_forecast + [last_weather] * (self.horizon - len(weather_forecast))
        
        # Determine regime
        regime = self._infer_regime(state)
        if regime != state.regime:
            state = state.model_copy(deep=True)
            state.regime = regime
        
        # Get candidate actions
        actions = self._get_candidate_actions(state, regime)
        
        # Get effective parameters
        config = self.resolver.resolve_effective_config(state)
        params = self.resolver.get_regime_params(state)
        
        # Simulate each action
        results = []
        for action in actions:
            cost, trajectory = self._simulate_action(
                state, action, weather_forecast, regime, params
            )
            results.append({
                "action": action,
                "cost": cost,
                "trajectory": trajectory
            })
        
        # Select minimum cost
        results.sort(key=lambda x: x["cost"])
        best = results[0]
        second_best = results[1] if len(results) > 1 else None
        
        # Generate advice
        confidence = self._assess_confidence(state, best, regime, config)
        rationale = self._generate_rationale(state, best, regime, params)
        counterfactuals = self._generate_counterfactuals(best, second_best)
        next_question = self._next_question(state)
        risk_warnings = self._generate_warnings(state, best, regime)
        
        return AdviceResponse(
            farm_id=state.farm_id,
            advice_date=state.state_date,
            recommended_action=best["action"],
            target_description=self._action_description(best["action"], regime, params),
            confidence=confidence,
            rationale=rationale,
            counterfactuals=counterfactuals,
            next_observation_question=next_question,
            risk_warnings=risk_warnings,
            regime_used=regime,
            mode_used=state.mode
        )
    
    def _infer_regime(self, state: WorldState) -> str:
        """Infer regime from state"""
        if state.regime != "AUTO":
            return state.regime
        
        # Auto-infer based on conditions
        if not state.irrigation_access:
            return "RAINFED"
        
        if state.water_table_depth_cm is not None:
            # Has AWD tube measurement
            return "AWD"
        
        # Default to continuous
        return "CONTINUOUS"
    
    def _get_candidate_actions(self, state: WorldState, regime: str) -> List[str]:
        """Actions available for regime"""
        if regime == "RAINFED":
            return ["HOLD", "DRAIN", "ALERT_ONLY"]
        elif regime == "AWD":
            return ["IRRIGATE", "HOLD", "DRAIN"]
        elif regime == "CONTINUOUS":
            return ["IRRIGATE", "HOLD"]
        return ["HOLD"]
    
    def _simulate_action(
        self,
        state: WorldState,
        action: str,
        forecast: List[WeatherSummary],
        regime: str,
        params: Dict[str, Any]
    ) -> Tuple[float, List[WorldState]]:
        """Forward simulate and compute cost"""
        
        current = state.model_copy(deep=True)
        trajectory = [current]
        total_cost = 0.0
        
        for i, day_weather in enumerate(forecast[:self.horizon]):
            # Apply action on first day only
            day_action = action if i == 0 else "HOLD"
            
            # Step forward
            current = self.hydrology.step(current, day_action, day_weather, params)
            trajectory.append(current)
            
            # Compute daily cost
            cost = self._daily_cost(current, day_action, day_weather, regime, params)
            total_cost += cost
        
        return total_cost, trajectory
    
    def _daily_cost(
        self,
        state: WorldState,
        action: str,
        weather: WeatherSummary,
        regime: str,
        params: Dict[str, Any]
    ) -> float:
        """Cost function - lower is better"""
        cost = 0.0
        
        # 1. Crop stress penalty (stage-weighted)
        if regime == "AWD":
            trigger_depth = params.get("trigger_depth_cm", 15.0)
            
            # Penalty if water table too deep (dry stress)
            if state.water_table_depth_cm and state.water_table_depth_cm > trigger_depth:
                excess_depth = state.water_table_depth_cm - trigger_depth
                
                # Higher penalty for sensitive stages
                if state.growth_stage in ["panicle_initiation", "heading", "grain_filling"]:
                    cost += COST_WEIGHTS["stress_sensitive_stage"] * excess_depth
                else:
                    cost += COST_WEIGHTS["stress_normal_stage"] * excess_depth
            
            # CRITICAL: Heavy penalty for unnecessary irrigation when water is adequate
            # AWD handbook says: irrigate ONLY when water table >= 15cm trigger
            # If current water table is shallow (< trigger), DO NOT irrigate
            if action == "IRRIGATE" and state.water_table_depth_cm and state.water_table_depth_cm < trigger_depth:
                # Massive penalty to prevent early irrigation
                margin = trigger_depth - state.water_table_depth_cm
                # The more adequate the water (smaller margin), the bigger the penalty
                cost += 100.0 * (1.0 + margin / trigger_depth)  # Very high penalty
        
        elif regime == "CONTINUOUS":
            # Penalty if water too low
            min_ponding = params.get("min_ponding_cm", 2.0)
            if state.ponded_water_cm < min_ponding:
                deficit = min_ponding - state.ponded_water_cm
                cost += COST_WEIGHTS["stress_normal_stage"] * deficit
        
        # 2. Excess ponding penalty
        max_ponding = params.get("max_ponding_cm", 5.0)
        if state.ponded_water_cm > max_ponding:
            excess = state.ponded_water_cm - max_ponding
            cost += COST_WEIGHTS["excess_ponding"] * excess
        
        # 3. Base water use penalty
        if action == "IRRIGATE":
            cost += COST_WEIGHTS["water_use"]
        
        # 4. Unnecessary irrigation if rain forecast high
        if action == "IRRIGATE" and weather.rain_next_72h_mm > 20:
            cost += COST_WEIGHTS["unnecessary_irrigation_rain"]
        
        return cost
    
    def _assess_confidence(
        self,
        state: WorldState,
        best_result: Dict,
        regime: str,
        config: Dict
    ) -> str:
        """Determine confidence level"""
        
        confidence_score = 0
        
        # Factor 1: Measurement quality
        if state.water_table_depth_cm is not None:
            confidence_score += 3  # Numeric AWD tube measurement
        elif state.ponded_water_cm > 0:
            confidence_score += 2  # Ponded water observation
        else:
            confidence_score += 1  # Only qualitative
        
        # Factor 2: Weather availability
        if state.rain_next_72h_mm >= 0:
            confidence_score += 2
        else:
            confidence_score += 1
        
        # Factor 3: Rule source
        if state.mode == "handbook_only" or regime == "AWD":
            confidence_score += 2  # Handbook-grounded
        else:
            confidence_score += 1  # General rules
        
        # Factor 4: Growth stage known
        if state.growth_stage and state.growth_stage != "unknown":
            confidence_score += 1
        
        # Map score to confidence level
        if confidence_score >= 7:
            return "high"
        elif confidence_score >= 5:
            return "medium"
        else:
            return "low"
    
    def _generate_rationale(
        self,
        state: WorldState,
        best_result: Dict,
        regime: str,
        params: Dict
    ) -> List[RationaleBullet]:
        """Generate provenance-tagged rationale — deduplicated and relevant to chosen action"""
        rationale = []
        seen_texts = set()
        
        def add_unique(text, source_type, reference, confidence):
            key = text.lower().strip()
            if key not in seen_texts:
                seen_texts.add(key)
                rationale.append(RationaleBullet(
                    text=text, source_type=source_type,
                    reference=reference, confidence=confidence
                ))
        
        best_action = best_result["action"]
        
        # Get applicable rules
        hb_rules, gen_rules = self.resolver.get_all_applicable_rules(state)
        
        # Filter handbook rules: skip rules whose action contradicts the chosen action
        for rule in hb_rules:
            rule_action = rule.action.lower()
            # Skip contradictions
            if best_action == "IRRIGATE" and "stop" in rule_action:
                continue
            if best_action == "HOLD" and "trigger_irrigation" in rule_action:
                continue
            add_unique(
                self._format_rule_text(rule.action, rule.condition),
                "HANDBOOK", rule.json_path, "high"
            )
        
        # Add general rules (if not in handbook_only mode), also filtered
        if state.mode != "handbook_only":
            for rule in gen_rules:
                rule_action = rule.action.lower()
                if best_action == "IRRIGATE" and "stop" in rule_action:
                    continue
                if best_action == "HOLD" and "irrigate" in rule_action:
                    continue
                add_unique(
                    self._format_rule_text(rule.action, rule.condition),
                    "GENERAL", rule.reference_label, "medium"
                )
        
        # Add observation-based reasoning
        if best_action == "IRRIGATE":
            if regime == "AWD" and state.water_table_depth_cm:
                add_unique(
                    f"Water table depth at {state.water_table_depth_cm:.1f} cm",
                    "OBSERVATION", "field_measurement", "high"
                )
            if state.soil_cracks in ["visible", "deep"]:
                add_unique(
                    f"{state.soil_cracks.capitalize()} cracks observed in field",
                    "OBSERVATION", "field_observation", "high"
                )
        
        # Add weather-based reasoning
        if state.rain_next_72h_mm > 20 and best_action == "HOLD":
            add_unique(
                f"Heavy rain forecasted ({state.rain_next_72h_mm:.1f} mm in next 72 hours)",
                "WEATHER", "forecast_data", "medium"
            )
        
        return rationale
    
    def _format_rule_text(self, action: str, condition: str) -> str:
        """Format rule into readable text"""
        import re
        # Clean up common patterns
        text = action.replace("_", " ").strip()
        # Fix "refill to 3 to 5 cm" → "Refill to 3-5 cm"
        m = re.match(r'refill to (\d+\.?\d*) to (\d+\.?\d*) cm', text, re.IGNORECASE)
        if m:
            return f"Refill to {m.group(1)}-{m.group(2)} cm"
        return text.title()
    
    def _generate_counterfactuals(
        self,
        best: Dict,
        second_best: Dict
    ) -> List[CounterfactualOutcome]:
        """Generate what-if scenarios"""
        if not second_best:
            return []
        
        counterfactuals = []
        
        # Best action outcome
        best_final_state = best["trajectory"][-1]
        counterfactuals.append(CounterfactualOutcome(
            action=best["action"],
            outcome_summary=self._summarize_outcome(best_final_state, best["action"]),
            risk_level=self._assess_risk(best_final_state)
        ))
        
        # Second best outcome
        second_final_state = second_best["trajectory"][-1]
        counterfactuals.append(CounterfactualOutcome(
            action=second_best["action"],
            outcome_summary=self._summarize_outcome(second_final_state, second_best["action"]),
            risk_level=self._assess_risk(second_final_state)
        ))
        
        return counterfactuals
    
    def _summarize_outcome(self, final_state: WorldState, action: str) -> str:
        """Summarize predicted outcome"""
        parts = []
        
        if action == "IRRIGATE":
            parts.append(f"Field refilled to ~{final_state.ponded_water_cm:.1f} cm")
        elif action == "HOLD":
            if final_state.water_table_depth_cm:
                parts.append(f"Water table at ~{final_state.water_table_depth_cm:.1f} cm after {self.horizon} days")
            else:
                parts.append(f"Ponded water ~{final_state.ponded_water_cm:.1f} cm after {self.horizon} days")
        elif action == "DRAIN":
            parts.append(f"Field drained, water table at ~{final_state.water_table_depth_cm or 0:.1f} cm")
        
        return ", ".join(parts)
    
    def _assess_risk(self, final_state: WorldState) -> str:
        """Assess risk level of final state"""
        if final_state.water_table_depth_cm and final_state.water_table_depth_cm > 20:
            return "high"
        elif final_state.ponded_water_cm > 7:
            return "high"
        elif final_state.water_table_depth_cm and final_state.water_table_depth_cm > 15:
            return "medium"
        else:
            return "low"
    
    def _next_question(self, state: WorldState) -> str:
        """Generate next observation question"""
        if state.regime == "AWD":
            if state.water_table_depth_cm is not None:
                return "Check AWD tube depth tomorrow"
            else:
                return "Check for soil cracks tomorrow"
        elif state.regime == "CONTINUOUS":
            return "Check ponded water depth tomorrow"
        elif state.regime == "RAINFED":
            return "Check for rainfall and soil moisture tomorrow"
        
        return "Check field conditions tomorrow"
    
    def _generate_warnings(
        self,
        state: WorldState,
        best_result: Dict,
        regime: str
    ) -> List[str]:
        """Generate risk warnings"""
        warnings = []
        
        # Sensitive stage warnings
        if state.growth_stage in ["panicle_initiation", "heading"]:
            if state.water_table_depth_cm and state.water_table_depth_cm > 12:
                warnings.append(
                    f"⚠️ {state.growth_stage.replace('_', ' ').title()} stage is sensitive to water stress. Monitor closely."
                )
        
        # Heavy rain warning
        if state.rain_next_72h_mm > 30 and best_result["action"] == "IRRIGATE":
            warnings.append(
                f"⚠️ Heavy rain forecasted ({state.rain_next_72h_mm:.0f} mm). Consider delaying irrigation."
            )
        
        # Excess ponding warning
        final_state = best_result["trajectory"][-1]
        if final_state.ponded_water_cm > 6:
            warnings.append(
                "⚠️ Excess ponding may increase disease risk. Consider drainage if prolonged."
            )
        
        # Drought warning for rainfed
        if regime == "RAINFED" and state.rain_next_72h_mm < 5:
            warnings.append(
                "⚠️ Low rainfall expected. Rainfed crop may experience stress."
            )
        
        return warnings
    
    def _action_description(
        self,
        action: str,
        regime: str,
        params: Dict
    ) -> str:
        """Generate action description"""
        if action == "IRRIGATE":
            target = params.get("refill_target_cm", 4.0)
            if regime == "AWD":
                min_cm = params.get("refill_target_min_cm", 3.0)
                max_cm = params.get("refill_target_max_cm", 5.0)
                return f"Refill to {min_cm:.0f}-{max_cm:.0f} cm (shallow ponding)"
            else:
                return f"Irrigate to maintain ~{target:.0f} cm"
        
        elif action == "HOLD":
            return "Do not irrigate yet - monitor conditions"
        
        elif action == "DRAIN":
            return "Drain field to reduce ponding"
        
        elif action == "ALERT_ONLY":
            return "No irrigation available - monitor for stress"
        
        return action
