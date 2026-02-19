import re
from typing import Dict, Any, Optional
from datetime import datetime


class SlotExtractor:
    """Extract slot values from farmer responses"""
    
    GROWTH_STAGE_MAPPING = {
        "tillering": ["tillering", "vegetative", "early", "many stems", "bushy"],
        "panicle_initiation": ["panicle", "pi", "before flower", "pre-flower"],
        "flowering": ["flowering", "flower", "bloom", "panicle out"],
        "grain_filling": ["grain", "filling", "after flower", "maturity", "ripening"]
    }
    
    SOIL_TEXTURE_MAPPING = {
        "clay": ["clay", "heavy", "sticky"],
        "loam": ["loam", "medium", "good"],
        "sandy": ["sand", "sandy", "light", "drain fast", "loose"]
    }
    
    PERCOLATION_MAPPING = {
        "low": ["slow", "low", "stays long", "2-3 days", "clay"],
        "medium": ["medium", "moderate", "1-2 days", "loam"],
        "high": ["fast", "high", "drain quick", "within day", "sandy"]
    }
    
    STRESS_MAPPING = {
        True: ["yes", "rolling", "curling", "wilting", "stressed", "drooping"],
        False: ["no", "healthy", "fine", "good", "normal", "ok"]
    }
    
    CRACKING_MAPPING = {
        "none": ["no", "none", "no crack"],
        "mild": ["mild", "small", "thin", "light", "few"],
        "severe": ["severe", "wide", "deep", "bad", "many"]
    }
    
    @staticmethod
    def extract_water_level(text: str) -> Optional[Dict[str, Any]]:
        """Extract water level from farmer's response"""
        text_lower = text.lower()
        
        if any(phrase in text_lower for phrase in [
            "no tube",
            "don't have tube",
            "dont have tube",
            "don't have a tube",
            "dont have a tube",
            "can't measure",
            "cannot measure",
            "can't check",
            "cannot check",
        ]):
            return {
                "water.water_table_cm_below_surface": None,
                "water.standing_water_cm": None
            }
        
        patterns = [
            r"(\d+\.?\d*)\s*cm\s*(below|under|depth)",
            r"water table.*?(\d+\.?\d*)\s*cm",
            r"tube.*?(\d+\.?\d*)\s*cm",
            r"(\d+\.?\d*)\s*cm.*?tube", # Handle "18 cm using tube"
            r"(\d+\.?\d*)\s*cm.*?below"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                value = float(match.group(1))
                return {"water.water_table_cm_below_surface": value}
        
        # Fallback: if just "X cm" is mentioned and looks like a reasonable water table depth (e.g. 10-30)
        simple_match = re.search(r"(\d+\.?\d*)\s*cm", text_lower)
        if simple_match:
            val = float(simple_match.group(1))
            # Heuristic: if value is > 5 and < 50, assume it's tube reading unless 'standing' is mentioned
            if 5 < val < 50 and "standing" not in text_lower:
                 return {"water.water_table_cm_below_surface": val}
        
        standing_patterns = [
            r"standing.*?(\d+\.?\d*)\s*cm",
            r"(\d+\.?\d*)\s*cm.*?standing",
            r"water.*?(\d+\.?\d*)\s*cm.*?(deep|high)"
        ]
        
        for pattern in standing_patterns:
            match = re.search(pattern, text_lower)
            if match:
                value = float(match.group(1))
                return {"water.standing_water_cm": value}
        
        if any(word in text_lower for word in ["dry", "no water", "no standing"]):
            return {"water.standing_water_cm": 0}
        
        return None
    
    @staticmethod
    def extract_growth_stage(text: str) -> Optional[Dict[str, Any]]:
        """Extract growth stage from farmer's response"""
        text_lower = text.lower()
        
        for stage, keywords in SlotExtractor.GROWTH_STAGE_MAPPING.items():
            if any(keyword in text_lower for keyword in keywords):
                return {"crop.growth_stage": stage}
        
        date_patterns = [
            r"(\d{4})-(\d{1,2})-(\d{1,2})",
            r"(\d{1,2})/(\d{1,2})/(\d{4})",
            r"planted.*?(\d+).*?days? ago",
            r"(\d+).*?days? (after|since)"
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    if "ago" in pattern or "after" in pattern:
                        days = int(match.group(1))
                        return {"crop.days_after": days}
                    else:
                        return {"crop.sow_or_transplant_date": match.group(0)}
                except:
                    pass
        
        return None
    
    @staticmethod
    def extract_soil_texture(text: str) -> Optional[Dict[str, Any]]:
        """Extract soil texture from farmer's response"""
        text_lower = text.lower()
        
        for texture, keywords in SlotExtractor.SOIL_TEXTURE_MAPPING.items():
            if any(keyword in text_lower for keyword in keywords):
                percolation = SlotExtractor._infer_percolation_from_texture(texture)
                return {
                    "soil.texture_class": texture,
                    "soil.percolation_class": percolation
                }
        
        return None
    
    @staticmethod
    def extract_percolation(text: str) -> Optional[Dict[str, Any]]:
        """Extract percolation/drainage class from farmer's response"""
        text_lower = text.lower()
        
        for perc_class, keywords in SlotExtractor.PERCOLATION_MAPPING.items():
            if any(keyword in text_lower for keyword in keywords):
                return {"soil.percolation_class": perc_class}
        
        return None
    
    @staticmethod
    def extract_bunded_field(text: str) -> Optional[Dict[str, Any]]:
        """Extract whether field is bunded"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["yes", "bunded", "levee", "hold water", "paddy"]):
            return {"soil.bunded_lowland": True}
        elif any(word in text_lower for word in ["no", "not bunded", "drain away", "upland"]):
            return {"soil.bunded_lowland": False}
        
        return None
    
    @staticmethod
    def extract_stress_symptoms(text: str) -> Optional[Dict[str, Any]]:
        """Extract stress symptom observation"""
        text_lower = text.lower()
        
        for value, keywords in SlotExtractor.STRESS_MAPPING.items():
            if any(keyword in text_lower for keyword in keywords):
                return {"observations.stress_symptoms_flag": value}
        
        return None
    
    @staticmethod
    def extract_cracking_level(text: str) -> Optional[Dict[str, Any]]:
        """Extract soil cracking level"""
        text_lower = text.lower()
        
        for level, keywords in SlotExtractor.CRACKING_MAPPING.items():
            if any(keyword in text_lower for keyword in keywords):
                return {"observations.cracking_level": level}
        
        return None
    
    @staticmethod
    def extract_location(text: str) -> Optional[Dict[str, Any]]:
        """Extract location information"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["village", "town", "district", "location"]):
            # Handle "village is X" or "village X"
            match = re.search(r"(?:village|town|district|location|from)\s+(?:is\s+)?([A-Za-z\s]+)", text, re.IGNORECASE)
            if match:
                loc = match.group(1).strip()
                # Clean up trailing words if needed
                return {"farm.location": loc}
        
        return None
    
    @staticmethod
    def extract_rainfall_expectation(text: str) -> Optional[Dict[str, Any]]:
        """Extract rainfall expectation"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["heavy rain", "monsoon", "lot of rain", "rain coming"]):
            return {"weather.forecast_rain_next_7d_mm": 60.0}
        elif any(word in text_lower for word in ["no rain", "dry", "light rain"]):
            return {"weather.forecast_rain_next_7d_mm": 5.0}
        
        amount_match = re.search(r"(\d+\.?\d*)\s*mm", text_lower)
        if amount_match:
            return {"weather.forecast_rain_next_7d_mm": float(amount_match.group(1))}
        
        return None
    
    @staticmethod
    def extract_area(text: str) -> Optional[Dict[str, Any]]:
        """Extract field area"""
        text_lower = text.lower()
        match = re.search(r"(\d+\.?\d*)\s*(?:ha|hectares?|acres?)", text_lower)
        if match:
            # Simple assumption: just store the number for now, assumed hectares if ambiguous
            return {"farm.area_ha": float(match.group(1))}
        return None

    @staticmethod
    def extract_all(text: str) -> Dict[str, Any]:
        """Run all extractors and return combined results"""
        extractions = {}
        
        extractors = [
            SlotExtractor.extract_water_level,
            SlotExtractor.extract_growth_stage,
            SlotExtractor.extract_soil_texture,
            SlotExtractor.extract_percolation,
            SlotExtractor.extract_bunded_field,
            SlotExtractor.extract_stress_symptoms,
            SlotExtractor.extract_cracking_level,
            SlotExtractor.extract_location,
            SlotExtractor.extract_rainfall_expectation,
            SlotExtractor.extract_area
        ]
        
        for extractor in extractors:
            result = extractor(text)
            if result:
                extractions.update(result)
        
        return extractions
    
    @staticmethod
    def _infer_percolation_from_texture(texture: str) -> str:
        """Infer percolation class from soil texture"""
        mapping = {
            "clay": "low",
            "loam": "medium",
            "sandy": "high"
        }
        return mapping.get(texture, "medium")
