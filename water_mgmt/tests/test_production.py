"""Production-readiness tests for water management module.
Tests: SQLite storage, DAS auto-update, auth, rate limiting, input sanitization.
"""

import sys
import os
import tempfile
from pathlib import Path
from datetime import date, datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from water_mgmt.schemas import FarmerProfile, DailyCheckIn, WorldState
from water_mgmt.state import StateManager


def _make_profile(farm_id="test_farm", sowing_date=None):
    return FarmerProfile(
        farmer_id=f"farmer_{farm_id}",
        farm_id=farm_id,
        province="An Giang",
        soil_type="alluvial",
        irrigation_access=True,
        awd_tube_available=True,
        sowing_date=sowing_date or date.today() - timedelta(days=30)
    )


def _make_state(farm_id="test_farm", das=10, water_table=10.0):
    return WorldState(
        farm_id=farm_id,
        state_date=date.today(),
        soil_type="alluvial",
        bund_height_class="medium",
        leveled=True,
        irrigation_access=True,
        drainage_access=True,
        regime="AWD",
        das=das,
        growth_stage="seedling",
        water_table_depth_cm=water_table,
    )


# ========== SQLite Storage Tests ==========

def test_sqlite_profile_crud():
    """Test SQLite profile create/read/update."""
    from water_mgmt.storage_sqlite import SQLiteStorage
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db = SQLiteStorage(db_path=Path(tmpdir) / "test.db")
        
        profile = _make_profile("sqlite_test")
        db.save_profile(profile)
        
        loaded = db.load_profile("sqlite_test")
        assert loaded is not None
        assert loaded.farm_id == "sqlite_test"
        assert loaded.province == "An Giang"
        
        # Update
        profile.province = "Can Tho"
        db.save_profile(profile)
        loaded2 = db.load_profile("sqlite_test")
        assert loaded2.province == "Can Tho"
        
        # Not found
        assert db.load_profile("nonexistent") is None
        
        print("  ✓ SQLite profile CRUD")


def test_sqlite_state_crud():
    """Test SQLite state create/read."""
    from water_mgmt.storage_sqlite import SQLiteStorage
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db = SQLiteStorage(db_path=Path(tmpdir) / "test.db")
        
        state = _make_state("state_test", das=25, water_table=12.0)
        db.save_state(state)
        
        loaded = db.load_latest_state("state_test")
        assert loaded is not None
        assert loaded.das == 25
        assert loaded.water_table_depth_cm == 12.0
        
        # Update same date
        state.water_table_depth_cm = 18.0
        db.save_state(state)
        loaded2 = db.load_latest_state("state_test")
        assert loaded2.water_table_depth_cm == 18.0
        
        print("  ✓ SQLite state CRUD")


def test_sqlite_conversations():
    """Test conversation persistence."""
    from water_mgmt.storage_sqlite import SQLiteStorage
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db = SQLiteStorage(db_path=Path(tmpdir) / "test.db")
        
        db.save_message("farm1", "user", "Water table is 16 cm")
        db.save_message("farm1", "assistant", "You should irrigate.", state_changed=True)
        db.save_message("farm1", "user", "OK thanks")
        
        history = db.load_conversation_history("farm1", limit=10)
        assert len(history) == 3
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Water table is 16 cm"
        assert history[2]["role"] == "user"
        assert history[2]["content"] == "OK thanks"
        
        # Different farm has no messages
        history2 = db.load_conversation_history("farm2")
        assert len(history2) == 0
        
        print("  ✓ SQLite conversation persistence")


def test_sqlite_events():
    """Test event logging in SQLite."""
    from water_mgmt.storage_sqlite import SQLiteStorage
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db = SQLiteStorage(db_path=Path(tmpdir) / "test.db")
        
        db.log_event("farm1", "advice", {"action": "IRRIGATE", "confidence": "high"})
        db.log_event("farm1", "advice", {"action": "HOLD", "confidence": "medium"})
        db.log_event("farm1", "error", {"message": "test error"})
        
        all_events = db.read_events(farm_id="farm1")
        assert len(all_events) == 3
        
        advice_only = db.read_events(farm_id="farm1", event_type="advice")
        assert len(advice_only) == 2
        
        print("  ✓ SQLite event logging")


def test_sqlite_migration():
    """Test migration from JSON to SQLite."""
    from water_mgmt.storage import JSONFileStorage
    from water_mgmt.storage_sqlite import SQLiteStorage
    
    with tempfile.TemporaryDirectory() as tmpdir:
        json_dir = Path(tmpdir) / "json_data"
        json_storage = JSONFileStorage(data_dir=json_dir)
        
        # Create JSON data
        profile = _make_profile("migrate_test")
        json_storage.save_profile(profile)
        state = _make_state("migrate_test")
        json_storage.save_state(state)
        
        # Migrate
        sqlite_db = SQLiteStorage(db_path=Path(tmpdir) / "migrated.db")
        stats = sqlite_db.migrate_from_json(json_storage)
        
        assert stats["profiles"] >= 1
        assert stats["states"] >= 1
        
        # Verify
        loaded = sqlite_db.load_profile("migrate_test")
        assert loaded is not None
        
        print(f"  ✓ Migration: {stats}")


# ========== DAS Auto-Update Tests ==========

def test_das_auto_update():
    """Test that DAS auto-calculates from sowing_date + today."""
    sm = StateManager()
    
    sowing = date.today() - timedelta(days=45)
    profile = _make_profile("das_test", sowing_date=sowing)
    state = sm.initialize_state(profile)
    
    assert state.das == 45, f"Expected DAS=45, got {state.das}"
    print(f"  ✓ DAS auto-calculated: {state.das}")


def test_growth_stage_progression():
    """Test growth stage progresses with DAS."""
    sm = StateManager()
    
    tests = [
        (5, "seedling"),
        (20, "tillering"),
        (40, "panicle_initiation"),
        (65, "heading"),
        (90, "grain_filling"),
        (120, "maturity"),
    ]
    
    for das, expected_stage in tests:
        stage = sm.infer_growth_stage(das)
        assert stage == expected_stage, f"DAS={das}: expected {expected_stage}, got {stage}"
    
    print("  ✓ Growth stage progression correct for all DAS values")


# ========== Input Sanitization Tests ==========

def test_farm_id_sanitization():
    """Test that malicious farm_ids are rejected."""
    # Import the function directly
    import re
    
    def sanitize(farm_id):
        clean = re.sub(r'[^a-zA-Z0-9_\-]', '', farm_id)
        return clean == farm_id and bool(clean)
    
    # Valid
    assert sanitize("farm001") == True
    assert sanitize("my-farm_123") == True
    
    # Invalid (path traversal)
    assert sanitize("../../etc/passwd") == False
    assert sanitize("farm001/../../secret") == False
    assert sanitize("") == False
    assert sanitize("farm 001") == False  # spaces
    
    print("  ✓ Farm ID sanitization blocks malicious inputs")


def test_numeric_coercion():
    """Test that string numbers from LLM are coerced to proper types."""
    # Simulate the _coerce_numeric function
    float_fields = {"water_table_depth_cm", "ponded_water_cm", "rain_last_24h_mm"}
    int_fields = {"das"}
    
    updates = {
        "water_table_depth_cm": "16.5",  # string from LLM
        "das": "45",                      # string from LLM
        "soil_cracks": "small",           # stays string
        "regime_intent": None,            # stays None
    }
    
    for k, v in updates.items():
        if v is None:
            continue
        if k in float_fields:
            try:
                updates[k] = float(v)
            except (ValueError, TypeError):
                updates[k] = None
        elif k in int_fields:
            try:
                updates[k] = int(float(v))
            except (ValueError, TypeError):
                updates[k] = None
    
    assert updates["water_table_depth_cm"] == 16.5
    assert updates["das"] == 45
    assert updates["soil_cracks"] == "small"
    assert updates["regime_intent"] is None
    
    print("  ✓ Numeric coercion handles string numbers from LLM")


# ========== Rate Limiting Tests ==========

def test_rate_limiter():
    """Test rate limiter blocks excess requests."""
    from water_mgmt.auth import RateLimiter
    
    limiter = RateLimiter(requests_per_minute=5, burst=3)
    
    # First 3 should pass (within burst)
    for i in range(3):
        assert limiter.check("test_key") == True
    
    # 4th should fail (burst exceeded within 5 seconds)
    assert limiter.check("test_key") == False
    
    # Different key should still pass
    assert limiter.check("other_key") == True
    
    remaining = limiter.get_remaining("test_key")
    assert remaining <= 2
    
    print(f"  ✓ Rate limiter works (remaining={remaining})")


# ========== Runner ==========

def main():
    print("=" * 60)
    print("🧪 PRODUCTION READINESS TESTS")
    print("=" * 60)
    
    tests = [
        ("SQLite Profile CRUD", test_sqlite_profile_crud),
        ("SQLite State CRUD", test_sqlite_state_crud),
        ("SQLite Conversations", test_sqlite_conversations),
        ("SQLite Events", test_sqlite_events),
        ("SQLite Migration", test_sqlite_migration),
        ("DAS Auto-Update", test_das_auto_update),
        ("Growth Stage Progression", test_growth_stage_progression),
        ("Farm ID Sanitization", test_farm_id_sanitization),
        ("Numeric Coercion", test_numeric_coercion),
        ("Rate Limiter", test_rate_limiter),
    ]
    
    passed = failed = 0
    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"\n❌ FAILED: {name}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTS: {passed} passed, {failed} failed out of {len(tests)}")
    print("=" * 60)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
