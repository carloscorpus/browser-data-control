import pytest
import json
import tempfile
import os
from pathlib import Path
from core.config_loader import load_config

class TestRealConfigCompatibility:
    """Tests específicos para verificar compatibilidad con tu configuración real"""
    
    def test_load_actual_config_file(self):
        """Test que puede cargar tu archivo de configuración real"""
        config_path = Path(__file__).parent.parent / "src" / "config" / "config.json"
        
        if config_path.exists():
            # Si existe tu config real, probarlo
            config = load_config(str(config_path))
            
            # Verificar que carga correctamente tu configuración
            assert config.db.host == "127.0.0.1"
            assert config.db.user == "root"
            assert config.db.database == "test-bot-devconsulting"
            assert config.cleaner.mode == "profile"
            assert config.safety.dry_run == True
        else:
            pytest.skip("Config real no encontrado, saltando test")
    
    def test_config_structure_matches_real(self):
        """Test que la estructura del config coincida con lo esperado"""
        # Simular exactamente tu estructura real
        real_like_config = {
            "db": {
                "host": "127.0.0.1",
                "port": 3306,
                "user": "root",
                "password": "",
                "database": "test-bot-devconsulting",
                "status_query": "SELECT practitioner_id FROM practitioners WHERE practitioner_status = 'I';"
            },
            "scheduler": {
                "type": "cron",
                "cron": {
                    "day_of_week": "*",
                    "hour": 13,
                    "minute": 26
                }
            },
            "cleaner": {
                "mode": "profile",
                "files_to_remove": ["Login Data", "Cookies", "Web Data", "Local Storage"],
                "allow_permanent_delete": False,
                "quarantine_dir": "C:/browser-data-control/quarantine",
                "browser_profiles": []
            },
            "logging": {
                "level": "INFO",
                "log_file": "logs/browser-data-control.log"
            },
            "safety": {
                "dry_run": True
            }
        }
        
        # Usar el mismo patrón que funciona en test_config_loader.py
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
            json.dump(real_like_config, f)
        
        try:
            config = load_config(temp_path)
            
            # Verificar cada sección
            assert config.db.database == "test-bot-devconsulting"
            assert config.db.user == "root"
            assert config.db.password == ""
            assert config.cleaner.mode == "profile"
            assert config.safety.dry_run == True
            assert config.scheduler.cron.hour == 13
            
        finally:
            # Eliminar archivo de forma segura en Windows
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except PermissionError:
                    import time
                    time.sleep(0.1)
                    os.unlink(temp_path)