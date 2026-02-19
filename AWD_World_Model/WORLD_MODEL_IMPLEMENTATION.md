# AWD World Model Implementation Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Core Components](#core-components)
4. [Data Flow](#data-flow)
5. [Provenance Tracking](#provenance-tracking)
6. [State Management](#state-management)
7. [LLM Integration](#llm-integration)
8. [RAG Integration](#rag-integration)
9. [Decision Engine](#decision-engine)
10. [UI Presentation](#ui-presentation)
11. [Key Design Decisions](#key-design-decisions)

---

## Overview

The AWD (Alternate Wetting and Drying) World Model is a **temporal reasoning system** that maintains a comprehensive, updatable representation of farm state for precision agriculture. It combines:

- **Multi-source state updates** (chat extraction, sidebar inputs, API)
- **Per-field provenance tracking** (source, timestamp, confidence)
- **Temporal snapshots** for historical analysis and prediction
- **LLM-enhanced conversation** with slot extraction and intent classification
- **RAG-augmented responses** from agricultural handbooks
- **Decision logic** for irrigation recommendations and safety checks

### Purpose
Enable transparent, explainable agricultural assistance by maintaining a **single source of truth** about farm conditions with full audit trail and temporal reasoning capabilities.

---

## Architecture

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit UI Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Sidebar    │  │     Chat     │  │  World Model │      │
│  │   Inputs     │  │  Interface   │  │   Dashboard  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          └──────────┬───────┴──────────┬───────┘
                     ▼                  ▼
          ┌─────────────────────────────────────┐
          │   ConversationalAWDHandler          │
          │  ┌──────────────────────────────┐   │
          │  │  Intent Classification       │   │
          │  │  Slot Extraction (LLM/Regex) │   │
          │  │  State Updates               │   │
          │  │  Response Generation         │   │
          │  └──────────────────────────────┘   │
          └─────────┬───────────────────────────┘
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│FarmState │ │  State   │ │   RAG    │
│ +Prov.   │ │ History  │ │  Client  │
└──────────┘ └──────────┘ └──────────┘
       │            │            │
       ▼            ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│Decision  │ │Persist.  │ │  Qdrant  │
│ Engine   │ │ Manager  │ │  Vector  │
└──────────┘ └──────────┘ └──────────┘
```

---

## Core Components

### 1. FarmState (`farm_state.py`)

**Pydantic-based hierarchical state model** with nested structures and provenance tracking.

```python
class FarmState(BaseModel):
    farm: FarmProfile
    crop: CropInfo
    soil: SoilInfo
    water: WaterInfo
    weather: WeatherInfo
    observations: ObservationInfo
    field_provenance: Dict[str, FieldProvenance] = {}  # Key: dot-notation field path
```

#### Key Features:
- **Nested structure** mirrors farm domain (water.water_table_cm_below_surface)
- **Dot notation updates** via `update_from_dict()` for flat slot extraction
- **Provenance recording** for every field update with source/timestamp/confidence
- **Summary generation** for LLM context
- **Missing slot detection** for required fields

#### Example:
```python
farm_state.update_from_dict(
    {"water.water_table_cm_below_surface": 15},
    source="llm_extraction",
    confidence=0.9,
    timestamp="2026-01-28T00:00:00"
)
# Provenance automatically recorded:
# field_provenance["water.water_table_cm_below_surface"] = 
#   FieldProvenance(source="llm_extraction", timestamp="...", confidence=0.9)
```

### 2. FieldProvenance

```python
class FieldProvenance(BaseModel):
    source: str              # "llm_extraction", "regex_extraction", "sidebar_input", "api_update"
    timestamp: str           # ISO 8601 format
    confidence: Optional[float] = None  # 0.0-1.0 for extraction confidence
```

Tracks **where, when, and how confident** each piece of information came from.

### 3. StateHistoryTracker (`state_tracker.py`)

**Temporal snapshot system** for world model history.

```python
class StateSnapshot(BaseModel):
    timestamp: str
    state: Dict[str, Any]         # Full farm state copy
    trigger: str                   # What caused this snapshot
    confidence: float              # Extraction/update confidence
    prediction: Optional[Dict]     # Future predictions at this point
```

#### Capabilities:
- **Snapshot management**: Add, retrieve recent history (max 100 snapshots)
- **Diff computation**: `get_state_changes(field_path)` returns temporal deltas
- **Trajectory extraction**: Track how specific fields evolved over time
- **Export/Import**: JSON serialization for persistence

#### Example:
```python
state_tracker.add_snapshot(
    state=farm_state.model_dump(),
    trigger="chat_extraction",
    confidence=0.9,
    prediction=prediction_data
)

# Get water level trajectory
water_trajectory = state_tracker.get_state_trajectory(
    "water.water_table_cm_below_surface"
)
# Returns: [(timestamp, value), (timestamp, value), ...]
```

### 4. ConversationalAWDHandler (`conversational_handler.py`)

**Orchestrates the entire conversation flow** with multi-stage processing.

#### Processing Pipeline:
```
User Question
    ↓
1. Slot Extraction (LLM or Regex)
    ↓
2. State Update with Provenance
    ↓
3. Intent Classification (LLM or Regex)
    ↓
4. RAG Context Retrieval (if LLM enabled)
    ↓
5. Response Generation (Base + LLM Enhancement)
    ↓
Response + Metadata
```

#### Slot Extraction Strategy:
- **LLM extraction** (if `use_llm=True`): `llm_slot_extractor.py`
  - Uses Qwen model with structured prompt
  - Handles natural language variations
  - Early-exit guard prevents extraction from questions
  - Confidence: 0.9
  
- **Regex fallback**: `slot_extractor.py`
  - Pattern-based extraction for common phrases
  - Faster but less flexible
  - Confidence: 0.7

#### Intent Classification:
- **LLM classification**: Context-aware, handles ambiguity
- **Regex patterns**: Fast, deterministic for known patterns
- **Required slots**: Each intent specifies what fields are needed

### 5. AWDDecisionEngine (`decision_logic.py`)

**Domain-specific logic** for irrigation recommendations and safety checks.

#### Key Methods:

**`check_feasibility(farm_state)`**
- Validates if AWD is suitable for this field
- Checks: bunded field, soil percolation, water control
- Returns: feasible (bool), reasons (list)

**`check_safety(farm_state)`**
- Determines if current AWD practice is safe
- Checks: flowering stage, stress symptoms, water depth limits
- Returns: safe (bool), warnings (list)

**`recommend_action(farm_state)`**
- Decides irrigation timing based on current conditions
- Logic:
  - Water at 15cm depth → irrigate
  - Flowering stage → maintain 3-5cm standing water
  - Stress symptoms → stop AWD, irrigate immediately
- Returns: action, reasoning, urgency

**`predict_drying_rate(farm_state)`**
- Forecasts when irrigation will be needed
- Uses: soil percolation, temperature, current water depth
- Returns: drying_rate_cm_per_day, days_until_irrigation

#### Example Decision Logic:
```python
# Safety check
if farm_state.crop.growth_stage == "flowering":
    return {
        "safe": False,
        "reasons": ["Flowering stage - maintain continuous shallow flooding"]
    }

# Irrigation timing
if water_depth >= 15:
    return {
        "action": "irrigate_now",
        "reasoning": "Water table at safe AWD threshold",
        "urgency": "high"
    }
```

---

## Data Flow

### User Chat Message Flow

```
1. User sends message: "water is 15cm below surface"
   ↓
2. ConversationalAWDHandler._process_question_async()
   ↓
3. LLM Slot Extraction:
   - Input: "water is 15cm below surface"
   - Output: {"water.water_table_cm_below_surface": 15}
   ↓
4. State Update with Provenance:
   farm_state.update_from_dict(
       {"water.water_table_cm_below_surface": 15},
       source="llm_extraction",
       confidence=0.9
   )
   ↓
5. Intent Classification:
   - Intent: "irrigation_now"
   - Confidence: 0.95
   ↓
6. RAG Context Retrieval (if enabled):
   - Query reformulation: "irrigation_now water depth 15cm threshold..."
   - Qdrant search → 3 chunks with scores
   - Filter by relevance > 0.5
   ↓
7. Response Generation:
   - Base response from decision engine
   - LLM enhancement with RAG context
   - Citations appended
   ↓
8. State Snapshot:
   state_tracker.add_snapshot(
       state=farm_state.model_dump(),
       trigger="chat_extraction",
       confidence=0.9
   )
   ↓
9. UI Update:
   - Chat message displayed
   - Provenance shown in expander
   - World Model dashboard refreshed
   - Predictions updated
```

### Sidebar Input Flow

```
1. User changes slider: water_depth = 12
   ↓
2. Streamlit callback triggered
   ↓
3. farm_state.water.water_table_cm_below_surface = 12
   ↓
4. Provenance recorded:
   field_provenance["water.water_table_cm_below_surface"] = 
       FieldProvenance(source="sidebar_input", timestamp=now(), confidence=None)
   ↓
5. State snapshot added:
   state_tracker.add_snapshot(
       state=farm_state.model_dump(),
       trigger="sidebar_update:water.water_table_cm_below_surface",
       confidence=1.0
   )
   ↓
6. UI auto-refreshes via st.rerun()
```

### API Update Flow

```
1. POST /api/update_state
   Body: {"water": {"water_table_cm_below_surface": 15}}
   ↓
2. api_router.py handler
   ↓
3. farm_state.update_from_dict(
       updates,
       source="api_update",
       confidence=None
   )
   ↓
4. Persistence manager saves state
   ↓
5. Response: updated state + provenance
```

---

## Provenance Tracking

### Design Philosophy

**Every field value must have an audit trail**: who/what updated it, when, and with what confidence.

### Provenance Sources

| Source | Confidence | Trigger | Use Case |
|--------|-----------|---------|----------|
| `llm_extraction` | 0.9 | Chat message processed by LLM | Natural language updates |
| `regex_extraction` | 0.7 | Chat message processed by regex | Pattern-matched updates |
| `sidebar_input` | None (implicit 1.0) | User manual slider/dropdown | Direct user input |
| `api_update` | None | External API call | Sensor data, integrations |
| `weather_auto_fetch` | 1.0 | Location-based weather API | Automatic weather data |

### Provenance Storage

```python
# In FarmState
field_provenance: Dict[str, FieldProvenance] = {}

# Example after multiple updates:
{
    "water.water_table_cm_below_surface": FieldProvenance(
        source="llm_extraction",
        timestamp="2026-01-28T12:30:00",
        confidence=0.9
    ),
    "crop.growth_stage": FieldProvenance(
        source="sidebar_input",
        timestamp="2026-01-28T12:25:00",
        confidence=None
    ),
    "weather.current_temp_c": FieldProvenance(
        source="weather_auto_fetch",
        timestamp="2026-01-28T12:00:00",
        confidence=1.0
    )
}
```

### Provenance in UI

**Chat Extraction Expander:**
```
📋 Extracted Information
━━━━━━━━━━━━━━━━━━
• Water Table Depth: 15 cm 🟢 High
  ↳ Source: llm_extraction | Time: 12:30 PM | Confidence: 90%

• Growth Stage: flowering
  ↳ Source: sidebar_input | Time: 12:25 PM
```

**World Model Provenance Tab:**
```
Latest provenance for each world-model field:

| Field | Value | Source | Timestamp | Confidence |
|-------|-------|--------|-----------|------------|
| water.water_table_cm_below_surface | 15 | llm_extraction | 12:30 PM | 0.9 |
| crop.growth_stage | flowering | sidebar_input | 12:25 PM | - |
```

---

## State Management

### Persistence Strategy

**StatePersistenceManager** (`state_persistence.py`) handles disk persistence.

```python
class StatePersistenceManager:
    def __init__(self, base_dir: str):
        self.state_file = os.path.join(base_dir, "farm_state.json")
        self.history_file = os.path.join(base_dir, "state_history.json")
```

#### Save Operation:
```python
def save_state(self, farm_state: FarmState, state_tracker: StateHistoryTracker):
    # Serialize FarmState including provenance
    state_data = farm_state.model_dump()
    
    # Serialize history
    history_data = state_tracker.export_history()
    
    # Write to disk
    with open(self.state_file, 'w') as f:
        json.dump(state_data, f, indent=2)
    with open(self.history_file, 'w') as f:
        json.dump(history_data, f, indent=2)
```

#### Load Operation:
```python
def load_state(self) -> tuple[FarmState, StateHistoryTracker]:
    # Load from disk
    with open(self.state_file) as f:
        state_data = json.load(f)
    
    # Reconstruct FarmState (provenance included)
    farm_state = FarmState(**state_data)
    
    # Reconstruct history
    state_tracker = StateHistoryTracker()
    state_tracker.import_history(history_data)
    
    return farm_state, state_tracker
```

### Session State Management (Streamlit)

```python
# Initialize on first load
if "farm_state" not in st.session_state:
    st.session_state.farm_state, st.session_state.state_tracker = \
        persistence_manager.load_state()

# Update via references
st.session_state.farm_state.water.water_table_cm_below_surface = 15

# Save on changes
persistence_manager.save_state(
    st.session_state.farm_state,
    st.session_state.state_tracker
)
```

---

## LLM Integration

### Architecture

**Two LLM systems** run in parallel:

1. **Qwen TPU (Primary)** - Custom deployment for slot extraction and response generation
2. **OpenAI (RAG only)** - Embeddings for vector search

### Qwen Client (`llm_client.py`)

```python
async def generate_awd_response(
    user_question: str,
    farm_context: str,
    base_response: str,
    intent: str,
    rag_context: str = ""
) -> str:
    """
    Generate LLM-enhanced response with:
    - User question
    - Farm state context
    - Base rule-based response
    - RAG handbook context
    """
    prompt = f"""
    You are an AWD irrigation advisor. Based on the information below, provide advice.
    
    Farm Context: {farm_context}
    Handbook Context: {rag_context}
    Base Recommendation: {base_response}
    
    User Question: {user_question}
    """
    
    response = await qwen_client.chat.completions.create(
        model=QWEN_CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content
```

### Slot Extraction (`llm_slot_extractor.py`)

**Critical anti-hallucination guards:**

```python
async def extract_slots_with_llm(text: str) -> Dict[str, Any]:
    # Guard 1: Programmatic question detection
    question_patterns = [r'^what\s', r'^how\s', r'^should\s+i\s', r'\?$']
    if any(re.search(p, text.lower()) for p in question_patterns):
        return {}  # Don't extract from questions
    
    # Guard 2: Strict prompt
    prompt = """
    CRITICAL: Extract ONLY if providing factual farm information.
    Do NOT extract from questions or advice requests.
    If message is a question, return {}.
    """
    
    # LLM extraction with low temperature
    response = await qwen_client.chat.completions.create(
        model=QWEN_CHAT_MODEL,
        messages=[...],
        temperature=0.1  # Very conservative
    )
```

### Intent Classification (`llm_intent_classifier.py`)

```python
async def classify_intent_with_llm(
    question: str,
    farm_state_summary: str,
    conversation_context: str = None
) -> Dict:
    """
    Returns:
    {
        "intent": "irrigation_now",
        "confidence": 0.95,
        "reasoning": "User asking about current irrigation needs",
        "requires_farm_state": true,
        "urgency": "high"
    }
    """
```

---

## RAG Integration

### Components

1. **Qdrant Vector Database** - Stores handbook chunks as embeddings
2. **OpenAI Embeddings** - `text-embedding-3-small` model
3. **Query Reformulation** - Expands short questions for better retrieval
4. **Score Filtering** - Rejects low-relevance results

### Query Reformulation Strategy

**Problem**: Short questions like "what is awd?" don't match document embeddings.

**Solution**: Expand queries with domain keywords based on intent.

```python
def _reformulate_query_for_rag(question: str, intent: str) -> str:
    intent_templates = {
        "awd_basics": "alternate wetting drying AWD rice water management methodology...",
        "benefits": "water savings methane emission reduction yield carbon credits...",
        "irrigation_now": "irrigation timing water depth 15cm safe threshold decision..."
    }
    
    if intent in intent_templates:
        return f"{question} {intent_templates[intent]}"
    return question
```

**Example:**
- Input: `"what is awd?"`
- Intent: `awd_basics`
- Reformulated: `"what is awd? alternate wetting and drying AWD rice water management methodology practice technique definition explanation how it works"`

### Retrieval Flow

```python
async def retrieve_context(query: str, top_k: int = 3) -> Dict[str, Any]:
    # 1. Get Qdrant client (lazy init with health check)
    client = get_qdrant_client()
    
    # 2. Generate query embedding
    query_vector = await embed_text(query)
    
    # 3. Search with timeout
    search_result = await asyncio.wait_for(
        loop.run_in_executor(pool, lambda: client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=top_k,
            timeout=15
        )),
        timeout=17
    )
    
    # 4. Log scores for diagnostics
    scores = [f"{h.score:.3f}" for h in search_result.points]
    print(f"Retrieved {len(search_result.points)} docs (scores: {scores})")
    
    # 5. Filter by relevance threshold
    SCORE_THRESHOLD = 0.5
    filtered = [hit for hit in search_result.points if hit.score >= SCORE_THRESHOLD]
    
    # 6. Format citations
    citations = [{
        "title": hit.payload.get("title"),
        "content": hit.payload.get("content"),
        "score": hit.score,
        "chapter_title": hit.payload.get("chapter_title")
    } for hit in filtered]
    
    return {"context_text": "...", "citations": citations}
```

### Error Handling

**Graceful degradation** - system continues without RAG if:
- Credentials missing → Silent disable
- Connection timeout → Warning + continue
- Low relevance scores → Empty context
- Collection not found → Error message

---

## Decision Engine

### Rule-Based Logic

The `AWDDecisionEngine` implements **domain expert knowledge** as executable rules.

#### Feasibility Rules

```python
def check_feasibility(self, farm_state: FarmState) -> Dict[str, Any]:
    if not farm_state.soil.bunded_lowland:
        return {
            "feasible": False,
            "reasons": ["Non-bunded field - cannot hold water for AWD"]
        }
    
    if farm_state.soil.percolation_class == "high":
        return {
            "feasible": False,
            "reasons": ["Very high percolation - water drains too fast for safe AWD"]
        }
    
    return {"feasible": True, "reasons": []}
```

#### Safety Rules

```python
def check_safety(self, farm_state: FarmState) -> Dict[str, Any]:
    warnings = []
    
    # Critical stage check
    if farm_state.crop.growth_stage == "flowering":
        warnings.append("CRITICAL: Flowering stage - maintain 3-5cm standing water")
        return {"safe": False, "warnings": warnings}
    
    # Water depth check
    depth = farm_state.water.water_table_cm_below_surface
    if depth and depth > 20:
        warnings.append("Water too deep - risk of root damage")
        return {"safe": False, "warnings": warnings}
    
    # Stress symptom check
    if farm_state.observations.stress_symptoms_flag:
        warnings.append("Crop stress detected - stop AWD and irrigate")
        return {"safe": False, "warnings": warnings}
    
    return {"safe": True, "warnings": []}
```

#### Prediction Logic

```python
@staticmethod
def predict_drying_rate(farm_state: FarmState) -> Dict[str, Any]:
    # Percolation rate by soil type (cm/day)
    perc_rates = {"low": 0.5, "medium": 1.0, "high": 2.0}
    percolation = perc_rates.get(farm_state.soil.percolation_class, 1.0)
    
    # Evapotranspiration (temperature-based, cm/day)
    temp = farm_state.weather.current_temp_c or 28
    et_rate = 0.3 + (temp - 25) * 0.05  # Simplified ET model
    
    # Total drying rate
    drying_rate = percolation + et_rate
    
    # Days until 15cm threshold
    current_depth = farm_state.water.water_table_cm_below_surface or 5
    remaining_depth = 15 - current_depth
    days_remaining = max(0, remaining_depth / drying_rate)
    
    return {
        "status": "predicting",
        "drying_rate_cm_per_day": round(drying_rate, 2),
        "days_until_irrigation": round(days_remaining, 1),
        "percolation_rate": percolation,
        "et_rate": round(et_rate, 2)
    }
```

---

## UI Presentation

### Streamlit App Structure (`streamlit_app.py`)

```
┌─────────────────────────────────────────────────────────┐
│                    Sidebar                              │
│  - Farm Profile (location, area)                       │
│  - Crop Details (variety, growth stage, planting date) │
│  - Soil Info (texture, percolation, bunded)            │
│  - Water Status (depth, standing water)                │
│  - Weather (auto-fetched + manual override)            │
│  - Observations (stress, cracking)                      │
│  [Update Profile Button] → triggers state snapshot      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   Main Content Area                      │
│                                                          │
│  🌾 AWD Water Advisor                                   │
│  Ask about irrigation, water levels, or AWD safety.     │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Suggestions & Advisories (Proactive Monitor) │    │
│  │  - 🟢 Good timing for AWD practice             │    │
│  │  - 🔴 Critical: Irrigate now (15cm threshold)  │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  🗂️ World Model State & Predictions            │    │
│  │                                                  │    │
│  │  📊 State Timeline (last 10 updates)            │    │
│  │  [Chart showing field changes over time]        │    │
│  │                                                  │    │
│  │  🔮 Predictions & Trajectories                  │    │
│  │  - Water trajectory: 5cm → 10cm → 15cm          │    │
│  │  - Prediction: Irrigate in 3.2 days             │    │
│  │  [Plotly chart: current + predicted drying]     │    │
│  │                                                  │    │
│  │  📋 Provenance (Latest for each field)          │    │
│  │  | Field | Value | Source | Time | Confidence | │    │
│  │  | water | 15cm  | chat   | 1:30 | 0.9        | │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  💬 Chat Interface                              │    │
│  │                                                  │    │
│  │  User: water is 15cm below surface              │    │
│  │  ┌──────────────────────────────────────┐      │    │
│  │  │ 📋 Extracted Information             │      │    │
│  │  │ • Water Table: 15cm 🟢 High          │      │    │
│  │  │   Source: llm_extraction | 0.9       │      │    │
│  │  └──────────────────────────────────────┘      │    │
│  │                                                  │    │
│  │  Assistant: Good timing! Your water table...    │    │
│  │  📚 [Citation 1] AWD Handbook, p.27              │    │
│  │                                                  │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  [Chat Input Box] "Ask me something..."                 │
└─────────────────────────────────────────────────────────┘
```

### Key UI Components

**1. Provenance Display in Chat:**
```python
with st.expander("📋 Extracted Information", expanded=True):
    for key, value in extracted_slots.items():
        prov = farm_state.field_provenance.get(key)
        st.write(f"• {display_name}: {value} {confidence_badge}")
        if prov:
            st.caption(f"↳ Source: {prov.source} | Time: {prov.timestamp} | Conf: {prov.confidence}")
```

**2. Timeline Visualization:**
```python
timeline_data = []
for snapshot in state_tracker.get_recent_history(10):
    timeline_data.append({
        "time": snapshot.timestamp,
        "trigger": snapshot.trigger,
        "confidence": snapshot.confidence
    })

fig = px.line(timeline_data, x="time", y="confidence", 
              hover_data=["trigger"], title="State Update Timeline")
st.plotly_chart(fig)
```

**3. Prediction Plot:**
```python
current_depth = farm_state.water.water_table_cm_below_surface or 5
prediction = decision_engine.predict_drying_rate(farm_state)

# Current trajectory
water_trajectory = state_tracker.get_state_trajectory("water.water_table_cm_below_surface")

# Future prediction
if prediction["status"] == "predicting":
    future_days = np.linspace(0, prediction["days_until_irrigation"], 20)
    future_depths = current_depth + (prediction["drying_rate_cm_per_day"] * future_days)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=past_times, y=past_depths, name="Historical", mode="lines+markers"))
    fig.add_trace(go.Scatter(x=future_times, y=future_depths, name="Predicted", mode="lines", line=dict(dash="dash")))
    fig.add_hline(y=15, line_dash="dot", annotation_text="Irrigation Threshold")
    
    st.plotly_chart(fig)
```

**4. Provenance Table:**
```python
prov_data = []
for field_path, prov in farm_state.field_provenance.items():
    value = get_nested_value(farm_state, field_path)
    prov_data.append({
        "Field": field_path,
        "Value": str(value),
        "Source": prov.source,
        "Timestamp": prov.timestamp,
        "Confidence": prov.confidence if prov.confidence else "-"
    })

df = pd.DataFrame(prov_data)
df["Value"] = df["Value"].astype(str)  # Arrow serialization fix
st.dataframe(df, use_container_width=True)
```

---

## Key Design Decisions

### 1. Provenance as First-Class Citizen

**Decision**: Track source/timestamp/confidence for every field update.

**Rationale**:
- Transparency for farmers (know where data came from)
- Debugging extraction errors (LLM vs regex)
- Confidence weighting for conflicting updates
- Audit trail for regulatory compliance

**Trade-off**: Extra storage and complexity, but essential for trust.

### 2. Dot Notation for Nested Updates

**Decision**: Use flat keys like `"water.water_table_cm_below_surface"` instead of nested dicts.

**Rationale**:
- Simpler slot extraction (LLM outputs flat JSON)
- Easier provenance tracking (one key per field)
- Clean API for partial updates

**Implementation**:
```python
def update_from_dict(self, updates: Dict[str, Any], source: str, ...):
    for key, value in updates.items():
        if '.' in key:
            parts = key.split('.')
            obj = self
            for part in parts[:-1]:
                obj = getattr(obj, part)
            setattr(obj, parts[-1], value)
        else:
            setattr(self, key, value)
        
        self.field_provenance[key] = FieldProvenance(source=source, ...)
```

### 3. Temporal Snapshots vs. Event Sourcing

**Decision**: Store full state snapshots at each update instead of event log.

**Rationale**:
- Simpler queries (no replay needed)
- Easy diff computation between snapshots
- Natural for UI timeline visualization
- Max 100 snapshots keeps memory bounded

**Trade-off**: More storage, but state is small (~10KB per snapshot).

### 4. LLM + Regex Hybrid

**Decision**: Try LLM extraction first, fall back to regex if LLM fails.

**Rationale**:
- LLM handles natural language variations
- Regex provides guaranteed extraction for known patterns
- Fallback ensures robustness when LLM unavailable

**Confidence tracking** lets system know which method was used.

### 5. RAG Query Reformulation

**Decision**: Expand short questions with intent-based keywords.

**Rationale**:
- Short questions ("what is awd?") don't match document embeddings well
- Adding domain terms ("alternate wetting drying methodology...") improves recall
- Intent-specific templates target relevant content

**Alternative considered**: Let LLM reformulate queries, but that adds latency and cost.

### 6. Score Threshold Filtering

**Decision**: Reject RAG results below 0.5 relevance score.

**Rationale**:
- Low-score chunks are often irrelevant or confusing
- Better to provide no context than bad context
- Lets LLM work from base knowledge instead of misleading sources

**Tunable**: Adjust threshold based on collection quality.

### 7. Graceful Degradation

**Decision**: System works fully without RAG or LLM if unavailable.

**Rationale**:
- Core world model (state, provenance, timeline) is LLM-independent
- Decision engine uses rule-based logic
- RAG adds citations but isn't essential for advice
- Ensures reliability even with network/API issues

**Layers of fallback**:
```
Full system (LLM + RAG)
    ↓ (LLM fails)
Rule-based + Regex extraction
    ↓ (Network fails)
Local state management + UI still functional
```

### 8. Single Source of Truth

**Decision**: `FarmState` is the canonical representation, all other views derive from it.

**Rationale**:
- Avoids sync issues between sidebar, chat, and dashboard
- Provenance applies uniformly regardless of update source
- State snapshots capture complete world model at each point

**Implementation**: Streamlit session state holds the single `farm_state` object, all components read/write to it.

### 9. Async/Await for LLM Operations

**Decision**: All LLM and RAG operations are async with timeouts.

**Rationale**:
- Prevents UI blocking on slow API calls
- Enables timeout handling (15s for RAG, 10s for embeddings)
- Better user experience (loading indicators)

**Example**:
```python
async def process_question(question: str):
    async with asyncio.timeout(30):
        result = await handler.process_question(question, ...)
    return result
```

### 10. Provenance in Session State vs. Database

**Decision**: Provenance stored in `FarmState.field_provenance` dict, persisted to JSON.

**Rationale**:
- Simple serialization with Pydantic
- No database dependency
- Easy to version control and debug
- Fast lookup by field path

**Alternative considered**: Separate provenance database table, but overkill for this scale.

---

## Summary

The AWD World Model is a **production-ready temporal reasoning system** that demonstrates:

✅ **Multi-source state management** with full provenance tracking  
✅ **LLM-enhanced conversation** with anti-hallucination guards  
✅ **RAG-augmented responses** with quality filtering  
✅ **Temporal reasoning** via snapshot history and predictions  
✅ **Transparent UI** showing data lineage and confidence  
✅ **Graceful degradation** when external services fail  
✅ **Domain-specific logic** for agricultural decision-making  

### Future Enhancements

- **Multi-field support**: Track multiple farms in one session
- **Conflict resolution**: Handle contradictory updates from different sources
- **Provenance versioning**: Rollback to previous states
- **Advanced predictions**: ML models for yield forecasting
- **Mobile app**: Field data collection with offline support
- **Sensor integration**: Auto-update from IoT water level sensors

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-28  
**Author**: AWD World Model Team
