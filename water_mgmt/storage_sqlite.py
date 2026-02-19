"""SQLite storage layer - production replacement for JSON file storage"""

import sqlite3
import json
from pathlib import Path
from typing import Optional, List
from datetime import date, datetime
from contextlib import contextmanager
import secrets

from .schemas import FarmerProfile, DailyCheckIn, WorldState
from .config import DATA_DIR


DB_PATH = DATA_DIR / "rice_assistant.db"


class SQLiteStorage:
    """SQLite-based storage with proper concurrency and persistence."""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    @contextmanager
    def _get_conn(self):
        """Thread-safe connection with WAL mode for concurrent reads."""
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_db(self):
        """Create tables if they don't exist."""
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

                CREATE TABLE IF NOT EXISTS farm_ownership (
                    farm_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_farm_owner_user ON farm_ownership(user_id);

                CREATE TABLE IF NOT EXISTS profiles (
                    farm_id TEXT PRIMARY KEY,
                    data JSON NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                
                CREATE TABLE IF NOT EXISTS states (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    farm_id TEXT NOT NULL,
                    state_date TEXT NOT NULL,
                    data JSON NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    UNIQUE(farm_id, state_date)
                );
                CREATE INDEX IF NOT EXISTS idx_states_farm_date 
                    ON states(farm_id, state_date DESC);
                
                CREATE TABLE IF NOT EXISTS checkins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    farm_id TEXT NOT NULL,
                    checkin_date TEXT NOT NULL,
                    data JSON NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                CREATE INDEX IF NOT EXISTS idx_checkins_farm_date 
                    ON checkins(farm_id, checkin_date DESC);
                
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    farm_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    state_changed INTEGER NOT NULL DEFAULT 0,
                    state_updates JSON,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                CREATE INDEX IF NOT EXISTS idx_conversations_farm 
                    ON conversations(farm_id, created_at DESC);
                
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    farm_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    data JSON NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                CREATE INDEX IF NOT EXISTS idx_events_farm_type 
                    ON events(farm_id, event_type, created_at DESC);
            """)

    # ========== USERS & OWNERSHIP ==========

    def create_user(self, email: str, password_hash: str) -> dict:
        user_id = "u_" + secrets.token_hex(16)
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)",
                (user_id, email.lower().strip(), password_hash)
            )
        return {"user_id": user_id, "email": email.lower().strip()}

    def get_user_by_email(self, email: str) -> Optional[dict]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT id, email, password_hash FROM users WHERE email = ?",
                (email.lower().strip(),)
            ).fetchone()
            if not row:
                return None
            return {"user_id": row["id"], "email": row["email"], "password_hash": row["password_hash"]}

    def get_user_by_id(self, user_id: str) -> Optional[dict]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT id, email FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()
            if not row:
                return None
            return {"user_id": row["id"], "email": row["email"]}

    def claim_farm(self, farm_id: str, user_id: str) -> None:
        with self._get_conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO farm_ownership (farm_id, user_id) VALUES (?, ?)",
                (farm_id, user_id)
            )

    def get_farm_owner(self, farm_id: str) -> Optional[str]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT user_id FROM farm_ownership WHERE farm_id = ?",
                (farm_id,)
            ).fetchone()
            return row["user_id"] if row else None

    def user_owns_farm(self, user_id: str, farm_id: str) -> bool:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM farm_ownership WHERE farm_id = ? AND user_id = ?",
                (farm_id, user_id)
            ).fetchone()
            return row is not None
    
    # ========== PROFILES ==========
    
    def save_profile(self, profile: FarmerProfile) -> None:
        data = json.dumps(profile.model_dump(mode='json'), default=str)
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO profiles (farm_id, data, updated_at)
                VALUES (?, ?, datetime('now'))
                ON CONFLICT(farm_id) DO UPDATE SET 
                    data = excluded.data,
                    updated_at = datetime('now')
            """, (profile.farm_id, data))
    
    def load_profile(self, farm_id: str) -> Optional[FarmerProfile]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT data FROM profiles WHERE farm_id = ?", (farm_id,)
            ).fetchone()
            if not row:
                return None
            return FarmerProfile(**json.loads(row["data"]))
    
    # ========== STATES ==========
    
    def save_state(self, state: WorldState) -> None:
        data = json.dumps(state.model_dump(mode='json'), default=str)
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO states (farm_id, state_date, data)
                VALUES (?, ?, ?)
                ON CONFLICT(farm_id, state_date) DO UPDATE SET 
                    data = excluded.data
            """, (state.farm_id, state.state_date.isoformat(), data))
    
    def load_latest_state(self, farm_id: str) -> Optional[WorldState]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT data FROM states WHERE farm_id = ? ORDER BY state_date DESC LIMIT 1",
                (farm_id,)
            ).fetchone()
            if not row:
                return None
            return WorldState(**json.loads(row["data"]))
    
    def load_state_by_date(self, farm_id: str, target_date: date) -> Optional[WorldState]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT data FROM states WHERE farm_id = ? AND state_date = ?",
                (farm_id, target_date.isoformat())
            ).fetchone()
            if not row:
                return None
            return WorldState(**json.loads(row["data"]))
    
    # ========== CHECK-INS ==========
    
    def save_checkin(self, checkin: DailyCheckIn) -> None:
        data = json.dumps(checkin.model_dump(mode='json'), default=str)
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO checkins (farm_id, checkin_date, data) VALUES (?, ?, ?)",
                (checkin.farm_id, checkin.checkin_date.isoformat(), data)
            )
    
    def load_recent_checkins(self, farm_id: str, n: int = 7) -> List[DailyCheckIn]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT data FROM checkins WHERE farm_id = ? ORDER BY checkin_date DESC LIMIT ?",
                (farm_id, n)
            ).fetchall()
            return [DailyCheckIn(**json.loads(row["data"])) for row in rows]
    
    # ========== CONVERSATIONS ==========
    
    def save_message(self, farm_id: str, role: str, content: str,
                     state_changed: bool = False, state_updates: dict = None) -> None:
        updates_json = json.dumps(state_updates, default=str) if state_updates else None
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO conversations (farm_id, role, content, state_changed, state_updates) VALUES (?, ?, ?, ?, ?)",
                (farm_id, role, content, int(state_changed), updates_json)
            )
    
    def load_conversation_history(self, farm_id: str, limit: int = 20) -> List[dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT role, content FROM conversations WHERE farm_id = ? ORDER BY id DESC LIMIT ?",
                (farm_id, limit)
            ).fetchall()
            # Reverse to get chronological order
            return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]
    
    # ========== EVENTS (replaces NDJSON log) ==========
    
    def log_event(self, farm_id: str, event_type: str, data: dict) -> None:
        data_json = json.dumps(data, default=str)
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO events (farm_id, event_type, data) VALUES (?, ?, ?)",
                (farm_id, event_type, data_json)
            )
    
    def read_events(self, farm_id: str = None, event_type: str = None, limit: int = 50) -> List[dict]:
        with self._get_conn() as conn:
            query = "SELECT data, created_at FROM events WHERE 1=1"
            params = []
            if farm_id:
                query += " AND farm_id = ?"
                params.append(farm_id)
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            rows = conn.execute(query, params).fetchall()
            return [json.loads(row["data"]) for row in rows]
    
    # ========== MIGRATION ==========
    
    def migrate_from_json(self, json_storage) -> dict:
        """Migrate data from JSONFileStorage to SQLite."""
        from .storage import JSONFileStorage
        
        stats = {"profiles": 0, "states": 0, "checkins": 0}
        
        # Migrate profiles
        if json_storage.profiles_dir.exists():
            for f in json_storage.profiles_dir.glob("*.json"):
                try:
                    with open(f) as fh:
                        profile = FarmerProfile(**json.load(fh))
                    self.save_profile(profile)
                    stats["profiles"] += 1
                except Exception as e:
                    print(f"  Skip profile {f.name}: {e}")
        
        # Migrate states
        if json_storage.states_dir.exists():
            for farm_dir in json_storage.states_dir.iterdir():
                if farm_dir.is_dir():
                    for f in farm_dir.glob("*.json"):
                        try:
                            with open(f) as fh:
                                state = WorldState(**json.load(fh))
                            self.save_state(state)
                            stats["states"] += 1
                        except Exception as e:
                            print(f"  Skip state {f.name}: {e}")
        
        # Migrate checkins
        if json_storage.checkins_dir.exists():
            for farm_dir in json_storage.checkins_dir.iterdir():
                if farm_dir.is_dir():
                    for f in farm_dir.glob("*.json"):
                        try:
                            with open(f) as fh:
                                checkin = DailyCheckIn(**json.load(fh))
                            self.save_checkin(checkin)
                            stats["checkins"] += 1
                        except Exception as e:
                            print(f"  Skip checkin {f.name}: {e}")
        
        return stats
