"""General agronomic rules (non-handbook)"""

from typing import List, Dict, Any
from pydantic import BaseModel
from .schemas import WorldState


class GeneralRule(BaseModel):
    """Rule from general agronomic practice"""
    rule_id: str
    condition: str
    action: str
    source_type: str = "GENERAL"
    reference_label: str
    confidence: str = "medium"


class GeneralRuleSet:
    """Conservative agronomic defaults for gaps"""
    
    def __init__(self):
        self.rules = self._define_rules()
    
    def _define_rules(self) -> List[GeneralRule]:
        """Define general practice rules"""
        return [
            GeneralRule(
                rule_id="continuous_baseline",
                condition="regime=CONTINUOUS and ponded_water_cm < 2",
                action="irrigate_to_maintain_shallow_ponding",
                reference_label="Traditional shallow flooding practice",
                confidence="medium"
            ),
            GeneralRule(
                rule_id="continuous_maintain",
                condition="regime=CONTINUOUS and ponded_water_cm >= 2 and ponded_water_cm <= 5",
                action="hold_current_level",
                reference_label="Traditional shallow flooding practice",
                confidence="medium"
            ),
            GeneralRule(
                rule_id="sensitive_stage_buffer",
                condition="growth_stage in [panicle_initiation, heading] and water_table_depth > 10",
                action="reduce_drying_tolerance_buffer",
                reference_label="General stress avoidance principle",
                confidence="medium"
            ),
            GeneralRule(
                rule_id="rainfed_constraint",
                condition="irrigation_access=false",
                action="no_irrigation_only_alerts",
                reference_label="Rainfed system constraint",
                confidence="high"
            ),
            GeneralRule(
                rule_id="heavy_rain_delay",
                condition="rain_next_72h_mm > 20 and action=IRRIGATE",
                action="consider_delaying_irrigation",
                reference_label="Water use efficiency principle",
                confidence="medium"
            ),
            GeneralRule(
                rule_id="early_establishment_shallow",
                condition="growth_stage=seedling and ponded_water_cm > 5",
                action="avoid_deep_flooding_early",
                reference_label="Seedling establishment practice",
                confidence="medium"
            ),
            GeneralRule(
                rule_id="maturity_drydown",
                condition="growth_stage=maturity",
                action="prepare_harvest_drying",
                reference_label="Pre-harvest drying practice",
                confidence="medium"
            ),
            GeneralRule(
                rule_id="drainage_disease_prevention",
                condition="ponded_water_cm > 7 and days_ponded > 7",
                action="consider_drainage_for_disease_prevention",
                reference_label="Disease management principle",
                confidence="low"
            ),
            GeneralRule(
                rule_id="no_tube_conservative",
                condition="water_table_depth_cm is None and soil_cracks in [visible, deep]",
                action="irrigate_if_no_measurement_but_cracks_visible",
                reference_label="Conservative field observation-based practice",
                confidence="medium"
            )
        ]
    
    def get_applicable_rules(self, state: WorldState) -> List[GeneralRule]:
        """Return rules matching current state"""
        applicable = []
        
        for rule in self.rules:
            if self._evaluate_condition(rule.condition, state):
                applicable.append(rule)
        
        return applicable
    
    def _evaluate_condition(self, condition: str, state: WorldState) -> bool:
        """Evaluate if condition matches state"""
        import re
        
        # Split on ' and ' to evaluate each sub-condition
        parts = [p.strip() for p in condition.split(" and ")]
        
        for part in parts:
            part_lower = part.lower().strip()
            
            if part_lower == "regime=continuous":
                if state.regime != "CONTINUOUS":
                    return False
            
            elif part_lower == "regime=rainfed":
                if state.regime != "RAINFED":
                    return False
            
            elif part_lower == "irrigation_access=false":
                if state.irrigation_access:
                    return False
            
            elif "ponded_water_cm" in part_lower:
                # Handle >=, <=, >, < operators
                m = re.search(r'ponded_water_cm\s*(>=|<=|>|<)\s*([\d.]+)', part_lower)
                if m:
                    op, val = m.group(1), float(m.group(2))
                    pw = state.ponded_water_cm if state.ponded_water_cm is not None else 0.0
                    if op == '>=' and not (pw >= val): return False
                    elif op == '<=' and not (pw <= val): return False
                    elif op == '>' and not (pw > val): return False
                    elif op == '<' and not (pw < val): return False
                else:
                    return False
            
            elif "water_table_depth" in part_lower:
                m = re.search(r'water_table_depth(?:_cm)?\s*(>=|<=|>|<)\s*([\d.]+)', part_lower)
                if m:
                    op, val = m.group(1), float(m.group(2))
                    wt = state.water_table_depth_cm
                    if wt is None:
                        return False
                    if op == '>=' and not (wt >= val): return False
                    elif op == '<=' and not (wt <= val): return False
                    elif op == '>' and not (wt > val): return False
                    elif op == '<' and not (wt < val): return False
                elif "is none" in part_lower:
                    if state.water_table_depth_cm is not None:
                        return False
                else:
                    return False
            
            elif part_lower.startswith("growth_stage="):
                stage = part_lower.split("=")[1].strip()
                if state.growth_stage != stage:
                    return False
            
            elif "growth_stage in" in part_lower:
                # Extract stages from bracket list
                stages = re.findall(r'[\w]+', part_lower.split("in")[1])
                if state.growth_stage not in stages:
                    return False
            
            elif "soil_cracks in" in part_lower:
                values = re.findall(r'[\w]+', part_lower.split("in")[1])
                if state.soil_cracks not in values:
                    return False
            
            elif "soil_cracks=" in part_lower:
                expected = part_lower.split("=")[1].strip()
                if state.soil_cracks != expected:
                    return False
            
            elif "rain_next_72h_mm" in part_lower:
                m = re.search(r'rain_next_72h_mm\s*(>=|<=|>|<)\s*([\d.]+)', part_lower)
                if m:
                    op, val = m.group(1), float(m.group(2))
                    rain = state.rain_next_72h_mm if state.rain_next_72h_mm is not None else 0.0
                    if op == '>' and not (rain > val): return False
                    elif op == '>=' and not (rain >= val): return False
                    elif op == '<' and not (rain < val): return False
                    elif op == '<=' and not (rain <= val): return False
                else:
                    return False
            
            elif "action=" in part_lower:
                # Meta-condition — skip, handled by rationale filter
                pass
            
            elif "days_ponded" in part_lower:
                # Not tracked in current state, skip rule
                return False
            
            else:
                # Unknown condition — don't match
                return False
        
        return True
    
    def get_continuous_flooding_target(self) -> float:
        """Default target for continuous flooding"""
        return 3.0  # cm
    
    def get_stress_buffer(self, growth_stage: str) -> float:
        """Additional buffer for sensitive stages"""
        sensitive_stages = ["panicle_initiation", "heading", "grain_filling"]
        if growth_stage in sensitive_stages:
            return 5.0  # Reduce acceptable drying by 5cm
        return 0.0
