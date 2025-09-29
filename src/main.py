from core.config_loader import load_config
from core.db_manager import DBManager
from core.logger import setup_logging
from core.chromium_cleaner import ChromiumCleaner
import os

def main():
    logger = setup_logging()
    try:
        cfg = load_config()
        logger.info("✅ Configuración cargada correctamente")

        db_cfg = cfg.db
        db = DBManager(
            host=db_cfg.host,
            port=db_cfg.port,
            user=db_cfg.user,
            password=db_cfg.password or "",
            database=db_cfg.database
        )

        system_user = os.getenv("USERNAME")
        logger.info(f"Usuario del sistema actual: {system_user}")

        inactives = db.get_inactive_for_user(system_user)

        if inactives:
            logger.info(f"⚠️ El usuario {system_user} está inactivo en la BD → ejecutar limpieza")
            cleaner = ChromiumCleaner(logger, cfg)
            cleaner.clean_profiles()
        else:
            logger.info(f"✅ El usuario {system_user} está activo o no está registrado → no se limpia nada")

    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
