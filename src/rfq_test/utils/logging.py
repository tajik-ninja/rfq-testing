"""Logging configuration with file rotation."""

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_logging(
    level: int = logging.INFO,
    log_dir: Optional[Path] = None,
    log_to_file: bool = True,
    log_to_console: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """Configure logging with console and file output.
    
    Args:
        level: Logging level
        log_dir: Directory for log files (default: ./logs)
        log_to_file: Enable file logging
        log_to_console: Enable console logging
        max_bytes: Max size per log file before rotation
        backup_count: Number of backup files to keep
        
    Returns:
        Root logger
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Format
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_to_file:
        if log_dir is None:
            log_dir = Path.cwd() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = log_dir / f"rfq_test_{timestamp}.log"
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        root_logger.info(f"Logging to file: {log_file}")
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a named logger.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class TestLogCapture:
    """Context manager to capture logs during a test.
    
    Usage:
        with TestLogCapture() as capture:
            do_something()
        assert "expected" in capture.output
    """
    
    def __init__(self, logger_name: Optional[str] = None, level: int = logging.DEBUG):
        self.logger_name = logger_name
        self.level = level
        self.handler: Optional[logging.Handler] = None
        self.records: list[logging.LogRecord] = []
    
    def __enter__(self) -> "TestLogCapture":
        logger = logging.getLogger(self.logger_name)
        
        class ListHandler(logging.Handler):
            def __init__(self, records: list):
                super().__init__()
                self.records = records
            
            def emit(self, record):
                self.records.append(record)
        
        self.handler = ListHandler(self.records)
        self.handler.setLevel(self.level)
        logger.addHandler(self.handler)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.handler:
            logger = logging.getLogger(self.logger_name)
            logger.removeHandler(self.handler)
    
    @property
    def output(self) -> str:
        """Get all log output as a single string."""
        return "\n".join(record.getMessage() for record in self.records)
    
    @property
    def messages(self) -> list[str]:
        """Get all log messages as a list."""
        return [record.getMessage() for record in self.records]
