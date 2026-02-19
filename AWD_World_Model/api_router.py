from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    from .farm_state import FarmState
    from .conversational_handler import ConversationalAWDHandler
except ImportError:
    from farm_state import FarmState
    from conversational_handler import ConversationalAWDHandler

router = APIRouter(prefix="/api/awd", tags=["AWD Assistant"])

farm_states: Dict[str, FarmState] = {}

awd_handler = ConversationalAWDHandler()


class AWDQuestionRequest(BaseModel):
    user_id: str
    question: str
    session_id: Optional[str] = None


class AWDQuestionResponse(BaseModel):
    response: str
    needs_more_info: bool
    questions: List[str]
    confidence: str
    intent: str
    farm_state_summary: str
    timestamp: str


class StateUpdateRequest(BaseModel):
    user_id: str
    updates: Dict[str, Any]


class StateResponse(BaseModel):
    user_id: str
    farm_state: Dict[str, Any]
    summary: str


def get_or_create_farm_state(user_id: str) -> FarmState:
    """Get or create farm state for a user"""
    if user_id not in farm_states:
        farm_states[user_id] = FarmState()
    return farm_states[user_id]


@router.post("/ask", response_model=AWDQuestionResponse)
async def ask_awd_question(request: AWDQuestionRequest):
    """
    Ask AWD assistant a question with intelligent slot-filling
    
    The assistant will:
    - Classify the intent
    - Extract information from the question
    - Ask follow-up questions if needed
    - Provide advice when sufficient data is available
    - Use Qwen LLM for enhanced natural responses (when available)
    """
    try:
        farm_state = get_or_create_farm_state(request.user_id)
        
        # Use async version with LLM enhancement
        result = await awd_handler.process_question_async(
            question=request.question,
            farm_state=farm_state,
            context={"session_id": request.session_id}
        )
        
        return AWDQuestionResponse(
            response=result["response"],
            needs_more_info=result["needs_more_info"],
            questions=result["questions"],
            confidence=result["confidence"],
            intent=result["intent"],
            farm_state_summary=farm_state.to_summary(),
            timestamp=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")


@router.post("/state/update", response_model=StateResponse)
async def update_farm_state(request: StateUpdateRequest):
    """
    Manually update farm state for a user
    
    Use this to set or update specific farm parameters
    """
    try:
        farm_state = get_or_create_farm_state(request.user_id)
        farm_state.update_from_dict(request.updates, source="api_update", confidence=1.0)
        
        return StateResponse(
            user_id=request.user_id,
            farm_state=farm_state.dict(),
            summary=farm_state.to_summary()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating state: {str(e)}")


@router.get("/state/{user_id}", response_model=StateResponse)
async def get_farm_state(user_id: str):
    """Get current farm state for a user"""
    try:
        farm_state = get_or_create_farm_state(user_id)
        
        return StateResponse(
            user_id=user_id,
            farm_state=farm_state.dict(),
            summary=farm_state.to_summary()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving state: {str(e)}")


@router.delete("/state/{user_id}")
async def reset_farm_state(user_id: str):
    """Reset farm state for a user"""
    try:
        if user_id in farm_states:
            del farm_states[user_id]
        
        return {"message": f"Farm state reset for user {user_id}"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting state: {str(e)}")


@router.get("/info/help")
async def get_help():
    """Get information about AWD assistant capabilities"""
    return {
        "title": "AWD Assistant - Alternate Wetting and Drying Advisory",
        "description": "Intelligent conversational assistant for AWD water management in rice cultivation",
        "capabilities": [
            "Irrigation timing recommendations",
            "Safety checks for current drying level",
            "Feasibility assessment for AWD practice",
            "Water and emission savings estimates",
            "Educational content about AWD",
            "Troubleshooting guidance"
        ],
        "intents": [
            {
                "name": "irrigation_now",
                "examples": ["Should I irrigate today?", "Can I wait to water?", "When to irrigate?"]
            },
            {
                "name": "scheduling",
                "examples": ["When is next irrigation?", "How many days can I dry?"]
            },
            {
                "name": "feasibility",
                "examples": ["Can I do AWD?", "Is AWD suitable for my field?"]
            },
            {
                "name": "safety",
                "examples": ["Is it safe to let it dry?", "Will this harm my crop?"]
            },
            {
                "name": "benefits",
                "examples": ["How much water will I save?", "What are AWD benefits?"]
            },
            {
                "name": "education",
                "examples": ["What is AWD?", "How to do AWD?", "How to install tube?"]
            }
        ],
        "usage": "Simply ask questions naturally. The assistant will ask follow-up questions if it needs more information about your field."
    }
