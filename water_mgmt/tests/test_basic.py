"""Basic smoke tests for water management module"""

from datetime import date
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from water_mgmt.schemas import FarmerProfile, DailyCheckIn, WorldState
from water_mgmt.storage import JSONFileStorage
from water_mgmt.state import StateManager
from water_mgmt.weather import StubWeatherAdapter
from water_mgmt.hydrology import HydrologyCoreSimulator
from water_mgmt.rules_handbook import HandbookRuleSet
from water_mgmt.rules_general import GeneralRuleSet
from water_mgmt.resolver import PolicyResolver
from water_mgmt.planner import WaterManagementPlanner
from water_mgmt.llm_extractor import MockSlotExtractor


def test_profile_creation():
    """Test creating and saving a profile"""
    print("\n✓ Testing profile creation...")
    
    storage = JSONFileStorage()
    
    profile = FarmerProfile(
        farmer_id="test_farmer",
        farm_id="test_farm",
        province="An Giang",
        soil_type="alluvial",
        irrigation_access=True,
        awd_tube_available=True,
        sowing_date=date(2024, 1, 15)
    )
    
    storage.save_profile(profile)
    loaded = storage.load_profile("test_farm")
    
    assert loaded is not None
    assert loaded.farm_id == "test_farm"
    assert loaded.province == "An Giang"
    
    print("  ✓ Profile created and loaded successfully")


def test_state_initialization():
    """Test state initialization from profile"""
    print("\n✓ Testing state initialization...")
    
    storage = JSONFileStorage()
    state_manager = StateManager()
    
    profile = FarmerProfile(
        farmer_id="test_farmer",
        farm_id="test_farm_2",
        province="An Giang",
        soil_type="alluvial",
        irrigation_access=True,
        sowing_date=date(2024, 1, 1)
    )
    
    state = state_manager.build_initial_state(profile, date(2024, 2, 15))
    
    assert state.farm_id == "test_farm_2"
    assert state.soil_type == "alluvial"
    assert state.irrigation_access == True
    assert state.das == 45  # 45 days after sowing
    
    print(f"  ✓ State initialized, DAS={state.das}, stage={state.growth_stage}")


def test_awd_trigger():
    """Test AWD irrigation trigger"""
    print("\n✓ Testing AWD trigger logic...")
    
    handbook = HandbookRuleSet()
    
    # Create state with water table at trigger depth
    state = WorldState(
        farm_id="test_farm",
        state_date=date.today(),
        soil_type="alluvial",
        bund_height_class="medium",
        leveled=True,
        irrigation_access=True,
        drainage_access=True,
        regime="AWD",
        water_table_depth_cm=16.0,  # Above 15cm threshold
        soil_cracks="small"
    )
    
    result = handbook.evaluate_awd_trigger(state)
    
    assert result["triggered"] == True
    assert "HANDBOOK" in result["source"]
    
    print(f"  ✓ AWD trigger activated: {result['reason']}")


def test_hydrology_simulation():
    """Test water balance simulation"""
    print("\n✓ Testing hydrology simulation...")
    
    hydrology = HydrologyCoreSimulator()
    weather_adapter = StubWeatherAdapter()
    
    # Set weather
    weather_adapter.set_weather(rain_24h=10.0, et0=5.0)
    weather = weather_adapter.get_forecast({})
    
    # Initial state
    state = WorldState(
        farm_id="test_farm",
        state_date=date.today(),
        soil_type="alluvial",
        bund_height_class="medium",
        leveled=True,
        irrigation_access=True,
        drainage_access=True,
        ponded_water_cm=2.0
    )
    
    # Simulate irrigation
    new_state = hydrology.step(state, "IRRIGATE", weather, {"refill_target_cm": 4.0})
    
    assert new_state.ponded_water_cm > state.ponded_water_cm
    
    print(f"  ✓ Simulation: {state.ponded_water_cm:.1f}cm → {new_state.ponded_water_cm:.1f}cm")


def test_planner_recommendation():
    """Test planner produces valid recommendation"""
    print("\n✓ Testing planner...")
    
    # Initialize components
    hydrology = HydrologyCoreSimulator()
    handbook = HandbookRuleSet()
    general = GeneralRuleSet()
    resolver = PolicyResolver(handbook, general)
    planner = WaterManagementPlanner(hydrology, resolver)
    weather_adapter = StubWeatherAdapter()
    
    # Create state needing irrigation (AWD trigger)
    state = WorldState(
        farm_id="test_farm",
        state_date=date.today(),
        soil_type="alluvial",
        bund_height_class="medium",
        leveled=True,
        irrigation_access=True,
        drainage_access=True,
        regime="AWD",
        water_table_depth_cm=16.0,  # Above trigger
        growth_stage="tillering"
    )
    
    # Get forecast
    forecast = weather_adapter.get_multi_day_forecast({}, days=7)
    
    # Get advice
    advice = planner.plan(state, forecast)
    
    assert advice.recommended_action in ["IRRIGATE", "HOLD", "DRAIN", "ALERT_ONLY"]
    assert advice.confidence in ["high", "medium", "low"]
    assert len(advice.rationale) > 0
    
    print(f"  ✓ Recommendation: {advice.recommended_action}")
    print(f"  ✓ Confidence: {advice.confidence}")
    print(f"  ✓ Rationale items: {len(advice.rationale)}")
    
    # Check provenance
    has_handbook = any(r.source_type == "HANDBOOK" for r in advice.rationale)
    print(f"  ✓ Has handbook provenance: {has_handbook}")


def test_slot_extraction():
    """Test mock slot extraction"""
    print("\n✓ Testing slot extraction...")
    
    extractor = MockSlotExtractor()
    
    # Test clear AWD tube measurement
    result = extractor.extract("water table is 15 cm below soil surface")
    
    assert "water_table_depth_cm" in result.slots
    assert result.slots["water_table_depth_cm"] == 15.0
    assert result.confidence > 0.5
    
    print(f"  ✓ Extracted: {result.slots}")
    print(f"  ✓ Confidence: {result.confidence}")
    
    # Test ambiguous measurement
    result2 = extractor.extract("my water level is 10 cm now")
    
    if result2.need_clarification:
        print(f"  ✓ Clarification requested: {result2.need_clarification[0].question}")


def test_end_to_end():
    """Test complete workflow"""
    print("\n✓ Testing end-to-end workflow...")
    
    # Setup
    storage = JSONFileStorage()
    state_manager = StateManager()
    weather_adapter = StubWeatherAdapter()
    hydrology = HydrologyCoreSimulator()
    handbook = HandbookRuleSet()
    general = GeneralRuleSet()
    resolver = PolicyResolver(handbook, general)
    planner = WaterManagementPlanner(hydrology, resolver)
    
    # Create profile
    profile = FarmerProfile(
        farmer_id="e2e_farmer",
        farm_id="e2e_farm",
        province="An Giang",
        soil_type="alluvial",
        irrigation_access=True,
        awd_tube_available=True,
        sowing_date=date(2024, 1, 1)
    )
    storage.save_profile(profile)
    
    # Create check-in
    checkin = DailyCheckIn(
        farm_id="e2e_farm",
        checkin_date=date(2024, 2, 15),
        measurement_mode="awd_tube",
        water_table_depth_cm=16.0,
        soil_cracks="small"
    )
    
    # Build state
    state = state_manager.build_initial_state(profile, date(2024, 2, 15))
    state = state_manager.apply_checkin(state, checkin)
    
    # Get weather
    weather = weather_adapter.get_forecast({})
    forecast = weather_adapter.get_multi_day_forecast({}, days=7)
    
    state.rain_last_24h_mm = weather.rain_last_24h_mm
    state.rain_next_72h_mm = weather.rain_next_72h_mm
    
    # Get advice
    advice = planner.plan(state, forecast)
    
    # Save
    storage.save_state(state)
    
    # Verify
    loaded_state = storage.load_latest_state("e2e_farm")
    assert loaded_state is not None
    
    print(f"  ✓ Complete workflow executed")
    print(f"  ✓ Final recommendation: {advice.recommended_action}")
    print(f"  ✓ State saved and reloaded")


def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 WATER MANAGEMENT MODULE - SMOKE TESTS")
    print("=" * 60)
    
    tests = [
        test_profile_creation,
        test_state_initialization,
        test_awd_trigger,
        test_hydrology_simulation,
        test_planner_recommendation,
        test_slot_extraction,
        test_end_to_end
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n❌ FAILED: {test.__name__}")
            print(f"   Error: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("✅ All tests passed!")
    else:
        print(f"⚠️  {failed} test(s) failed")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
