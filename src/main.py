from core.config_loader import load_config
from core.db_manager import DBManager
from core.logger import setup_logging
from core.chromium_cleaner import ChromiumCleaner
from core.scheduler import TaskScheduler
import os

def register_user_to_system(db, system_user):
    """Función para registrar el practitioner_id en el sistema operativo"""
    practitioner_id = input("Por favor, ingrese su código de registro (practitioner_id): ").strip()

    # Verificar si el ID existe en la base de datos
    query = "SELECT practitioner_id FROM practitioners WHERE practitioner_id = %s;"
    db.connect()
    with db.conn.cursor() as cursor:
        cursor.execute(query, (practitioner_id,))
        result = cursor.fetchone()
        
    if result:
        # Verificar si el usuario ya está registrado en la tabla practitioner_system_users
        check_query = "SELECT * FROM practitioner_system_users WHERE practitioner_id = %s AND system_username = %s;"
        with db.conn.cursor() as cursor:
            cursor.execute(check_query, (practitioner_id, system_user))
            existing_user = cursor.fetchone()

        if existing_user:
            print("Este usuario ya está registrado con el sistema.")
        else:
            # Registrar el usuario con su sistema operativo
            insert_query = "INSERT INTO practitioner_system_users (practitioner_id, system_username) VALUES (%s, %s);"
            with db.conn.cursor() as cursor:
                cursor.execute(insert_query, (practitioner_id, system_user))
                db.conn.commit()
            print(f"Usuario {practitioner_id} registrado exitosamente en el sistema {system_user}.")
    else:
        print("Usuario no encontrado en la base de datos.")

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

        # Registra al usuario en la base de datos si es necesario
        register_user_to_system(db, system_user)

        def job():
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
