from typing import List, Tuple
import re


class IntentClassifier:
    """Classify farmer questions into AWD advisory intents"""
    
    INTENT_PATTERNS = {
        "irrigation_now": [
            r"should i (irrigate|water)",
            r"(irrigate|water) (now|today)",
            r"can i wait",
            r"how much water (do|should|to|need)",
            r"amount of water (to|should|need)",
            r"when to (irrigate|water)",
            r"need to (irrigate|water)",
            r"time to (irrigate|water)"
        ],
        "scheduling": [
            r"when (is|will be) (the )?next irrigation",
            r"how many days",
            r"how long (can|should) i (wait|dry)",
            r"irrigation schedule",
            r"drying period"
        ],
        "feasibility": [
            r"can i (do|practice|use|try) awd",
            r"is awd (possible|suitable|feasible)",
            r"will awd work",
            r"suitable for awd",
            r"can i start awd"
        ],
        "safety": [
            r"is it safe",
            r"(safe|ok) to (dry|wait|let it dry)",
            r"will (it|this) (harm|damage|hurt)",
            r"risk of",
            r"yield (loss|drop|reduction)",
            r"stress",
            r"is this dangerous"
        ],
        "troubleshooting": [
            r"soil (is )?(cracking|cracks)",
            r"leaves? (rolling|curling|wilting)",
            r"plants? (look|looking) stressed",
            r"tube (reading|not working)",
            r"confused about",
            r"problem with",
            r"wrong with"
        ],
        "education": [
            r"what is awd",
            r"how (does|to do) awd",
            r"explain awd",
            r"(how to|install|make) (water )?tube",
            r"awd (method|technique|practice)",
            r"tell me about awd",
            r"steps (of|for) awd"
        ],
        "benefits": [
            r"(how much|amount of) (water|money) (can i|will i) (save|reduce)",
            r"(benefits?|advantages?|why use)",
            r"(save|reduce|lower) (water|methane|emissions?)",
            r"(affect|impact) (yield|production)",
            r"carbon credit",
            r"environment",
            r"climate"
        ],
        "info_provide": [
            r"my (field|farm) is",
            r"area is",
            r"soil is",
            r"location is",
            r"village is",
            r"variety is",
            r"planted on",
            r"sowing date"
        ]
    }
    
    REQUIRED_SLOTS = {
        "irrigation_now": [
            "water.water_table_cm_below_surface",
            "weather.forecast_rain_next_7d_mm"
        ],
        "scheduling": [
            "water.water_table_cm_below_surface",
            "crop.growth_stage",
            "soil.percolation_class"
        ],
        "feasibility": [
            "soil.bunded_lowland",
            "soil.texture_class",
            "weather.forecast_rain_next_7d_mm"
        ],
        "safety": [
            "crop.growth_stage",
            "water.water_table_cm_below_surface",
            "observations.stress_symptoms_flag"
        ],
        "troubleshooting": [
            "crop.growth_stage",
            "water.water_table_cm_below_surface",
            "observations.cracking_level"
        ],
        "education": [],
        "benefits": []
    }
    
    FARMER_FRIENDLY_QUESTIONS = {
        "crop.growth_stage": {
            "question": "What stage is your rice crop in right now?",
            "options": ["Tillering (early growth, many stems)", "Panicle initiation (before flowering)", 
                       "Flowering (flowers visible)", "Grain filling (after flowering)"],
            "alternative": "If you planted/transplanted recently, tell me the date instead"
        },
        "water.water_table_cm_below_surface": {
            "question": "What is the water level in your field?",
            "options": ["Measure with tube: how many cm below soil surface?", 
                       "Or if there's standing water: how many cm deep?"],
            "alternative": "If you don't have a tube, describe the water situation"
        },
        "soil.texture_class": {
            "question": "What type of soil is in your field?",
            "options": ["Clay (heavy, sticky when wet)", "Loam (medium, good structure)", 
                       "Sandy (light, drains fast)"],
            "alternative": None
        },
        "soil.bunded_lowland": {
            "question": "Is this a bunded paddy field?",
            "options": ["Yes - has bunds/levees to hold water", "No - water drains away easily"],
            "alternative": None
        },
        "soil.percolation_class": {
            "question": "How fast does water drain in your field?",
            "options": ["Slow (water stays 2-3+ days)", "Medium (water stays 1-2 days)", 
                       "Fast (water drains within a day)"],
            "alternative": "This is related to soil type"
        },
        "weather.forecast_rain_next_7d_mm": {
            "question": "Is heavy rain expected in the next week?",
            "options": ["Yes, monsoon/heavy rain coming", "No, dry or light rain", "Not sure"],
            "alternative": "Tell me your village/location and I can check the forecast"
        },
        "observations.stress_symptoms_flag": {
            "question": "Are your plants showing any stress signs?",
            "options": ["Yes - leaves rolling/curling or wilting", "No - plants look healthy"],
            "alternative": None
        },
        "observations.cracking_level": {
            "question": "Is the soil cracking?",
            "options": ["No cracks", "Mild cracks (thin lines)", "Severe cracks (wide, deep)"],
            "alternative": None
        }
    }
    
    @staticmethod
    def classify(question: str) -> Tuple[str, float]:
        """Classify question into an intent with confidence score"""
        question_lower = question.lower()
        
        scores = {}
        for intent, patterns in IntentClassifier.INTENT_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, question_lower):
                    score += 1
            if score > 0:
                scores[intent] = score
        
        if not scores:
            if len(question.split()) < 5:
                return "unclear", 0.3
            return "irrigation_now", 0.4
        
        best_intent = max(scores, key=scores.get)
        confidence = min(scores[best_intent] / len(IntentClassifier.INTENT_PATTERNS[best_intent]), 1.0)
        
        return best_intent, confidence
    
    @staticmethod
    def requires_farm_state(intent: str) -> bool:
        """Check if intent requires specific farm state"""
        return intent in ["irrigation_now", "scheduling", "feasibility", "safety", "troubleshooting"]
    
    @staticmethod
    def get_required_slots(intent: str) -> List[str]:
        """Get required state slots for an intent"""
        return IntentClassifier.REQUIRED_SLOTS.get(intent, [])
    
    @staticmethod
    def get_farmer_question(slot: str) -> dict:
        """Get farmer-friendly question for a slot"""
        return IntentClassifier.FARMER_FRIENDLY_QUESTIONS.get(slot, {
            "question": f"Please provide: {slot}",
            "options": [],
            "alternative": None
        })
