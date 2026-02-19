"""
State Persistence for AWD World Model
Handles saving and loading farm state and history across sessions
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path


class StatePersistenceManager:
    """
    Manages persistence of farm state and history
    Enables continuity across sessions
    """
    
    def __init__(self, storage_dir: str = ".awd_state"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
    
    def save_state(
        self, 
        user_id: str, 
        farm_state: Dict[str, Any],
        state_history: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save farm state and history for a user
        
        Args:
            user_id: Unique user identifier
            farm_state: Current farm state dictionary
            state_history: JSON string of state history
            metadata: Additional metadata (last_update, session_count, etc.)
        
        Returns:
            True if save successful
        """
        try:
            user_dir = self.storage_dir / user_id
            user_dir.mkdir(exist_ok=True)
            
            # Save current state
            state_file = user_dir / "farm_state.json"
            with open(state_file, 'w') as f:
                json.dump({
                    "state": farm_state,
                    "last_updated": datetime.now().isoformat(),
                    "metadata": metadata or {}
                }, f, indent=2)
            
            # Save state history if provided
            if state_history:
                history_file = user_dir / "state_history.json"
                with open(history_file, 'w') as f:
                    f.write(state_history)
            
            return True
            
        except Exception as e:
            print(f"❌ State Persistence: Error saving state for {user_id}: {str(e)}")
            return False
    
    def load_state(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Load farm state for a user
        
        Returns:
            Dictionary with 'state', 'last_updated', 'metadata', 'history'
            None if no saved state found
        """
        try:
            user_dir = self.storage_dir / user_id
            if not user_dir.exists():
                return None
            
            state_file = user_dir / "farm_state.json"
            if not state_file.exists():
                return None
            
            with open(state_file, 'r') as f:
                state_data = json.load(f)
            
            # Load history if exists
            history_file = user_dir / "state_history.json"
            if history_file.exists():
                with open(history_file, 'r') as f:
                    state_data['history'] = f.read()
            else:
                state_data['history'] = None
            
            return state_data
            
        except Exception as e:
            print(f"❌ State Persistence: Error loading state for {user_id}: {str(e)}")
            return None
    
    def delete_state(self, user_id: str) -> bool:
        """Delete saved state for a user"""
        try:
            user_dir = self.storage_dir / user_id
            if user_dir.exists():
                import shutil
                shutil.rmtree(user_dir)
                return True
            return False
        except Exception as e:
            print(f"❌ State Persistence: Error deleting state for {user_id}: {str(e)}")
            return False
    
    def list_saved_users(self) -> list:
        """List all users with saved states"""
        try:
            return [d.name for d in self.storage_dir.iterdir() if d.is_dir()]
        except Exception as e:
            print(f"❌ State Persistence: Error listing users: {str(e)}")
            return []
    
    def get_state_age(self, user_id: str) -> Optional[int]:
        """Get age of saved state in days"""
        state_data = self.load_state(user_id)
        if state_data and 'last_updated' in state_data:
            last_update = datetime.fromisoformat(state_data['last_updated'])
            age = (datetime.now() - last_update).days
            return age
        return None


class ProactiveMonitor:
    """
    Proactive monitoring system that generates alerts and suggestions
    based on farm state and predictions
    """
    
    def __init__(self):
        self.alert_history = []
    
    def check_for_alerts(
        self, 
        farm_state: Dict[str, Any],
        prediction: Optional[Dict[str, Any]] = None,
        state_history: Optional[list] = None
    ) -> list:
        """
        Check farm state and generate proactive alerts/suggestions
        
        Returns:
            List of alert dictionaries with 'type', 'urgency', 'message', 'action'
        """
        alerts = []
        
        # Extract state components
        water = farm_state.get('water', {})
        crop = farm_state.get('crop', {})
        observations = farm_state.get('observations', {})
        
        water_depth = water.get('water_table_cm_below_surface')
        growth_stage = crop.get('growth_stage')
        stress = observations.get('stress_symptoms_flag')
        cracking = observations.get('cracking_level')
        
        # Alert 1: Water depth approaching safe limit
        if water_depth is not None:
            if growth_stage == 'flowering' and water_depth >= 10:
                alerts.append({
                    'type': 'critical',
                    'urgency': 'high',
                    'message': '⚠️ CRITICAL: Water depth at 10cm during flowering! Your crop is at risk.',
                    'action': 'Irrigate immediately to 5cm standing water.',
                    'reasoning': 'Flowering stage requires shallow water depth (<10cm) to prevent yield loss.'
                })
            elif water_depth >= 15:
                alerts.append({
                    'type': 'warning',
                    'urgency': 'high',
                    'message': '⚠️ Water depth reached safe limit (15cm).',
                    'action': 'Plan irrigation within 24 hours.',
                    'reasoning': 'AWD recommends re-irrigation when water reaches 15cm below surface.'
                })
            elif water_depth >= 12 and prediction and prediction.get('days_remaining', 0) <= 2:
                alerts.append({
                    'type': 'advisory',
                    'urgency': 'medium',
                    'message': '📊 Water depth at 12cm, predicted to reach 15cm in 2 days.',
                    'action': 'Prepare for irrigation in 1-2 days.',
                    'reasoning': 'Based on drying rate prediction and current depth.'
                })
        
        # Alert 2: Stress symptoms detected
        if stress:
            alerts.append({
                'type': 'warning',
                'urgency': 'high',
                'message': '🌾 Stress symptoms detected (leaf rolling/wilting).',
                'action': 'Check water level immediately. Consider irrigating if depth > 10cm.',
                'reasoning': 'Stress symptoms indicate plants may be experiencing water deficit.'
            })
        
        # Alert 3: Severe soil cracking
        if cracking == 'severe':
            alerts.append({
                'type': 'warning',
                'urgency': 'medium',
                'message': '🌍 Severe soil cracking observed.',
                'action': 'Irrigate soon to prevent further cracking and root damage.',
                'reasoning': 'Severe cracking can damage roots and reduce water retention.'
            })
        
        # Alert 4: State hasn't been updated recently
        if state_history and len(state_history) > 0:
            # state_history contains StateSnapshot objects, not dicts
            last_snapshot = state_history[-1]
            last_update = last_snapshot.timestamp if hasattr(last_snapshot, 'timestamp') else None
            
            if last_update:
                from datetime import datetime, timedelta
                last_time = datetime.fromisoformat(last_update)
                days_since = (datetime.now() - last_time).days
                
                if days_since >= 3:
                    alerts.append({
                        'type': 'reminder',
                        'urgency': 'low',
                        'message': f'📅 No updates in {days_since} days.',
                        'action': 'Update your water level measurement to get accurate advice.',
                        'reasoning': 'Regular monitoring improves prediction accuracy.'
                    })
        
        # Alert 5: Approaching critical growth stage
        if growth_stage == 'panicle_initiation':
            alerts.append({
                'type': 'advisory',
                'urgency': 'medium',
                'message': '🌾 Approaching flowering stage soon.',
                'action': 'Be extra careful with water management. Maintain shallower water depth (<10cm).',
                'reasoning': 'Flowering is the most critical stage for water management in rice.'
            })
        
        # Alert 6: Good conditions for AWD
        if (water_depth is not None and 5 <= water_depth <= 12 and 
            growth_stage in ['tillering', 'grain_filling'] and not stress):
            alerts.append({
                'type': 'positive',
                'urgency': 'low',
                'message': '✅ Excellent AWD conditions!',
                'action': 'Continue monitoring. No action needed yet.',
                'reasoning': 'Water depth is in safe range for your growth stage.'
            })
        
        return alerts
    
    def get_proactive_suggestions(
        self,
        farm_state: Dict[str, Any],
        prediction: Optional[Dict[str, Any]] = None
    ) -> list:
        """
        Generate proactive suggestions for optimization
        
        Returns:
            List of suggestion dictionaries
        """
        suggestions = []
        
        water = farm_state.get('water', {})
        soil = farm_state.get('soil', {})
        
        # Suggestion 1: Install water tube if not monitoring
        if water.get('water_table_cm_below_surface') is None:
            suggestions.append({
                'title': 'Install Water Monitoring Tube',
                'benefit': 'Track water levels accurately for better AWD practice',
                'priority': 'high',
                'steps': [
                    'Cut PVC pipe (20-25cm length, 10cm diameter)',
                    'Drill holes in lower half',
                    'Install in field corner, 15cm deep',
                    'Check daily during drying phase'
                ]
            })
        
        # Suggestion 2: Improve drainage if percolation is slow
        if soil.get('percolation_class') == 'low':
            suggestions.append({
                'title': 'Consider Drainage Improvement',
                'benefit': 'Better AWD suitability with improved drainage',
                'priority': 'low',
                'steps': [
                    'Check for compacted soil layers',
                    'Consider field leveling',
                    'May need subsurface drainage for very heavy clay'
                ]
            })
        
        # Suggestion 3: Weather monitoring
        suggestions.append({
            'title': 'Monitor Weather Forecasts',
            'benefit': 'Plan irrigation around rainfall to save water',
            'priority': 'medium',
            'steps': [
                'Check 7-day rainfall forecast',
                'Delay irrigation if heavy rain expected',
                'Adjust drying schedule based on weather'
            ]
        })
        
        return suggestions
