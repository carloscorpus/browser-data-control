# src/core/config_loader.py
from __future__ import annotations
from typing import List, Optional
import json
import os
from pydantic import BaseModel, Field, ValidationError


class DBConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 3306
    user: str
    # password can be provided directly (not recommended) or via env var (recommended)
    password: Optional[str] = None
    password_env_var: Optional[str] = None
    database: str
    # Flexible query: permite adaptar el SQL sin tocar el código
    status_query: str = "SELECT id FROM practitioner WHERE status = 'I';"


class CronConfig(BaseModel):
    day_of_week: str = "fri"
    hour: int = 14
    minute: int = 0


class SchedulerConfig(BaseModel):
    type: str = "cron"  # por ahora soportamos cron
    cron: CronConfig = CronConfig()


class CleanerConfig(BaseModel):
    # "files" borra/limpia archivos sensibles (Login Data, Cookies...),
    # "profile" borra directorio completo del perfil (más agresivo).
    mode: str = "files"
    files_to_remove: List[str] = Field(
        default_factory=lambda: ["Login Data", "Cookies", "Web Data", "Local Storage"]
    )
    allow_permanent_delete: bool = False
    # path donde mover respaldos/quarantine si quieres no borrar inmediatamente
    quarantine_dir: Optional[str] = None
    # si vacío, el cleaner intentará detectar rutas por defecto
    browser_profiles: List[str] = Field(default_factory=list)


class LoggingConfig(BaseModel):
    level: str = "INFO"
    log_file: str = "logs/browser-data-control.log"


class SafetyConfig(BaseModel):
    dry_run: bool = True  # empieza con dry-run = true por seguridad


class AppConfig(BaseModel):
    db: DBConfig
    scheduler: SchedulerConfig = SchedulerConfig()
    cleaner: CleanerConfig = CleanerConfig()
    logging: LoggingConfig = LoggingConfig()
    safety: SafetyConfig = SafetyConfig()


def load_config(path: str = None) -> AppConfig:
    """
    Lee y valida config.json. Si db.password_env_var está definido, intenta tomar la
    contraseña de la variable de entorno correspondiente (preferido).
    Lanza ValidationError / ConfigError en caso de problemas.
    """
    if path is None:
        # Detectar la ruta del archivo de configuración relativa al directorio del script
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(script_dir, "config", "config.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Archivo de configuración no encontrado: {path}")

    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)

    try:
        cfg = AppConfig.parse_obj(raw)
    except ValidationError as ve:
        raise Exception(f"Error validando config.json: {ve}")

    # resolver password desde variable de entorno (si existe)
    pw_env = getattr(cfg.db, "password_env_var", None)
    if pw_env:
        pw = os.getenv(pw_env)
        if pw:
            cfg.db.password = pw
    return cfg
