"""FastAPI endpoints for water management module"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from pathlib import Path

from .schemas import (
    FarmerProfile, DailyCheckIn, WorldState, AdviceResponse, 
    ChatExtractionResult
)
from .storage import JSONFileStorage
from .storage_sqlite import SQLiteStorage
from .state import StateManager
from .llm_extractor import LLMSlotExtractor, MockSlotExtractor
from .weather import StubWeatherAdapter, OpenWeatherAdapter
from .hydrology import HydrologyCoreSimulator
from .rules_handbook import HandbookRuleSet
from .rules_general import GeneralRuleSet
from .resolver import PolicyResolver
from .planner import WaterManagementPlanner
from .logger import EventLogger
from .explain import ExplanationGenerator
from .config import OPENAI_API_KEY, WEATHER_API_KEY
from .auth import verify_api_key, rate_limiter
from .log_config import log
from .user_auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

@asynccontextmanager
async def lifespan(app):
    """Startup / shutdown events"""
    print("=" * 60)
    print("🌾 Rice Water Management API Starting")
    print("=" * 60)
    print(f"Handbook loaded: {len(handbook.rules)} rules")
    print(f"General rules: {len(general.rules)} rules")
    print(f"Extractor: {'LLM' if isinstance(extractor, LLMSlotExtractor) else 'Mock'}")
    print(f"Mode: {resolver.mode}")
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        print(f"UI available at: http://localhost:8000/")
    else:
        print("Warning: Static files not found")
    print("=" * 60)
    yield

# Initialize FastAPI app
app = FastAPI(
    title="Rice Water Management API",
    description="Production-grade water management for rice farming in Mekong Delta",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware - restrict in production via RICE_CORS_ORIGINS env var
import os as _os
_cors_origins = _os.getenv("RICE_CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
storage = SQLiteStorage()
json_storage = JSONFileStorage()  # Keep for migration
from .state_observations import ObservationRecorder
_observer = ObservationRecorder(storage=storage)
state_manager = StateManager(observer=_observer)
# Weather adapter (real API with fallback to stub)
try:
    if WEATHER_API_KEY:
        weather_adapter = OpenWeatherAdapter(api_key=WEATHER_API_KEY)
        print(f"Weather: OpenWeatherMap (live)")
    else:
        weather_adapter = StubWeatherAdapter()
        print("Weather: Stub (no WEATHER_API key)")
except Exception as e:
    print(f"Weather: Stub (init failed: {e})")
    weather_adapter = StubWeatherAdapter()
hydrology = HydrologyCoreSimulator()
handbook = HandbookRuleSet()
general = GeneralRuleSet()
resolver = PolicyResolver(handbook, general, mode="handbook_plus")
planner = WaterManagementPlanner(hydrology, resolver)
logger = EventLogger()

# LLM extractor (with fallback to mock if no API key)
try:
    if OPENAI_API_KEY:
        extractor = LLMSlotExtractor()
        print(f"Extractor: OpenAI LLM ({extractor.model})")
    else:
        print("Extractor: Mock (no OPENAI_API_KEY)")
        extractor = MockSlotExtractor()
except Exception as e:
    print(f"Extractor: Mock (LLM init failed: {e})")
    extractor = MockSlotExtractor()


# ============================================================================
# PROFILE ENDPOINTS
# ============================================================================

class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/auth/register")
def register_user(payload: RegisterRequest):
    """Register a user with email+password."""
    email = (payload.email or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email")
    if not payload.password or len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    existing = storage.get_user_by_email(email) if hasattr(storage, "get_user_by_email") else None
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = storage.create_user(email=email, password_hash=hash_password(payload.password))
    token = create_access_token(user_id=user["user_id"], email=user["email"])
    return {"token": token, "user": {"user_id": user["user_id"], "email": user["email"]}}


@app.post("/auth/login")
def login_user(payload: LoginRequest):
    """Login with email+password."""
    email = (payload.email or "").strip().lower()
    user = storage.get_user_by_email(email) if hasattr(storage, "get_user_by_email") else None
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not verify_password(payload.password or "", user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user_id=user["user_id"], email=user["email"])
    return {"token": token, "user": {"user_id": user["user_id"], "email": user["email"]}}


@app.get("/auth/me")
def auth_me(current_user: Optional[dict] = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not logged in")
    return {"user": current_user}


@app.get("/farms")
def list_farms(current_user: Optional[dict] = Depends(get_current_user)):
    """List all farms owned by the logged-in user."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")
    farms = []
    if hasattr(storage, "get_farms_for_user"):
        farms = storage.get_farms_for_user(current_user["user_id"])
    return {"farms": farms}


class ClaimFarmRequest(BaseModel):
    farm_id: str


@app.post("/farms/claim")
def claim_farm(payload: ClaimFarmRequest, current_user: Optional[dict] = Depends(get_current_user)):
    """Claim ownership of an existing farm_id for the logged-in user."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")
    farm_id = _sanitize_farm_id(payload.farm_id)
    owner = storage.get_farm_owner(farm_id) if hasattr(storage, "get_farm_owner") else None
    if owner and owner != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Farm is already owned by another user")
    if hasattr(storage, "claim_farm"):
        storage.claim_farm(farm_id, current_user["user_id"])
    return {"status": "success", "farm_id": farm_id}


def _require_farm_access(farm_id: str, current_user: Optional[dict]):
    """Enforce farm ownership if user auth is enabled.
    In optional-auth mode, anonymous access is allowed.
    """
    # If not logged in, allow only when auth mode is optional.
    # get_current_user already raises 401 in required mode.
    if not current_user:
        return

    if hasattr(storage, "get_farm_owner") and hasattr(storage, "user_owns_farm"):
        owner = storage.get_farm_owner(farm_id)
        if owner is None:
            # Unclaimed farm: don't auto-claim on read; allow read to ease migration/dev.
            return
        if not storage.user_owns_farm(current_user["user_id"], farm_id):
            raise HTTPException(status_code=403, detail="You do not have access to this farm")


@app.post("/profile", response_model=dict)
def create_or_update_profile(profile: FarmerProfile, current_user: Optional[dict] = Depends(get_current_user)):
    """Create or update farmer profile"""
    try:
        profile.farm_id = _sanitize_farm_id(profile.farm_id)
        _require_farm_access(profile.farm_id, current_user)
        storage.save_profile(profile)

        # Auto-claim farm for logged-in users
        if current_user and hasattr(storage, "claim_farm"):
            storage.claim_farm(profile.farm_id, current_user["user_id"])

        # Auto-create initial state so DAS/stage/soil_type are available immediately
        try:
            existing_state = storage.load_latest_state(profile.farm_id)
            if not existing_state:
                initial_state = state_manager.initialize_state(profile)
                # Populate weather data from real API
                location = {"province": profile.province}
                weather = weather_adapter.get_forecast(location)
                initial_state.rain_last_24h_mm = weather.rain_last_24h_mm
                initial_state.rain_next_72h_mm = weather.rain_next_72h_mm
                initial_state.et0_next_24h_mm = weather.et0_next_24h_mm
                initial_state.temperature_next_24h_c = weather.temperature_next_24h_c
                storage.save_state(initial_state)
        except Exception:
            pass  # Non-fatal — state will be created on first chat

        return {
            "status": "success",
            "farm_id": profile.farm_id,
            "message": "Profile saved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save profile: {str(e)}")


@app.get("/profile/{farm_id}", response_model=FarmerProfile)
def get_profile(farm_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    """Get farmer profile"""
    farm_id = _sanitize_farm_id(farm_id)
    _require_farm_access(farm_id, current_user)
    profile = storage.load_profile(farm_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


# ============================================================================
# CHECK-IN ENDPOINTS
# ============================================================================

@app.post("/checkin", response_model=AdviceResponse)
def submit_checkin(checkin: DailyCheckIn, current_user: Optional[dict] = Depends(get_current_user)):
    """Submit daily check-in and get advice"""
    try:
        checkin.farm_id = _sanitize_farm_id(checkin.farm_id)
        _require_farm_access(checkin.farm_id, current_user)
        # Load or create state
        state = storage.load_latest_state(checkin.farm_id)
        
        if not state:
            # Create initial state from profile
            profile = storage.load_profile(checkin.farm_id)
            if not profile:
                raise HTTPException(status_code=404, detail="Farm profile not found")
            
            state = state_manager.build_initial_state(profile, checkin.checkin_date)
        
        # Apply check-in
        state = state_manager.apply_checkin(state, checkin)
        
        # Get weather using actual profile province
        profile = storage.load_profile(checkin.farm_id)
        location = {"province": profile.province if profile else "An Giang"}
        weather = weather_adapter.get_forecast(location)
        weather_forecast = weather_adapter.get_multi_day_forecast(location, days=7)
        
        # Update state with weather
        state.rain_last_24h_mm = weather.rain_last_24h_mm
        state.rain_next_72h_mm = weather.rain_next_72h_mm
        state.et0_next_24h_mm = weather.et0_next_24h_mm
        state.temperature_next_24h_c = weather.temperature_next_24h_c
        
        # Run planner
        advice = planner.plan(state, weather_forecast)
        
        # Save state
        storage.save_state(state)
        
        # Log event
        logger.log_advice_event(state, advice, checkin=checkin)
        
        return advice
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process check-in: {str(e)}")


# ============================================================================
# CHAT ENDPOINTS
# ============================================================================

class ChatRequest(BaseModel):
    """Unified chat request"""
    farm_id: str
    message: str
    conversation_history: Optional[list] = []

@app.post("/chat")
def unified_chat(request: ChatRequest, current_user: Optional[dict] = Depends(get_current_user)):
    """World-model-driven conversational assistant.
    
    Every message flows through:
    1. Build farm context (profile + current state + planner assessment)
    2. LLM extracts state changes AND generates conversational response
    3. If state changed → update world model → re-run planner
    4. Return conversational response + updated state
    """
    try:
        farm_id = _sanitize_farm_id(request.farm_id)

        _require_farm_access(farm_id, current_user)
        
        # Rate limiting per farm_id
        if not rate_limiter.check(farm_id):
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please wait a moment before trying again."
            )
        profile = storage.load_profile(farm_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Farm profile not found")
        
        state = storage.load_latest_state(farm_id) or state_manager.initialize_state(profile)
        
        # Auto-update DAS and growth stage from sowing_date + today
        state = _refresh_time_fields(state, profile)
        
        # Run planner on current state to give LLM assessment context
        location = {"province": profile.province}
        weather_forecast = weather_adapter.get_multi_day_forecast(location, days=7)
        current_advice = planner.plan(state, weather_forecast)
        
        # Build farm context for the LLM (now includes weather)
        farm_context = _build_farm_context(profile, state, weather_forecast)
        planner_assessment = _build_planner_assessment(state, current_advice)
        
        # Load persisted conversation history, merge with client-sent history
        db_history = storage.load_conversation_history(farm_id, limit=10) if hasattr(storage, 'load_conversation_history') else []
        history = db_history if db_history else (request.conversation_history or [])
        
        # Save user message to DB
        if hasattr(storage, 'save_message'):
            storage.save_message(farm_id, "user", request.message)
        
        # Unified LLM call: extract state + generate response
        if isinstance(extractor, LLMSlotExtractor):
            llm_result = extractor.world_model_chat(
                request.message,
                farm_context,
                planner_assessment,
                history
            )
        else:
            # Mock fallback: use old extraction + mock response
            llm_result = _mock_world_model_chat(request.message, state, farm_context)
        
        state_updates = llm_result.get("state_updates", {})
        state_changed = llm_result.get("state_changed", False)
        response_text = llm_result.get("response", "")
        
        # Debug: log what the LLM extracted
        log.info(f"[WORLD MODEL] state_changed={state_changed}, updates={state_updates}")
        
        # Always update weather data on the state (even if no state change from user)
        state = state_manager.update_state(state, profile, weather_forecast[0])
        
        # If state changed, merge LLM-extracted updates into world model
        advice_data = None
        if state_changed and state_updates:
            # Normalize keys: LLM may return "Regime intent" instead of "regime_intent"
            normalized = {}
            for k, v in state_updates.items():
                norm_key = k.lower().replace(" ", "_")
                normalized[norm_key] = v
            state_updates = normalized
            
            # Coerce string numbers to actual numbers and filter out nulls
            state_updates = _coerce_numeric(state_updates)
            clean_updates = {k: v for k, v in state_updates.items() if v is not None}
            
            if clean_updates:
                # Merge extracted state into world model
                state = state_manager.merge_extracted_data(state, clean_updates, trigger_message=request.message)
                
                # Re-run planner with updated state
                new_advice = planner.plan(state, weather_forecast)
                advice_data = new_advice.model_dump(mode='json')
                
                # Log the advice event
                try:
                    logger.log_advice_event(state, new_advice, user_message=request.message)
                except Exception:
                    pass
        
        # Always save state (weather + DAS are refreshed every call)
        storage.save_state(state)
        
        # Save assistant response to DB
        if hasattr(storage, 'save_message'):
            storage.save_message(
                farm_id, "assistant", response_text,
                state_changed=state_changed,
                state_updates=state_updates if state_changed else None
            )
        
        return {
            "type": "conversation",
            "response": response_text,
            "state_changed": state_changed,
            "state_updates": {k: v for k, v in state_updates.items() if v is not None} if state_changed else {},
            "state": {
                "das": state.das,
                "growth_stage": state.growth_stage,
                "regime": state.regime,
                "water_table_depth_cm": state.water_table_depth_cm,
                "ponded_water_cm": state.ponded_water_cm,
                "soil_cracks": state.soil_cracks
            },
            "advice": advice_data,
            "confidence": llm_result.get("confidence", 0.5)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(request.farm_id, "chat_error", str(e), {"message": request.message})
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


def _refresh_time_fields(state, profile):
    """Auto-update DAS, growth stage, and state_date from sowing_date + today.
    Fixes bug where DAS was frozen from first state creation."""
    today = date.today()
    state = state.model_copy(deep=True)
    state.state_date = today
    
    sowing = profile.sowing_date or profile.transplant_date if profile else None
    if sowing:
        state.das = (today - sowing).days
        state.growth_stage = state_manager.infer_growth_stage(state.das)
    
    state.last_updated = datetime.now()
    return state


def _sanitize_farm_id(farm_id: str) -> str:
    """Prevent path traversal and invalid characters in farm_id."""
    import re
    clean = re.sub(r'[^a-zA-Z0-9_\-]', '', farm_id)
    if not clean or clean != farm_id:
        raise HTTPException(status_code=400, detail="Invalid farm_id. Use only letters, numbers, hyphens, underscores.")
    return clean


def _coerce_numeric(updates: dict) -> dict:
    """Coerce LLM-returned string numbers to actual numbers.
    Fixes bug where LLM returns '16' instead of 16."""
    float_fields = {"water_table_depth_cm", "ponded_water_cm", "rain_last_24h_mm"}
    int_fields = {"das"}
    
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
    return updates


def _build_farm_context(profile, state, weather_forecast=None):
    """Build comprehensive farm context for the world-model LLM"""
    parts = []
    
    if profile:
        parts.append("FARMER PROFILE:")
        parts.append(f"  Farm ID: {profile.farm_id}")
        parts.append(f"  Province: {profile.province}")
        parts.append(f"  Soil Type: {profile.soil_type}")
        parts.append(f"  Irrigation Access: {'Yes' if profile.irrigation_access else 'No'}")
        parts.append(f"  Drainage Access: {'Yes' if profile.drainage_access else 'No'}")
        parts.append(f"  AWD Tube: {'Yes' if profile.awd_tube_available else 'No'}")
        parts.append(f"  Preferred Practice: {profile.preferred_practice}")
        if profile.sowing_date:
            parts.append(f"  Sowing Date: {profile.sowing_date}")
    
    if state:
        parts.append("\nCURRENT WORLD STATE:")
        parts.append(f"  Days After Sowing (DAS): {state.das}")
        parts.append(f"  Growth Stage: {state.growth_stage}")
        parts.append(f"  Water Regime: {state.regime}")
        parts.append(f"  Ponded Water: {state.ponded_water_cm:.1f} cm")
        if state.water_table_depth_cm is not None:
            parts.append(f"  Water Table Depth: {state.water_table_depth_cm:.1f} cm below surface")
        else:
            parts.append("  Water Table Depth: ⚠️ NOT YET MEASURED")
        parts.append(f"  Soil Cracks: {state.soil_cracks}")
        parts.append(f"  Soil Type: {state.soil_type}")
        
        # Flag missing critical data
        missing = []
        if state.water_table_depth_cm is None and profile and profile.awd_tube_available:
            missing.append("water table depth (farmer has AWD tube but hasn't reported a reading)")
        if state.soil_cracks in (None, "unknown"):
            missing.append("soil crack status")
        if state.das is None:
            missing.append("days after sowing")
        if missing:
            parts.append(f"\n  ⚠️ MISSING CRITICAL DATA: {', '.join(missing)}")
    
    if weather_forecast:
        parts.append("\nLIVE WEATHER (OpenWeatherMap):")
        if isinstance(weather_forecast, list) and len(weather_forecast) > 0:
            today_w = weather_forecast[0]
            parts.append(f"  Temperature: {today_w.temperature_next_24h_c}°C")
            parts.append(f"  Rain Last 24h: {today_w.rain_last_24h_mm} mm")
            parts.append(f"  ET₀ (evapotranspiration): {today_w.et0_next_24h_mm} mm/day")
            
            # Sum rain over forecast period
            total_72h = sum(d.rain_last_24h_mm for d in weather_forecast[:3])
            total_5d = sum(d.rain_last_24h_mm for d in weather_forecast[:5])
            parts.append(f"  Rain Forecast Next 3 days: {total_72h:.1f} mm")
            parts.append(f"  Rain Forecast Next 5 days: {total_5d:.1f} mm")
            
            if total_72h >= 20:
                parts.append("  📢 SIGNIFICANT RAIN EXPECTED — irrigation may be unnecessary")
            elif total_72h >= 10:
                parts.append("  🌧️ Moderate rain expected — factor into advice")
    
    return "\n".join(parts)


def _build_planner_assessment(state, advice):
    """Build planner assessment string for the LLM"""
    parts = [
        f"Recommended Action: {advice.recommended_action}",
        f"Confidence: {advice.confidence}",
        f"Regime: {advice.regime_used}",
    ]
    
    if advice.target_description:
        parts.append(f"Target: {advice.target_description}")
    
    if advice.rationale:
        parts.append("Rationale:")
        for r in advice.rationale:
            parts.append(f"  - {r.text} [{r.source_type}]")
    
    if advice.risk_warnings:
        parts.append("Warnings:")
        for w in advice.risk_warnings:
            parts.append(f"  ⚠️ {w}")
    
    if advice.counterfactuals:
        parts.append("What-if scenarios:")
        for cf in advice.counterfactuals:
            parts.append(f"  - {cf.action}: {cf.outcome_summary} (risk: {cf.risk_level})")
    
    return "\n".join(parts)


def _mock_world_model_chat(message, state, context):
    """Mock fallback for world_model_chat when no LLM available"""
    import re
    
    state_updates = {}
    state_changed = False
    
    message_lower = message.lower()
    
    # Extract water table depth
    cm_match = re.search(r'(\d+\.?\d*)\s*cm', message_lower)
    if cm_match:
        value = float(cm_match.group(1))
        if "below" in message_lower or "depth" in message_lower or "table" in message_lower:
            state_updates["water_table_depth_cm"] = value
            state_changed = True
        elif "standing" in message_lower or "ponded" in message_lower:
            state_updates["ponded_water_cm"] = value
            state_changed = True
    
    # Extract cracks
    if "crack" in message_lower:
        if "no " in message_lower or "none" in message_lower:
            state_updates["soil_cracks"] = "none"
        elif "small" in message_lower or "minor" in message_lower or "tiny" in message_lower:
            state_updates["soil_cracks"] = "small"
        elif any(w in message_lower for w in ["deep", "large", "big", "wide", "severe", "major"]):
            state_updates["soil_cracks"] = "deep"
        else:
            state_updates["soil_cracks"] = "visible"
        state_changed = True
    
    # Extract DAS
    das_match = re.search(r'(\d+)\s*(?:das|days?\s*(?:after|since))', message_lower)
    if das_match:
        state_updates["das"] = int(das_match.group(1))
        state_changed = True
    
    # Generate response
    if state_changed:
        wt = state_updates.get("water_table_depth_cm", state.water_table_depth_cm if state else None)
        cracks = state_updates.get("soil_cracks")
        
        if wt is not None and wt >= 15:
            response = f"📊 I've updated your field state. Water table at {wt}cm below surface - this has reached the AWD trigger threshold of 15cm. **You should irrigate now** to 3-5cm shallow ponding per the handbook."
        elif cracks in ["deep", "visible"]:
            response = f"📊 I've updated your field state. {cracks.capitalize()} cracks observed - this indicates the soil is drying significantly. Per the AWD handbook, **you should irrigate now** to 3-5cm shallow ponding."
        elif cracks == "small":
            response = f"📊 I've noted small cracks in your field. The soil is starting to dry but hasn't reached the critical point yet. **Keep monitoring daily** - irrigate if cracks widen or water table drops below 15cm."
        elif cracks == "none":
            response = "📊 I've noted no cracks in your field. Soil moisture looks adequate. **No irrigation needed yet.** Keep monitoring daily."
        elif wt is not None:
            response = f"📊 I've updated your field state. Water table at {wt}cm below surface - still above the 15cm AWD trigger. **No irrigation needed yet.** Keep monitoring daily."
        else:
            response = "📊 I've noted your field observation and updated the state. Based on the handbook, keep monitoring your water levels regularly."
    else:
        response = _generate_mock_response(message, context)
    
    return {
        "state_updates": state_updates,
        "state_changed": state_changed,
        "response": response,
        "confidence": 0.8 if state_changed else 0.5
    }


def _generate_mock_response(message: str, context: str):
    """Generate mock conversational response when LLM is not available"""
    message_lower = message.lower()
    
    # Greetings
    if any(greeting in message_lower for greeting in ["hello", "hi", "hey", "good morning", "good afternoon"]):
        return ("Hello! 👋 I'm your rice water management assistant. I can help you with:\n\n"
                "• When to irrigate based on AWD principles\n"
                "• Understanding your field conditions\n"
                "• Answering questions about rice farming\n"
                "• Explaining water management techniques\n\n"
                "What would you like to know?")
    
    # Should I irrigate questions
    elif any(phrase in message_lower for phrase in ["should i irrigate", "should i water", "need to irrigate", "time to irrigate"]):
        return ("To give you the best irrigation recommendation, I need to know your current field conditions. "
                "Please tell me:\n\n"
                "• Your water table depth (if you have an AWD tube)\n"
                "• OR if you see any soil cracks\n"
                "• OR the standing water level\n\n"
                "For example: 'Water table is 16 cm below surface' or 'I see small cracks in my field'")
    
    # AWD questions
    elif "awd" in message_lower or "alternate wetting" in message_lower:
        return ("🌾 **AWD (Alternate Wetting and Drying)** is a water-saving irrigation technique:\n\n"
                "**How it works:**\n"
                "• Let water level drop to 15cm below soil surface\n"
                "• Then re-irrigate to 3-5cm shallow ponding\n"
                "• Repeat this cycle throughout the season\n\n"
                "**Benefits:**\n"
                "✓ Saves 15-30% water\n"
                "✓ Reduces methane emissions\n"
                "✓ Maintains yield if done correctly\n"
                "✓ Strengthens root systems\n\n"
                "Would you like to know how to implement AWD on your farm?")
    
    # Timing questions
    elif "when" in message_lower and ("irrigate" in message_lower or "water" in message_lower):
        return ("⏰ **When to Irrigate with AWD:**\n\n"
                "**Trigger:** Water table reaches **15 cm** below soil surface (use AWD tube to measure)\n"
                "**OR** when you see visible soil cracks\n\n"
                "**Sensitive Stages (Don't let it get too dry):**\n"
                "• Panicle initiation (35-55 days)\n"
                "• Flowering/heading (60-80 days)\n"
                "• Grain filling (80-110 days)\n\n"
                "During these stages, keep 3-5cm standing water. Would you like me to check your current conditions?")
    
    # Crack questions
    elif "crack" in message_lower:
        return ("**Soil Cracks in Rice Fields:**\n\n"
                "🟢 **Small hairline cracks** → Normal in AWD, no immediate action needed\n"
                "🟡 **Visible cracks** → Monitor closely, consider irrigating soon\n"
                "🔴 **Deep/wide cracks** → Irrigate immediately, especially during sensitive stages\n\n"
                "**AWD Rule:** Irrigate when water table is 15cm below surface OR when cracks appear.\n\n"
                "What kind of cracks are you seeing?")
    
    # How-to questions
    elif "how" in message_lower and ("measure" in message_lower or "check" in message_lower):
        return ("**How to Monitor Your Field:**\n\n"
                "**Best method:** AWD tube (perforated pipe, 15-30cm long)\n"
                "• Install it in your field\n"
                "• Check daily water level inside tube\n"
                "• Irrigate when water reaches 15cm below soil\n\n"
                "**Without tube:**\n"
                "• Watch for soil cracks\n"
                "• Use a stick to feel soil moisture\n"
                "• Measure standing water with ruler\n\n"
                "Would you like help interpreting your measurements?")
    
    # General help
    elif "help" in message_lower or "what can you do" in message_lower:
        return ("I can help you with:\n\n"
                "💧 **Irrigation advice** based on your field measurements\n"
                "📊 **AWD water management** techniques and timing\n"
                "🌱 **Growth stage** specific recommendations\n"
                "❓ **Questions** about rice farming practices\n\n"
                "Just ask me anything, or tell me your current field conditions!")
    
    # Default response
    else:
        return (f"I understand you're asking about: '{message}'\n\n"
                "I'm here to help with rice water management! You can:\n"
                "• Ask me questions about AWD or irrigation\n"
                "• Tell me your field measurements for specific advice\n"
                "• Learn about best practices for your growth stage\n\n"
                "What would you like to know more about?")


# ============================================================================
# STATE ENDPOINTS
# ============================================================================

@app.get("/state/{farm_id}", response_model=WorldState)
def get_state(farm_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    """Get current world state for farm"""
    farm_id = _sanitize_farm_id(farm_id)
    _require_farm_access(farm_id, current_user)
    profile = storage.load_profile(farm_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Farm profile not found")
    state = storage.load_latest_state(farm_id)
    if not state:
        state = state_manager.initialize_state(profile)
        location = {"province": profile.province}
        weather = weather_adapter.get_forecast(location)
        state.rain_last_24h_mm = weather.rain_last_24h_mm
        state.rain_next_72h_mm = weather.rain_next_72h_mm
        state.et0_next_24h_mm = weather.et0_next_24h_mm
        state.temperature_next_24h_c = weather.temperature_next_24h_c
        storage.save_state(state)
    state = _refresh_time_fields(state, profile)
    return state


@app.get("/advice/latest/{farm_id}")
def get_latest_advice(farm_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    """Get latest advice for farm"""
    farm_id = _sanitize_farm_id(farm_id)
    _require_farm_access(farm_id, current_user)
    events = logger.read_events(farm_id=farm_id, event_type="advice", limit=1)
    if not events:
        raise HTTPException(status_code=404, detail="No advice found")
    return events[0]


@app.get("/conversations/{farm_id}")
def get_conversation_history(farm_id: str, limit: int = 50, current_user: Optional[dict] = Depends(get_current_user)):
    """Get persisted conversation history for a farm."""
    farm_id = _sanitize_farm_id(farm_id)
    _require_farm_access(farm_id, current_user)
    if hasattr(storage, 'load_conversation_history'):
        return {"messages": storage.load_conversation_history(farm_id, limit=limit)}
    return {"messages": []}


@app.post("/admin/migrate")
def migrate_json_to_sqlite():
    """One-time migration from JSON files to SQLite."""
    if not hasattr(storage, 'migrate_from_json'):
        raise HTTPException(status_code=400, detail="Storage does not support migration")
    stats = storage.migrate_from_json(json_storage)
    return {"status": "success", "migrated": stats}


# ============================================================================
# WORLD MODEL ENDPOINT
# ============================================================================

@app.get("/worldmodel/{farm_id}")
def get_world_model(farm_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    """Get world model: current state tracked from conversations + AWD handbook rules.
    No fabricated physics - only real data from farmer interactions."""
    try:
        farm_id = _sanitize_farm_id(farm_id)
        _require_farm_access(farm_id, current_user)
        profile = storage.load_profile(farm_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Farm profile not found")
        
        state = storage.load_latest_state(farm_id)
        if not state:
            # Auto-create state from profile if it doesn't exist yet
            state = state_manager.initialize_state(profile)
            location = {"province": profile.province}
            weather = weather_adapter.get_forecast(location)
            state.rain_last_24h_mm = weather.rain_last_24h_mm
            state.rain_next_72h_mm = weather.rain_next_72h_mm
            state.et0_next_24h_mm = weather.et0_next_24h_mm
            state.temperature_next_24h_c = weather.temperature_next_24h_c
            storage.save_state(state)
        
        # Auto-update DAS and growth stage
        state = _refresh_time_fields(state, profile)
        
        # Fetch live weather
        location = {"province": profile.province}
        weather = weather_adapter.get_forecast(location)
        weather_forecast = weather_adapter.get_multi_day_forecast(location, days=5)
        
        # AWD handbook rules (the only source of truth)
        awd_config = handbook.config or {}
        
        # Build AWD assessment based purely on handbook rules
        awd_assessment = _assess_awd_from_handbook(state, awd_config)
        
        # Get conversation history / state change log
        events = logger.read_events(farm_id=farm_id, event_type="advice", limit=10)
        
        # Build weather response
        weather_data = {
            "temperature_c": weather.temperature_next_24h_c,
            "rain_last_24h_mm": weather.rain_last_24h_mm,
            "et0_mm_day": weather.et0_next_24h_mm,
            "forecast_confidence": weather.forecast_confidence,
            "daily_forecast": [
                {
                    "day": i + 1,
                    "rain_mm": round(d.rain_last_24h_mm, 1),
                    "temp_c": round(d.temperature_next_24h_c, 1) if d.temperature_next_24h_c else None,
                }
                for i, d in enumerate(weather_forecast)
            ],
            "rain_next_3d_mm": round(sum(d.rain_last_24h_mm for d in weather_forecast[:3]), 1),
            "rain_next_5d_mm": round(sum(d.rain_last_24h_mm for d in weather_forecast[:5]), 1),
        }
        
        return {
            "state": state.model_dump(mode='json'),
            "profile": profile.model_dump(mode='json') if profile else None,
            "weather": weather_data,
            "awd_rules": {
                "trigger_depth_cm": awd_config.get("awd_trigger_depth_cm", 15),
                "refill_min_cm": awd_config.get("refill_target_min_cm", 3),
                "refill_max_cm": awd_config.get("refill_target_max_cm", 5),
                "schedule": {
                    "day_1_7": "Keep moist for germination",
                    "day_12_22": "Drain - let soil dry to oxygenate roots",
                    "day_28_40": "Drain again - second drying cycle",
                    "sensitive_stages": "Panicle initiation, flowering, grain filling - maintain 3-5cm",
                    "pre_harvest": "Final drying 7-15 days before harvest"
                }
            },
            "awd_assessment": awd_assessment,
            "recent_events": events[:5] if events else []
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"World model error: {str(e)}")


def _assess_awd_from_handbook(state, awd_config):
    """Pure handbook-based assessment using the 10-phase AWD schedule with 3 wet-dry cycles."""
    from .awd_progress import get_current_phase
    
    trigger = awd_config.get("awd_trigger_depth_cm", 15)
    refill_min = awd_config.get("awd_refill_min_cm", 3)
    refill_max = awd_config.get("awd_refill_max_cm", 5)
    
    assessment = {
        "should_irrigate": False,
        "reason": "",
        "das_phase": "",
        "is_sensitive_stage": False,
        "current_phase": None,
    }
    
    das = state.das
    phase = get_current_phase(das)
    
    if phase:
        assessment["current_phase"] = phase
        assessment["das_phase"] = f"{phase['icon']} {phase['name']} (Day {phase['day_start']}–{phase['day_end']}): {phase['rule']}"
        
        # Drying phases: farmer should NOT irrigate unless water table > 15cm
        if phase["is_drying"]:
            wt = state.water_table_depth_cm
            if wt is not None and wt >= trigger:
                assessment["should_irrigate"] = True
                assessment["reason"] = f"Water table at {wt:.1f}cm — reached AWD trigger ({trigger}cm). Re-flood to {refill_min}–{refill_max}cm."
            elif wt is not None:
                assessment["reason"] = f"Drying phase: water table at {wt:.1f}cm (threshold: {trigger}cm). Let field continue drying."
            else:
                assessment["reason"] = f"Drying phase (Cycle {phase.get('cycle', '?')}): allow water table to fall to {trigger}cm before re-flooding."
        else:
            # Non-drying phases: maintain shallow flood
            assessment["reason"] = phase["rule"]
    elif das is not None:
        assessment["das_phase"] = f"Day {das}: Post-season or between phases"
    
    # Sensitive stage check (Phase 8: Day 60–70)
    sensitive = state.growth_stage in ["panicle_initiation", "heading"] or (das is not None and 60 <= das <= 70)
    assessment["is_sensitive_stage"] = sensitive
    
    # AWD trigger check (applies in all phases)
    wt = state.water_table_depth_cm
    if wt is not None:
        if wt >= trigger and not (phase and phase["is_drying"]):
            assessment["should_irrigate"] = True
            assessment["reason"] = f"Water table at {wt:.1f}cm below surface — exceeds AWD trigger of {trigger}cm. Irrigate to {refill_min}–{refill_max}cm."
    
    # Soil crack check
    if state.soil_cracks in ["visible", "deep"]:
        if not (phase and phase["is_drying"]):
            assessment["should_irrigate"] = True
        assessment["reason"] += f" Soil cracks ({state.soil_cracks}) detected — handbook says irrigate."
    
    # Sensitive stage override
    if sensitive:
        assessment["should_irrigate"] = True if (wt is not None and wt > 5) else assessment["should_irrigate"]
        assessment["reason"] += f" ⚠️ SENSITIVE STAGE — avoid deep drying, maintain {refill_min}–{refill_max}cm continuous flood."
    
    return assessment


# ============================================================================
# AWD PROGRESS & CERTIFICATE ENDPOINTS
# ============================================================================

@app.get("/awd-progress/{farm_id}")
def get_awd_progress(farm_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    """Get AWD progress: phase schedule, current phase, verification criteria, certificate eligibility."""
    from .awd_progress import calculate_progress, get_phase_schedule, get_verification_criteria
    farm_id = _sanitize_farm_id(farm_id)
    _require_farm_access(farm_id, current_user)
    
    profile = storage.load_profile(farm_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Farm profile not found")
    
    state = storage.load_latest_state(farm_id)
    if not state:
        state = state_manager.initialize_state(profile)
    state = _refresh_time_fields(state, profile)
    
    # Get observation + checkin history for verification
    observations = _observer.get_observations(farm_id=farm_id, limit=200)
    checkins = []
    if hasattr(storage, 'load_recent_checkins'):
        checkins = storage.load_recent_checkins(farm_id, n=50)
    
    progress = calculate_progress(
        farm_id=farm_id,
        das=state.das,
        state=state,
        observations=observations,
        checkins=checkins,
    )
    
    return {
        "progress": progress.model_dump(mode='json'),
        "schedule": get_phase_schedule(),
        "criteria": get_verification_criteria(),
        "state": {
            "das": state.das,
            "growth_stage": state.growth_stage,
            "ponded_water_cm": state.ponded_water_cm,
            "water_table_depth_cm": state.water_table_depth_cm,
            "soil_cracks": state.soil_cracks,
            "regime": state.regime,
        },
    }


@app.get("/awd-certificate/{farm_id}")
def get_awd_certificate(farm_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    """Generate AWD completion certificate data."""
    from .awd_progress import calculate_progress
    farm_id = _sanitize_farm_id(farm_id)
    _require_farm_access(farm_id, current_user)
    
    profile = storage.load_profile(farm_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Farm profile not found")
    
    state = storage.load_latest_state(farm_id)
    if not state:
        raise HTTPException(status_code=400, detail="No state data — cannot issue certificate")
    state = _refresh_time_fields(state, profile)
    
    observations = _observer.get_observations(farm_id=farm_id, limit=200)
    checkins = []
    if hasattr(storage, 'load_recent_checkins'):
        checkins = storage.load_recent_checkins(farm_id, n=50)
    
    progress = calculate_progress(
        farm_id=farm_id, das=state.das, state=state,
        observations=observations, checkins=checkins,
    )
    
    if not progress.certificate_eligible:
        return {
            "eligible": False,
            "message": "Not all verification criteria have been met yet.",
            "criteria_met": progress.criteria_met,
            "cycles_completed": progress.cycles_completed,
        }
    
    from datetime import datetime as dt
    return {
        "eligible": True,
        "certificate": {
            "title": "AWD Completion Certificate",
            "subtitle": "Alternate Wetting & Drying — Three Wet-Dry Cycles",
            "farm_id": farm_id,
            "farmer_id": profile.farmer_id,
            "province": profile.province,
            "district": profile.district,
            "variety_duration": profile.variety_duration,
            "sowing_date": profile.sowing_date.isoformat() if profile.sowing_date else None,
            "completion_date": dt.now().strftime("%B %d, %Y"),
            "cycles_completed": progress.cycles_completed,
            "criteria_met": progress.criteria_met,
            "das_at_completion": state.das,
            "regime": state.regime,
            "verification_summary": (
                f"Farmer successfully implemented AWD with {progress.cycles_completed} wet-dry cycles. "
                f"All {len([v for v in progress.criteria_met.values() if v])} of 6 verification criteria met."
            ),
        },
    }


# ============================================================================
# STATE OBSERVATION ENDPOINTS
# ============================================================================

@app.get("/state-space")
def get_state_space():
    """Get the formal state space definition — all variables, types, ranges, units."""
    from .state_space import state_space_summary
    return state_space_summary()


@app.get("/state/{farm_id}/observations")
def get_observations(
    farm_id: str,
    field_name: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 50,
    current_user: Optional[dict] = Depends(get_current_user),
):
    """Get observation history for a farm — every recorded state change."""
    farm_id = _sanitize_farm_id(farm_id)
    _require_farm_access(farm_id, current_user)
    observations = _observer.get_observations(
        farm_id=farm_id, field_name=field_name, source=source, limit=limit,
    )
    return {"farm_id": farm_id, "count": len(observations), "observations": observations}


@app.get("/state/{farm_id}/snapshots")
def get_snapshots(
    farm_id: str,
    limit: int = 20,
    current_user: Optional[dict] = Depends(get_current_user),
):
    """Get state snapshot history — full state at each recorded point in time."""
    farm_id = _sanitize_farm_id(farm_id)
    _require_farm_access(farm_id, current_user)
    snapshots = _observer.get_snapshots(farm_id=farm_id, limit=limit)
    return {"farm_id": farm_id, "count": len(snapshots), "snapshots": snapshots}


@app.get("/state/{farm_id}/timeline/{field_name}")
def get_field_timeline(
    farm_id: str,
    field_name: str,
    limit: int = 30,
    current_user: Optional[dict] = Depends(get_current_user),
):
    """Get the value timeline for a single state variable."""
    farm_id = _sanitize_farm_id(farm_id)
    _require_farm_access(farm_id, current_user)
    timeline = _observer.get_field_timeline(
        farm_id=farm_id, field_name=field_name, limit=limit,
    )
    return {"farm_id": farm_id, "field_name": field_name, "count": len(timeline), "timeline": timeline}


# ============================================================================
# CONFIGURATION ENDPOINTS
# ============================================================================

@app.post("/mode/{farm_id}")
def set_mode(farm_id: str, mode: str):
    """Set operational mode for farm"""
    if mode not in ["handbook_only", "handbook_plus", "general_only"]:
        raise HTTPException(status_code=400, detail="Invalid mode")
    
    # Load and update state
    state = storage.load_latest_state(farm_id)
    if not state:
        raise HTTPException(status_code=404, detail="Farm state not found")
    
    state.mode = mode
    storage.save_state(state)
    
    # Update resolver
    resolver.set_mode(mode)
    
    return {"status": "success", "mode": mode}


@app.post("/regime/{farm_id}")
def set_regime(farm_id: str, regime: str):
    """Set irrigation regime for farm"""
    if regime not in ["AWD", "CONTINUOUS", "RAINFED", "AUTO"]:
        raise HTTPException(status_code=400, detail="Invalid regime")
    
    state = storage.load_latest_state(farm_id)
    if not state:
        raise HTTPException(status_code=404, detail="Farm state not found")
    
    state.regime = regime
    storage.save_state(state)
    
    return {"status": "success", "regime": regime}


@app.post("/weather/manual")
def set_manual_weather(
    rain_24h: Optional[float] = None,
    rain_72h: Optional[float] = None,
    et0: Optional[float] = None,
    temp: Optional[float] = None
):
    """Manually set weather values (for testing)"""
    weather_adapter.set_weather(rain_24h, rain_72h, et0, temp)
    return {"status": "success", "message": "Weather values updated"}


# ============================================================================
# TRAJECTORY AND LOGGING ENDPOINTS
# ============================================================================

@app.get("/trajectory/{farm_id}")
def get_trajectory(farm_id: str, days: int = 30):
    """Get advice trajectory for farm"""
    trajectory = logger.get_trajectory(farm_id, days)
    return {"farm_id": farm_id, "days": days, "events": trajectory}


@app.get("/logs/{farm_id}")
def get_logs(farm_id: str, limit: int = 100):
    """Get all logs for farm"""
    events = logger.read_events(farm_id=farm_id, limit=limit)
    return {"farm_id": farm_id, "count": len(events), "events": events}


# ============================================================================
# EXPLANATION ENDPOINTS
# ============================================================================

@app.get("/explain/{farm_id}")
def get_explanation(farm_id: str, language: str = "EN"):
    """Get formatted explanation of latest advice"""
    events = logger.read_events(farm_id=farm_id, event_type="advice", limit=1)
    if not events:
        raise HTTPException(status_code=404, detail="No advice found")
    
    # Reconstruct AdviceResponse from event
    advice_data = events[0]["recommendation"]
    rationale_data = events[0]["rationale"]
    
    # This is simplified - in production, fully reconstruct AdviceResponse
    explanation = f"""
Farm: {farm_id}
Action: {advice_data['action']}
Target: {advice_data.get('target', 'N/A')}
Confidence: {advice_data['confidence']}
Regime: {advice_data['regime']}

Rationale:
"""
    
    for i, r in enumerate(rationale_data, 1):
        explanation += f"{i}. {r['text']} [{r['source_type']}]\n"
    
    return {"explanation": explanation}


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "components": {
            "storage": "ok",
            "handbook": "ok" if handbook.config else "warning",
            "extractor": "llm" if isinstance(extractor, LLMSlotExtractor) else "mock"
        }
    }


# ============================================================================
# STATIC FILES AND UI
# ============================================================================

@app.get("/")
def root():
    """Serve UI homepage"""
    index_file = Path(__file__).parent / "static" / "index.html"
    if index_file.exists():
        return FileResponse(index_file, headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache"})
    else:
        return {
            "name": "Rice Water Management API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
            "ui": "UI not found. Ensure static files are in water_mgmt/static/"
        }

@app.get("/{filename}")
def serve_static(filename: str):
    """Serve static files"""
    static_file = Path(__file__).parent / "static" / filename
    if static_file.exists() and static_file.is_file():
        return FileResponse(static_file, headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache"})
    raise HTTPException(status_code=404, detail="File not found")


# ============================================================================
# STARTUP
# ============================================================================

# (startup logic moved to lifespan context manager above)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
