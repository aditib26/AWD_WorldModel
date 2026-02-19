"""Rule precedence resolver"""

from typing import Dict, Any, Tuple, List
from .schemas import WorldState
from .rules_handbook import HandbookRuleSet, HandbookRule
from .rules_general import GeneralRuleSet, GeneralRule


class PolicyResolver:
    """Combine handbook and general rules with precedence"""
    
    def __init__(
        self,
        handbook: HandbookRuleSet,
        general: GeneralRuleSet,
        mode: str = "handbook_plus"
    ):
        self.handbook = handbook
        self.general = general
        self.mode = mode
    
    def set_mode(self, mode: str):
        """Change operational mode"""
        if mode not in ["handbook_only", "handbook_plus", "general_only"]:
            raise ValueError(f"Invalid mode: {mode}")
        self.mode = mode
    
    def resolve_effective_config(self, state: WorldState) -> Dict[str, Any]:
        """Merge handbook and general configs with precedence"""
        
        config = {}
        
        if self.mode == "handbook_only":
            # Only handbook configuration
            config = self.handbook.config.copy()
        
        elif self.mode == "handbook_plus":
            # Start with general defaults, override with handbook
            if state.regime == "CONTINUOUS":
                config["target_ponding_cm"] = self.general.get_continuous_flooding_target()
            
            # Handbook overrides
            config.update(self.handbook.config)
            
            # Add general stress buffer if applicable
            if state.growth_stage:
                buffer = self.general.get_stress_buffer(state.growth_stage)
                if buffer > 0:
                    config["stress_buffer_cm"] = buffer
        
        elif self.mode == "general_only":
            # Testing mode - only general rules
            if state.regime == "CONTINUOUS":
                config["target_ponding_cm"] = self.general.get_continuous_flooding_target()
            config["stress_buffer_cm"] = self.general.get_stress_buffer(state.growth_stage or "unknown")
        
        # Add soil-specific parameters
        from .hydrology import HydrologyCoreSimulator
        simulator = HydrologyCoreSimulator()
        soil_params = simulator.get_soil_params_by_type(state.soil_type)
        config.update(soil_params)
        
        return config
    
    def get_all_applicable_rules(
        self,
        state: WorldState
    ) -> Tuple[List[HandbookRule], List[GeneralRule]]:
        """Return (handbook_rules, general_rules) both applicable"""
        
        hb_rules = self.handbook.get_applicable_rules(state)
        
        gen_rules = []
        if self.mode != "handbook_only":
            gen_rules = self.general.get_applicable_rules(state)
        
        return hb_rules, gen_rules
    
    def resolve_conflicts(
        self,
        hb_rules: List[HandbookRule],
        gen_rules: List[GeneralRule]
    ) -> Dict[str, Any]:
        """Resolve conflicts between rule sets"""
        
        resolution = {
            "primary_rules": [],
            "supporting_rules": [],
            "overridden_rules": []
        }
        
        # Handbook rules are always primary
        resolution["primary_rules"] = hb_rules
        
        # Check for conflicts
        hb_actions = {rule.action for rule in hb_rules}
        
        for gen_rule in gen_rules:
            # Check if general rule conflicts with handbook
            if self._conflicts_with_handbook(gen_rule, hb_rules):
                resolution["overridden_rules"].append({
                    "rule": gen_rule,
                    "reason": "Conflicts with handbook rule"
                })
            else:
                # General rule is supporting
                resolution["supporting_rules"].append(gen_rule)
        
        return resolution
    
    def _conflicts_with_handbook(
        self,
        gen_rule: GeneralRule,
        hb_rules: List[HandbookRule]
    ) -> bool:
        """Check if general rule conflicts with any handbook rule"""
        
        # Simple conflict detection
        # In production, use more sophisticated logic
        
        gen_action = gen_rule.action.lower()
        
        for hb_rule in hb_rules:
            hb_action = hb_rule.action.lower()
            
            # Check for opposite actions
            if "irrigate" in gen_action and "stop" in hb_action:
                return True
            if "stop" in gen_action and "irrigate" in hb_action:
                return True
            if "drain" in gen_action and "refill" in hb_action:
                return True
        
        return False
    
    def should_irrigate(self, state: WorldState) -> Dict[str, Any]:
        """Determine if irrigation is recommended"""
        
        result = {
            "should_irrigate": False,
            "reason": None,
            "source": None,
            "confidence": "low",
            "target_cm": None
        }
        
        # Check regime
        if state.regime == "RAINFED":
            result["reason"] = "Rainfed system - no irrigation available"
            result["source"] = "GENERAL"
            result["confidence"] = "high"
            return result
        
        if not state.irrigation_access:
            result["reason"] = "No irrigation access"
            result["source"] = "OBSERVATION"
            result["confidence"] = "high"
            return result
        
        # AWD regime
        if state.regime == "AWD":
            trigger_result = self.handbook.evaluate_awd_trigger(state)
            
            if trigger_result["triggered"]:
                min_cm, max_cm = self.handbook.get_refill_target()
                result["should_irrigate"] = True
                result["reason"] = trigger_result["reason"]
                result["source"] = "HANDBOOK"
                result["confidence"] = "high"
                result["target_cm"] = (min_cm + max_cm) / 2
                return result
            else:
                result["reason"] = "AWD trigger not reached"
                result["source"] = "HANDBOOK"
                result["confidence"] = "high"
                return result
        
        # Continuous flooding regime
        if state.regime == "CONTINUOUS":
            target = self.general.get_continuous_flooding_target()
            
            if state.ponded_water_cm < 2.0:
                result["should_irrigate"] = True
                result["reason"] = "Ponded water below minimum for continuous flooding"
                result["source"] = "GENERAL"
                result["confidence"] = "medium"
                result["target_cm"] = target
                return result
        
        return result
    
    def get_regime_params(self, state: WorldState) -> Dict[str, Any]:
        """Get regime-specific parameters"""
        
        params = {}
        
        if state.regime == "AWD":
            min_cm, max_cm = self.handbook.get_refill_target()
            params["refill_target_cm"] = (min_cm + max_cm) / 2
            params["trigger_depth_cm"] = self.handbook.config["awd_trigger_depth_cm"]
            params["max_ponding_cm"] = self.handbook.config["max_ponding_cm"]
        
        elif state.regime == "CONTINUOUS":
            params["refill_target_cm"] = self.general.get_continuous_flooding_target()
            params["min_ponding_cm"] = 2.0
            params["max_ponding_cm"] = 5.0
        
        elif state.regime == "RAINFED":
            params["no_irrigation"] = True
        
        return params
