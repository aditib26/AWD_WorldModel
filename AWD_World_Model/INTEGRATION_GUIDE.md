# Integration Guide - AWD World Model Assistant

This guide shows how to integrate the AWD assistant into your existing Rice Assistant backend **when you're ready**. All code remains in the `AWD_World_Model` folder.

---

## Option 1: Add as New API Router (Recommended)

### Step 1: Import in main.py

Add this single line to your `/RA_Backend/main.py`:

```python
# Add to imports section (around line 24)
from AWD_World_Model.api_router import router as awd_router

# Add to router includes section (around line 108)
app.include_router(awd_router)
```

That's it! The AWD assistant is now available at:
- `POST /api/awd/ask` - Ask questions
- `GET /api/awd/state/{user_id}` - Get farm state
- `POST /api/awd/state/update` - Update state
- `DELETE /api/awd/state/{user_id}` - Reset state
- `GET /api/awd/info/help` - Get help

### Step 2: Test the API

```bash
# Start your backend
cd RA_Backend
python main.py

# In another terminal, test the endpoint
curl -X POST http://localhost:8000/api/awd/ask \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_farmer",
    "question": "Should I irrigate today?"
  }'
```

---

## Option 2: Integrate into Existing Assistant

If you want to integrate AWD into your existing assistant chatbot:

### In your assistant.py (or wherever chat logic is):

```python
# Add import at top
import sys
sys.path.append('../')  # Adjust path as needed
from AWD_World_Model import ConversationalAWDHandler, FarmState

# Initialize (once, globally or in your assistant class)
awd_handler = ConversationalAWDHandler()
user_farm_states = {}  # Store per user

# In your chat processing function:
def process_user_message(user_id: str, message: str):
    # Detect AWD-related questions
    awd_keywords = ["awd", "irrigat", "water", "dry", "flood", "tube"]
    
    if any(keyword in message.lower() for keyword in awd_keywords):
        # Route to AWD assistant
        if user_id not in user_farm_states:
            user_farm_states[user_id] = FarmState()
        
        result = awd_handler.process_question(
            question=message,
            farm_state=user_farm_states[user_id]
        )
        
        # Return AWD response
        response = result['response']
        
        # Optionally add follow-up questions
        if result['needs_more_info'] and result['questions']:
            response += "\n\n" + "\n\n".join(result['questions'][:2])
        
        return {
            "response": response,
            "source": "awd_assistant",
            "confidence": result['confidence']
        }
    
    # Otherwise, use your regular RAG/assistant logic
    return regular_assistant_response(message)
```

---

## Option 3: Standalone Usage (Python Script)

Use the AWD assistant independently:

```python
from AWD_World_Model import ConversationalAWDHandler, FarmState

handler = ConversationalAWDHandler()
state = FarmState()

# Single question
result = handler.process_question("Should I irrigate today?", state)
print(result['response'])

# Multi-turn conversation
questions = [
    "Should I irrigate today?",
    "Water table is 14cm below surface",
    "Crop is in tillering stage",
    "No rain expected"
]

for q in questions:
    result = handler.process_question(q, state)
    print(f"\nQ: {q}")
    print(f"A: {result['response']}\n")
    if not result['needs_more_info']:
        print("✅ Sufficient info - gave full advice")
        break
```

---

## Frontend Integration

### Example React/Frontend Code

```javascript
// Call the AWD API
async function askAWDQuestion(question) {
  const response = await fetch('http://localhost:8000/api/awd/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: currentUserId,
      question: question
    })
  });
  
  const data = await response.json();
  
  // Display response
  displayMessage(data.response);
  
  // If needs more info, show follow-up questions
  if (data.needs_more_info && data.questions.length > 0) {
    data.questions.forEach(q => {
      displayFollowUpQuestion(q);
    });
  }
  
  // Show confidence level
  if (data.confidence === 'low') {
    showInfoBadge('Need more information for accurate advice');
  }
}
```

---

## Database Persistence (Optional)

To persist farm state across sessions:

### Add to your User/Farm model:

```python
# In your database models
class Farm(Base):
    __tablename__ = "farms"
    
    # ... existing fields ...
    
    # Add AWD state field
    awd_state = Column(JSON, nullable=True)

# Save state
farm.awd_state = farm_state.dict()
db.commit()

# Load state
loaded_state = FarmState(**farm.awd_state)
```

---

## Environment Variables (if needed)

None required currently. The system works out of the box.

If you add weather API integration later:
```env
WEATHER_API_KEY=your_key_here
```

---

## Testing Checklist

Before deployment, test these scenarios:

- [ ] Ask simple question without context
- [ ] Provide partial information
- [ ] Complete multi-turn conversation
- [ ] Ask educational question
- [ ] Check feasibility
- [ ] Safety check during flowering
- [ ] Troubleshooting with stress symptoms
- [ ] API endpoints return proper JSON
- [ ] State persists across questions
- [ ] Reset state works

Run `python example_usage.py` to see all scenarios.

---

## API Response Structure

```typescript
interface AWDResponse {
  response: string;              // Main response text
  needs_more_info: boolean;      // True if more data needed
  questions: string[];           // Follow-up questions (max 3)
  confidence: 'high' | 'medium' | 'low';
  intent: string;                // Detected intent
  farm_state_summary: string;    // Current known state
  timestamp: string;             // ISO timestamp
}
```

---

## Monitoring & Logging

Add logging to track usage:

```python
import logging

# In your process_question wrapper:
logging.info(f"AWD question from {user_id}: {question}")
logging.info(f"Intent: {result['intent']}, Confidence: {result['confidence']}")

if result['needs_more_info']:
    logging.info(f"Missing slots: {result['questions']}")
else:
    logging.info(f"Provided full advice")
```

---

## Common Issues & Solutions

### Issue: Import errors
**Solution**: Ensure `AWD_World_Model` is in your Python path
```python
import sys
sys.path.append('/path/to/Aditi_Rice_Assistant')
```

### Issue: State not persisting
**Solution**: Use a proper state store (dict, database, Redis)
```python
# Global state store
from collections import defaultdict
farm_states = defaultdict(FarmState)

# Or use database
farm.awd_state = state.dict()
```

### Issue: Questions not extracting info
**Solution**: Check extraction with debug:
```python
from AWD_World_Model import SlotExtractor
extracted = SlotExtractor.extract_all(user_message)
print(f"Extracted: {extracted}")
```

---

## No Changes Required

The following files are **not modified**:
- ✅ `RA_Backend/main.py` (unless you choose Option 1)
- ✅ `RA_Backend/api/assistant.py`
- ✅ `RA_Backend/database/` files
- ✅ `RA_Frontend/` files
- ✅ Any existing code

Everything stays in `AWD_World_Model/` until you're ready to integrate.

---

## Quick Start

**Want to try it now without integration?**

```bash
cd AWD_World_Model
python example_usage.py
```

This runs all examples and shows you exactly how the system works.

**Want to integrate into backend?**

Just add 2 lines to `RA_Backend/main.py`:
```python
from AWD_World_Model.api_router import router as awd_router
app.include_router(awd_router)
```

Then restart your backend and visit `http://localhost:8000/api/docs` to see the new endpoints.

---

## Support

- **Examples**: See `example_usage.py`
- **Architecture**: See `README.md`
- **API Docs**: Visit `/api/docs` after integration
- **Decision Logic**: Check `decision_logic.py`

Ready when you are! 🚀
