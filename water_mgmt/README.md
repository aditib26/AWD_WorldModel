# Rice Water Management World Model

Production-grade water management module for rice farming in the Mekong Delta. Supports AWD and traditional irrigation regimes with provenance-tracked decision making.

## Features

- **Hybrid State Space Model**: Physics-based water balance + rule-based policies
- **Multiple Regimes**: AWD, Continuous Flooding, Rainfed
- **Provenance Tracking**: Handbook-grounded vs general practice rules
- **LLM Slot Extraction**: Natural language input processing
- **MPC Planning**: Short-horizon optimization with uncertainty
- **Automatic Data Collection**: Every interaction logged for future learning

## Architecture

```
┌─────────────────────────────────────────────────┐
│              User Interface                      │
│         (CLI, API, or Future UI)                │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│            LLM Slot Extractor                    │
│         (Natural language → structured)          │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│             State Manager                        │
│    (Profile + Check-in + Chat → World State)    │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│      Rule Engine & Policy Resolver               │
│   Handbook Rules ──→ Precedence ←── General Rules│
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│         MPC Planner + Hydrology Core             │
│  (Simulate actions → Select best → Explain)      │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│      Advice Response + Event Logger              │
│   (Provenance-tagged advice + trajectory logs)   │
└──────────────────────────────────────────────────┘
```

## Quick Start

### Installation

```bash
cd water_mgmt
pip install -r requirements.txt
```

### Set OpenAI API Key (optional)

```bash
export OPENAI_API_KEY="your-key-here"
```

If not set, system will use mock slot extractor for testing.

### Option 1: CLI Demo

```bash
python -m water_mgmt.cli_demo
```

Interactive commands:
- `create` - Create farm profile
- `checkin` - Daily check-in
- `chat` - Chat with assistant
- `advice` - Get irrigation advice
- `show` - Show current state
- `help` - Show all commands

### Option 2: API Server

```bash
python -m water_mgmt.api
```

Then access:
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Example Usage

### Create Profile

```python
from water_mgmt.schemas import FarmerProfile
from water_mgmt.storage import JSONFileStorage
from datetime import date

storage = JSONFileStorage()

profile = FarmerProfile(
    farmer_id="farmer001",
    farm_id="farm001",
    province="An Giang",
    soil_type="alluvial",
    irrigation_access=True,
    awd_tube_available=True,
    sowing_date=date(2024, 1, 15)
)

storage.save_profile(profile)
```

### Submit Check-in and Get Advice

```python
from water_mgmt.schemas import DailyCheckIn
from water_mgmt.state import StateManager
from water_mgmt.weather import StubWeatherAdapter
from water_mgmt.planner import WaterManagementPlanner
from water_mgmt.hydrology import HydrologyCoreSimulator
from water_mgmt.rules_handbook import HandbookRuleSet
from water_mgmt.rules_general import GeneralRuleSet
from water_mgmt.resolver import PolicyResolver
from datetime import date

# Initialize components
state_manager = StateManager()
weather_adapter = StubWeatherAdapter()
hydrology = HydrologyCoreSimulator()
handbook = HandbookRuleSet()
general = GeneralRuleSet()
resolver = PolicyResolver(handbook, general)
planner = WaterManagementPlanner(hydrology, resolver)

# Create check-in
checkin = DailyCheckIn(
    farm_id="farm001",
    checkin_date=date.today(),
    measurement_mode="awd_tube",
    water_table_depth_cm=16.0,  # Above trigger threshold
    soil_cracks="small"
)

# Build state
profile = storage.load_profile("farm001")
state = state_manager.build_initial_state(profile, date.today())
state = state_manager.apply_checkin(state, checkin)

# Get weather
weather = weather_adapter.get_forecast({})
forecast = weather_adapter.get_multi_day_forecast({}, days=7)

# Get advice
advice = planner.plan(state, forecast)

print(f"Recommendation: {advice.recommended_action}")
print(f"Target: {advice.target_description}")
print(f"Confidence: {advice.confidence}")
```

## Operational Modes

### handbook_only
- Only handbook-grounded rules affect decisions
- General rules can only add optional notes
- Use when strict document compliance required

### handbook_plus (default)
- Handbook rules have precedence
- General rules fill gaps
- Best for production use

### general_only
- Only general agronomic rules
- Use for testing or non-handbook regions

## Irrigation Regimes

### AWD (Alternate Wetting and Drying)
- Requires AWD tube measurement or crack observation
- Triggers at 15 cm below soil surface (handbook default)
- Refills to 3-5 cm shallow ponding
- Reduces water use and methane emissions

### CONTINUOUS (Traditional Flooding)
- Maintains shallow standing water (2-5 cm)
- Irrigates when water drops below minimum
- Standard practice for farmers without AWD

### RAINFED
- No irrigation available
- System provides stress warnings only
- Drainage advice when needed

### AUTO
- System automatically infers regime from conditions
- Based on irrigation access and measurement capability

## Data Collection

Every advice session is logged as NDJSON:

```json
{
  "event_type": "advice",
  "timestamp": "2024-02-15T10:30:00",
  "farm_id": "farm001",
  "state_before": {...},
  "weather": {...},
  "recommendation": {...},
  "rationale": [...],
  "follow_up_key": "farm001_2024-02-15"
}
```

Follow-up observations can be linked to original advice for learning.

## Provenance Tracking

Every rationale bullet is tagged:

- **[HANDBOOK]** - From AWD manual (high confidence)
- **[GENERAL]** - Standard agronomic practice (medium confidence)
- **[OBSERVATION]** - From field measurement (high confidence)
- **[WEATHER]** - From forecast data (medium confidence)
- **[DERIVED]** - System inference (low-medium confidence)

Example:

```
Recommendation: IRRIGATE

Why:
1. Water table depth (16.0 cm) reached AWD trigger threshold (15 cm) [HANDBOOK]
2. Small cracks observed in field [OBSERVATION]
3. No significant rainfall forecast [WEATHER]

Confidence: HIGH ⭐⭐⭐
```

## API Endpoints

### Profile Management
- `POST /profile` - Create/update profile
- `GET /profile/{farm_id}` - Get profile

### Daily Operations
- `POST /checkin` - Submit check-in, get advice
- `POST /chat` - Chat message, get advice or clarification
- `GET /state/{farm_id}` - Get current state

### Configuration
- `POST /mode/{farm_id}` - Set operational mode
- `POST /regime/{farm_id}` - Set irrigation regime
- `POST /weather/manual` - Set manual weather (testing)

### Logging & Analysis
- `GET /trajectory/{farm_id}` - Get advice trajectory
- `GET /logs/{farm_id}` - Get all logs
- `GET /explain/{farm_id}` - Get formatted explanation

## File Structure

```
water_mgmt/
├── __init__.py
├── config.py              # Configuration & constants
├── schemas.py             # Pydantic models
├── storage.py             # Persistence layer
├── state.py               # State assembly & merge
├── llm_extractor.py       # LLM slot extraction
├── weather.py             # Weather adapter
├── hydrology.py           # Water balance simulator
├── rules_handbook.py      # Handbook-grounded rules
├── rules_general.py       # General agronomic rules
├── resolver.py            # Rule precedence resolver
├── planner.py             # MPC planning engine
├── explain.py             # Explanation formatter
├── logger.py              # Event logging
├── api.py                 # FastAPI endpoints
├── cli_demo.py            # CLI interface
├── requirements.txt       # Dependencies
└── README.md              # This file
```

## Testing

Run simple smoke test:

```bash
python -m water_mgmt.tests.test_basic
```

## Future Enhancements (Phase 2)

1. **Probabilistic Model**: Replace deterministic hydrology with particle filter
2. **Parameter Learning**: Learn percolation rates from logged trajectories
3. **Policy Learning**: Bandit-style threshold optimization
4. **Real Weather API**: Integrate OpenWeatherMap or local API
5. **Multi-regime Comparison**: Simulate AWD vs continuous side-by-side
6. **Mobile UI**: Farmer-facing profile + check-in interface
7. **Vietnamese NLP**: Fine-tune slot extraction for Vietnamese language

## Production Deployment

### Docker

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY water_mgmt/ /app/water_mgmt/
COPY requirements.txt /app/
RUN pip install -r requirements.txt
CMD ["python", "-m", "water_mgmt.api"]
```

### Environment Variables

```bash
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-4o
```

## Support

For questions or issues, contact the development team.

## License

Proprietary - Rice Assistant Project
