import sys
import pytest
from pathlib import Path

# Agregar src al PYTHONPATH para que los imports funcionen
project_root = Path(__file__).parent.parent
src_path = project_root / "src"

if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Fixture global para configuración mock
@pytest.fixture
def mock_config():
    """Configuración mock basada en tu configuración real"""
    from unittest.mock import Mock
    
    config = Mock()
    
    # DB config - Como tu configuración real
    config.db.host = "127.0.0.1"
    config.db.port = 3306
    config.db.user = "root"
    config.db.password = ""  # ← Como tu config real
    config.db.database = "test-bot-devconsulting"  # ← Como tu config real
    config.db.status_query = "SELECT practitioner_id FROM practitioners WHERE practitioner_status = 'I';"
    
    # Cleaner config - Como tu configuración real
    config.cleaner.mode = "profile"  # ← Como tu config real
    config.cleaner.files_to_remove = ["Login Data", "Cookies", "Web Data", "Local Storage"]
    config.cleaner.allow_permanent_delete = False
    config.cleaner.quarantine_dir = "C:/browser-data-control/quarantine"
    config.cleaner.browser_profiles = []
    
    # Safety config - SIEMPRE dry_run en tests
    config.safety.dry_run = True  # ← IMPORTANTE: siempre en tests
    
    # Scheduler config
    config.scheduler.type = "cron"
    config.scheduler.cron.day_of_week = "*"
    config.scheduler.cron.hour = 13
    config.scheduler.cron.minute = 26
    
    # Logging config
    config.logging.level = "INFO"
    config.logging.log_file = "logs/browser-data-control.log"
    
    return config

@pytest.fixture
def mock_logger():
    """Logger mock reutilizable para todos los tests"""
    from unittest.mock import Mock
    return Mock()

@pytest.fixture
def real_db_config():
    """Configuración de DB real para tests de integración (solo estructura, no conexión real)"""
    return {
        "host": "127.0.0.1",
        "port": 3306,
        "user": "root",
        "password": "",
        "database": "test-bot-devconsulting"
    }