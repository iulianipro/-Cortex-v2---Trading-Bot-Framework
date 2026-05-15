"""
Structured logging system with JSON output for monitoring/dashboards
"""

import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_obj['data'] = record.extra_data
        
        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_obj, default=str)


def get_logger(name: str, 
               log_file: Optional[str] = None,
               level: int = logging.INFO) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        log_file: Optional file path to write logs
        level: Logging level
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Console handler with JSON formatting
    if not logger.handlers:  # Avoid adding duplicate handlers
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(JSONFormatter())
        logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(JSONFormatter())
            logger.addHandler(file_handler)
    
    return logger


class LogContext:
    """Context manager for structured logging with extra data"""
    
    def __init__(self, logger: logging.Logger, data: Dict[str, Any]):
        self.logger = logger
        self.data = data
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.log_error(f"Exception in context: {exc_val}")
        return False
    
    def log_info(self, message: str):
        """Log info with context data"""
        record = self.logger.makeRecord(
            self.logger.name,
            logging.INFO,
            "(context)",
            0,
            message,
            (),
            None
        )
        record.extra_data = self.data
        self.logger.handle(record)
    
    def log_error(self, message: str):
        """Log error with context data"""
        record = self.logger.makeRecord(
            self.logger.name,
            logging.ERROR,
            "(context)",
            0,
            message,
            (),
            None
        )
        record.extra_data = self.data
        self.logger.handle(record)
