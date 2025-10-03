import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import pytest
from core.exceptions import ConfigError, DatabaseConnectionError, CleanerError

def test_config_error_creation():
    """Test que verifica la creación de ConfigError."""
    error = ConfigError("Configuration file not found")
    assert str(error) == "Configuration file not found"
    assert isinstance(error, Exception)

def test_database_connection_error():
    """Test que verifica DatabaseConnectionError."""
    error = DatabaseConnectionError("Cannot connect to MySQL")
    assert str(error) == "Cannot connect to MySQL"
    assert isinstance(error, Exception)

def test_cleaner_error():
    """Test que verifica CleanerError.""" 
    error = CleanerError("Failed to clean Chrome profiles")
    assert str(error) == "Failed to clean Chrome profiles"
    assert isinstance(error, Exception)

def test_exceptions_inheritance():
    """Test que verifica que todas las excepciones heredan de Exception."""
    config_err = ConfigError("test")
    db_err = DatabaseConnectionError("test")
    cleaner_err = CleanerError("test")
    
    assert isinstance(config_err, Exception)
    assert isinstance(db_err, Exception)
    assert isinstance(cleaner_err, Exception)