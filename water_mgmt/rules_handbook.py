"""Handbook-grounded rules and thresholds"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from .schemas import WorldState
from .config import HANDBOOK_PATH


class HandbookRule(BaseModel):
    """Single rule from handbook"""
    rule_id: str
    condition: str
    action: str
    source_type: str = "HANDBOOK"
    json_path: str
    page_ref: Optional[str] = None
    confidence: str = "high"


class HandbookRuleSet:
    """Load and apply handbook-grounded rules"""
    
    def __init__(self, handbook_path: Path = HANDBOOK_PATH):
        self.handbook_path = handbook_path
        self.rules: List[HandbookRule] = []
        self.config: Dict[str, Any] = {}
        
        if handbook_path.exists():
            self._load_from_json()
        else:
            print(f"Warning: Handbook not found at {handbook_path}, using defaults")
            self._load_defaults()
    
    def _load_from_json(self):
        """Extract AWD rules and config from handbook JSON"""
        
        with open(self.handbook_path, 'r') as f:
            handbook_data = json.load(f)
        
        # Extract AWD-specific configuration
        # This searches the handbook structure for AWD content
        awd_config = self._extract_awd_config(handbook_data)
        
        if awd_config:
            self.config = awd_config
        else:
            print("Warning: No AWD configuration found in handbook, using defaults")
            self._load_defaults()
        
        # Build rules from config
        self._build_rules_from_config()
    
    def _extract_awd_config(self, handbook_data: Dict) -> Optional[Dict[str, Any]]:
        """Extract AWD configuration from handbook metadata"""
        
        # Default config
        config = {
            "awd_trigger_depth_cm": 15.0,
            "refill_target_min_cm": 3.0,
            "refill_target_max_cm": 5.0,
            "max_ponding_cm": 5.0,
            "sensitive_stages": ["panicle_initiation", "heading", "flowering", "grain_filling"],
            "pre_harvest_stop_days_min": 7,
            "pre_harvest_stop_days_max": 15
        }
        
        # Search for AWD section with metadata
        sections = handbook_data.get("sections", [])
        for section in sections:
            # Check if this is the AWD section
            title = section.get("title", "").lower()
            if "awd" in title or "alternate wetting" in title or "water management" in title:
                metadata = section.get("metadata", {})
                
                # Extract structured attributes
                if metadata.get("type") == "practice" and metadata.get("name") == "AWD":
                    attributes = metadata.get("attributes", {})
                    
                    if "threshold_depth_cm" in attributes:
                        config["awd_trigger_depth_cm"] = float(attributes["threshold_depth_cm"])
                    
                    if "reflood_depth_cm_min" in attributes:
                        config["refill_target_min_cm"] = float(attributes["reflood_depth_cm_min"])
                    
                    if "reflood_depth_cm_max" in attributes:
                        config["refill_target_max_cm"] = float(attributes["reflood_depth_cm_max"])
                        config["max_ponding_cm"] = float(attributes["reflood_depth_cm_max"])
                    
                    if "final_drydown_days_before_harvest_min" in attributes:
                        config["pre_harvest_stop_days_min"] = int(attributes["final_drydown_days_before_harvest_min"])
                    
                    if "final_drydown_days_before_harvest_max" in attributes:
                        config["pre_harvest_stop_days_max"] = int(attributes["final_drydown_days_before_harvest_max"])
                    
                    print(f"✓ Loaded AWD config from handbook: trigger={config['awd_trigger_depth_cm']}cm, refill={config['refill_target_min_cm']}-{config['refill_target_max_cm']}cm")
                    return config
        
        # If not found in metadata, search text content
        print("⚠ AWD metadata not found, using defaults")
        return config
    
    def _load_defaults(self):
        """Load default AWD configuration"""
        self.config = {
            "awd_trigger_depth_cm": 15.0,
            "refill_target_min_cm": 3.0,
            "refill_target_max_cm": 5.0,
            "max_ponding_cm": 5.0,
            "sensitive_stages": ["panicle_initiation", "heading"],
            "pre_harvest_stop_days_min": 7,
            "pre_harvest_stop_days_max": 15
        }
    
    def _build_rules_from_config(self):
        """Build rule objects from configuration"""
        
        self.rules = [
            HandbookRule(
                rule_id="awd_trigger_depth",
                condition=f"regime=AWD and water_table_depth_cm >= {self.config['awd_trigger_depth_cm']}",
                action="trigger_irrigation",
                json_path="awd_section.irrigation_trigger",
                confidence="high"
            ),
            HandbookRule(
                rule_id="awd_trigger_cracks",
                condition="regime=AWD and soil_cracks in ['visible', 'deep']",
                action="trigger_irrigation",
                json_path="awd_section.irrigation_trigger",
                confidence="high"
            ),
            HandbookRule(
                rule_id="awd_refill_target",
                condition="regime=AWD and action=IRRIGATE",
                action=f"refill_to_{self.config['refill_target_min_cm']}_to_{self.config['refill_target_max_cm']}_cm",
                json_path="awd_section.refill_target",
                confidence="high"
            ),
            HandbookRule(
                rule_id="max_ponding_limit",
                condition=f"ponded_water_cm > {self.config['max_ponding_cm']}",
                action="avoid_excess_ponding",
                json_path="awd_section.shallow_water",
                confidence="high"
            ),
            HandbookRule(
                rule_id="sensitive_stage_protection",
                condition=f"growth_stage in {self.config['sensitive_stages']}",
                action="reduce_stress_tolerance",
                json_path="awd_section.stage_management",
                confidence="high"
            ),
            HandbookRule(
                rule_id="pre_harvest_drydown",
                condition=f"days_to_harvest < {self.config['pre_harvest_stop_days_max']}",
                action="stop_irrigation",
                json_path="awd_section.pre_harvest",
                confidence="high"
            )
        ]
    
    def get_applicable_rules(self, state: WorldState) -> List[HandbookRule]:
        """Return rules matching current state"""
        applicable = []
        
        for rule in self.rules:
            if self._evaluate_condition(rule.condition, state):
                applicable.append(rule)
        
        return applicable
    
    def _evaluate_condition(self, condition: str, state: WorldState) -> bool:
        """Simple condition evaluator"""
        
        # Split on 'and' to evaluate each sub-condition
        parts = [p.strip() for p in condition.split(" and ")]
        
        for part in parts:
            if part == f"regime=AWD":
                if state.regime != "AWD":
                    return False
            
            elif "water_table_depth_cm >=" in part:
                threshold = float(part.split(">=")[1].strip().split()[0])
                if state.water_table_depth_cm is None or state.water_table_depth_cm < threshold:
                    return False
            
            elif "soil_cracks in" in part:
                if state.soil_cracks not in ["visible", "deep"]:
                    return False
            
            elif "growth_stage in" in part:
                sensitive_stages = self.config.get("sensitive_stages", [])
                if state.growth_stage not in sensitive_stages:
                    return False
            
            elif "ponded_water_cm >" in part:
                threshold = float(part.split(">")[1].strip().split()[0])
                if state.ponded_water_cm is None or state.ponded_water_cm <= threshold:
                    return False
            
            elif "days_to_harvest <" in part:
                threshold = float(part.split("<")[1].strip().split()[0])
                days_to_harvest = getattr(state, 'days_to_harvest', None)
                if days_to_harvest is None or days_to_harvest >= threshold:
                    return False
            
            elif "action=IRRIGATE" in part:
                # Meta-condition: only applies when irrigation is already triggered
                # Check if any trigger condition is met
                trigger_depth = self.config.get("awd_trigger_depth_cm", 15)
                depth_triggered = (state.water_table_depth_cm is not None and 
                                   state.water_table_depth_cm >= trigger_depth)
                cracks_triggered = state.soil_cracks in ["visible", "deep"]
                if not (depth_triggered or cracks_triggered):
                    return False
            
            else:
                # Unknown condition — don't match by default
                return False
        
        return True
    
    def evaluate_awd_trigger(self, state: WorldState) -> Dict[str, Any]:
        """Check if AWD irrigation trigger conditions are met"""
        
        if state.regime != "AWD":
            return {
                "triggered": False,
                "reason": None,
                "source": "HANDBOOK",
                "confidence": "high"
            }
        
        trigger_depth = self.config["awd_trigger_depth_cm"]
        
        # Check 1: Water table depth
        depth_trigger = False
        if state.water_table_depth_cm is not None:
            depth_trigger = state.water_table_depth_cm >= trigger_depth
        
        # Check 2: Visible cracks
        cracks_trigger = state.soil_cracks in ["visible", "deep"]
        
        triggered = depth_trigger or cracks_trigger
        
        reason = None
        if depth_trigger:
            reason = f"Water table depth ({state.water_table_depth_cm:.1f} cm) reached AWD trigger threshold ({trigger_depth} cm)"
        elif cracks_trigger:
            reason = f"{state.soil_cracks.capitalize()} cracks observed"
        
        return {
            "triggered": triggered,
            "reason": reason,
            "source": "HANDBOOK",
            "json_path": "awd_section.irrigation_trigger",
            "confidence": "high"
        }
    
    def get_refill_target(self) -> tuple:
        """Get AWD refill target range"""
        return (
            self.config["refill_target_min_cm"],
            self.config["refill_target_max_cm"]
        )
    
    def is_sensitive_stage(self, growth_stage: Optional[str]) -> bool:
        """Check if current stage is sensitive"""
        if not growth_stage:
            return False
        return growth_stage in self.config.get("sensitive_stages", [])
