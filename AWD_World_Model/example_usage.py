"""
Example usage of the AWD Conversational Assistant
This demonstrates how to use the assistant in different scenarios
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from farm_state import FarmState
from conversational_handler import ConversationalAWDHandler


def example_1_simple_question():
    """Example 1: Simple question with progressive slot filling"""
    print("=" * 60)
    print("EXAMPLE 1: Simple Irrigation Question")
    print("=" * 60)
    
    handler = ConversationalAWDHandler()
    state = FarmState()
    
    question = "Should I irrigate today?"
    result = handler.process_question(question, state)
    
    print(f"\nFarmer: {question}")
    print(f"\nAssistant Response:\n{result['response']}")
    
    if result['needs_more_info']:
        print("\n--- Follow-up Questions ---")
        for i, q in enumerate(result['questions'], 1):
            print(f"\n{i}. {q}")
    
    print("\n" + "=" * 60 + "\n")


def example_2_with_partial_info():
    """Example 2: Question with some information provided"""
    print("=" * 60)
    print("EXAMPLE 2: Question with Partial Information")
    print("=" * 60)
    
    handler = ConversationalAWDHandler()
    state = FarmState()
    
    question = "Water table is 14cm below surface. Should I irrigate?"
    result = handler.process_question(question, state)
    
    print(f"\nFarmer: {question}")
    print(f"\nExtracted Info: Water table = 14cm")
    print(f"\nAssistant Response:\n{result['response']}")
    
    if result['needs_more_info']:
        print("\n--- Still Need to Know ---")
        for i, q in enumerate(result['questions'], 1):
            print(f"\n{i}. {q}")
    
    print(f"\nFarm State Summary: {state.to_summary()}")
    print("\n" + "=" * 60 + "\n")


def example_3_complete_conversation():
    """Example 3: Complete conversation with multiple turns"""
    print("=" * 60)
    print("EXAMPLE 3: Multi-turn Conversation")
    print("=" * 60)
    
    handler = ConversationalAWDHandler()
    state = FarmState()
    
    conversation = [
        "Should I irrigate today?",
        "The water tube shows 14cm below surface",
        "The crop is in tillering stage",
        "No heavy rain expected"
    ]
    
    for turn, question in enumerate(conversation, 1):
        print(f"\n--- Turn {turn} ---")
        print(f"Farmer: {question}")
        
        result = handler.process_question(question, state)
        
        print(f"\nAssistant:\n{result['response']}")
        
        if result['needs_more_info'] and result['questions']:
            print("\n[Assistant asks for more info]")
            for q in result['questions'][:2]:
                print(f"  • {q.split('**')[1] if '**' in q else q}")
        
        print(f"\nKnown State: {state.to_summary()}")
    
    print("\n" + "=" * 60 + "\n")


def example_4_educational_question():
    """Example 4: Educational question (no slot filling needed)"""
    print("=" * 60)
    print("EXAMPLE 4: Educational Question")
    print("=" * 60)
    
    handler = ConversationalAWDHandler()
    state = FarmState()
    
    question = "What is AWD and how does it work?"
    result = handler.process_question(question, state)
    
    print(f"\nFarmer: {question}")
    print(f"\nIntent: {result['intent']}")
    print(f"Needs Farm Info: {result['needs_more_info']}")
    print(f"\nAssistant Response:\n{result['response'][:500]}...")
    print("\n[Full educational content provided]")
    
    print("\n" + "=" * 60 + "\n")


def example_5_feasibility_check():
    """Example 5: Feasibility check for a specific field"""
    print("=" * 60)
    print("EXAMPLE 5: Feasibility Check")
    print("=" * 60)
    
    handler = ConversationalAWDHandler()
    state = FarmState()
    
    conversation = [
        "Can I do AWD in my field?",
        "Yes, it's a bunded paddy field",
        "The soil is clay loam",
        "No heavy rain expected this week"
    ]
    
    for question in conversation:
        print(f"\nFarmer: {question}")
        result = handler.process_question(question, state)
        
        if result['needs_more_info']:
            print(f"Assistant: [Asks follow-up]")
            if result['questions']:
                print(f"  → {result['questions'][0].split('**')[1] if '**' in result['questions'][0] else result['questions'][0]}")
        else:
            print(f"\nAssistant Final Answer:\n{result['response']}")
    
    print("\n" + "=" * 60 + "\n")


def example_6_safety_check():
    """Example 6: Safety check during critical stage"""
    print("=" * 60)
    print("EXAMPLE 6: Safety Check - Flowering Stage")
    print("=" * 60)
    
    handler = ConversationalAWDHandler()
    state = FarmState()
    
    state.update_from_dict({
        "crop.growth_stage": "flowering",
        "water.water_table_cm_below_surface": 12.0
    })
    
    question = "Is it safe to keep drying?"
    result = handler.process_question(question, state)
    
    print(f"\nCurrent State:")
    print(f"  - Growth stage: Flowering")
    print(f"  - Water table: 12cm below surface")
    
    print(f"\nFarmer: {question}")
    print(f"\nAssistant Response:\n{result['response']}")
    print(f"\nConfidence: {result['confidence']}")
    
    print("\n" + "=" * 60 + "\n")


def example_7_troubleshooting():
    """Example 7: Troubleshooting stress symptoms"""
    print("=" * 60)
    print("EXAMPLE 7: Troubleshooting")
    print("=" * 60)
    
    handler = ConversationalAWDHandler()
    state = FarmState()
    
    question = "My rice leaves are rolling and the soil has severe cracks. What should I do?"
    result = handler.process_question(question, state)
    
    print(f"\nFarmer: {question}")
    print(f"\nExtracted Observations:")
    print(f"  - Stress symptoms: Detected")
    print(f"  - Soil cracking: Severe")
    
    print(f"\nAssistant Response:\n{result['response']}")
    print(f"\nIntent: {result['intent']}")
    
    print("\n" + "=" * 60 + "\n")


def example_8_api_integration():
    """Example 8: How to use with FastAPI (code structure)"""
    print("=" * 60)
    print("EXAMPLE 8: API Integration Pattern")
    print("=" * 60)
    
    print("""
The AWD assistant can be integrated into your FastAPI backend like this:

```python
# In your main.py or api router:

from AWD_World_Model.api_router import router as awd_router

app.include_router(awd_router)
```

Then make POST requests to:

```
POST /api/awd/ask
{
    "user_id": "farmer_123",
    "question": "Should I irrigate today?"
}
```

Response includes:
- response: The assistant's answer
- needs_more_info: Whether more data is needed
- questions: Follow-up questions if needed
- confidence: high/medium/low
- intent: Detected intent
- farm_state_summary: Current known farm state

The assistant automatically:
✓ Maintains state per user
✓ Extracts information from questions
✓ Asks only necessary follow-ups
✓ Provides advice when ready
""")
    
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    print("\n" + "🌾" * 30)
    print("AWD CONVERSATIONAL ASSISTANT - EXAMPLE USAGE")
    print("🌾" * 30 + "\n")
    
    example_1_simple_question()
    example_2_with_partial_info()
    example_3_complete_conversation()
    example_4_educational_question()
    example_5_feasibility_check()
    example_6_safety_check()
    example_7_troubleshooting()
    example_8_api_integration()
    
    print("✅ All examples completed!\n")
