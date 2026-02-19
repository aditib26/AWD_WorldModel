# AWD World Model - Conversational Assistant

A complete, production-ready conversational AI system for **Alternate Wetting and Drying (AWD)** water management in rice cultivation.

## 🎯 What This Does

This is a **slot-filling conversational assistant** that helps farmers make AWD irrigation decisions by:

1. **Understanding farmer questions** naturally (no rigid commands)
2. **Extracting information** automatically from responses
3. **Asking targeted follow-ups** when data is missing
4. **Providing expert advice** when sufficient context is available
5. **Explaining decisions** with context-aware reasoning

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Farmer Question                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Intent Classifier                               │
│  (irrigation_now, safety, feasibility, education, etc.)      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Slot Extractor                                  │
│  Extracts: water level, growth stage, soil type, etc.       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Farm State Store                                │
│  Maintains: crop, water, soil, weather, observations        │
└──────────────────────┬──────────────────────────────────────┘
                       │
           ┌───────────┴───────────┐
           │                       │
           ▼                       ▼
   Missing Slots?           All Data Present?
           │                       │
           ▼                       ▼
   Ask Follow-ups          Decision Engine
   (max 3 at a time)       (feasibility, safety, action)
           │                       │
           └───────────┬───────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         Response Generator                                   │
│  Creates: advice + explanation + confidence                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Components

### 1. **farm_state.py**
Farm state data model with:
- Crop state (stage, age, variety)
- Water state (depth, last irrigation)
- Soil properties (texture, drainage)
- Weather context (rainfall, forecast)
- Observations (stress, cracking)

### 2. **intent_classifier.py**
Classifies farmer questions into:
- `irrigation_now` - "Should I irrigate?"
- `scheduling` - "When is next irrigation?"
- `feasibility` - "Can I do AWD?"
- `safety` - "Is it safe to dry?"
- `troubleshooting` - "Leaves are rolling"
- `education` - "What is AWD?"
- `benefits` - "How much water saved?"

### 3. **slot_extractor.py**
Automatically extracts from text:
- Water levels (tube readings, standing water)
- Growth stages (tillering, flowering, etc.)
- Soil types (clay, loam, sandy)
- Stress symptoms
- Rainfall expectations

### 4. **decision_logic.py**
Core AWD decision engine:
- `check_feasibility()` - Is field suitable?
- `check_safety()` - Is current drying safe?
- `recommend_action()` - What to do now?
- Emission & water savings estimates

### 5. **conversational_handler.py**
Main orchestrator that:
- Processes questions end-to-end
- Manages slot-filling flow
- Generates progressive follow-ups
- Returns complete responses

### 6. **educational_content.py**
Rich educational content:
- AWD basics and methodology
- Water tube installation
- Benefits breakdown
- Stage-by-stage guidance
- Troubleshooting guides

### 7. **api_router.py**
FastAPI router with endpoints:
- `POST /api/awd/ask` - Ask questions
- `GET /api/awd/state/{user_id}` - Get state
- `POST /api/awd/state/update` - Update state
- `GET /api/awd/info/help` - Get help

---

## 🚀 Usage

### Basic Python Usage

```python
from AWD_World_Model import ConversationalAWDHandler, FarmState

# Initialize
handler = ConversationalAWDHandler()
state = FarmState()

# Ask question
result = handler.process_question(
    question="Should I irrigate today?",
    farm_state=state
)

print(result['response'])

if result['needs_more_info']:
    for q in result['questions']:
        print(f"Follow-up: {q}")
```

### FastAPI Integration

```python
# In your main.py
from AWD_World_Model.api_router import router as awd_router

app.include_router(awd_router)
```

### API Request Example

```bash
curl -X POST http://localhost:8000/api/awd/ask \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "farmer_123",
    "question": "Should I irrigate today?"
  }'
```

### Response Format

```json
{
  "response": "To give you accurate advice, I need 3 quick details:\n\n**What is the water level now?**...",
  "needs_more_info": true,
  "questions": [
    "**What is the water level now?**\n1. Measure with tube: how many cm below soil surface?\n2. Or if there's standing water: how many cm deep?"
  ],
  "confidence": "low",
  "intent": "irrigation_now",
  "farm_state_summary": "No farm data collected yet",
  "timestamp": "2026-01-27T13:00:00Z"
}
```

---

## 📋 Example Conversations

### Example 1: Progressive Slot Filling

```
Farmer: "Should I irrigate today?"
Assistant: "I need 3 details: water level, crop stage, rainfall forecast"

Farmer: "Water table is 14cm below surface"
Assistant: "Good. What crop stage: tillering, flowering, or grain filling?"

Farmer: "Tillering"
Assistant: "Is heavy rain expected in next 7 days?"

Farmer: "No rain expected"
Assistant: "✅ Water level good (14cm). You can wait 1-2 days. 
           Irrigate when water table reaches 15cm below surface."
```

### Example 2: Educational Question

```
Farmer: "What is AWD?"
Assistant: [Provides complete AWD explanation]
- No slot filling needed
- Immediate comprehensive answer
```

### Example 3: Safety Warning

```
Farmer: "Should I wait longer? I'm at flowering stage"
Assistant: "⚠️ CRITICAL: Flowering stage is highly sensitive.
           What's your current water depth?"

Farmer: "12cm below surface"
Assistant: "🚨 Irrigate NOW. At flowering, never exceed 10cm depth.
           Refill to 5cm standing water immediately."
```

---

## 🎛️ Slot Requirements by Intent

| Intent | Required Slots |
|--------|---------------|
| `irrigation_now` | water depth, growth stage, rain forecast |
| `scheduling` | water depth, growth stage, soil percolation |
| `feasibility` | field type, soil texture, rain forecast |
| `safety` | growth stage, water depth, stress symptoms |
| `troubleshooting` | growth stage, water depth, observations |
| `education` | None (immediate answer) |
| `benefits` | None (uses defaults or known state) |

---

## 🧠 Smart Features

### 1. **Automatic Information Extraction**
Understands natural language:
- "14cm below surface" → `water.water_table_cm_below_surface = 14`
- "flowering stage" → `crop.growth_stage = flowering`
- "clay soil" → `soil.texture_class = clay`, `soil.percolation_class = low`

### 2. **Progressive Questioning**
Asks only what's needed:
- Maximum 3 questions per turn
- Prioritizes most critical slots
- Offers alternatives ("Or tell me your village for forecast")

### 3. **Tentative Advice**
Gives partial guidance when possible:
```
"⚠️ Tentative advice: Based on water depth, you should likely irrigate soon.
To be certain, I need to know your crop stage."
```

### 4. **Context-Aware Decisions**
- Flowering stage → Strict 10cm limit
- Tillering stage → Safe up to 15cm
- Heavy rain forecast → Don't recommend AWD
- Sandy soil → Don't recommend AWD

### 5. **Farmer-Friendly Language**
Instead of technical terms:
- "Water table depth" → "Tube reading in cm below soil"
- "Percolation class" → "How fast does water drain?"
- "Phenological stage" → "Crop stage: tillering, flowering, etc."

---

## 🔌 Integration with Existing Backend

To integrate with your Rice Assistant backend:

1. **Import the router** in `main.py`:
```python
from AWD_World_Model.api_router import router as awd_router
app.include_router(awd_router)
```

2. **Use in chatbot** flow:
```python
# Detect AWD-related questions
if "awd" in user_message.lower() or "irrigate" in user_message.lower():
    # Route to AWD assistant
    awd_result = awd_handler.process_question(user_message, user_farm_state)
    return awd_result['response']
```

3. **Persist state** in your database:
```python
# Save farm state per user
user.awd_state = farm_state.dict()
db.commit()
```

---

## 📊 Decision Logic Details

### Feasibility Checks
- ❌ Not bunded field → "AWD requires bunded paddy field"
- ❌ Sandy soil → "Water drains too fast for safe AWD"
- ❌ Heavy rain (>50mm) → "Not recommended during monsoon"
- ✅ Clay/loam + bunded + controlled rain → "Field suitable for AWD"

### Safety Checks
- 🚨 Flowering + depth >10cm → "IRRIGATE NOW"
- ⚠️ Stress symptoms → "Stop drying, irrigate immediately"
- ⚠️ Severe cracking → "Risk of root damage, irrigate now"
- ⚠️ Depth >20cm → "Excessive drying, irrigate immediately"

### Action Recommendations
- 0-10cm: "Continue drying, monitor daily"
- 10-15cm: "Prepare to irrigate soon"
- 15cm+: "Irrigate NOW to 5cm standing water"

---

## 🧪 Testing

Run the example usage:

```bash
cd AWD_World_Model
python example_usage.py
```

This demonstrates:
- ✅ Simple questions with slot filling
- ✅ Multi-turn conversations
- ✅ Educational queries
- ✅ Feasibility checks
- ✅ Safety warnings
- ✅ Troubleshooting guidance

---

## 📚 Documentation for Farmers

The assistant includes rich educational content:
- **AWD basics** - What, why, how
- **Installation guide** - Water tube setup
- **Benefits** - Water & emission savings with numbers
- **Stage guide** - What to do at each growth stage
- **Troubleshooting** - Common problems & solutions

All content is farmer-friendly, no technical jargon.

---

## 🔮 Future Enhancements

Optional upgrades (not needed for current functionality):

1. **Weather API integration** - Auto-fill forecast from location
2. **Learned transition model** - ML-based water table prediction
3. **Multi-language support** - Hindi, Bengali, etc.
4. **Voice integration** - Voice input/output
5. **Image analysis** - Detect stress from leaf photos
6. **Carbon credit tracking** - Calculate exact emission reductions

---

## 🎓 Key Design Principles

1. **No rigid commands** - Natural conversation
2. **Progressive questioning** - Never overwhelm with 10 questions
3. **Always safe** - Conservative advice during critical stages
4. **Explainable** - Every recommendation has reasoning
5. **Farmer-first** - Language they understand
6. **Stateful** - Remembers context across conversation
7. **Extensible** - Easy to add new intents/logic

---

## 📞 Support

For questions about implementation:
- See `example_usage.py` for code examples
- Check `api_router.py` for API integration
- Review `conversational_handler.py` for flow logic

For questions about AWD science:
- See `educational_content.py` for detailed explanations
- Refer to IRRI AWD guidelines (in your Documents folder)

---

## ✅ Ready to Use

This system is **complete and production-ready**:
- ✅ Full conversational flow
- ✅ Intelligent slot-filling
- ✅ Research-grade decision logic
- ✅ Farmer-friendly interface
- ✅ FastAPI endpoints
- ✅ Example usage
- ✅ Educational content
- ✅ Comprehensive documentation

**You can start using it immediately by importing the router into your main.py.**
