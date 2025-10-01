from core.config_loader import load_config
from core.db_manager import DBManager
from core.logger import setup_logging

from core.chromium_cleaner import ChromiumCleaner
from core.scheduler import TaskScheduler
from core.ip_utils import get_public_ip
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

        # Solicitar practitioner_id al usuario (por consola)
        try:
            practitioner_id = int(input("Ingrese su practitioner_id: "))
        except Exception:
            logger.error("practitioner_id inválido. Debe ser un número entero.")
            return

        def register_ip():
            ip = get_public_ip()
            if ip:
                try:
                    if not db.conn:
                        db.connect()
                    with db.conn.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO practitioner_system_users (practitioner_id, system_username, ip_address)
                            VALUES (%s, %s, %s)
                            ON DUPLICATE KEY UPDATE ip_address=VALUES(ip_address)
                            """,
                            (practitioner_id, system_user, ip)
                        )
                        db.conn.commit()
                    logger.info(f"IP pública registrada en la BD: {ip}")
                except Exception as e:
                    logger.error(f"No se pudo registrar la IP pública: {e}")
            else:
                logger.warning("No se pudo obtener la IP pública.")

        def job():
            register_ip()
            inactives = db.get_inactive_for_user(system_user)
            if inactives:
                logger.info(f"⚠️ El usuario {system_user} está inactivo en la BD → ejecutar limpieza")
                cleaner = ChromiumCleaner(logger, cfg)
                cleaner.clean_profiles()
            else:
                logger.info(f"✅ El usuario {system_user} está activo/no registrado → no se limpia nada")

        sched = TaskScheduler(logger)
        sched.add_cron_job(
            job,
            cfg.scheduler.cron.day_of_week,
            cfg.scheduler.cron.hour,
            cfg.scheduler.cron.minute
        )
        sched.start()

    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
