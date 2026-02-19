"""
LLM-Based Intent Classification for AWD Assistant
Replaces rigid pattern matching with intelligent understanding
"""

import json
import os
from typing import Dict, Any, Tuple, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

QWEN_TPU_ENDPOINT = os.getenv("QWEN_TPU_ENDPOINT")
QWEN_CHAT_MODEL = os.getenv("QWEN_CHAT_MODEL")
API_KEY = os.getenv("QWEN_API_KEY", os.getenv("API_KEY", "no-key-required"))

_qwen_client: Optional[AsyncOpenAI] = None


INTENT_CLASSIFICATION_PROMPT = """You are an expert at understanding farmer questions about AWD (Alternate Wetting and Drying) irrigation.

**Available Intents:**

1. **irrigation_now** - Farmer asking if they should irrigate right now
   Examples: "Should I water today?", "Do I need to irrigate?", "Is it time to add water?"

2. **safety_check** - Farmer concerned about crop safety with current water level
   Examples: "Is my crop safe?", "Will my rice be okay?", "Am I risking my plants?"

3. **benefits** - Asking about AWD benefits, savings, or why to use AWD
   Examples: "Why use AWD?", "How much water will I save?", "What are the benefits?"

4. **awd_basics** - General questions about AWD methodology
   Examples: "What is AWD?", "How does AWD work?", "Tell me about alternate wetting"

5. **tube_installation** - Questions about installing or using water tubes
   Examples: "How do I install a tube?", "Where should I place the tube?", "How to read the tube?"

6. **feasibility** - Asking if AWD will work for their specific field
   Examples: "Can I use AWD in sandy soil?", "Will this work for me?", "Is my field suitable?"

7. **growth_stage_advice** - Questions about specific growth stages
   Examples: "What about during flowering?", "Is AWD safe in tillering?", "Critical stages?"

8. **troubleshooting** - Problems or issues with AWD practice
   Examples: "My field is cracking", "Plants look stressed", "Water drains too fast"

9. **water_calculation** - Asking about water amounts, savings, or measurements
   Examples: "How much water do I need?", "Calculate my savings", "Water requirements?"

10. **info_provide** - Farmer providing information or updates (not asking for advice)
    Examples: "My water level is 18cm", "The field is at flowering stage", "Soil is clay"

11. **general_question** - Other rice farming questions or chitchat
    Examples: "What about fertilizer?", "Hello", "When to harvest?"

**Classification Rules:**
- Choose the MOST SPECIFIC intent that matches the question
- If farmer is clearly asking for irrigation advice → irrigation_now
- If expressing concern about safety → safety_check
- If just stating facts without asking → info_provide
- Consider context: "flowering" + "safe" → safety_check, not growth_stage_advice
- Default to general_question only if no AWD-related intent matches

**Response Format:**
Return ONLY a JSON object:
{
    "intent": "intent_name",
    "confidence": 0.95,
    "reasoning": "Brief explanation of why this intent was chosen",
    "requires_farm_state": true,
    "urgency": "high|medium|low"
}

**urgency levels:**
- high: Immediate irrigation decisions, safety concerns
- medium: Feasibility checks, troubleshooting
- low: Education, general questions

Now classify this question:"""


async def ensure_qwen_client() -> Optional[AsyncOpenAI]:
    """Ensure Qwen client is initialized"""
    global _qwen_client
    if _qwen_client is None:
        if not QWEN_TPU_ENDPOINT or not QWEN_CHAT_MODEL:
            return None
        try:
            _qwen_client = AsyncOpenAI(
                base_url=QWEN_TPU_ENDPOINT,
                api_key=API_KEY
            )
        except Exception as e:
            print(f"❌ LLM Intent Classifier: Failed to initialize Qwen: {str(e)}")
            return None
    return _qwen_client


async def classify_intent_with_llm(
    question: str, 
    conversation_context: Optional[str] = None,
    farm_state_summary: Optional[str] = None
) -> Dict[str, Any]:
    """
    Classify user intent using LLM for more flexible understanding
    
    Args:
        question: User's question
        conversation_context: Recent conversation history
        farm_state_summary: Current farm state context
        
    Returns:
        Dictionary with intent, confidence, reasoning, and metadata
    """
    client = await ensure_qwen_client()
    if not client:
        return {
            "intent": "general_question",
            "confidence": 0.5,
            "reasoning": "LLM not available, using fallback",
            "requires_farm_state": False,
            "urgency": "medium"
        }
    
    try:
        # Build context-aware prompt
        prompt = INTENT_CLASSIFICATION_PROMPT + f"\n\n{question}"
        
        if conversation_context:
            prompt = f"Recent conversation: {conversation_context}\n\n" + prompt
        
        if farm_state_summary:
            prompt = f"Farm context: {farm_state_summary}\n\n" + prompt
        
        response = await client.chat.completions.create(
            model=QWEN_CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert intent classifier for agricultural assistance. Return ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for consistent classification
            max_tokens=300
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean up markdown
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        # Parse JSON
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON
            import re
            json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                print(f"⚠️ LLM Intent Classifier: Could not parse: {content}")
                return {
                    "intent": "general_question",
                    "confidence": 0.5,
                    "reasoning": "Parse error",
                    "requires_farm_state": False,
                    "urgency": "medium"
                }
        
        # Validate intent
        valid_intents = [
            "irrigation_now", "safety_check", "benefits", "awd_basics",
            "tube_installation", "feasibility", "growth_stage_advice",
            "troubleshooting", "water_calculation", "info_provide", "general_question"
        ]
        
        if result.get("intent") not in valid_intents:
            result["intent"] = "general_question"
        
        # Ensure required fields
        result.setdefault("confidence", 0.8)
        result.setdefault("reasoning", "Classified by LLM")
        result.setdefault("requires_farm_state", result["intent"] not in ["awd_basics", "benefits", "general_question"])
        result.setdefault("urgency", "medium")
        
        print(f"✅ LLM Intent Classifier: {result['intent']} (confidence: {result['confidence']:.2f})")
        
        return result
        
    except Exception as e:
        print(f"❌ LLM Intent Classifier: Error: {str(e)}")
        return {
            "intent": "general_question",
            "confidence": 0.5,
            "reasoning": f"Classification error: {str(e)}",
            "requires_farm_state": False,
            "urgency": "medium"
        }


async def classify_with_multi_intent(
    question: str,
    conversation_context: Optional[str] = None,
    farm_state_summary: Optional[str] = None
) -> Dict[str, Any]:
    """
    Advanced: Detect multiple intents in complex questions
    
    Returns:
        {
            "primary_intent": "intent_name",
            "secondary_intents": ["intent2", "intent3"],
            "confidence": 0.95,
            "reasoning": "explanation"
        }
    """
    client = await ensure_qwen_client()
    if not client:
        simple_result = await classify_intent_with_llm(question, conversation_context, farm_state_summary)
        return {
            "primary_intent": simple_result["intent"],
            "secondary_intents": [],
            "confidence": simple_result["confidence"],
            "reasoning": simple_result["reasoning"]
        }
    
    multi_prompt = INTENT_CLASSIFICATION_PROMPT.replace(
        "Return ONLY a JSON object:",
        """Return ONLY a JSON object (for complex questions with multiple intents):
{
    "primary_intent": "main_intent",
    "secondary_intents": ["intent2", "intent3"],
    "confidence": 0.95,
    "reasoning": "explanation"
}"""
    )
    
    try:
        prompt = multi_prompt + f"\n\n{question}"
        if conversation_context:
            prompt = f"Recent conversation: {conversation_context}\n\n" + prompt
        
        response = await client.chat.completions.create(
            model=QWEN_CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert intent classifier. Detect multiple intents if present."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=400
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean and parse
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        result = json.loads(content)
        
        return result
        
    except Exception as e:
        print(f"⚠️ Multi-intent classification failed: {str(e)}")
        simple_result = await classify_intent_with_llm(question, conversation_context, farm_state_summary)
        return {
            "primary_intent": simple_result["intent"],
            "secondary_intents": [],
            "confidence": simple_result["confidence"],
            "reasoning": simple_result["reasoning"]
        }


# Backward compatibility wrapper
class LLMIntentClassifier:
    """
    LLM-based intent classifier with fallback to pattern-based classification
    """
    
    @staticmethod
    async def classify(
        question: str,
        use_llm: bool = True,
        conversation_context: Optional[str] = None,
        farm_state_summary: Optional[str] = None
    ) -> Tuple[str, float]:
        """
        Classify intent (returns tuple for backward compatibility)
        
        Returns:
            (intent_name, confidence_score)
        """
        if use_llm:
            result = await classify_intent_with_llm(question, conversation_context, farm_state_summary)
            return result["intent"], result["confidence"]
        else:
            # Fallback to regex-based classifier
            from .intent_classifier import IntentClassifier
            return IntentClassifier().classify(question)
    
    @staticmethod
    async def classify_detailed(
        question: str,
        conversation_context: Optional[str] = None,
        farm_state_summary: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get detailed classification with reasoning"""
        return await classify_intent_with_llm(question, conversation_context, farm_state_summary)
