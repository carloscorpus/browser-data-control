class ConfigError(Exception):
    """Errores relacionados con la configuración (config.json)."""

class DatabaseConnectionError(Exception):
    """Error al conectar con la base de datos."""

class CleanerError(Exception):
    """Error al intentar limpiar datos del navegador."""
