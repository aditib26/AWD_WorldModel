"""
Example usage with Qwen LLM enhancement
Shows the difference between rule-based and LLM-enhanced responses
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from farm_state import FarmState
from conversational_handler import ConversationalAWDHandler
from llm_client import init_qwen_client, is_qwen_available


async def example_with_llm():
    """Example showing LLM-enhanced responses"""
    print("=" * 60)
    print("QWEN LLM INTEGRATION EXAMPLE")
    print("=" * 60)
    
    # Initialize Qwen client
    print("\n🔧 Initializing Qwen client...")
    success = await init_qwen_client()
    
    if success:
        print("✅ Qwen client ready")
    else:
        print("⚠️ Qwen not available, using rule-based responses")
    
    print(f"Qwen status: {'Available' if is_qwen_available() else 'Not available'}\n")
    
    handler = ConversationalAWDHandler(use_llm=True)
    state = FarmState()
    
    # Set up a complete scenario
    state.update_from_dict({
        "crop.growth_stage": "tillering",
        "water.water_table_cm_below_surface": 14.0,
        "soil.texture_class": "loam",
        "weather.forecast_rain_next_7d_mm": 5.0
    })
    
    print("=" * 60)
    print("SCENARIO: Farmer asks about irrigation")
    print("=" * 60)
    print(f"\nFarm State:")
    print(f"  - Crop stage: Tillering")
    print(f"  - Water table: 14cm below surface")
    print(f"  - Soil: Loam")
    print(f"  - Rain forecast: 5mm (light)")
    
    question = "Should I irrigate today?"
    print(f"\n💬 Farmer: {question}")
    
    # Get LLM-enhanced response
    result = await handler.process_question_async(
        question=question,
        farm_state=state
    )
    
    print(f"\n{'🤖 LLM-Enhanced' if result.get('llm_enhanced') else '📋 Rule-Based'} Response:")
    print("-" * 60)
    print(result['response'])
    print("-" * 60)
    print(f"\nIntent: {result['intent']}")
    print(f"Confidence: {result['confidence']}")
    print(f"LLM Enhanced: {result.get('llm_enhanced', False)}")
    
    print("\n" + "=" * 60)


async def example_educational_llm():
    """Example showing LLM-enhanced educational content"""
    print("\n" + "=" * 60)
    print("EDUCATIONAL QUESTION WITH LLM")
    print("=" * 60)
    
    handler = ConversationalAWDHandler(use_llm=True)
    state = FarmState()
    
    question = "What is AWD and how much water can I save?"
    print(f"\n💬 Farmer: {question}")
    
    result = await handler.process_question_async(
        question=question,
        farm_state=state
    )
    
    print(f"\n{'🤖 LLM-Enhanced' if result.get('llm_enhanced') else '📋 Rule-Based'} Response:")
    print("-" * 60)
    print(result['response'][:500] + "..." if len(result['response']) > 500 else result['response'])
    print("-" * 60)
    print(f"\nLLM Enhanced: {result.get('llm_enhanced', False)}")
    
    print("\n" + "=" * 60)


async def example_comparison():
    """Compare rule-based vs LLM-enhanced responses"""
    print("\n" + "=" * 60)
    print("COMPARISON: Rule-Based vs LLM-Enhanced")
    print("=" * 60)
    
    handler_rule_based = ConversationalAWDHandler(use_llm=False)
    handler_llm = ConversationalAWDHandler(use_llm=True)
    
    state1 = FarmState()
    state2 = FarmState()
    
    # Same scenario
    for state in [state1, state2]:
        state.update_from_dict({
            "crop.growth_stage": "flowering",
            "water.water_table_cm_below_surface": 12.0,
            "observations.stress_symptoms_flag": False
        })
    
    question = "Is it safe to keep drying?"
    print(f"\n💬 Farmer: {question}")
    print(f"Context: Flowering stage, 12cm depth, no stress")
    
    # Rule-based
    print("\n📋 RULE-BASED RESPONSE:")
    print("-" * 60)
    result1 = handler_rule_based.process_question(question, state1)
    print(result1['response'][:300] + "..." if len(result1['response']) > 300 else result1['response'])
    
    # LLM-enhanced
    print("\n🤖 LLM-ENHANCED RESPONSE:")
    print("-" * 60)
    result2 = await handler_llm.process_question_async(question, state2)
    print(result2['response'][:300] + "..." if len(result2['response']) > 300 else result2['response'])
    
    print("\n" + "=" * 60)


async def main():
    print("\n" + "🌾" * 30)
    print("AWD ASSISTANT WITH QWEN LLM INTEGRATION")
    print("🌾" * 30 + "\n")
    
    await example_with_llm()
    await example_educational_llm()
    await example_comparison()
    
    print("\n✅ All LLM examples completed!\n")


if __name__ == "__main__":
    asyncio.run(main())
