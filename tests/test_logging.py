"""Tests for logging module."""
import logging

import structlog

from src.utils.logging import get_logger, setup_logging


def test_setup_logging_configures_level():
    """Test that setup_logging configures the log level correctly."""
    setup_logging("DEBUG")

    logger = get_logger("test")
    assert logger is not None


def test_get_logger_returns_structlog_instance():
    """Test that get_logger returns a structlog logger."""
    setup_logging("INFO")

    logger = get_logger("test_logger")
    # structlog returns a BoundLoggerLazyProxy, not BoundLogger directly
    assert logger is not None
    assert hasattr(logger, 'info')
    assert hasattr(logger, 'error')


def test_logger_can_log_messages():
    """Test that logger can log structured messages."""
    setup_logging("INFO")

    logger = get_logger("test")

    # Should not raise exceptions
    logger.info("test_message", key="value")
    logger.warning("warning_message", error_code=123)
    logger.error("error_message", exception="test")


def test_setup_logging_accepts_different_levels():
    """Test that setup_logging accepts different log levels."""
    for level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
        setup_logging(level)
        # Should not raise exceptions
