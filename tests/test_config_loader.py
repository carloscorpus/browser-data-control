import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import pytest
from core.config_loader import load_config, AppConfig, DBConfig
from pydantic import ValidationError

def test_load_config_default(monkeypatch, tmp_path):
    # Crear un config.json temporal
    config_data = {
        "db": {
            "host": "localhost",
            "port": 3306,
            "user": "user",
            "password": "pass",
            "database": "testdb"
        }
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(str(config_data).replace("'", '"'))
    monkeypatch.setenv("PWD", str(tmp_path))
    cfg = load_config(str(config_path))
    assert isinstance(cfg, AppConfig)
    assert cfg.db.host == "localhost"

def test_load_config_env_password(monkeypatch, tmp_path):
    config_data = {
        "db": {
            "host": "localhost",
            "port": 3306,
            "user": "user",
            "password_env_var": "DB_PASS",
            "database": "testdb"
        }
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(str(config_data).replace("'", '"'))
    monkeypatch.setenv("DB_PASS", "secret")
    cfg = load_config(str(config_path))
    assert cfg.db.password_env_var == "DB_PASS"

def test_load_config_invalid(monkeypatch, tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text("{invalid json}")
    with pytest.raises(Exception):
        load_config(str(config_path))