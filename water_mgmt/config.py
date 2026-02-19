"""Configuration and constants for water management module"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Paths
BASE_DIR = Path(__file__).parent.parent

# Load .env from project root
load_dotenv(BASE_DIR / ".env")
HANDBOOK_PATH = BASE_DIR / "handbook_enhanced_v4_english_visuals.json"
DATA_DIR = BASE_DIR / "water_mgmt_data"
LOG_FILE = DATA_DIR / "water_events.ndjson"

# Create data directory
DATA_DIR.mkdir(exist_ok=True)

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# Weather
WEATHER_API_KEY = os.getenv("WEATHER_API")

# Bucket to cm mapping
BUCKET_TO_CM = {
    "zero": 0.0,
    "one_two": 1.5,
    "three_five": 4.0,
    "over_five": 6.0
}

# Bund height mapping
BUND_HEIGHT_CM = {
    "low": 10.0,
    "medium": 20.0,
    "high": 30.0,
    "unknown": 15.0
}

# Growth stage DAS mapping (conservative estimates)
DAS_TO_STAGE = [
    (0, 14, "seedling"),
    (15, 34, "tillering"),
    (35, 59, "panicle_initiation"),
    (60, 79, "heading"),
    (80, 109, "grain_filling"),
    (110, 200, "maturity")
]

# Default hydrological parameters
DEFAULT_PARAMS = {
    "percolation_mm_per_day": 5.0,
    "infiltration_mm_per_day": 10.0,
    "runoff_factor": 0.2,  # 20% of rain becomes runoff
    "effective_rain_factor": 0.8,  # 80% of rain is effective
}

# Crop coefficients by stage
KC_BY_STAGE = {
    "seedling": 1.05,
    "tillering": 1.10,
    "panicle_initiation": 1.20,
    "heading": 1.20,
    "grain_filling": 1.10,
    "maturity": 0.95,
    "unknown": 1.10
}

# MPC planning
PLANNING_HORIZON_DAYS = 7

# Cost function weights
COST_WEIGHTS = {
    "stress_sensitive_stage": 10.0,
    "stress_normal_stage": 5.0,
    "excess_ponding": 5.0,
    "water_use": 2.0,
    "unnecessary_irrigation_rain": 8.0
}
