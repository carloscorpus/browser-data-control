from core.config_loader import load_config
from core.db_manager import DBManager
from core.logger import setup_logging
from core.chromium_cleaner import ChromiumCleaner
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

        inactives = db.get_inactive_practitioners()
        logger.info(f"Usuarios inactivos encontrados: {inactives}")

        if inactives:
            cleaner = ChromiumCleaner(logger, cfg)
            cleaner.clean_profiles()

    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
