import pytest
import json
import tempfile
import os
from pathlib import Path
from core.config_loader import load_config, AppConfig
from core.exceptions import ConfigurationError

class TestConfigLoader:
    
    def test_load_valid_config_like_real(self):
        """Test que carga una configuración similar a la real"""
        valid_config = {
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
        
        # Crear archivo temporal de forma más segura para Windows
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
            json.dump(valid_config, f)
        
        try:
            config = load_config(temp_path)
            assert isinstance(config, AppConfig)
            
            # Verificar DB config como la real
            assert config.db.host == "127.0.0.1"
            assert config.db.port == 3306
            assert config.db.user == "root"
            assert config.db.password == ""
            assert config.db.database == "test-bot-devconsulting"
            assert "practitioners" in config.db.status_query
            
            # Verificar cleaner config como la real
            assert config.cleaner.mode == "profile"
            assert "Login Data" in config.cleaner.files_to_remove
            assert "Cookies" in config.cleaner.files_to_remove
            
            # Verificar safety
            assert config.safety.dry_run == True
            
        finally:
            # Eliminar archivo de forma segura en Windows
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except PermissionError:
                    # En Windows, a veces necesita un pequeño delay
                    import time
                    time.sleep(0.1)
                    os.unlink(temp_path)
    
    def test_missing_db_user_required(self):
        """Test que falla si falta el usuario de DB (campo requerido)"""
        invalid_config = {
            "db": {
                "host": "127.0.0.1",
                "port": 3306,
                # user faltante - es requerido según tu modelo
                "password": "",
                "database": "test-bot-devconsulting"
            },
            "scheduler": {"type": "cron", "cron": {"day_of_week": "*", "hour": 13, "minute": 26}},
            "cleaner": {"mode": "profile", "files_to_remove": [], "allow_permanent_delete": False, "quarantine_dir": "C:/test", "browser_profiles": []},
            "logging": {"level": "INFO", "log_file": "test.log"},
            "safety": {"dry_run": True}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
            json.dump(invalid_config, f)
        
        try:
            with pytest.raises((ConfigurationError, Exception)):
                load_config(temp_path)
        finally:
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except PermissionError:
                    import time
                    time.sleep(0.1)
                    os.unlink(temp_path)
    
    def test_missing_database_required(self):
        """Test que falla si falta el nombre de la base de datos (campo requerido)"""
        invalid_config = {
            "db": {
                "host": "127.0.0.1",
                "port": 3306,
                "user": "root",
                "password": ""
                # database faltante - es requerido según tu modelo
            },
            "scheduler": {"type": "cron", "cron": {"day_of_week": "*", "hour": 13, "minute": 26}},
            "cleaner": {"mode": "profile", "files_to_remove": [], "allow_permanent_delete": False, "quarantine_dir": "C:/test", "browser_profiles": []},
            "logging": {"level": "INFO", "log_file": "test.log"},
            "safety": {"dry_run": True}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
            json.dump(invalid_config, f)
        
        try:
            with pytest.raises((ConfigurationError, Exception)):
                load_config(temp_path)
        finally:
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except PermissionError:
                    import time
                    time.sleep(0.1)
                    os.unlink(temp_path)
    
    def test_config_file_not_found(self):
        """Test que falla si el archivo de configuración no existe"""
        with pytest.raises((ConfigurationError, FileNotFoundError)):
            load_config("archivo_inexistente.json")
    
    def test_default_values_applied(self):
        """Test que los valores por defecto se aplican correctamente"""
        minimal_config = {
            "db": {
                "user": "root",
                "database": "test-bot-devconsulting"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
            json.dump(minimal_config, f)
        
        try:
            config = load_config(temp_path)
            
            # Verificar valores por defecto según tu modelo
            assert config.db.host == "127.0.0.1"
            assert config.db.port == 3306
            assert config.scheduler.type == "cron"
            
        finally:
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except PermissionError:
                    import time
                    time.sleep(0.1)
                    os.unlink(temp_path)
    
    def test_empty_password_valid(self):
        """Test que password vacío es válido (como en tu config real)"""
        config_with_empty_password = {
            "db": {
                "user": "root",
                "password": "",
                "database": "test-bot-devconsulting"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
            json.dump(config_with_empty_password, f)
        
        try:
            config = load_config(temp_path)
            assert config.db.password == ""
            assert config.db.user == "root"
            assert config.db.database == "test-bot-devconsulting"
        finally:
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except PermissionError:
                    import time
                    time.sleep(0.1)
                    os.unlink(temp_path)
    
    def test_custom_status_query(self):
        """Test que acepta queries personalizados como el tuyo"""
        config_with_custom_query = {
            "db": {
                "user": "root",
                "database": "test-bot-devconsulting",
                "status_query": "SELECT practitioner_id FROM practitioners WHERE practitioner_status = 'I';"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
            json.dump(config_with_custom_query, f)
        
        try:
            config = load_config(temp_path)
            assert config.db.status_query == "SELECT practitioner_id FROM practitioners WHERE practitioner_status = 'I';"
            assert "practitioner_status" in config.db.status_query
        finally:
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except PermissionError:
                    import time
                    time.sleep(0.1)
                    os.unlink(temp_path)