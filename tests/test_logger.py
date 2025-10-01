import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import pytest
from core.logger import setup_logging
import logging

def test_setup_logging_creates_logger(tmp_path):
    log_file = tmp_path / "test.log"
    logger = setup_logging(str(log_file), level="DEBUG")
    assert logger.name == "browser_data_control"
    assert logger.level == logging.DEBUG
    # Verifica que el archivo de log se crea
    logger.info("test message")
    logger.handlers[1].flush()
    assert log_file.exists()

def test_setup_logging_multiple_calls(tmp_path):
    log_file = tmp_path / "test2.log"
    logger1 = setup_logging(str(log_file), level="INFO")
    logger2 = setup_logging(str(log_file), level="INFO")
    assert logger1 is logger2