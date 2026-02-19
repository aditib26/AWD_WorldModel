"""NDJSON event logging for trajectory collection"""

import json
from pathlib import Path
from datetime import datetime, date
from typing import Optional
from .schemas import WorldState, AdviceResponse, DailyCheckIn
from .config import LOG_FILE


class EventLogger:
    """NDJSON event logging for water management decisions"""
    
    def __init__(self, log_file: Path = LOG_FILE):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log_advice(
        self,
        farm_id: str,
        state: WorldState,
        advice: AdviceResponse,
        extraction = None,
        language: str = "EN"
    ) -> None:
        """Log advice with extraction context (API-compatible signature)"""
        user_message = None
        if extraction and hasattr(extraction, 'evidence') and extraction.evidence:
            user_message = " | ".join(extraction.evidence[:2])
        
        self.log_advice_event(state, advice, user_message=user_message)
    
    def log_advice_event(
        self,
        state: WorldState,
        advice: AdviceResponse,
        user_message: Optional[str] = None,
        checkin: Optional[DailyCheckIn] = None
    ) -> None:
        """Log one advice event"""
        
        event = {
            "event_type": "advice",
            "timestamp": datetime.now().isoformat(),
            "farm_id": state.farm_id,
            "state_date": state.state_date.isoformat(),
            
            # Input
            "user_message": user_message,
            "checkin": checkin.model_dump(mode='json') if checkin else None,
            
            # State
            "state_before": {
                "das": state.das,
                "growth_stage": state.growth_stage,
                "ponded_water_cm": state.ponded_water_cm,
                "water_table_depth_cm": state.water_table_depth_cm,
                "soil_cracks": state.soil_cracks,
                "soil_type": state.soil_type,
                "regime": state.regime
            },
            
            # Weather
            "weather": {
                "rain_last_24h_mm": state.rain_last_24h_mm,
                "rain_next_72h_mm": state.rain_next_72h_mm,
                "et0_next_24h_mm": state.et0_next_24h_mm,
                "temperature_next_24h_c": state.temperature_next_24h_c
            },
            
            # Advice
            "recommendation": {
                "action": advice.recommended_action,
                "target": advice.target_description,
                "confidence": advice.confidence,
                "regime": advice.regime_used,
                "mode": advice.mode_used
            },
            
            # Provenance
            "rationale": [
                {
                    "text": r.text,
                    "source_type": r.source_type,
                    "reference": r.reference,
                    "confidence": r.confidence
                }
                for r in advice.rationale
            ],
            
            # For follow-up linkage
            "follow_up_key": f"{state.farm_id}_{state.state_date.isoformat()}"
        }
        
        self._append_event(event)
    
    def log_follow_up(
        self,
        farm_id: str,
        original_date: date,
        state_after: WorldState,
        farmer_response: Optional[str] = None
    ) -> None:
        """Log follow-up observation"""
        
        event = {
            "event_type": "follow_up",
            "timestamp": datetime.now().isoformat(),
            "farm_id": farm_id,
            "original_date": original_date.isoformat(),
            
            "state_after": {
                "ponded_water_cm": state_after.ponded_water_cm,
                "water_table_depth_cm": state_after.water_table_depth_cm,
                "soil_cracks": state_after.soil_cracks,
                "das": state_after.das,
                "growth_stage": state_after.growth_stage
            },
            
            "farmer_response": farmer_response,
            "follow_up_key": f"{farm_id}_{original_date.isoformat()}"
        }
        
        self._append_event(event)
    
    def log_error(
        self,
        farm_id: str,
        error_type: str,
        error_message: str,
        context: Optional[dict] = None
    ) -> None:
        """Log an error event"""
        
        event = {
            "event_type": "error",
            "timestamp": datetime.now().isoformat(),
            "farm_id": farm_id,
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {}
        }
        
        self._append_event(event)
    
    def _append_event(self, event: dict) -> None:
        """Append event to NDJSON log file"""
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(event, default=str) + '\n')
    
    def read_events(
        self,
        farm_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> list:
        """Read events from log file"""
        
        if not self.log_file.exists():
            return []
        
        events = []
        with open(self.log_file, 'r') as f:
            for line in f:
                if line.strip():
                    event = json.loads(line)
                    
                    # Filter by farm_id
                    if farm_id and event.get("farm_id") != farm_id:
                        continue
                    
                    # Filter by event_type
                    if event_type and event.get("event_type") != event_type:
                        continue
                    
                    events.append(event)
                    
                    # Limit results
                    if limit and len(events) >= limit:
                        break
        
        return events
    
    def get_trajectory(self, farm_id: str, days: int = 30) -> list:
        """Get advice trajectory for a farm"""
        events = self.read_events(farm_id=farm_id, event_type="advice")
        
        # Sort by date
        events.sort(key=lambda e: e.get("state_date", ""))
        
        # Return last N days
        return events[-days:]
