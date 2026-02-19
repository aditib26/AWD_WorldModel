"""
State History Tracker for AWD World Model
Tracks farm state evolution over time and provides temporal reasoning
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import json


@dataclass
class StateSnapshot:
    """A snapshot of farm state at a specific time"""
    timestamp: str
    state: Dict[str, Any]
    trigger: str  # What caused this state update
    confidence: float  # Confidence in this state (0.0-1.0)
    prediction: Optional[Dict[str, Any]] = None  # Predicted future state
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class StateHistoryTracker:
    """
    Tracks farm state evolution over time
    Enables temporal reasoning and visualization of World Model state transitions
    """
    
    def __init__(self, max_history: int = 100):
        self.history: List[StateSnapshot] = []
        self.max_history = max_history
        self.predictions: List[Dict[str, Any]] = []
    
    def add_snapshot(
        self, 
        state: Dict[str, Any], 
        trigger: str,
        confidence: float = 1.0,
        prediction: Optional[Dict[str, Any]] = None
    ):
        """Add a new state snapshot to history"""
        snapshot = StateSnapshot(
            timestamp=datetime.now().isoformat(),
            state=state.copy(),
            trigger=trigger,
            confidence=confidence,
            prediction=prediction
        )
        
        self.history.append(snapshot)
        
        # Keep history within limit
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def get_recent_history(self, n: int = 10) -> List[StateSnapshot]:
        """Get the n most recent state snapshots"""
        return self.history[-n:]
    
    def get_state_at_time(self, timestamp: str) -> Optional[StateSnapshot]:
        """Get state snapshot closest to given timestamp"""
        for snapshot in reversed(self.history):
            if snapshot.timestamp <= timestamp:
                return snapshot
        return None
    
    def get_state_changes(self, field: str, n: int = 10) -> List[Dict[str, Any]]:
        """Get history of changes for a specific field"""
        changes = []
        prev_value_set = False
        prev_value = None
        for snapshot in self.history[-n:]:
            # Navigate nested field paths like "water.water_table_cm_below_surface"
            value = snapshot.state
            missing = False
            for key in field.split('.'):
                if isinstance(value, dict) and key in value:
                    value = value.get(key)
                else:
                    missing = True
                    break
            
            if missing:
                continue

            if (not prev_value_set) or value != prev_value:
                changes.append({
                    "timestamp": snapshot.timestamp,
                    "value": value,
                    "trigger": snapshot.trigger,
                    "confidence": snapshot.confidence
                })
                prev_value_set = True
                prev_value = value
        
        return changes
    
    def get_timeline_data(self) -> List[Dict[str, Any]]:
        """Get timeline data for visualization"""
        timeline = []
        for snapshot in self.history:
            # Extract key metrics for timeline
            water_depth = None
            standing_water = None
            growth_stage = None
            
            state = snapshot.state
            if isinstance(state, dict):
                if 'water' in state and isinstance(state['water'], dict):
                    water_depth = state['water'].get('water_table_cm_below_surface')
                    standing_water = state['water'].get('standing_water_cm')
                if 'crop' in state and isinstance(state['crop'], dict):
                    growth_stage = state['crop'].get('growth_stage')
            
            timeline.append({
                "timestamp": snapshot.timestamp,
                "water_depth": water_depth,
                "standing_water": standing_water,
                "growth_stage": growth_stage,
                "trigger": snapshot.trigger,
                "confidence": snapshot.confidence
            })
        
        return timeline
    
    def get_prediction_accuracy(self) -> Dict[str, Any]:
        """
        Calculate accuracy of past predictions vs actual state
        Demonstrates World Model's predictive capability
        """
        accuracies = []
        
        for i, snapshot in enumerate(self.history[:-1]):
            if snapshot.prediction:
                # Compare prediction with next actual state
                next_state = self.history[i + 1].state
                
                # Calculate accuracy for predicted water level
                if 'water_level_cm' in snapshot.prediction:
                    predicted = snapshot.prediction['water_level_cm']
                    actual_dict = next_state.get('water', {})
                    actual = actual_dict.get('water_table_cm_below_surface')
                    
                    if actual is not None:
                        error = abs(predicted - actual)
                        accuracy = max(0, 1 - (error / 30))  # 30cm = max reasonable error
                        accuracies.append(accuracy)
        
        if accuracies:
            return {
                "average_accuracy": sum(accuracies) / len(accuracies),
                "predictions_made": len(accuracies),
                "confidence": "high" if sum(accuracies) / len(accuracies) > 0.8 else "medium"
            }
        
        return {
            "average_accuracy": None,
            "predictions_made": 0,
            "confidence": "unknown"
        }
    
    def get_state_trajectory(self, field: str) -> Dict[str, Any]:
        """
        Get trajectory of a specific field over time
        Shows how World Model tracks state evolution
        """
        changes = self.get_state_changes(field, n=len(self.history))
        
        if not changes:
            return {"field": field, "trajectory": [], "trend": "no_data"}
        
        # Calculate trend
        values = [c['value'] for c in changes if isinstance(c['value'], (int, float))]
        if len(values) >= 2:
            trend = "increasing" if values[-1] > values[0] else "decreasing" if values[-1] < values[0] else "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "field": field,
            "trajectory": changes,
            "trend": trend,
            "current_value": changes[-1]['value'] if changes else None,
            "change_count": len(changes)
        }
    
    def export_history(self) -> str:
        """Export history as JSON for persistence"""
        return json.dumps([s.to_dict() for s in self.history], indent=2)
    
    def import_history(self, json_data: str):
        """Import history from JSON"""
        try:
            data = json.loads(json_data)
            self.history = [
                StateSnapshot(
                    timestamp=s['timestamp'],
                    state=s['state'],
                    trigger=s['trigger'],
                    confidence=s.get('confidence', 1.0),
                    prediction=s.get('prediction')
                )
                for s in data
            ]
        except Exception as e:
            print(f"❌ Error importing state history: {str(e)}")
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get summary of current state tracking"""
        if not self.history:
            return {
                "total_snapshots": 0,
                "oldest_timestamp": None,
                "newest_timestamp": None,
                "tracking_active": False
            }
        
        return {
            "total_snapshots": len(self.history),
            "oldest_timestamp": self.history[0].timestamp,
            "newest_timestamp": self.history[-1].timestamp,
            "tracking_active": True,
            "avg_confidence": sum(s.confidence for s in self.history) / len(self.history)
        }
    
    def clear_history(self):
        """Clear all history (use with caution)"""
        self.history = []
        self.predictions = []
