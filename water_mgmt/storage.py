"""Storage layer for profiles, check-ins, and states"""

import json
from pathlib import Path
from typing import Optional, List
from datetime import date
from .schemas import FarmerProfile, DailyCheckIn, WorldState
from .config import DATA_DIR


class StorageAdapter:
    """Base interface for storage operations"""
    
    def save_profile(self, profile: FarmerProfile) -> None:
        raise NotImplementedError
    
    def load_profile(self, farm_id: str) -> Optional[FarmerProfile]:
        raise NotImplementedError
    
    def save_checkin(self, checkin: DailyCheckIn) -> None:
        raise NotImplementedError
    
    def load_recent_checkins(self, farm_id: str, n: int = 7) -> List[DailyCheckIn]:
        raise NotImplementedError
    
    def save_state(self, state: WorldState) -> None:
        raise NotImplementedError
    
    def load_latest_state(self, farm_id: str) -> Optional[WorldState]:
        raise NotImplementedError


class JSONFileStorage(StorageAdapter):
    """File-based JSON storage for development"""
    
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.profiles_dir = self.data_dir / "profiles"
        self.checkins_dir = self.data_dir / "checkins"
        self.states_dir = self.data_dir / "states"
        
        self.profiles_dir.mkdir(exist_ok=True)
        self.checkins_dir.mkdir(exist_ok=True)
        self.states_dir.mkdir(exist_ok=True)
    
    def save_profile(self, profile: FarmerProfile) -> None:
        """Save farmer profile"""
        file_path = self.profiles_dir / f"{profile.farm_id}.json"
        with open(file_path, 'w') as f:
            json.dump(profile.model_dump(mode='json'), f, indent=2, default=str)
    
    def load_profile(self, farm_id: str) -> Optional[FarmerProfile]:
        """Load farmer profile"""
        file_path = self.profiles_dir / f"{farm_id}.json"
        if not file_path.exists():
            return None
        
        with open(file_path, 'r') as f:
            data = json.load(f)
            return FarmerProfile(**data)
    
    def save_checkin(self, checkin: DailyCheckIn) -> None:
        """Save daily check-in"""
        farm_dir = self.checkins_dir / checkin.farm_id
        farm_dir.mkdir(exist_ok=True)
        
        file_path = farm_dir / f"{checkin.checkin_date.isoformat()}.json"
        with open(file_path, 'w') as f:
            json.dump(checkin.model_dump(mode='json'), f, indent=2, default=str)
    
    def load_recent_checkins(self, farm_id: str, n: int = 7) -> List[DailyCheckIn]:
        """Load last N check-ins for a farm"""
        farm_dir = self.checkins_dir / farm_id
        if not farm_dir.exists():
            return []
        
        checkin_files = sorted(farm_dir.glob("*.json"), reverse=True)[:n]
        checkins = []
        
        for file_path in checkin_files:
            with open(file_path, 'r') as f:
                data = json.load(f)
                checkins.append(DailyCheckIn(**data))
        
        return checkins
    
    def save_state(self, state: WorldState) -> None:
        """Save world state"""
        farm_dir = self.states_dir / state.farm_id
        farm_dir.mkdir(exist_ok=True)
        
        file_path = farm_dir / f"{state.state_date.isoformat()}.json"
        with open(file_path, 'w') as f:
            json.dump(state.model_dump(mode='json'), f, indent=2, default=str)
    
    def load_latest_state(self, farm_id: str) -> Optional[WorldState]:
        """Load most recent state for a farm"""
        farm_dir = self.states_dir / farm_id
        if not farm_dir.exists():
            return None
        
        state_files = sorted(farm_dir.glob("*.json"), reverse=True)
        if not state_files:
            return None
        
        with open(state_files[0], 'r') as f:
            data = json.load(f)
            return WorldState(**data)
    
    def load_state_by_date(self, farm_id: str, target_date: date) -> Optional[WorldState]:
        """Load state for specific date"""
        file_path = self.states_dir / farm_id / f"{target_date.isoformat()}.json"
        if not file_path.exists():
            return None
        
        with open(file_path, 'r') as f:
            data = json.load(f)
            return WorldState(**data)
