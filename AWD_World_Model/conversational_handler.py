from typing import Dict, Any, List, Optional, Tuple
import asyncio

try:
    from .farm_state import FarmState
    from .intent_classifier import IntentClassifier
    from .slot_extractor import SlotExtractor
    from .llm_slot_extractor import LLMSlotExtractor, extract_slots_with_llm
    from .llm_intent_classifier import classify_intent_with_llm
    from .decision_strategies import MultiTechniqueDecisionEngine
    from .educational_content import EducationalContent
    from .llm_client import generate_awd_response, generate_educational_response, is_qwen_available
    from .rag_client import retrieve_context
except ImportError:
    from farm_state import FarmState
    from intent_classifier import IntentClassifier
    from slot_extractor import SlotExtractor
    from llm_slot_extractor import LLMSlotExtractor, extract_slots_with_llm
    from llm_intent_classifier import classify_intent_with_llm
    from decision_strategies import MultiTechniqueDecisionEngine
    from educational_content import EducationalContent
    from llm_client import generate_awd_response, generate_educational_response, is_qwen_available
    from rag_client import retrieve_context


class ConversationalAWDHandler:
    """
    Main conversational interface for AWD advisory system
    Handles slot-filling, progressive questioning, and response generation
    """
    
    def __init__(self, use_llm: bool = True):
        self.intent_classifier = IntentClassifier()
        self.slot_extractor = SlotExtractor()
        self.decision_engine = MultiTechniqueDecisionEngine()
        self.educational_content = EducationalContent()
        self.use_llm = use_llm  # Enable/disable Qwen enhancement
    
    def process_question(
        self, 
        question: str, 
        farm_state: FarmState,
        context: Optional[Dict[str, Any]] = None,
        use_llm_override: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Main entry point: process farmer question and return response (sync version)
        For async with LLM enhancement, use process_question_async
        
        Returns:
            {
                "response": str,  # Main response text
                "needs_more_info": bool,  # Whether more info is needed
                "questions": List[str],  # Follow-up questions if needed
                "confidence": str,  # high/medium/low
                "state_updates": Dict,  # Updates to apply to farm state
                "intent": str  # Detected intent
            }
        """
        # Sync version - no LLM enhancement
        return self._process_question_sync(question, farm_state, context)
    
    async def process_question_async(
        self, 
        question: str, 
        farm_state: FarmState,
        context: Optional[Dict[str, Any]] = None,
        use_llm_override: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Async entry point with LLM enhancement support
        """
        use_llm = use_llm_override if use_llm_override is not None else self.use_llm
        return await self._process_question_async(question, farm_state, context, use_llm)
    
    def _process_question_sync(
        self, 
        question: str, 
        farm_state: FarmState,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Synchronous processing without LLM enhancement"""
        extracted = self.slot_extractor.extract_all(question)
        if extracted:
            farm_state.update_from_dict(extracted, source="regex_extraction", confidence=0.7)
        
        intent, confidence = self.intent_classifier.classify(question)
        
        if not self.intent_classifier.requires_farm_state(intent):
            response = self._handle_educational_intent(intent, question, farm_state)
            return {
                "response": response,
                "needs_more_info": False,
                "questions": [],
                "confidence": "high",
                "state_updates": extracted,
                "intent": intent
            }
        
        required_slots = self.intent_classifier.get_required_slots(intent)
        missing_slots = farm_state.get_missing_slots(required_slots)
        
        if missing_slots:
            questions = self._generate_slot_questions(missing_slots, farm_state)
            intro_message = self._generate_intro_message(intent, farm_state, missing_slots)
            tentative_advice = self._generate_tentative_response(
                intent, farm_state, missing_slots
            )
            
            full_response = intro_message
            if tentative_advice:
                full_response = tentative_advice + "\n\n" + intro_message
            
            return {
                "response": full_response,
                "needs_more_info": True,
                "questions": questions[:3],
                "confidence": "medium" if tentative_advice else "low",
                "state_updates": extracted,
                "intent": intent
            }
        
        response = self._generate_full_response(intent, farm_state)
        
        return {
            "response": response,
            "needs_more_info": False,
            "questions": [],
            "confidence": "high",
            "state_updates": extracted,
            "intent": intent
        }
    
    async def _process_question_async(
        self,
        question: str,
        farm_state: FarmState,
        context: Optional[Dict[str, Any]],
        use_llm: bool
    ) -> Dict[str, Any]:
        """Async processing with optional LLM enhancement and RAG"""
        
        # Use LLM-based extraction if enabled, otherwise fall back to regex
        if use_llm:
            # Build conversation context for better extraction
            conversation_context = None
            if context and 'conversation_history' in context:
                recent_history = context['conversation_history'][-3:]  # Last 3 exchanges
                conversation_context = " ".join([msg.get('content', '') for msg in recent_history])
            
            extracted = await extract_slots_with_llm(question, conversation_context)
            if extracted:
                extraction_source = "llm_extraction"
                extraction_confidence = 0.9
            else:  # Fallback to regex if LLM fails
                extracted = self.slot_extractor.extract_all(question)
                extraction_source = "regex_extraction"
                extraction_confidence = 0.7
        else:
            extracted = self.slot_extractor.extract_all(question)
            extraction_source = "regex_extraction"
            extraction_confidence = 0.7
            
        if extracted:
            farm_state.update_from_dict(
                extracted,
                source=extraction_source,
                confidence=extraction_confidence
            )
        
        # Use LLM-based intent classification if enabled
        if use_llm:
            farm_summary = farm_state.to_summary()
            intent_result = await classify_intent_with_llm(
                question=question,
                conversation_context=conversation_context if 'conversation_context' in locals() else None,
                farm_state_summary=farm_summary
            )
            intent = intent_result["intent"]
            confidence = intent_result["confidence"]
            intent_reasoning = intent_result.get("reasoning", "")
        else:
            intent, confidence = self.intent_classifier.classify(question)
            intent_reasoning = ""
        
        # Retrieve RAG context if LLM is enabled
        rag_context = ""
        citations = []
        # RAG disabled due to timeout issues
        # if use_llm:
        #     # Reformulate query for better retrieval based on intent
        #     search_query = self._reformulate_query_for_rag(question, intent)
        #     rag_result = await retrieve_context(search_query)
        #     rag_context = rag_result.get("context_text", "")
        #     citations = rag_result.get("citations", [])
        
        if not self.intent_classifier.requires_farm_state(intent):
            base_response = self._handle_educational_intent(intent, question, farm_state)
            
            # Enhance with LLM if available
            if use_llm and is_qwen_available():
                response = await generate_educational_response(
                    user_question=question,
                    base_content=base_response,
                    rag_context=rag_context
                )
            else:
                response = base_response
            
            return {
                "response": response,
                "needs_more_info": False,
                "questions": [],
                "confidence": "high",
                "state_updates": extracted,
                "intent": intent,
                "llm_enhanced": use_llm and is_qwen_available(),
                "citations": citations
            }
        
        required_slots = self.intent_classifier.get_required_slots(intent)
        missing_slots = farm_state.get_missing_slots(required_slots)
        
        if missing_slots:
            questions = self._generate_slot_questions(missing_slots, farm_state)
            intro_message = self._generate_intro_message(intent, farm_state, missing_slots)
            tentative_advice = self._generate_tentative_response(
                intent, farm_state, missing_slots
            )
            
            full_response = intro_message
            if tentative_advice:
                full_response = tentative_advice + "\n\n" + intro_message
            
            return {
                "response": full_response,
                "needs_more_info": True,
                "questions": questions[:3],
                "confidence": "medium" if tentative_advice else "low",
                "state_updates": extracted,
                "intent": intent,
                "llm_enhanced": False,
                "citations": []
            }
        
        # Generate full response
        base_response = self._generate_full_response(intent, farm_state)
        
        # Enhance with LLM if available
        if use_llm and is_qwen_available():
            farm_context = farm_state.to_summary()
            response = await generate_awd_response(
                user_question=question,
                farm_context=farm_context,
                base_response=base_response,
                intent=intent,
                rag_context=rag_context
            )
        else:
            response = base_response
        
        return {
            "response": response,
            "needs_more_info": False,
            "questions": [],
            "confidence": "high",
            "state_updates": extracted,
            "intent": intent,
            "llm_enhanced": use_llm and is_qwen_available(),
            "citations": citations
        }
    
    def _handle_educational_intent(
        self, 
        intent: str, 
        question: str,
        farm_state: FarmState
    ) -> str:
        """Handle educational/informational questions"""
        
        if intent == "info_provide":
            summary = farm_state.to_summary()
            return f"Got it! I've updated your farm details. Current context: {summary}"
            
        elif intent == "benefits":
            return EducationalContent.get_benefits_content()
            
        elif intent == "education" or intent == "awd_basics":
            return EducationalContent.explain_awd_basics()
            
        elif intent == "tube_installation":
            return EducationalContent.explain_water_tube_installation()
            
        else:
            return "I'm here to help with AWD water management. Ask me about irrigation timing, water levels, or AWD benefits!"
    
    def _generate_slot_questions(
        self, 
        missing_slots: List[str],
        farm_state: FarmState
    ) -> List[str]:
        """Generate farmer-friendly questions for missing slots"""
        
        questions = []
        
        for slot in missing_slots[:3]:
            question_data = self.intent_classifier.get_farmer_question(slot)
            
            question_text = f"**{question_data['question']}**\n"
            
            if question_data['options']:
                for i, option in enumerate(question_data['options'], 1):
                    question_text += f"\n{i}. {option}"
            
            if question_data.get('alternative'):
                question_text += f"\n\n*{question_data['alternative']}*"
            
            questions.append(question_text)
        
        return questions
    
    def _generate_intro_message(
        self,
        intent: str,
        farm_state: FarmState,
        missing_slots: List[str]
    ) -> str:
        """Generate introductory message when asking for missing info"""
        
        intent_messages = {
            "irrigation_now": "To give you accurate irrigation advice, I need a few details about your field:",
            "scheduling": "To help you plan your irrigation schedule, I need to know:",
            "feasibility": "To check if AWD is suitable for your field, please tell me:",
            "safety": "To assess if current drying is safe, I need:",
            "troubleshooting": "To help troubleshoot this issue, I need some information:"
        }
        
        num_missing = len(missing_slots)
        base_message = intent_messages.get(intent, "To answer your question accurately, I need some information:")
        
        if farm_state.to_summary() != "No farm data collected yet":
            return f"**Current info**: {farm_state.to_summary()}\n\n{base_message}"
        else:
            return base_message
    
    def _generate_tentative_response(
        self,
        intent: str,
        farm_state: FarmState,
        missing_slots: List[str]
    ) -> Optional[str]:
        """Generate a tentative response when some data is available"""
        
        if intent == "irrigation_now":
            if farm_state.water.water_table_cm_below_surface:
                depth = farm_state.water.water_table_cm_below_surface
                if depth >= 15:
                    return "⚠️ **Tentative advice**: Based on water depth ({:.0f}cm), you should likely irrigate soon.".format(depth)
                elif depth < 10:
                    return "📊 **Tentative advice**: Water level seems good ({:.0f}cm). You can likely continue drying.".format(depth)
        
        elif intent == "safety":
            if farm_state.crop.growth_stage == "flowering":
                return "⚠️ **Important**: Flowering stage is sensitive to water stress."
            if farm_state.observations.stress_symptoms_flag:
                return "🚨 **Warning**: Stress symptoms detected. This needs immediate attention."
        
        elif intent == "feasibility":
            if farm_state.soil.bunded_lowland is False:
                return "❌ AWD requires a bunded paddy field. Your field is not suitable for AWD practice."
        
        elif intent == "troubleshooting":
            if farm_state.observations.stress_symptoms_flag or farm_state.observations.cracking_level == "severe":
                return "🚨 **Immediate action needed**: These symptoms suggest water stress."
        
        return None
    
    def _generate_full_response(
        self,
        intent: str,
        farm_state: FarmState
    ) -> str:
        """Generate complete response with all required data"""
        
        if intent in ["irrigation_now", "scheduling"]:
            return self._generate_irrigation_advice(farm_state)
        
        elif intent == "feasibility":
            return self._generate_feasibility_response(farm_state)
        
        elif intent == "safety":
            return self._generate_safety_response(farm_state)
        
        elif intent == "troubleshooting":
            return self._generate_troubleshooting_response(farm_state)
        
        else:
            return self._generate_irrigation_advice(farm_state)
    
    def _generate_irrigation_advice(self, farm_state: FarmState) -> str:
        """Generate irrigation recommendation with explanation"""
        
        advice = self.decision_engine.get_full_advice(farm_state)
        prediction = self.decision_engine.predict_drying_rate(farm_state)
        
        response_parts = []
        
        response_parts.append(f"## 💧 AWD Irrigation Advice\n")
        response_parts.append(f"**Current situation**: {farm_state.to_summary()}\n")
        
        if advice['status'] != 'ok':
            response_parts.append(f"⚠️ **{advice['message']}**\n")
            response_parts.append(f"**Action**: {advice['recommendation']}")
        else:
            response_parts.append(f"✅ {advice['message']}\n")
            response_parts.append(f"**Recommendation**: {advice['recommendation']}\n")
            
            depth = farm_state.water.water_table_cm_below_surface
            if depth and depth < 10:
                response_parts.append("\n📝 **Next steps**:")
                response_parts.append("- Monitor water level daily")
                response_parts.append("- Check for any stress symptoms")
                response_parts.append("- Prepare irrigation equipment when depth reaches 15cm")
                
                # Add prediction if available
                if prediction.get("status") == "predicting":
                    days = prediction['days_remaining']
                    response_parts.append(f"\n🔮 **Prediction**: At current drying rates, you will reach the 15cm target in about **{days} days**.")
        
        return "\n".join(response_parts)
    
    def _generate_feasibility_response(self, farm_state: FarmState) -> str:
        """Generate feasibility assessment"""
        
        feasible, message = self.decision_engine.check_feasibility(farm_state)
        
        response_parts = []
        response_parts.append("## 🔍 AWD Feasibility Check\n")
        
        if feasible:
            response_parts.append(f"✅ **{message}**\n")
            response_parts.append("You can practice AWD in your field. Here's what you need:\n")
            response_parts.append("1. **Water tube**: Install a perforated PVC pipe to monitor water table")
            response_parts.append("2. **Daily monitoring**: Check water level, especially during critical stages")
            response_parts.append("3. **AWD cycles**: Let water table drop to 15cm below surface, then re-irrigate\n")
            
            water_savings = self.decision_engine.estimate_water_savings(farm_state)
            response_parts.append(f"**Expected benefits**: Save ~{water_savings['water_saved_percent']:.0f}% water and reduce methane emissions by ~48%")
        else:
            response_parts.append(f"❌ **{message}**\n")
            response_parts.append("**Alternative**: Continue with conventional shallow flooding method for best results.")
        
        return "\n".join(response_parts)
    
    def _generate_safety_response(self, farm_state: FarmState) -> str:
        """Generate safety assessment"""
        
        safe, message = self.decision_engine.check_safety(farm_state)
        
        response_parts = []
        response_parts.append("## 🛡️ AWD Safety Check\n")
        
        if safe:
            response_parts.append(f"✅ **{message}**\n")
            
            stage = farm_state.crop.growth_stage
            if stage == "flowering":
                response_parts.append("⚠️ **Note**: You're in flowering stage. Monitor closely and don't let water table go below 10cm.")
            elif stage == "grain_filling":
                response_parts.append("📊 Monitor daily during grain filling to ensure good grain development.")
        else:
            response_parts.append(f"⚠️ **{message}**\n")
        
        return "\n".join(response_parts)
    
    def _generate_troubleshooting_response(self, farm_state: FarmState) -> str:
        """Generate troubleshooting guidance"""
        
        response_parts = []
        response_parts.append("## 🔧 Troubleshooting Guide\n")
        
        if farm_state.observations.cracking_level == "severe":
            response_parts.append("**Severe soil cracking detected**")
            response_parts.append("- Irrigate immediately to prevent root damage")
            response_parts.append("- Next cycle: irrigate earlier (at 12cm instead of 15cm)")
        
        if farm_state.observations.stress_symptoms_flag:
            response_parts.append("**Crop stress symptoms detected**")
            response_parts.append("- Stop AWD immediately and irrigate")
            response_parts.append("- Maintain shallow water for 3-5 days")
            response_parts.append("- Resume AWD only after full recovery")
        
        depth = farm_state.water.water_table_cm_below_surface
        if depth and depth > 20:
            response_parts.append("**Water table too deep**")
            response_parts.append("- Irrigate now - excessive drying can harm roots")
            response_parts.append("- Target: 15cm maximum depth for safe AWD")
        
        if not response_parts[1:]:
            response_parts.append("Everything looks normal. Continue monitoring daily and irrigate at 15cm depth.")
        
        return "\n".join(response_parts)
    
    def _reformulate_query_for_rag(self, question: str, intent: str) -> str:
        """
        Reformulate user question into a detailed search query for better RAG retrieval
        
        Short questions like "what is awd?" don't match document embeddings well.
        Expand them into descriptive queries that match how content is written.
        """
        intent_query_templates = {
            "awd_basics": "alternate wetting and drying AWD rice water management methodology practice technique definition explanation how it works",
            "benefits": "AWD alternate wetting drying benefits advantages water savings methane emission reduction yield impact carbon credits",
            "tube_installation": "water tube installation pani nali perforated pipe measurement monitoring depth reading",
            "irrigation_now": "AWD irrigation timing when to irrigate water depth 15cm safe threshold decision",
            "safety_check": "AWD safety water stress crop damage flowering stage critical period risk",
            "feasibility": "AWD suitability soil type bunded field percolation drainage requirements conditions",
            "troubleshooting": "AWD problems soil cracking leaf rolling stress symptoms tube issues solutions",
        }
        
        # If we have a template for this intent, use it
        if intent in intent_query_templates:
            # Combine original question with expanded terms for better recall
            expanded = intent_query_templates[intent]
            return f"{question} {expanded}"
        
        # Otherwise return original question
        return question
    
    def generate_clarification_prompt(self) -> str:
        """Generate prompt when intent is unclear"""
        return """I'm here to help with AWD water management! What would you like to know?

**I can help with**:
1. **Irrigation timing** - "Should I irrigate today?"
2. **Safety check** - "Is it safe to let the field dry?"
3. **Feasibility** - "Can I practice AWD in my field?"
4. **Benefits** - "How much water can I save?"
5. **Setup & how-to** - "How do I start AWD?"

Just ask your question naturally, and I'll guide you!"""
