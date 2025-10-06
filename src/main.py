from core.config_loader import load_config
from core.db_manager import DBManager
from core.logger import setup_logging

from core.chromium_cleaner import ChromiumCleaner
from core.scheduler import TaskScheduler
from core.ip_utils import get_public_ip
import os
import sys
import argparse

def parse_main_arguments():
    """
    Parsea argumentos de línea de comandos para el modo principal o administrativo.
    
    Returns:
        argparse.Namespace: Argumentos parseados
    """
    parser = argparse.ArgumentParser(
        description="Browser Data Control",
        add_help=False  # Evitamos conflictos con argumentos admin
    )
    
    # Comandos administrativos
    parser.add_argument('--consultar-inhabilitados', action='store_true', 
                       help='Muestra usuarios inhabilitados')
    parser.add_argument('--eliminar-un-usuario', type=int, metavar='ID',
                       help='Limpia datos de Chromium del usuario especificado')
    parser.add_argument('--eliminar-varios-usuarios', action='store_true',
                       help='Limpia datos de Chromium de todos los usuarios inhabilitados')
    parser.add_argument('--cambiar-hora-de-eliminacion', action='store_true',
                       help='Cambia la hora programada')
    parser.add_argument('--day', type=str, help='Día de la semana')
    parser.add_argument('--hour', type=int, help='Hora (0-23)')
    parser.add_argument('--minute', type=int, help='Minuto (0-59)')
    parser.add_argument('--help', '-h', action='store_true', help='Muestra ayuda')
    
    return parser.parse_known_args()[0]

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


        # Registrar IP y validar existencia del usuario antes de iniciar el scheduler
        ip = get_public_ip()
        if not ip:
            logger.warning("No se pudo obtener la IP pública. El programa terminará.")
            return
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
            logger.error("El usuario no está registrado o hay un error en la BD. El programa terminará.")
            return

        def job():
            # Ya se registró la IP al inicio, solo ejecutar limpieza
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
    # Verificar si se están usando comandos administrativos
    args = parse_main_arguments()
    
    # Si se especifica algún comando administrativo, usar el módulo admin
    if any([args.consultar_inhabilitados, args.eliminar_un_usuario, 
            args.eliminar_varios_usuarios, args.cambiar_hora_de_eliminacion, 
            args.help]):
        
        if args.help:
            print("""
Browser Data Control - Sistema de limpieza automática de navegadores

USO NORMAL:
  python main.py                    # Ejecuta el modo de monitoreo normal

COMANDOS ADMINISTRATIVOS:
  python main.py --consultar-inhabilitados
  python main.py --eliminar-un-usuario <ID>        # Limpia datos de Chromium del usuario
  python main.py --eliminar-varios-usuarios        # Limpia datos de Chromium de todos los inhabilitados
  python main.py --cambiar-hora-de-eliminacion --day "*" --hour 18 --minute 30

EJEMPLOS:
  python main.py --consultar-inhabilitados
  python main.py --eliminar-un-usuario 123         # Limpia datos de navegador del usuario 123
  python main.py --cambiar-hora-de-eliminacion --hour 20 --minute 0

NOTA: Los comandos de "eliminación" NO borran usuarios de la base de datos,
      sino que limpian sus datos de navegador (Chromium/Chrome).
            """)
            sys.exit(0)
        
        # Importar y ejecutar comandos administrativos
        from admin_commands import AdminCommands
        
        try:
            admin = AdminCommands()
            
            if args.consultar_inhabilitados:
                admin.consultar_inhabilitados()
                
            elif args.eliminar_un_usuario:
                admin.eliminar_un_usuario(args.eliminar_un_usuario)
                
            elif args.eliminar_varios_usuarios:
                admin.eliminar_varios_usuarios()
                
            elif args.cambiar_hora_de_eliminacion:
                if not any([args.day, args.hour is not None, args.minute is not None]):
                    print("❌ Error: Debe especificar al menos --day, --hour o --minute")
                    print("Ejemplo: python main.py --cambiar-hora-de-eliminacion --hour 20 --minute 0")
                    sys.exit(1)
                
                admin.cambiar_hora_eliminacion(
                    day_of_week=args.day,
                    hour=args.hour,
                    minute=args.minute
                )
        
        except KeyboardInterrupt:
            print("\n⚠️ Operación cancelada por el usuario")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            sys.exit(1)
    
    else:
        # Modo normal de operación
        main()
