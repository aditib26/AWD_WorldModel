"""LLM-Based Slot Extraction for AWD Assistant
Uses Qwen to intelligently extract structured farm information from natural language
"""

import json
import os
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

QWEN_TPU_ENDPOINT = os.getenv("QWEN_TPU_ENDPOINT")
QWEN_CHAT_MODEL = os.getenv("QWEN_CHAT_MODEL")
API_KEY = os.getenv("QWEN_API_KEY", os.getenv("API_KEY", "no-key-required"))

_qwen_client: Optional[AsyncOpenAI] = None


SLOT_EXTRACTION_PROMPT = """You are a precise farm information extractor. Your job is to ONLY extract factual information that is explicitly stated.

**CRITICAL RULES:**
1. Extract ONLY if the user is providing factual information about their farm
2. Do NOT extract from questions, requests for advice, or educational queries
3. Do NOT guess or infer ANY values
4. If the message is a question or request ("what", "how", "should I", "can I"), return {}
5. If no farm facts are stated, return {}

**Available Fields:**
- water.water_table_cm_below_surface (float): Water depth below surface in cm (from tube reading)
- water.standing_water_cm (float): Standing water depth in cm
- crop.growth_stage (string): One of ["tillering", "panicle_initiation", "flowering", "grain_filling"]
- crop.sow_or_transplant_date (string): Date in YYYY-MM-DD format
- crop.days_after (int): Days since planting
- soil.texture_class (string): One of ["clay", "loam", "sandy"]
- soil.percolation_class (string): One of ["low", "medium", "high"]
- soil.bunded_lowland (boolean): Whether field has bunds/levees
- observations.stress_symptoms_flag (boolean): Whether plants show stress (leaf rolling, wilting)
- observations.cracking_level (string): One of ["none", "mild", "severe"]
- farm.location (string): Village/town name
- farm.area_ha (float): Field area in hectares
- weather.forecast_rain_next_7d_mm (float): Expected rainfall in mm

**Special Cases:**
- If user says they CANNOT measure water ("no tube", "can't measure"), set both water fields to null
- Growth stage mapping: "tillering"/"vegetative" → "tillering", "panicle"/"PI" → "panicle_initiation", "flowering"/"bloom" → "flowering", "grain filling"/"ripening" → "grain_filling"
- Soil texture: "clay"/"heavy" → "clay", "loam"/"medium" → "loam", "sandy"/"light" → "sandy"
- Percolation: "slow"/"2-3 days" → "low", "moderate"/"1-2 days" → "medium", "fast"/"within day" → "high"

**Examples (EXTRACT):**

Input: "water is 15cm below surface in my field near Patna village"
Output: {"water.water_table_cm_below_surface": 15, "farm.location": "Patna"}

Input: "I have 2 hectares of rice at flowering stage with 5cm standing water"
Output: {"farm.area_ha": 2, "crop.growth_stage": "flowering", "water.standing_water_cm": 5}

Input: "my soil is clay and drains slowly, the plants are in tillering phase"
Output: {"soil.texture_class": "clay", "soil.percolation_class": "low", "crop.growth_stage": "tillering"}

Input: "I don't have a tube to measure"
Output: {"water.water_table_cm_below_surface": null, "water.standing_water_cm": null}

**Examples (DO NOT EXTRACT - return {}):**

Input: "what is AWD?"
Output: {}

Input: "should I irrigate today?"
Output: {}

Input: "how does AWD work?"
Output: {}

Input: "can I practice AWD on my field?"
Output: {}

Input: "when should I irrigate?"
Output: {}

Input: "tell me about water management"
Output: {}

Now extract from this message:"""


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
            print(f"❌ LLM Slot Extractor: Failed to initialize Qwen: {str(e)}")
            return None
    return _qwen_client


async def extract_slots_with_llm(text: str, conversation_context: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract farm information slots from natural language using LLM
    
    Args:
        text: User's natural language input
        conversation_context: Optional context from previous conversation
        
    Returns:
        Dictionary with extracted slot-value pairs
    """
    # Early exit for questions and requests - don't extract anything
    text_lower = text.lower().strip()
    question_patterns = [
        r'^what\s',
        r'^how\s',
        r'^why\s',
        r'^when\s',
        r'^where\s',
        r'^can\s+i\s',
        r'^should\s+i\s',
        r'^is\s+it\s',
        r'^do\s+i\s',
        r'^does\s',
        r'^tell\s+me\s',
        r'^explain\s',
        r'\?$'  # Ends with question mark
    ]
    
    import re
    for pattern in question_patterns:
        if re.search(pattern, text_lower):
            # This is a question/request, not farm information
            return {}
    
    client = await ensure_qwen_client()
    if not client:
        return {}
    
    try:
        # Build prompt with context if available
        prompt = SLOT_EXTRACTION_PROMPT + f"\n\n{text}"
        if conversation_context:
            prompt = f"Context: {conversation_context}\n\n" + prompt
        
        response = await client.chat.completions.create(
            model=QWEN_CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You are a precise information extraction system. Return ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for consistent extraction
            max_tokens=500
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean up markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        # Parse JSON
        try:
            extracted = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from text
            import re
            json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
            if json_match:
                extracted = json.loads(json_match.group(0))
            else:
                print(f"⚠️ LLM Slot Extractor: Could not parse JSON from response: {content}")
                return {}
        
        # Validate and clean extracted data
        validated = {}
        for key, value in extracted.items():
            if isinstance(value, str) and value.strip() == "":
                continue
            validated[key] = value
        
        if validated:
            print(f"✅ LLM Slot Extractor: Extracted {len(validated)} slots from: '{text[:50]}...'")
            print(f"   Slots: {list(validated.keys())}")
        
        return validated
        
    except Exception as e:
        print(f"❌ LLM Slot Extractor: Error during extraction: {str(e)}")
        return {}


async def extract_slots_with_confidence(text: str, conversation_context: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract slots with confidence scores for each extraction
    
    Returns:
        Dictionary with extracted slots and their confidence levels
        Format: {
            "slots": {"slot.name": value, ...},
            "confidence": {"slot.name": 0.0-1.0, ...},
            "reasoning": "Brief explanation of extractions"
        }
    """
    client = await ensure_qwen_client()
    if not client:
        return {"slots": {}, "confidence": {}, "reasoning": "LLM not available"}
    
    confidence_prompt = SLOT_EXTRACTION_PROMPT + f"""

Additionally, provide:
1. Confidence score (0.0-1.0) for each extracted field
2. Brief reasoning for the extraction

Return JSON format:
{{
    "slots": {{"field.name": value, ...}},
    "confidence": {{"field.name": 0.95, ...}},
    "reasoning": "explanation"
}}

Message to extract from:
{text}"""
    
    try:
        if conversation_context:
            confidence_prompt = f"Context: {conversation_context}\n\n" + confidence_prompt
        
        response = await client.chat.completions.create(
            model=QWEN_CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You are a precise information extraction system with confidence estimation."},
                {"role": "user", "content": confidence_prompt}
            ],
            temperature=0.1,
            max_tokens=700
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean markdown
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        result = json.loads(content)
        
        # Validate structure
        if "slots" not in result:
            result = {"slots": result, "confidence": {}, "reasoning": ""}
        
        return result
        
    except Exception as e:
        print(f"❌ LLM Slot Extractor: Error during confidence extraction: {str(e)}")
        # Fallback to basic extraction
        slots = await extract_slots_with_llm(text, conversation_context)
        return {"slots": slots, "confidence": {}, "reasoning": ""}


# Backward compatibility wrapper
class LLMSlotExtractor:
    """
    LLM-based slot extractor with fallback to regex patterns
    Maintains compatibility with existing SlotExtractor interface
    """
    
    @staticmethod
    async def extract_all(text: str, use_llm: bool = True, conversation_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract all slots from text using LLM (with regex fallback)
        
        Args:
            text: User input text
            use_llm: Whether to use LLM (True) or fallback to regex (False)
            conversation_context: Optional conversation context
            
        Returns:
            Dictionary of extracted slots
        """
        if use_llm:
            slots = await extract_slots_with_llm(text, conversation_context)
            if slots:
                return slots
        
        # Fallback to regex-based extraction
        from .slot_extractor import SlotExtractor
        return SlotExtractor.extract_all(text)
    
    @staticmethod
    async def extract_all_with_confidence(text: str, conversation_context: Optional[str] = None) -> Dict[str, Any]:
        """Extract slots with confidence scores"""
        return await extract_slots_with_confidence(text, conversation_context)
