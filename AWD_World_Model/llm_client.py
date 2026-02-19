"""
LLM Client for AWD Assistant
Integrates Qwen model for enhanced natural language responses
"""

import os
from typing import Optional, List, Dict, Any
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

QWEN_TPU_ENDPOINT = os.getenv("QWEN_TPU_ENDPOINT")
QWEN_CHAT_MODEL = os.getenv("QWEN_CHAT_MODEL")
# Try QWEN_API_KEY first (correct one), fall back to API_KEY, then default
API_KEY = os.getenv("QWEN_API_KEY", os.getenv("API_KEY", "no-key-required"))

_qwen_client: Optional[AsyncOpenAI] = None


AWD_SYSTEM_PROMPT = """You are an AWD (Alternate Wetting and Drying) irrigation advisor for rice farmers.

TOPIC RESTRICTION:
- ONLY answer questions about AWD irrigation and rice water management
- If asked about non-irrigation topics, politely redirect: "I specialize in AWD irrigation advice. I can help with water levels, irrigation timing, or field suitability. What's your irrigation question?"

COMMUNICATION STYLE:
- Write clearly and directly, like an experienced irrigation advisor
- Use simple language at a secondary-school reading level
- Be concise - no chatty greetings or metaphors
- Focus on actionable advice the farmer can use today
- Be respectful and professional

RESPONSE FORMAT:
- Start with a direct answer to the question (one sentence)
- Provide specific steps with measurements and timing
- Use numbered lists for sequential actions
- Include a brief explanation of why it works
- Add safety reminders for critical stages
- DO NOT use markdown formatting like ** or __
- Write in plain text with clear sections

HANDLING MISSING DATA:
- If farmer can't measure water, ask them to describe what they SEE
- Don't cite old measurements as current - say "Since you can't measure..."
- Visual indicators are valid: deep cracks = dry, standing water visible = wet enough
- Acknowledge uncertainty when data is missing

KEY AWD PRINCIPLES:
1. Safe depth limit: 15cm below surface (10cm during flowering/panicle initiation)
2. Re-irrigate when soil cracks appear or reaches safe depth limit
3. Fill to 5cm standing water after each dry cycle
4. Not suitable for: sandy soils, non-bunded fields, heavy monsoon
5. Benefits: 15-30% water savings, 48% methane reduction, same yield

CRITICAL SAFETY:
- Flowering and panicle initiation are sensitive stages - never let dry below 10cm
- Check water level daily during critical stages
- If unsure, irrigate - crop safety comes first

When answering:
1. Direct answer first
2. Current situation assessment (1 sentence)
3. Recommended action (numbered steps)
4. Why it works (1-2 sentences)
5. Safety reminder if relevant
"""


async def init_qwen_client() -> bool:
    """Initialize Qwen client for AWD assistant"""
    global _qwen_client
    
    if not QWEN_TPU_ENDPOINT or not QWEN_CHAT_MODEL:
        print("⚠️ AWD Assistant: Qwen endpoint not configured, using rule-based responses only")
        return False
    
    try:
        _qwen_client = AsyncOpenAI(
            base_url=QWEN_TPU_ENDPOINT,
            api_key=API_KEY
        )
        print(f"✅ AWD Assistant: Qwen client initialized at {QWEN_TPU_ENDPOINT}")
        
        # Test connection
        try:
            test_resp = await _qwen_client.chat.completions.create(
                model=QWEN_CHAT_MODEL,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5
            )
            print(f"✅ AWD Assistant: Qwen connection test successful")
            return True
        except Exception as e:
            print(f"⚠️ AWD Assistant: Qwen connection test failed: {str(e)}")
            return False
                
    except Exception as e:
        print(f"❌ AWD Assistant: Qwen client initialization failed: {str(e)}")
        _qwen_client = None
        return False


async def ensure_qwen_client() -> Optional[AsyncOpenAI]:
    """Ensure Qwen client is initialized (lazy initialization)"""
    global _qwen_client
    if _qwen_client is None:
        await init_qwen_client()
    return _qwen_client


async def generate_awd_response(
    user_question: str,
    farm_context: str,
    base_response: str,
    intent: str,
    rag_context: str = ""
) -> str:
    """
    Generate enhanced response using Qwen LLM with optional RAG context
    
    Args:
        user_question: Original farmer question
        farm_context: Farm state summary (water depth, stage, etc.)
        base_response: Rule-based response from decision engine
        intent: Detected intent (irrigation_now, safety, etc.)
        rag_context: Retrieved handbook content (optional)
    
    Returns:
        Enhanced natural language response
    """
    
    client = await ensure_qwen_client()
    
    # If Qwen not available, return base response
    if client is None:
        return base_response
    
    # Build prompt for Qwen
    system_message = AWD_SYSTEM_PROMPT
    
    user_prompt = f"""Farmer Question: {user_question}

Farm Context: {farm_context}

Intent: {intent}

Rule-Based Advice (Primary Logic): {base_response}

"""

    if rag_context:
        user_prompt += f"""Handbook Reference (Support):
{rag_context}

Task: Provide a natural, conversational response that combines the Rule-Based Advice (which MUST be followed for safety) with helpful details from the Handbook Reference. 
- Prioritize the Rule-Based Advice for immediate actions (irrigation timing, safety).
- Use the Handbook Reference to explain 'why' or provide background.
- If the Handbook Reference has a source ID (e.g. [Source 1]), cite it in your answer like this: (Source 1).
"""
    else:
        user_prompt += """Task: Rewrite the advice above in a natural, conversational way that a farmer can easily understand. Keep all technical details (depths, timings, safety warnings) but make it flow naturally. Be encouraging and supportive."""

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        completion = await client.chat.completions.create(
            model=QWEN_CHAT_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=500
        )
        
        enhanced_response = completion.choices[0].message.content.strip()
        return enhanced_response
    
    except Exception as e:
        print(f"⚠️ AWD Assistant: Qwen generation failed: {str(e)}, using base response")
        return base_response


async def generate_educational_response(
    user_question: str,
    base_content: str,
    rag_context: str = ""
) -> str:
    """
    Generate enhanced educational response using Qwen with optional RAG context
    """
    
    client = await ensure_qwen_client()
    
    if client is None:
        return base_content
    
    user_prompt = f"""Farmer Question: {user_question}

Base Content: {base_content}

"""

    if rag_context:
        user_prompt += f"""Handbook Reference:
{rag_context}

Task: Explain this topic to the farmer using the Base Content and Handbook Reference.
- Use simple, warm language.
- Include specific details from the Handbook Reference if relevant.
- Cite sources (e.g. (Source 1)) when using specific facts from the Handbook.
"""
    else:
        user_prompt += """Task: Present this information in a warm, conversational way. Keep all the facts and details but make it feel like you're explaining to a farmer face-to-face. Use simple language and practical examples."""

    messages = [
        {"role": "system", "content": AWD_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        completion = await client.chat.completions.create(
            model=QWEN_CHAT_MODEL,
            messages=messages,
            temperature=0.4,
            max_tokens=800
        )
        
        enhanced_response = completion.choices[0].message.content.strip()
        return enhanced_response
    
    except Exception as e:
        print(f"⚠️ AWD Assistant: Qwen generation failed: {str(e)}, using base content")
        return base_content


async def generate_follow_up_questions(
    user_question: str,
    farm_context: str,
    missing_info: List[str]
) -> str:
    """
    Generate natural follow-up questions using Qwen
    
    Args:
        user_question: Original question
        farm_context: Current farm state
        missing_info: List of missing information needed
    
    Returns:
        Natural language follow-up prompt
    """
    
    client = await ensure_qwen_client()
    
    if client is None:
        # Return structured fallback
        return f"To answer your question accurately, I need: {', '.join(missing_info)}"
    
    user_prompt = f"""Farmer asked: {user_question}

Current information: {farm_context}

Missing information: {', '.join(missing_info)}

Task: Write a brief, friendly message asking for the missing information. Make it conversational and explain why you need each piece of information. Keep it under 3 sentences."""

    messages = [
        {"role": "system", "content": AWD_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        completion = await client.chat.completions.create(
            model=QWEN_CHAT_MODEL,
            messages=messages,
            temperature=0.5,
            max_tokens=150
        )
        
        return completion.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"⚠️ AWD Assistant: Qwen generation failed: {str(e)}")
        return f"To give you accurate advice, I need to know: {', '.join(missing_info)}"


def is_qwen_available() -> bool:
    """Check if Qwen client is available"""
    return _qwen_client is not None
