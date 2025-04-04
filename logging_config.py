#!/usr/bin/env python3

import os
import logging
import logging.handlers
from typing import Dict, Any, Optional

# Constants
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_FILE = "match_list_change_detector.log"
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_BACKUP_COUNT = 5


def get_log_level(level_name: Optional[str] = None) -> int:
    """Convert a log level name to a logging level value."""
    level_name = level_name or os.environ.get("LOG_LEVEL", DEFAULT_LOG_LEVEL)
    level_name = level_name.upper()
    
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    return level_map.get(level_name, logging.INFO)


def configure_logging(
    logger_name: str = "match_list_change_detector",
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    log_dir: Optional[str] = None,
    log_file: Optional[str] = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Configure logging for the application.
    
    Args:
        logger_name: Name of the logger
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format string
        log_dir: Directory to store log files
        log_file: Log file name
        console_output: Whether to output logs to console
        
    Returns:
        Configured logger
    """
    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(get_log_level(log_level))
    
    # Clear existing handlers
    logger.handlers = []
    
    # Create formatter
    formatter = logging.Formatter(log_format or DEFAULT_LOG_FORMAT)
    
    # Create file handler
    log_dir = log_dir or os.environ.get("LOG_DIR", DEFAULT_LOG_DIR)
    log_file = log_file or os.environ.get("LOG_FILE", DEFAULT_LOG_FILE)
    
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    log_path = os.path.join(log_dir, log_file)
    
    # Use a rotating file handler to prevent logs from growing too large
    file_handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=DEFAULT_MAX_BYTES,
        backupCount=DEFAULT_BACKUP_COUNT
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    logger.info(f"Logging configured with level {log_level or DEFAULT_LOG_LEVEL}")
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger with the given name.
    
    If the logger doesn't exist, it will be created with default configuration.
    
    Args:
        name: Logger name (defaults to root logger name)
        
    Returns:
        Logger instance
    """
    logger_name = name or "match_list_change_detector"
    logger = logging.getLogger(logger_name)
    
    # If the logger doesn't have handlers, configure it
    if not logger.handlers:
        return configure_logging(logger_name)
    
    return logger
