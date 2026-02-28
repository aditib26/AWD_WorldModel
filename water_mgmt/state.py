"""State assembly and management logic"""

from datetime import date, datetime
from typing import Dict, Any, Optional
from .schemas import FarmerProfile, DailyCheckIn, WorldState, FieldProvenance
from .config import BUCKET_TO_CM, DAS_TO_STAGE
from .state_observations import ObservationRecorder


class StateManager:
    """Manages world state construction and updates"""
    
    def __init__(self, observer: Optional[ObservationRecorder] = None):
        self.observer = observer or ObservationRecorder()
    
    def _state_dict(self, state: WorldState) -> Dict[str, Any]:
        """Extract trackable fields from a WorldState as a flat dict."""
        return {
            "das": state.das,
            "growth_stage": state.growth_stage,
            "soil_type": state.soil_type,
            "bund_height_class": state.bund_height_class,
            "leveled": state.leveled,
            "ponded_water_cm": state.ponded_water_cm,
            "water_table_depth_cm": state.water_table_depth_cm,
            "soil_deficit_index": state.soil_deficit_index,
            "soil_cracks": state.soil_cracks,
            "rain_last_24h_mm": state.rain_last_24h_mm,
            "rain_next_72h_mm": state.rain_next_72h_mm,
            "et0_next_24h_mm": state.et0_next_24h_mm,
            "temperature_next_24h_c": state.temperature_next_24h_c,
            "irrigation_access": state.irrigation_access,
            "drainage_access": state.drainage_access,
            "can_irrigate_today": state.can_irrigate_today,
            "regime": state.regime,
            "mode": state.mode,
        }
    
    def build_initial_state(self, profile: FarmerProfile, today: date) -> WorldState:
        """Initialize state from profile"""
        
        # Calculate DAS if sowing date available
        das = None
        if profile.sowing_date:
            das = (today - profile.sowing_date).days
        elif profile.transplant_date:
            das = (today - profile.transplant_date).days
        
        # Infer growth stage from DAS
        growth_stage = self.infer_growth_stage(das) if das is not None else "unknown"
        
        state = WorldState(
            farm_id=profile.farm_id,
            state_date=today,
            das=das,
            growth_stage=growth_stage,
            soil_type=profile.soil_type,
            bund_height_class=profile.bund_height_class,
            leveled=profile.field_leveled,
            irrigation_access=profile.irrigation_access,
            drainage_access=profile.drainage_access,
            regime=self._infer_regime(profile),
            mode="handbook_plus"
        )
        
        # Set provenance for profile-derived fields
        now = datetime.now()
        state.field_provenance = {
            "soil_type": FieldProvenance(source="profile", last_updated=now, confidence=1.0),
            "bund_height_class": FieldProvenance(source="profile", last_updated=now, confidence=1.0),
            "irrigation_access": FieldProvenance(source="profile", last_updated=now, confidence=1.0),
            "drainage_access": FieldProvenance(source="profile", last_updated=now, confidence=1.0),
        }
        
        if das is not None:
            state.field_provenance["das"] = FieldProvenance(
                source="derived", last_updated=now, confidence=0.95
            )
            state.field_provenance["growth_stage"] = FieldProvenance(
                source="derived", last_updated=now, confidence=0.8
            )
        
        # Record initial state as snapshot
        self.observer.record_snapshot(
            farm_id=profile.farm_id,
            state_data=self._state_dict(state),
            trigger=f"profile_created:{profile.farm_id}",
            trigger_type="profile_init",
        )
        
        return state
    
    def apply_checkin(self, state: WorldState, checkin: DailyCheckIn) -> WorldState:
        """Merge check-in data into state"""
        
        before = self._state_dict(state)
        state = state.model_copy(deep=True)
        now = datetime.now()
        
        # Map bucket to cm if using bucket mode
        if checkin.measurement_mode == "standing_water_bucket" and checkin.ponded_bucket:
            state.ponded_water_cm = BUCKET_TO_CM.get(checkin.ponded_bucket, 0.0)
            state.field_provenance["ponded_water_cm"] = FieldProvenance(
                source="checkin", last_updated=now, confidence=0.7
            )
        
        # Set AWD tube depth if available
        if checkin.measurement_mode == "awd_tube" and checkin.water_table_depth_cm is not None:
            state.water_table_depth_cm = checkin.water_table_depth_cm
            state.field_provenance["water_table_depth_cm"] = FieldProvenance(
                source="checkin", last_updated=now, confidence=0.95
            )
        
        # Update soil cracks
        if checkin.soil_cracks != "unknown":
            state.soil_cracks = checkin.soil_cracks
            state.field_provenance["soil_cracks"] = FieldProvenance(
                source="checkin", last_updated=now, confidence=0.9
            )
        
        # Update heavy rain observation
        if checkin.heavy_rain_last_24h:
            state.rain_last_24h_mm = max(state.rain_last_24h_mm, 20.0)
        
        state.last_updated = now
        state = self.validate_and_cap(state)
        
        # Record observations for changed fields
        after = self._state_dict(state)
        changed = {k: v for k, v in after.items() if before.get(k) != v}
        if changed:
            self.observer.record_batch(
                farm_id=state.farm_id,
                old_state_dict=before,
                new_state_dict=after,
                changed_fields=changed,
                source="checkin",
                confidence=0.9,
                trigger=f"checkin:{checkin.checkin_date.isoformat()}",
                trigger_type="checkin_form",
            )
            self.observer.record_snapshot(
                farm_id=state.farm_id,
                state_data=after,
                trigger=f"checkin:{checkin.checkin_date.isoformat()}",
                trigger_type="checkin_form",
            )
        
        return state
    
    def merge_extracted_data(self, state: WorldState, slots: Dict[str, Any], trigger_message: str = None) -> WorldState:
        """Merge LLM-extracted slots into state (alias for apply_chat_slots)"""
        return self.apply_chat_slots(state, slots, trigger_message=trigger_message)
    
    def update_state(self, state: WorldState, profile: FarmerProfile, weather_forecast) -> WorldState:
        """Update state with weather forecast and profile data
        
        Args:
            state: Current world state
            profile: Farmer profile
            weather_forecast: Either a WeatherSummary object or list of WeatherSummary objects
        """
        before = self._state_dict(state)
        state = state.model_copy(deep=True)
        now = datetime.now()
        
        # Handle both single WeatherSummary and list
        from .schemas import WeatherSummary
        
        latest_weather = None
        if isinstance(weather_forecast, list) and len(weather_forecast) > 0:
            latest_weather = weather_forecast[0]
        elif isinstance(weather_forecast, WeatherSummary):
            latest_weather = weather_forecast
        
        # Update weather data if available
        if latest_weather:
            if hasattr(latest_weather, 'rain_last_24h_mm'):
                state.rain_last_24h_mm = latest_weather.rain_last_24h_mm
            if hasattr(latest_weather, 'rain_next_72h_mm'):
                state.rain_next_72h_mm = latest_weather.rain_next_72h_mm
            if hasattr(latest_weather, 'temperature_next_24h_c'):
                state.temperature_next_24h_c = latest_weather.temperature_next_24h_c
            if hasattr(latest_weather, 'et0_next_24h_mm'):
                state.et0_next_24h_mm = latest_weather.et0_next_24h_mm
        
        # Update DAS if sowing date in profile
        if profile.sowing_date:
            state = self.update_das(state, state.state_date, profile.sowing_date)
        
        state.last_updated = now
        
        # Record weather observations for changed fields
        after = self._state_dict(state)
        changed = {k: v for k, v in after.items() if before.get(k) != v}
        weather_fields = {"rain_last_24h_mm", "rain_next_72h_mm", "et0_next_24h_mm", "temperature_next_24h_c"}
        weather_changed = {k: v for k, v in changed.items() if k in weather_fields}
        other_changed = {k: v for k, v in changed.items() if k not in weather_fields}
        
        if weather_changed:
            self.observer.record_batch(
                farm_id=state.farm_id,
                old_state_dict=before,
                new_state_dict=after,
                changed_fields=weather_changed,
                source="weather",
                confidence=0.8,
                trigger="weather_api_update",
                trigger_type="weather_api",
            )
        if other_changed:
            self.observer.record_batch(
                farm_id=state.farm_id,
                old_state_dict=before,
                new_state_dict=after,
                changed_fields=other_changed,
                source="derived",
                confidence=0.95,
                trigger="das_recalc",
                trigger_type="das_calc",
            )
        
        return state
    
    def initialize_state(self, profile: FarmerProfile, today: Optional[date] = None) -> WorldState:
        """Initialize state from profile (alias for build_initial_state)"""
        if today is None:
            today = date.today()
        return self.build_initial_state(profile, today)
    
    def apply_chat_slots(self, state: WorldState, slots: Dict[str, Any], trigger_message: str = None) -> WorldState:
        """Merge LLM-extracted slots into state"""
        
        before = self._state_dict(state)
        state = state.model_copy(deep=True)
        now = datetime.now()
        
        # Map slot keys to state fields
        slot_mapping = {
            "ponded_water_cm": ("ponded_water_cm", 0.9),
            "water_table_depth_cm": ("water_table_depth_cm", 0.9),
            "das": ("das", 0.85),
            "growth_stage": ("growth_stage", 0.8),
            "soil_cracks": ("soil_cracks", 0.85),
            "irrigation_access": ("irrigation_access", 0.95),
            "drainage_access": ("drainage_access", 0.95),
            "rain_last_24h_mm": ("rain_last_24h_mm", 0.7),
        }
        
        for slot_key, value in slots.items():
            if slot_key in slot_mapping and value is not None:
                field_name, confidence = slot_mapping[slot_key]
                setattr(state, field_name, value)
                state.field_provenance[field_name] = FieldProvenance(
                    source="chat", last_updated=now, confidence=confidence
                )
        
        # Handle regime_intent - track what practice the farmer uses (AWD or not)
        if "regime_intent" in slots and slots["regime_intent"] not in (None, "unknown"):
            regime_map = {"AWD": "AWD", "CONTINUOUS": "CONTINUOUS", "RAINFED": "RAINFED"}
            new_regime = regime_map.get(slots["regime_intent"], state.regime)
            state.regime = new_regime
            state.field_provenance["regime"] = FieldProvenance(
                source="chat", last_updated=now, confidence=0.85
            )
        
        # Handle soil_type updates from chat
        if "soil_type" in slots and slots["soil_type"] not in (None, "unknown"):
            state.soil_type = slots["soil_type"]
            state.field_provenance["soil_type"] = FieldProvenance(
                source="chat", last_updated=now, confidence=0.85
            )
        
        # Re-infer growth stage if DAS was updated
        if "das" in slots and state.das is not None:
            state.growth_stage = self.infer_growth_stage(state.das)
            state.field_provenance["growth_stage"] = FieldProvenance(
                source="derived", last_updated=now, confidence=0.8
            )
        
        state.last_updated = now
        state = self.validate_and_cap(state)
        
        # Record observations for changed fields
        after = self._state_dict(state)
        changed = {k: v for k, v in after.items() if before.get(k) != v}
        if changed:
            self.observer.record_batch(
                farm_id=state.farm_id,
                old_state_dict=before,
                new_state_dict=after,
                changed_fields=changed,
                source="chat",
                confidence=0.85,
                trigger=trigger_message,
                trigger_type="user_message",
            )
            self.observer.record_snapshot(
                farm_id=state.farm_id,
                state_data=after,
                trigger=trigger_message,
                trigger_type="user_message",
            )
        
        return state
    
    def infer_growth_stage(self, das: int) -> str:
        """Map DAS to approximate growth stage"""
        if das < 0:
            return "unknown"
        
        for min_das, max_das, stage in DAS_TO_STAGE:
            if min_das <= das <= max_das:
                return stage
        
        return "maturity"
    
    def validate_and_cap(self, state: WorldState) -> WorldState:
        """Enforce physical constraints"""
        
        # Get bund height
        from .config import BUND_HEIGHT_CM
        bund_height = BUND_HEIGHT_CM.get(state.bund_height_class, 15.0)
        
        # Cap ponded water
        state.ponded_water_cm = max(0.0, min(state.ponded_water_cm, bund_height))
        
        # Cap water table depth
        if state.water_table_depth_cm is not None:
            state.water_table_depth_cm = max(0.0, min(state.water_table_depth_cm, 60.0))
        
        # Cap DAS
        if state.das is not None:
            state.das = max(0, min(state.das, 200))
        
        # Ensure soil deficit index is in range
        state.soil_deficit_index = max(0.0, min(state.soil_deficit_index, 1.0))
        
        return state
    
    def _infer_regime(self, profile: FarmerProfile) -> str:
        """Infer initial regime from profile"""
        if not profile.irrigation_access:
            return "RAINFED"
        
        if profile.preferred_practice == "AWD" or profile.awd_tube_available:
            return "AWD"
        
        if profile.preferred_practice == "TRADITIONAL":
            return "CONTINUOUS"
        
        return "AUTO"
    
    def update_das(self, state: WorldState, current_date: date, sowing_date: Optional[date]) -> WorldState:
        """Update DAS based on current date"""
        if sowing_date:
            state = state.model_copy(deep=True)
            state.das = (current_date - sowing_date).days
            state.growth_stage = self.infer_growth_stage(state.das)
            
            now = datetime.now()
            state.field_provenance["das"] = FieldProvenance(
                source="derived", last_updated=now, confidence=0.95
            )
            state.field_provenance["growth_stage"] = FieldProvenance(
                source="derived", last_updated=now, confidence=0.8
            )
        
        return state
