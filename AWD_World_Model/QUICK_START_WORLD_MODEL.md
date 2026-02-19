# 🚀 Quick Start: Testing the World Model

## Installation

```bash
cd /Users/aditibhatia/Desktop/Aditi_Rice_Assistant/AWD_World_Model

# Install new dependencies
pip install plotly pandas

# Ensure existing dependencies are installed
pip install streamlit pydantic openai python-dotenv qdrant-client
```

## Running the Application

```bash
streamlit run streamlit_app.py
```

## 🧪 Testing World Model Features

### Test 1: LLM-Based Multi-Slot Extraction

**Try this natural language input:**
```
"I have 2 hectares of rice near Patna village, currently at flowering stage, 
water level is 12cm below surface using the tube, soil is clay type"
```

**What to observe:**
- ✅ System extracts ALL 5 pieces of information in one go
- ✅ Shows "Information Extracted from Your Message" expander
- ✅ Displays confidence level
- ✅ No need to answer multiple follow-up questions

**Before:** Would ask 5 separate questions
**After:** Understands everything in one sentence

---

### Test 2: State Evolution Visualization

**Steps:**
1. Update water level: "water is 8cm"
2. Wait a moment, then: "water is 12cm"
3. Then: "water is 15cm"
4. Open "🧠 World Model State & Predictions" expander
5. Go to "📊 State Timeline" tab

**What to observe:**
- ✅ Interactive Plotly graph showing water level increasing over time
- ✅ Safe limit lines at 10cm and 15cm
- ✅ Recent state updates table with timestamps
- ✅ Trend analysis: "INCREASING"

---

### Test 3: Predictive Modeling

**Steps:**
1. Set up profile with soil type and growth stage
2. Provide current water level: "water is 8cm"
3. Open World Model dashboard → "🎯 Predictions" tab

**What to observe:**
- ✅ "Predicted Days to 15cm Depth" metric
- ✅ "Drying Rate" in cm/day
- ✅ Visual timeline showing predicted future trajectory
- ✅ Reasoning explanation for the prediction

---

### Test 4: Proactive Alerts

**Scenario A: Critical Alert**
```
Setup: Growth stage = flowering, water = 11cm
Input: "water is now 10cm"
```

**What to observe:**
- ✅ Red critical alert appears automatically
- ✅ "⚠️ CRITICAL: Water depth at 10cm during flowering!"
- ✅ Specific action recommendation
- ✅ Reasoning explanation

**Scenario B: Positive Feedback**
```
Setup: Growth stage = tillering, water = 8cm, no stress
```

**What to observe:**
- ✅ Green success message: "✅ Excellent AWD conditions!"
- ✅ Encouraging feedback with reasoning

---

### Test 5: Context-Aware Intent Understanding

**Complex question:**
```
"My plants are at flowering and I'm worried the water might be too low"
```

**What to observe:**
- ✅ Intent: "safety_check" (not just "flowering" → growth_stage_advice)
- ✅ Urgency: high
- ✅ Reasoning displayed showing why it understood concern
- ✅ Appropriate safety-focused response

---

### Test 6: Session Persistence

**Steps:**
1. Set up complete profile
2. Add water level: "water is 12cm"
3. Have a conversation
4. Close the Streamlit app
5. Reopen: `streamlit run streamlit_app.py`

**What to observe:**
- ✅ All profile information restored
- ✅ Water level still shows 12cm
- ✅ State history recovered in World Model dashboard
- ✅ Can continue conversation seamlessly

**Where it's saved:** `.awd_state/default_user/`

---

### Test 7: Confidence & Uncertainty

**Test A: High Confidence**
```
Input: "Should I irrigate?" (with complete profile)
```
**Observe:** 🟢 High Confidence badge

**Test B: Low Confidence**
```
Input: "Should I irrigate?" (without water level)
```
**Observe:** 🟠 Low Confidence badge + follow-up questions

---

### Test 8: Model Reasoning Transparency

**Check these for reasoning explanations:**

1. **Slot Extraction:**
   - Expand "🔍 Information Extracted from Your Message"
   - See what fields were updated and why

2. **Intent Classification:**
   - LLM provides reasoning for intent choice
   - Shows why it classified as irrigation_now vs safety_check

3. **Predictions:**
   - "💡 Model Reasoning:" explains calculation
   - Shows factors: soil type, percolation, weather

4. **Alerts:**
   - Every alert includes "💡 [reasoning]"
   - Explains why action is recommended

---

### Test 9: Trajectory Analysis

**Steps:**
1. Provide multiple updates over time
2. Open World Model → "📈 Trajectories" tab

**What to observe:**
- ✅ Water depth trend (increasing/decreasing/stable)
- ✅ Current value
- ✅ Number of updates tracked
- ✅ Growth stage transitions timeline

---

## 🎨 UI Features to Explore

### Main Dashboard
- **4 Metric Cards:** Crop Stage, Water Level, Next Irrigation, AI Status
- **Proactive Alerts:** Automatically appear based on state
- **Confidence Badges:** On every response

### World Model Dashboard (Expander)
- **Tab 1 - State Timeline:** Interactive water level graph
- **Tab 2 - Predictions:** Future trajectory visualization
- **Tab 3 - Trajectories:** Parameter trend analysis

### Chat Features
- **Citations Display:** RAG sources when available
- **Slot Extraction Display:** Shows what was understood
- **Follow-up Questions:** Only when truly needed

---

## 🐛 Troubleshooting

### LLM Features Not Working
- Check `.env` file has `QWEN_TPU_ENDPOINT` and `QWEN_API_KEY`
- AI Status should show "Online 🟢"
- Falls back to regex if LLM unavailable

### Graphs Not Displaying
- Install plotly: `pip install plotly`
- Check browser console for errors

### State Not Persisting
- Check `.awd_state/` folder exists
- Check write permissions

---

## 📊 Expected Behavior Examples

### Example 1: Smart Extraction
```
User: "18cm depth, flowering, clay soil near village"
System: [Extracts 4 fields]
        🟢 High Confidence
        "I understand you have clay soil in flowering stage 
        with water at 18cm. This is beyond the safe limit..."
```

### Example 2: Proactive Warning
```
[System detects water at 15cm during flowering]
⚠️ Warning appears automatically:
"Water depth reached safe limit during critical stage.
Plan irrigation within 24 hours."
```

### Example 3: Prediction
```
Current: 10cm depth
Prediction: "Will reach 15cm in 4 days"
[Shows visual timeline with predicted trajectory]
💡 "Based on loam soil with 1.2 cm/day drying rate"
```

---

## 🎯 Key Differences from Before

| Action | Old Behavior | New Behavior |
|--------|-------------|--------------|
| "water is 15cm in my Patna field" | "Please tell me water level" | Extracts both water + location |
| Complex question | Pattern match → wrong intent | LLM understands → correct intent |
| State tracking | Only current snapshot | Complete timeline with graphs |
| Predictions | Hidden/not emphasized | Visual dashboard with reasoning |
| Between sessions | Forgets everything | Remembers all state + history |
| Monitoring | Waits for questions | Proactive alerts |
| Confidence | Not shown | Every response has badge |

---

## 💡 Tips for Best Results

1. **Try Natural Language:** Don't overthink phrasing - LLM understands variations
2. **Provide Context:** Mention multiple details in one sentence
3. **Check Dashboard:** Explore World Model expander to see temporal reasoning
4. **Watch Alerts:** System proactively monitors your state
5. **Review Extractions:** Check what fields were updated for transparency

---

## 📚 Related Documentation

- `WORLD_MODEL_FEATURES.md` - Complete feature documentation
- `README.md` - Original system overview
- `QWEN_INTEGRATION.md` - LLM integration details

---

**Ready to test!** Start with Test 1 (multi-slot extraction) to see the immediate improvement in intelligence.
