"""
State Observation Recording for the AWD World Model.

Records every observation that changes (or attempts to change) the world state:
  - field name, old value, new value
  - source (chat, checkin, weather, derived, profile)
  - confidence score
  - raw input that triggered the change
  - timestamp

Provides a complete audit trail of how the world model evolved.
"""

from datetime import datetime
from typing import Optional, Any, List, Dict
from pydantic import BaseModel, Field
from .state_space import get_variable_meta, validate_value


# ---------------------------------------------------------------------------
# Observation Schema
# ---------------------------------------------------------------------------

class StateObservation(BaseModel):
    """A single observation that updates one state variable."""
    farm_id: str
    field_name: str
    old_value: Optional[Any] = None
    new_value: Any
    source: str  # "chat", "checkin", "weather", "derived", "profile", "system"
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    trigger: Optional[str] = None  # raw user message or event that caused this
    trigger_type: Optional[str] = None  # "user_message", "checkin_form", "weather_api", "das_calc"
    validated: bool = True  # whether the value passed state_space validation
    timestamp: datetime = Field(default_factory=datetime.now)


class StateSnapshot(BaseModel):
    """Full state snapshot at a point in time, for history replay."""
    farm_id: str
    snapshot_id: Optional[int] = None
    state_data: Dict[str, Any]
    trigger: Optional[str] = None
    trigger_type: Optional[str] = None
    observation_count: int = 0  # how many observations led to this snapshot
    timestamp: datetime = Field(default_factory=datetime.now)


# ---------------------------------------------------------------------------
# Observation Recorder
# ---------------------------------------------------------------------------

class ObservationRecorder:
    """
    Records state observations and snapshots.
    
    Plugs into StateManager to capture every state mutation with full provenance.
    Uses the SQLite storage layer for persistence.
    """
    
    def __init__(self, storage=None):
        self._storage = storage
        self._pending: List[StateObservation] = []
    
    def set_storage(self, storage):
        """Set or update the storage backend (called after app init)."""
        self._storage = storage
    
    # ---- Recording ----
    
    def record_observation(
        self,
        farm_id: str,
        field_name: str,
        old_value: Any,
        new_value: Any,
        source: str,
        confidence: float = 0.5,
        trigger: Optional[str] = None,
        trigger_type: Optional[str] = None,
    ) -> StateObservation:
        """Record a single state field change."""
        # Validate against state space
        valid = validate_value(field_name, new_value)
        
        obs = StateObservation(
            farm_id=farm_id,
            field_name=field_name,
            old_value=_serialise(old_value),
            new_value=_serialise(new_value),
            source=source,
            confidence=confidence,
            trigger=trigger,
            trigger_type=trigger_type,
            validated=valid,
        )
        
        self._pending.append(obs)
        
        # Persist immediately if storage available
        if self._storage and hasattr(self._storage, 'save_observation'):
            self._storage.save_observation(obs)
        
        return obs
    
    def record_batch(
        self,
        farm_id: str,
        old_state_dict: Dict[str, Any],
        new_state_dict: Dict[str, Any],
        changed_fields: Dict[str, Any],
        source: str,
        confidence: float = 0.5,
        trigger: Optional[str] = None,
        trigger_type: Optional[str] = None,
    ) -> List[StateObservation]:
        """Record observations for all changed fields in a batch."""
        observations = []
        for field_name, new_value in changed_fields.items():
            old_value = old_state_dict.get(field_name)
            # Skip if value didn't actually change
            if _serialise(old_value) == _serialise(new_value):
                continue
            obs = self.record_observation(
                farm_id=farm_id,
                field_name=field_name,
                old_value=old_value,
                new_value=new_value,
                source=source,
                confidence=confidence,
                trigger=trigger,
                trigger_type=trigger_type,
            )
            observations.append(obs)
        return observations
    
    def record_snapshot(
        self,
        farm_id: str,
        state_data: Dict[str, Any],
        trigger: Optional[str] = None,
        trigger_type: Optional[str] = None,
    ) -> StateSnapshot:
        """Record a full state snapshot."""
        snap = StateSnapshot(
            farm_id=farm_id,
            state_data=state_data,
            trigger=trigger,
            trigger_type=trigger_type,
            observation_count=len(self._pending),
        )
        
        if self._storage and hasattr(self._storage, 'save_snapshot'):
            self._storage.save_snapshot(snap)
        
        # Clear pending after snapshot
        self._pending.clear()
        return snap
    
    # ---- Querying ----
    
    def get_observations(
        self,
        farm_id: str,
        field_name: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Query observation history."""
        if self._storage and hasattr(self._storage, 'load_observations'):
            return self._storage.load_observations(
                farm_id=farm_id,
                field_name=field_name,
                source=source,
                limit=limit,
            )
        return []
    
    def get_snapshots(
        self,
        farm_id: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Query state snapshot history."""
        if self._storage and hasattr(self._storage, 'load_snapshots'):
            return self._storage.load_snapshots(farm_id=farm_id, limit=limit)
        return []
    
    def get_field_timeline(
        self,
        farm_id: str,
        field_name: str,
        limit: int = 30,
    ) -> List[Dict[str, Any]]:
        """Get the value timeline for a single state variable."""
        return self.get_observations(
            farm_id=farm_id, field_name=field_name, limit=limit
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialise(value: Any) -> Any:
    """Make a value JSON-safe for storage."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, dict)):
        return value
    # date, datetime → iso string
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return str(value)
