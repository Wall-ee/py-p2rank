"""
Logging utilities for P2Rank
"""
import logging
import sys
from typing import Optional


def setup_logging(level: str = "INFO", console: bool = True, log_file: Optional[str] = None):
    """
    Setup logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        console: Whether to log to console
        log_file: Optional log file path
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler) 