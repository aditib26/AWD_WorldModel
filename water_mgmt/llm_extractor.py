"""LLM-based slot extraction from natural language"""

import os
import json
from typing import Dict, Any, Optional, Tuple
from openai import OpenAI
from .schemas import ChatExtractionResult, ClarificationRequest
from .config import OPENAI_API_KEY, OPENAI_MODEL


# ============================================================================
# AWD HANDBOOK RULES - Source of truth for water management advice
# ============================================================================

AWD_HANDBOOK_RULES = """
=== AWD HANDBOOK RULES (Mekong Delta Rice Farming) ===
These are the ONLY rules you should follow for water management advice.

CORE AWD PRINCIPLE:
Irrigate ONLY when water table drops to 15 cm below soil surface, OR when soil cracks appear.
When re-flooding, water level should NOT exceed 3-5 cm (shallow ponding).

AWD SCHEDULE BY DAYS AFTER SOWING (DAS):
● Day 1-7: Keep field MOIST for germination. No standing water needed.
● Day 12-22: DRAIN water, let soil dry to oxygenate roots.
● Day 28-40: DRAIN again for second drying cycle.
● During growing: Monitor with AWD tube. Irrigate when water drops to 15cm below surface.
● 7-15 days before harvest: FINAL DRYING - stop irrigation completely.

MEASUREMENT THRESHOLDS:
- AWD trigger depth: 15 cm below soil surface
- Reflood target: 3-5 cm of shallow ponding
- Observation tube: perforated pipe, 10-15 cm height
- Soil cracks ("nứt chân chim"): signal that irrigation is needed

SENSITIVE STAGES (maintain shallow ponding, avoid deep drying):
- Panicle initiation
- Flowering/heading
- Grain filling

BENEFITS OF AWD:
- Saves 15-30% water
- Reduces methane emissions
- Strengthens root systems
- Reduces nutrient loss
- Lower input costs

PRE-SOWING: Do not flood field for >30 days before sowing (prevents waterlogging & methane).

SINGLE AWD OPTION: Some farmers apply AWD only once (days 28-40). Still reduces methane if 15cm threshold is respected.
"""


# Schema for the unified extract-and-respond call
UNIFIED_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "state_updates": {
            "type": "object",
            "description": "Any field state changes detected from the farmer's message",
            "properties": {
                "ponded_water_cm": {"type": ["number", "null"]},
                "water_table_depth_cm": {"type": ["number", "null"]},
                "das": {"type": ["integer", "null"]},
                "growth_stage": {
                    "type": ["string", "null"],
                    "enum": ["seedling", "tillering", "panicle_initiation",
                            "heading", "grain_filling", "maturity", "unknown", None]
                },
                "soil_cracks": {
                    "type": ["string", "null"],
                    "enum": ["none", "small", "visible", "deep", "unknown", None]
                },
                "regime_intent": {
                    "type": ["string", "null"],
                    "enum": ["AWD", "CONTINUOUS", "RAINFED", "unknown", None]
                },
                "rain_last_24h_mm": {"type": ["number", "null"]},
                "soil_type": {
                    "type": ["string", "null"],
                    "enum": ["alluvial", "acid_sulfate", "clay", "sandy", "unknown", None]
                }
            }
        },
        "state_changed": {
            "type": "boolean",
            "description": "True if any field state was updated from this message"
        },
        "response": {
            "type": "string",
            "description": "Conversational response to the farmer"
        },
        "confidence": {
            "type": "number",
            "description": "Confidence in the state extraction (0-1)"
        }
    },
    "required": ["state_updates", "state_changed", "response", "confidence"]
}


EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "slots": {
            "type": "object",
            "properties": {
                "ponded_water_cm": {"type": "number"},
                "water_table_depth_cm": {"type": "number"},
                "das": {"type": "integer"},
                "growth_stage": {
                    "type": "string",
                    "enum": ["seedling", "tillering", "panicle_initiation", 
                            "heading", "grain_filling", "maturity", "unknown"]
                },
                "soil_cracks": {
                    "type": "string",
                    "enum": ["none", "small", "visible", "deep", "unknown"]
                },
                "irrigation_access": {"type": "boolean"},
                "drainage_access": {"type": "boolean"},
                "rain_last_24h_mm": {"type": "number"},
                "regime_intent": {
                    "type": "string",
                    "enum": ["AWD", "CONTINUOUS", "RAINFED", "unknown"]
                }
            }
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "need_clarification": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field": {"type": "string"},
                    "question": {"type": "string"},
                    "reason": {"type": "string"}
                },
                "required": ["field", "question"]
            }
        },
        "evidence": {"type": "array", "items": {"type": "string"}},
        "unit_notes": {"type": "string"},
        "water_measurement_type": {
            "type": "string",
            "enum": ["ponded_depth", "awd_tube_depth", "qualitative_only", "unknown"]
        }
    },
    "required": ["slots", "confidence"]
}


SYSTEM_PROMPT = """You are a slot extractor for a rice farming water management system in the Mekong Delta.

Extract structured information from farmer messages about their rice field water conditions.

RULES:
1. Only extract facts explicitly stated - never guess numeric values
2. If user says "water level is 10 cm" without specifying type (standing water vs tube depth):
   - Set water_measurement_type = "unknown"
   - Add clarification: "Is that 10 cm of standing water above soil, or 10 cm below soil surface in an AWD tube?"
3. Convert units:
   - "mm" or "millimeters" → keep as mm
   - "cm" or "centimeters" → keep as cm
   - "inches" → convert to cm (1 inch = 2.54 cm) and note conversion
4. Vietnamese units: extract but don't convert unless clearly a measurement
5. Confidence:
   - 0.9-1.0: numeric measurement clearly stated with unit
   - 0.7-0.9: categorical observation clear (e.g., "small cracks")
   - 0.5-0.7: ambiguous or qualitative
   - < 0.5: very uncertain, needs clarification
6. Evidence: quote 2-3 short relevant spans from the message
7. Growth stages:
   - Early/young/seedling → "seedling"
   - Tillering/branching → "tillering"  
   - Panicle formation/initiation → "panicle_initiation"
   - Flowering/heading → "heading"
   - Grain filling/maturing → "grain_filling"
   - Ready to harvest/mature → "maturity"
8. Soil cracks:
   - No cracks/wet/muddy → "none"
   - Small/hairline cracks → "small"
   - Visible/clear cracks → "visible"
   - Deep/wide cracks → "deep"

Return only JSON matching the schema."""


class LLMSlotExtractor:
    """Extract structured slots from free text using OpenAI"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = OPENAI_MODEL):
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
    
    def extract_from_text(
        self,
        message: str,
        current_state: Optional[Any] = None
    ) -> ChatExtractionResult:
        """Extract from text with WorldState context"""
        state_summary = None
        if current_state:
            # Convert WorldState to dict summary
            state_summary = {
                "farm_id": current_state.farm_id,
                "das": current_state.das,
                "growth_stage": current_state.growth_stage,
                "regime": current_state.regime,
                "water_table_depth_cm": current_state.water_table_depth_cm,
                "ponded_water_cm": current_state.ponded_water_cm,
                "soil_cracks": current_state.soil_cracks
            }
        
        return self.extract(message, state_summary)
    
    def world_model_chat(
        self,
        message: str,
        farm_context: str,
        planner_assessment: str,
        conversation_history: list = None
    ) -> Dict[str, Any]:
        """Unified world-model chat: extract state changes AND generate response in one call.
        
        This is the core of the world-model-driven assistant.
        Every message flows through: extract state → (backend updates) → respond with handbook context.
        
        Returns dict with: state_updates, state_changed, response, confidence
        """
        
        # Determine stage sensitivity for prompt
        _sensitive_stages = {"panicle_initiation", "heading", "grain_filling"}
        _is_sensitive = False
        _growth_stage_str = ""
        if "Growth Stage:" in farm_context:
            for s in _sensitive_stages:
                if s in farm_context.lower():
                    _is_sensitive = True
                    break

        system_prompt = f"""You are an expert rice irrigation advisor for Mekong Delta farmers. You combine real-time weather data, the AWD handbook, and the farmer's own field observations to give precise, actionable advice.

═══ OUTPUT FORMAT (strict JSON) ═══
Return EXACTLY this JSON structure:
{{
  "state_updates": {{
    "water_table_depth_cm": null or number,
    "ponded_water_cm": null or number,
    "soil_cracks": null or "none"/"small"/"visible"/"deep",
    "das": null or integer,
    "growth_stage": null or "seedling"/"tillering"/"panicle_initiation"/"heading"/"grain_filling"/"maturity",
    "soil_type": null or "alluvial"/"acid_sulfate"/"clay"/"sandy",
    "rain_last_24h_mm": null or number,
    "regime_intent": null or "AWD"/"CONTINUOUS"/"RAINFED"
  }},
  "state_changed": true/false,
  "response": "your message to the farmer",
  "confidence": 0.0 to 1.0
}}

═══ STATE EXTRACTION RULES ═══
- Set a field ONLY if the farmer explicitly mentions or implies it. Otherwise null.
- "state_changed": true ONLY if you set at least one non-null value.
- Be precise with numbers — "16 cm below" → water_table_depth_cm: 16
- "knee-deep water" → ponded_water_cm: ~15; "ankle-deep" → ~8; "just covers soil" → ~2
- Crack synonyms: "nứt chân chim" = visible; "nứt sâu" = deep; "hairline" = small

═══ AWD HANDBOOK (your source of truth) ═══
{AWD_HANDBOOK_RULES}

═══ FARMER'S PROFILE & LIVE STATE ═══
{farm_context}

═══ PLANNER ASSESSMENT (rule engine result) ═══
{planner_assessment}

═══ HOW TO RESPOND ═══

1. ACKNOWLEDGE what the farmer told you (show you understood).

2. GIVE YOUR VERDICT — one clear action:
   • IRRIGATE: "You should irrigate now — refill to 3-5 cm."
   • HOLD: "No irrigation needed yet. Keep monitoring."
   • DRAIN: "You should drain excess water."
   • Or explain the planner's recommendation in simple terms.

3. EXPLAIN WHY in 1-2 sentences using the handbook rule + their data.
   Example: "Your water table at 16 cm has passed the 15 cm AWD trigger, so it's time to irrigate."

4. FACTOR IN WEATHER if relevant:
   • If significant rain is forecast → "However, Xmm of rain is expected in the next 3 days, so you may be able to wait and save water."
   • If hot/dry → "With high temperatures and evaporation, your field will dry faster than usual."
   • If no rain → mention it supports the irrigation recommendation.

5. TELL THEM THEIR NEXT STEP:
   • When to check again: "Check your AWD tube again tomorrow morning."
   • What to watch for: "If you see cracks forming, irrigate immediately."
   • Stage-specific: Mention if they're approaching a sensitive stage.

6. ASK FOR MISSING DATA (if critical info is unknown):
   • No water table reading but they have a tube → "Can you check your AWD tube and tell me the water level?"
   • No crack status → "Are you seeing any cracks in the soil?"
   • Don't ask more than one question per response.

{"⚠️ SENSITIVE STAGE ALERT: The crop is in " + farm_context.split("Growth Stage:")[1].split(chr(10))[0].strip() + " — a water-sensitive stage. Err on the side of irrigating. Do NOT recommend holding if water table is near 15cm." if _is_sensitive and "Growth Stage:" in farm_context else ""}

═══ CONFLICT DETECTION ═══
If the farmer's message CONFLICTS with their stored profile:
- Soil type mismatch → ask which is correct
- AWD tube mismatch → clarify
- Do NOT give advice until conflicts are resolved.

═══ LANGUAGE ═══
- If the farmer writes in Vietnamese, respond in Vietnamese.
- If in English, respond in English.
- Vietnamese: "mực nước" (water level), "tưới" (irrigate), "nứt" (cracks)

═══ TONE ═══
- Warm but professional. You're their trusted advisor, not a chatbot.
- Use 1-2 emojis max (🌾💧). Don't overdo it.
- Be concise: 3-5 sentences. Farmers are busy.
- Never say "I'm an AI" or "based on my training data."
- Sound like a knowledgeable neighbor who studied the handbook."""

        messages = [{"role": "system", "content": system_prompt}]
        
        if conversation_history:
            # Only include last 8 messages to stay within token limits
            messages.extend(conversation_history[-8:])
        
        messages.append({"role": "user", "content": message})
        
        import time
        
        last_error = None
        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.4,
                    max_tokens=800
                )
                
                raw_content = response.choices[0].message.content
                result = json.loads(raw_content)
                
                # Ensure required fields exist
                return {
                    "state_updates": result.get("state_updates", {}),
                    "state_changed": result.get("state_changed", False),
                    "response": result.get("response", "I'm sorry, I couldn't process that. Could you try again?"),
                    "confidence": result.get("confidence", 0.5)
                }
                
            except json.JSONDecodeError:
                # JSON parsing failed — use raw text as response
                return {
                    "state_updates": {},
                    "state_changed": False,
                    "response": raw_content if raw_content else "I had trouble processing that. Could you rephrase?",
                    "confidence": 0.0
                }
            except Exception as e:
                last_error = e
                if attempt < 2:
                    time.sleep(1.5 * (attempt + 1))  # Backoff: 1.5s, 3s
                    continue
        
        # All retries failed
        return {
            "state_updates": {},
            "state_changed": False,
            "response": f"I'm having trouble connecting right now. Please try again in a moment.",
            "confidence": 0.0
        }
    
    def generate_conversation_response(
        self,
        message: str,
        context: str,
        conversation_history: list = None
    ) -> str:
        """Legacy method - delegates to world_model_chat for backward compat"""
        result = self.world_model_chat(message, context, "No planner data available.", conversation_history)
        return result["response"]
    
    def extract(
        self,
        message: str,
        state_summary: Optional[Dict[str, Any]] = None
    ) -> ChatExtractionResult:
        """Extract slots from user message"""
        
        # Build context
        context = ""
        if state_summary:
            context = f"\n\nCurrent state summary: {json.dumps(state_summary, default=str)}"
        
        user_content = f"User message: {message}{context}"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "slot_extraction",
                        "strict": True,
                        "schema": EXTRACTION_SCHEMA
                    }
                },
                temperature=0.1,
                max_tokens=500
            )
            
            result_json = json.loads(response.choices[0].message.content)
            
            # Convert to ChatExtractionResult
            clarifications = [
                ClarificationRequest(**c)
                for c in result_json.get("need_clarification", [])
            ]
            
            return ChatExtractionResult(
                slots=result_json.get("slots", {}),
                confidence=result_json.get("confidence", 0.5),
                need_clarification=clarifications,
                evidence=result_json.get("evidence", []),
                unit_notes=result_json.get("unit_notes"),
                water_measurement_type=result_json.get("water_measurement_type")
            )
        
        except Exception as e:
            # Fallback: try function calling
            return self._fallback_extraction(message, state_summary, e)
    
    def _fallback_extraction(
        self,
        message: str,
        state_summary: Optional[Dict[str, Any]],
        original_error: Exception
    ) -> ChatExtractionResult:
        """Fallback to tool calling if structured output fails"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"User message: {message}"}
                ],
                tools=[{
                    "type": "function",
                    "function": {
                        "name": "extract_slots",
                        "description": "Extract structured slots from farmer message",
                        "parameters": EXTRACTION_SCHEMA
                    }
                }],
                tool_choice={"type": "function", "function": {"name": "extract_slots"}},
                temperature=0.1
            )
            
            tool_call = response.choices[0].message.tool_calls[0]
            function_args = json.loads(tool_call.function.arguments)
            
            clarifications = [
                ClarificationRequest(**c)
                for c in function_args.get("need_clarification", [])
            ]
            
            return ChatExtractionResult(
                slots=function_args.get("slots", {}),
                confidence=function_args.get("confidence", 0.5),
                need_clarification=clarifications,
                evidence=function_args.get("evidence", []),
                unit_notes=function_args.get("unit_notes"),
                water_measurement_type=function_args.get("water_measurement_type")
            )
        
        except Exception as e:
            # Both methods failed - return low confidence result
            return ChatExtractionResult(
                slots={},
                confidence=0.0,
                need_clarification=[
                    ClarificationRequest(
                        field="extraction_error",
                        question="Could you please rephrase your message?",
                        reason=f"Unable to extract information: {str(e)}"
                    )
                ],
                evidence=[]
            )


class MockSlotExtractor:
    """Mock extractor for testing without API calls"""
    
    def __init__(self):
        # Don't call parent init to avoid needing API key
        self.test_responses = {}
    
    def add_test_response(self, message_pattern: str, result: ChatExtractionResult):
        """Add a test response for specific message pattern"""
        self.test_responses[message_pattern.lower()] = result
    
    def extract_from_text(
        self,
        message: str,
        current_state: Optional[Any] = None
    ) -> ChatExtractionResult:
        """Extract from text with WorldState context"""
        state_summary = None
        if current_state:
            # Convert WorldState to dict summary
            state_summary = {
                "farm_id": getattr(current_state, 'farm_id', None),
                "das": getattr(current_state, 'das', None),
                "growth_stage": getattr(current_state, 'growth_stage', None),
                "regime": getattr(current_state, 'regime', None),
                "water_table_depth_cm": getattr(current_state, 'water_table_depth_cm', None),
                "ponded_water_cm": getattr(current_state, 'ponded_water_cm', None),
                "soil_cracks": getattr(current_state, 'soil_cracks', None)
            }
        
        return self.extract(message, state_summary)
    
    def extract(
        self,
        message: str,
        state_summary: Optional[Dict[str, Any]] = None
    ) -> ChatExtractionResult:
        """Return predefined test responses"""
        
        message_lower = message.lower()
        
        # Check for exact matches first
        if message_lower in self.test_responses:
            return self.test_responses[message_lower]
        
        # Check for partial matches
        for pattern, result in self.test_responses.items():
            if pattern in message_lower:
                return result
        
        # Default: extract numbers using simple regex
        import re
        
        slots = {}
        confidence = 0.5
        
        # Look for numeric values with units
        cm_match = re.search(r'(\d+\.?\d*)\s*cm', message_lower)
        if cm_match:
            value = float(cm_match.group(1))
            
            # Ambiguous - need clarification
            if "below" in message_lower or "tube" in message_lower or "depth" in message_lower:
                slots["water_table_depth_cm"] = value
                confidence = 0.9
            elif "standing" in message_lower or "ponded" in message_lower or "above" in message_lower:
                slots["ponded_water_cm"] = value
                confidence = 0.9
            else:
                # Unclear type
                return ChatExtractionResult(
                    slots={},
                    confidence=0.3,
                    need_clarification=[
                        ClarificationRequest(
                            field="water_measurement_type",
                            question="Is that standing water above soil, or depth below soil surface in AWD tube?",
                            reason="Measurement type not specified"
                        )
                    ],
                    evidence=[cm_match.group(0)],
                    water_measurement_type="unknown"
                )
        
        # Look for DAS
        das_match = re.search(r'(\d+)\s*days?\s*(after|since)?\s*(sowing|planting)', message_lower)
        if das_match:
            slots["das"] = int(das_match.group(1))
            confidence = max(confidence, 0.85)
        
        # Look for cracks
        if "crack" in message_lower:
            if "small" in message_lower or "hairline" in message_lower:
                slots["soil_cracks"] = "small"
            elif "deep" in message_lower or "wide" in message_lower:
                slots["soil_cracks"] = "deep"
            elif "visible" in message_lower or "see" in message_lower:
                slots["soil_cracks"] = "visible"
            else:
                slots["soil_cracks"] = "visible"
            confidence = max(confidence, 0.8)
        elif "no crack" in message_lower or "wet" in message_lower or "muddy" in message_lower:
            slots["soil_cracks"] = "none"
            confidence = max(confidence, 0.8)
        
        return ChatExtractionResult(
            slots=slots,
            confidence=confidence,
            need_clarification=[],
            evidence=[message[:100]],
            unit_notes=None,
            water_measurement_type=None
        )
