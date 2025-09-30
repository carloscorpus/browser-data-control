class ConfigError(Exception):
    """Errores relacionados con la configuración (config.json)."""

class ConfigurationError(Exception):
    """Excepción para errores de configuración (estándar para tests y compatibilidad)."""
    pass

class DatabaseConnectionError(Exception):
    """Error al conectar con la base de datos."""

class CleanerError(Exception):
    """Error al intentar limpiar datos del navegador."""