"""Pydantic schemas for water management module"""

from datetime import date, datetime
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field


class FarmerProfile(BaseModel):
    """Farmer and farm profile information"""
    farmer_id: str
    farm_id: str
    
    # Location
    province: str
    district: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_lon: Optional[float] = None
    
    # Crop establishment
    establishment: Literal["direct_seeded", "transplanted", "unknown"] = "unknown"
    sowing_date: Optional[date] = None
    transplant_date: Optional[date] = None
    variety_duration: Literal["short", "medium", "long", "unknown"] = "unknown"
    
    # Field characteristics
    soil_type: Literal["alluvial", "acid_sulfate", "clay", "sandy", "unknown"] = "unknown"
    bund_height_class: Literal["low", "medium", "high", "unknown"] = "unknown"
    field_leveled: bool = True
    
    # Water access
    irrigation_access: bool = True
    pump_available: bool = False
    drainage_access: bool = True
    
    # Management preference
    preferred_practice: Literal["AWD", "TRADITIONAL", "UNSURE"] = "UNSURE"
    awd_tube_available: bool = False
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class DailyCheckIn(BaseModel):
    """Daily field observation check-in"""
    farm_id: str
    checkin_date: date
    
    # Water measurement
    measurement_mode: Literal["awd_tube", "standing_water_bucket", "qualitative", "none"]
    
    # If awd_tube mode
    water_table_depth_cm: Optional[float] = None
    
    # If standing_water_bucket mode
    ponded_bucket: Optional[Literal["zero", "one_two", "three_five", "over_five"]] = None
    
    # Soil observations
    soil_cracks: Literal["none", "small", "visible", "deep", "unknown"] = "unknown"
    
    # Farmer actions
    irrigated_since_last: bool = False
    irrigation_duration_minutes: Optional[int] = None
    drained_since_last: bool = False
    
    # Weather observations
    heavy_rain_last_24h: bool = False
    
    # Optional
    notes: Optional[str] = None
    photo_url: Optional[str] = None
    
    timestamp: datetime = Field(default_factory=datetime.now)


class FieldProvenance(BaseModel):
    """Track source and confidence of each state field"""
    source: Literal["user", "profile", "checkin", "chat", "weather", "derived"]
    last_updated: datetime
    confidence: float = Field(ge=0.0, le=1.0)


class WorldState(BaseModel):
    """Complete water management world state"""
    farm_id: str
    state_date: date
    
    # Crop
    das: Optional[int] = None
    growth_stage: Optional[Literal[
        "seedling", "tillering", "panicle_initiation",
        "heading", "grain_filling", "maturity", "unknown"
    ]] = None
    expected_harvest_date: Optional[date] = None
    
    # Field
    soil_type: Literal["alluvial", "acid_sulfate", "clay", "sandy", "unknown"]
    bund_height_class: Literal["low", "medium", "high", "unknown"]
    leveled: bool
    
    # Water (latent state)
    ponded_water_cm: float = 0.0
    water_table_depth_cm: Optional[float] = None
    soil_deficit_index: float = 0.0
    soil_cracks: Literal["none", "small", "visible", "deep", "unknown"] = "unknown"
    
    # Weather
    rain_last_24h_mm: float = 0.0
    rain_next_72h_mm: float = 0.0
    et0_next_24h_mm: Optional[float] = None
    temperature_next_24h_c: Optional[float] = None
    
    # Constraints
    irrigation_access: bool
    drainage_access: bool
    can_irrigate_today: bool = True
    
    # Management
    regime: Literal["AWD", "CONTINUOUS", "RAINFED", "AUTO"] = "AUTO"
    mode: Literal["handbook_only", "handbook_plus", "general_only"] = "handbook_plus"
    
    # Provenance tracking
    field_provenance: Dict[str, FieldProvenance] = {}
    
    last_updated: datetime = Field(default_factory=datetime.now)


class ClarificationRequest(BaseModel):
    """Request for clarification from user"""
    field: str
    question: str
    reason: str


class ChatExtractionResult(BaseModel):
    """Result of LLM slot extraction from chat"""
    slots: Dict[str, Any] = {}
    confidence: float = Field(ge=0.0, le=1.0)
    need_clarification: List[ClarificationRequest] = []
    evidence: List[str] = []
    unit_notes: Optional[str] = None
    water_measurement_type: Optional[Literal[
        "ponded_depth", "awd_tube_depth", "qualitative_only", "unknown"
    ]] = None


class RationaleBullet(BaseModel):
    """Single rationale item with provenance"""
    text: str
    source_type: Literal["HANDBOOK", "GENERAL", "OBSERVATION", "WEATHER", "DERIVED"]
    reference: str
    confidence: Literal["high", "medium", "low"]


class CounterfactualOutcome(BaseModel):
    """What-if scenario outcome"""
    action: str
    outcome_summary: str
    risk_level: Literal["low", "medium", "high"]


class AdviceResponse(BaseModel):
    """Water management advice with provenance"""
    farm_id: str
    advice_date: date
    
    # Recommendation
    recommended_action: Literal["IRRIGATE", "HOLD", "DRAIN", "ALERT_ONLY"]
    target_description: Optional[str] = None
    
    # Confidence and reasoning
    confidence: Literal["high", "medium", "low"]
    rationale: List[RationaleBullet]
    
    # What-if scenarios
    counterfactuals: Optional[List[CounterfactualOutcome]] = None
    
    # Guidance
    next_observation_question: Optional[str] = None
    risk_warnings: Optional[List[str]] = None
    
    # Metadata
    regime_used: str
    mode_used: str
    timestamp: datetime = Field(default_factory=datetime.now)


class WeatherSummary(BaseModel):
    """Weather forecast summary"""
    rain_last_24h_mm: float = 0.0
    rain_next_72h_mm: float = 0.0
    et0_next_24h_mm: Optional[float] = None
    temperature_next_24h_c: Optional[float] = None
    forecast_confidence: Literal["high", "medium", "low"] = "medium"
