from typing import Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class FarmInfo(BaseModel):
    location: Optional[str] = None
    field_id: Optional[str] = None
    area_ha: Optional[float] = None


class CropState(BaseModel):
    establishment_method: Optional[str] = None
    sow_or_transplant_date: Optional[str] = None
    days_after: Optional[int] = None
    growth_stage: Optional[str] = None
    variety_name: Optional[str] = None
    variety_duration: Optional[str] = None


class WaterState(BaseModel):
    water_table_cm_below_surface: Optional[float] = None
    standing_water_cm: Optional[float] = None
    last_measured_ts: Optional[str] = None
    last_irrigation_ts: Optional[str] = None


class SoilState(BaseModel):
    texture_class: Optional[str] = None
    percolation_class: Optional[str] = None
    bunded_lowland: Optional[bool] = None


class WeatherState(BaseModel):
    rain_last_3d_mm: Optional[float] = None
    forecast_rain_next_7d_mm: Optional[float] = None
    temp_avg: Optional[float] = None
    PET_estimate: Optional[float] = None


class Constraints(BaseModel):
    irrigation_window: Optional[str] = None
    pump_cost: Optional[str] = None
    water_scarcity_flag: Optional[bool] = None


class Observations(BaseModel):
    cracking_level: Optional[str] = None
    stress_symptoms_flag: Optional[bool] = None


class ManagementState(BaseModel):
    mode: Literal["awd", "continuous_flooding", "rainfed"] = "awd"
    mode_source: Literal["sidebar_input", "chat_extraction", "inferred", "default"] = "default"
    mode_confidence: Optional[float] = None


class FieldProvenance(BaseModel):
    source: Optional[str] = None
    timestamp: Optional[str] = None
    confidence: Optional[float] = None


class FarmState(BaseModel):
    farm: FarmInfo = Field(default_factory=FarmInfo)
    crop: CropState = Field(default_factory=CropState)
    water: WaterState = Field(default_factory=WaterState)
    soil: SoilState = Field(default_factory=SoilState)
    weather: WeatherState = Field(default_factory=WeatherState)
    management: ManagementState = Field(default_factory=ManagementState)
    constraints: Constraints = Field(default_factory=Constraints)
    observations: Observations = Field(default_factory=Observations)
    field_provenance: Dict[str, FieldProvenance] = Field(default_factory=dict)
    
    def get_missing_slots(self, required_slots: list[str]) -> list[str]:
        """Check which required slots are missing"""
        missing = []
        for slot in required_slots:
            parts = slot.split('.')
            obj = self
            for part in parts:
                obj = getattr(obj, part)
                if obj is None:
                    missing.append(slot)
                    break
        return missing
    
    def update_from_dict(
        self,
        updates: Dict[str, Any],
        source: Optional[str] = None,
        confidence: Optional[float] = None,
        timestamp: Optional[str] = None
    ) -> None:
        """Update state from a flat dictionary"""
        ts = timestamp or datetime.now().isoformat()
        for key, value in updates.items():
            if '.' in key:
                parts = key.split('.')
                obj = self
                for part in parts[:-1]:
                    obj = getattr(obj, part)
                old_value = getattr(obj, parts[-1])
                if old_value == value and key in self.field_provenance:
                    continue
                setattr(obj, parts[-1], value)
            else:
                old_value = getattr(self, key, None)
                if old_value == value and key in self.field_provenance:
                    continue
                setattr(self, key, value)

            self.field_provenance[key] = FieldProvenance(
                source=source or "unknown",
                timestamp=ts,
                confidence=confidence
            )
    
    def to_summary(self) -> str:
        """Generate human-readable summary of known state"""
        summary_parts = []
        
        # Farm location and area
        if self.farm.location:
            summary_parts.append(f"Location: {self.farm.location}")
        if self.farm.area_ha:
            summary_parts.append(f"Farm area: {self.farm.area_ha} hectares")
        
        # Crop information
        if self.crop.variety_name:
            summary_parts.append(f"Rice variety: {self.crop.variety_name}")
        if self.crop.growth_stage:
            summary_parts.append(f"Crop stage: {self.crop.growth_stage}")
        if self.crop.days_after:
            summary_parts.append(f"Days after sowing: {self.crop.days_after}")
        elif self.crop.days_after and self.crop.establishment_method:
            summary_parts.append(f"{self.crop.days_after} days after {self.crop.establishment_method}")
        
        # Water status
        if self.water.water_table_cm_below_surface is not None:
            summary_parts.append(f"Water table: {self.water.water_table_cm_below_surface}cm below surface")
        elif self.water.standing_water_cm is not None:
            summary_parts.append(f"Standing water: {self.water.standing_water_cm}cm")
            
        # Soil information
        if self.soil.texture_class:
            summary_parts.append(f"Soil type: {self.soil.texture_class}")
        if self.soil.bunded_lowland is not None:
            bunded_status = "bunded (has levees)" if self.soil.bunded_lowland else "non-bunded"
            summary_parts.append(f"Field: {bunded_status}")
        if self.soil.percolation_class:
            summary_parts.append(f"Percolation: {self.soil.percolation_class}")
            
        # Weather
        if self.weather.forecast_rain_next_7d_mm is not None:
            summary_parts.append(f"Rain forecast (7d): {self.weather.forecast_rain_next_7d_mm}mm")
        if self.weather.temp_avg is not None:
            summary_parts.append(f"Temperature: {self.weather.temp_avg}°C")
        
        # Observations
        if self.observations.cracking_level:
            summary_parts.append(f"Field cracking: {self.observations.cracking_level}")
        if self.observations.stress_symptoms_flag:
            summary_parts.append(f"Stress symptoms observed: yes")
            
        return ", ".join(summary_parts) if summary_parts else "No farm data collected yet"
