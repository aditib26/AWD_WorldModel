"""Structured logging configuration - replaces print() statements"""

import logging
import logging.handlers
import json
import sys
from pathlib import Path
from datetime import datetime
from .config import DATA_DIR


LOG_DIR = DATA_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


class JSONFormatter(logging.Formatter):
    """JSON structured log formatter for production."""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, 'farm_id'):
            log_data["farm_id"] = record.farm_id
        if hasattr(record, 'event_type'):
            log_data["event_type"] = record.event_type
        if record.exc_info and record.exc_info[1]:
            log_data["error"] = str(record.exc_info[1])
            log_data["error_type"] = type(record.exc_info[1]).__name__
        return json.dumps(log_data, default=str)


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure structured logging for the app."""
    
    root_logger = logging.getLogger("rice_assistant")
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Prevent duplicate handlers on re-init
    if root_logger.handlers:
        return root_logger
    
    # Console handler - human-readable
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console_fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S"
    )
    console.setFormatter(console_fmt)
    root_logger.addHandler(console)
    
    # File handler - JSON structured, rotating
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)
    
    # Error file - errors only
    error_handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / "errors.log",
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(error_handler)
    
    return root_logger


# Module-level logger
log = setup_logging()
