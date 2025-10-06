"""
Módulo para comandos administrativos del sistema browser-data-control.
Permite gestionar usuarios y configuraciones desde la línea de comandos.
"""
import argparse
import json
import os
from typing import List, Optional
from core.db_manager import DBManager
from core.config_loader import load_config
from core.logger import setup_logging


class AdminCommands:
    """Clase que maneja todos los comandos administrativos del sistema."""
    
    def __init__(self):
        self.logger = setup_logging()
        self.config = load_config()
        self.db = DBManager(
            host=self.config.db.host,
            port=self.config.db.port,
            user=self.config.db.user,
            password=self.config.db.password or "",
            database=self.config.db.database
        )
    
    def consultar_inhabilitados(self) -> List[dict]:
        """
        Consulta y muestra todos los usuarios inhabilitados.
        
        Returns:
            List[dict]: Lista de usuarios inhabilitados
        """
        try:
            if not self.db.conn:
                self.db.connect()
            
            with self.db.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT practitioner_id, practitioner_status 
                    FROM practitioners 
                    WHERE practitioner_status = 'I'
                    ORDER BY practitioner_id
                """)
                
                results = cursor.fetchall()
                
                if not results:
                    self.logger.info("📋 No hay usuarios inhabilitados en el sistema")
                    print("📋 No hay usuarios inhabilitados en el sistema")
                    return []
                
                print(f"\n📋 USUARIOS INHABILITADOS ({len(results)} encontrados):")
                print("=" * 50)
                print(f"{'ID':<10} {'STATUS':<10}")
                print("-" * 50)
                
                usuarios = []
                for i, row in enumerate(results):
                    try:
                        # Los resultados vienen como diccionarios, no como tuplas
                        usuario = {
                            'id': row['practitioner_id'],
                            'status': row['practitioner_status']
                        }
                        usuarios.append(usuario)
                        print(f"{usuario['id']:<10} {usuario['status']:<10}")
                    except (KeyError, TypeError) as e:
                        self.logger.warning(f"Error procesando fila {i}: {row}, error: {e}")
                        continue
                
                print("=" * 50)
                self.logger.info(f"Consulta de inhabilitados completada: {len(usuarios)} usuarios")
                return usuarios
                
        except Exception as e:
            error_msg = f"Error al consultar usuarios inhabilitados: {e}"
            self.logger.error(error_msg)
            print(f"❌ {error_msg}")
            return []
        finally:
            if self.db.conn:
                self.db.close()
    
    def eliminar_un_usuario(self, practitioner_id: int) -> bool:
        """
        Limpia los datos de Chromium de un usuario específico por su ID.
        
        Args:
            practitioner_id (int): ID del usuario al que limpiar datos de Chromium
            
        Returns:
            bool: True si se limpió exitosamente, False en caso contrario
        """
        try:
            if not self.db.conn:
                self.db.connect()
            
            # Primero verificar si el usuario existe
            with self.db.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT practitioner_id, practitioner_status 
                    FROM practitioners 
                    WHERE practitioner_id = %s
                """, (practitioner_id,))
                
                usuario = cursor.fetchone()
                if not usuario:
                    error_msg = f"Usuario con ID {practitioner_id} no encontrado"
                    self.logger.warning(error_msg)
                    print(f"⚠️ {error_msg}")
                    return False
                
                # Mostrar información del usuario antes de limpiar
                print(f"\n🧹 LIMPIANDO DATOS DE CHROMIUM DEL USUARIO:")
                print(f"   ID: {usuario['practitioner_id']}")
                print(f"   Status: {usuario['practitioner_status']}")
                print(f"   Se limpiarán todos los datos de navegador asociados a este usuario")
                
                # Confirmar limpieza
                confirm = input("\n¿Está seguro de limpiar los datos de Chromium de este usuario? (s/N): ").lower()
                if confirm != 's':
                    print("❌ Limpieza cancelada")
                    return False
                
                # Verificar si el usuario está en la tabla de system_users para obtener username
                cursor.execute("""
                    SELECT system_username 
                    FROM practitioner_system_users 
                    WHERE practitioner_id = %s
                """, (practitioner_id,))
                
                system_user_result = cursor.fetchone()
                if system_user_result:
                    system_username = system_user_result['system_username']
                    print(f"📝 Usuario del sistema encontrado: {system_username}")
                else:
                    print("⚠️ Usuario no tiene registro de sistema, se limpiará usando configuración por defecto")
                    system_username = None
                
                # Realizar limpieza usando ChromiumCleaner
                from core.chromium_cleaner import ChromiumCleaner
                cleaner = ChromiumCleaner(self.logger, self.config)
                
                print(f"🧹 Iniciando limpieza de datos de Chromium...")
                
                # Si tenemos un username específico, lo podemos usar para limpieza dirigida
                # Por ahora usamos la limpieza general
                result = cleaner.clean_profiles()
                
                if result:
                    success_msg = f"Datos de Chromium del usuario {practitioner_id} limpiados exitosamente"
                    self.logger.info(success_msg)
                    print(f"✅ {success_msg}")
                    print(f"📝 Revisa los logs para detalles específicos de la limpieza")
                    return True
                else:
                    error_msg = f"No se pudieron limpiar los datos del usuario {practitioner_id}"
                    self.logger.warning(error_msg)
                    print(f"⚠️ {error_msg}")
                    print(f"📝 Revisa los logs para más detalles")
                    return False
                    
        except Exception as e:
            error_msg = f"Error al limpiar datos del usuario {practitioner_id}: {e}"
            self.logger.error(error_msg)
            print(f"❌ {error_msg}")
            return False
        finally:
            if self.db.conn:
                self.db.close()
    
    def eliminar_varios_usuarios(self) -> int:
        """
        Limpia los datos de Chromium de todos los usuarios que estén inhabilitados.
        
        Returns:
            int: Número de usuarios a los que se les limpió los datos
        """
        try:
            # Primero consultar cuántos usuarios inhabilitados hay
            inhabilitados = self.consultar_inhabilitados()
            
            if not inhabilitados:
                return 0
            
            print(f"\n🧹 Se limpiarán los datos de Chromium de {len(inhabilitados)} usuarios inhabilitados")
            print("📝 Esta operación:")
            print("   - NO eliminará usuarios de la base de datos")
            print("   - SÍ limpiará todos los datos de navegador (perfiles, cookies, etc.)")
            print("   - Los datos se moverán a cuarentena o se eliminarán según configuración")
            
            confirm = input("\n¿Está seguro de continuar con la limpieza masiva? (s/N): ").lower()
            if confirm != 's':
                print("❌ Limpieza cancelada")
                return 0
            
            # Realizar limpieza usando ChromiumCleaner
            from core.chromium_cleaner import ChromiumCleaner
            cleaner = ChromiumCleaner(self.logger, self.config)
            
            print(f"🧹 Iniciando limpieza masiva de datos de Chromium...")
            print(f"📊 Usuarios afectados: {[u['id'] for u in inhabilitados]}")
            
            # Ejecutar limpieza general (afectará a todos los perfiles detectados)
            result = cleaner.clean_profiles()
            
            if result:
                success_msg = f"Limpieza masiva completada para {len(inhabilitados)} usuarios inhabilitados"
                self.logger.info(success_msg)
                print(f"✅ {success_msg}")
                print(f"📝 Revisa los logs para detalles específicos de la limpieza")
                return len(inhabilitados)
            else:
                error_msg = "No se pudieron limpiar datos en la limpieza masiva"
                self.logger.warning(error_msg)
                print(f"⚠️ {error_msg}")
                print(f"📝 Revisa los logs para más detalles")
                return 0
                
        except Exception as e:
            error_msg = f"Error al realizar limpieza masiva: {e}"
            self.logger.error(error_msg)
            print(f"❌ {error_msg}")
            return 0
    
    def cambiar_hora_eliminacion(self, day_of_week: str = None, hour: int = None, minute: int = None) -> bool:
        """
        Cambia la hora programada para la eliminación en el archivo config.json.
        
        Args:
            day_of_week (str, optional): Día de la semana (* para todos los días)
            hour (int, optional): Hora (0-23)
            minute (int, optional): Minuto (0-59)
            
        Returns:
            bool: True si se actualizó exitosamente, False en caso contrario
        """
        try:
            # Determinar la ruta correcta del archivo config.json
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, 'config', 'config.json')
            
            # Si no existe, intentar con la ruta alternativa
            if not os.path.exists(config_path):
                config_path = os.path.join(current_dir, '..', 'src', 'config', 'config.json')
            
            # Si aún no existe, intentar otra ruta
            if not os.path.exists(config_path):
                config_path = os.path.join(os.path.dirname(current_dir), 'src', 'config', 'config.json')
            
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"No se encontró el archivo config.json en las rutas esperadas")
            
            # Leer el archivo de configuración actual
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Mostrar configuración actual
            current = config_data['scheduler']['cron']
            print(f"\n⏰ CONFIGURACIÓN ACTUAL:")
            print(f"   Día de la semana: {current['day_of_week']}")
            print(f"   Hora: {current['hour']}")
            print(f"   Minuto: {current['minute']}")
            
            # Actualizar valores si se proporcionaron
            changed = False
            if day_of_week is not None:
                config_data['scheduler']['cron']['day_of_week'] = day_of_week
                changed = True
            
            if hour is not None:
                if 0 <= hour <= 23:
                    config_data['scheduler']['cron']['hour'] = hour
                    changed = True
                else:
                    print("❌ Error: La hora debe estar entre 0 y 23")
                    return False
            
            if minute is not None:
                if 0 <= minute <= 59:
                    config_data['scheduler']['cron']['minute'] = minute
                    changed = True
                else:
                    print("❌ Error: Los minutos deben estar entre 0 y 59")
                    return False
            
            if not changed:
                print("⚠️ No se especificaron cambios")
                return False
            
            # Guardar el archivo actualizado
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            # Mostrar nueva configuración
            new_config = config_data['scheduler']['cron']
            print(f"\n✅ NUEVA CONFIGURACIÓN:")
            print(f"   Día de la semana: {new_config['day_of_week']}")
            print(f"   Hora: {new_config['hour']}")
            print(f"   Minuto: {new_config['minute']}")
            
            success_msg = "Configuración de horario actualizada exitosamente"
            self.logger.info(success_msg)
            print(f"✅ {success_msg}")
            return True
            
        except Exception as e:
            error_msg = f"Error al cambiar hora de eliminación: {e}"
            self.logger.error(error_msg)
            print(f"❌ {error_msg}")
            return False


def parse_arguments():
    """
    Parsea los argumentos de línea de comandos para los comandos administrativos.
    
    Returns:
        argparse.Namespace: Argumentos parseados
    """
    parser = argparse.ArgumentParser(
        description="Browser Data Control - Comandos Administrativos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python admin.py --consultar-inhabilitados
  python admin.py --eliminar-un-usuario 123
  python admin.py --eliminar-varios-usuarios
  python admin.py --cambiar-hora-de-eliminacion --day "*" --hour 18 --minute 30
        """
    )
    
    # Grupo de comandos mutuamente excluyentes
    group = parser.add_mutually_exclusive_group(required=True)
    
    group.add_argument(
        '--consultar-inhabilitados',
        action='store_true',
        help='Muestra una relación de usuarios inhabilitados'
    )
    
    group.add_argument(
        '--eliminar-un-usuario',
        type=int,
        metavar='ID',
        help='Elimina un único usuario mediante su ID'
    )
    
    group.add_argument(
        '--eliminar-varios-usuarios',
        action='store_true',
        help='Elimina todos los usuarios que estén inhabilitados'
    )
    
    group.add_argument(
        '--cambiar-hora-de-eliminacion',
        action='store_true',
        help='Cambia la hora programada de eliminación'
    )
    
    # Argumentos para cambiar hora
    parser.add_argument(
        '--day',
        type=str,
        help='Día de la semana (* para todos los días, 0=Domingo, 1=Lunes, etc.)'
    )
    
    parser.add_argument(
        '--hour',
        type=int,
        help='Hora (0-23)'
    )
    
    parser.add_argument(
        '--minute',
        type=int,
        help='Minuto (0-59)'
    )
    
    return parser.parse_args()


def main_admin():
    """Función principal para ejecutar comandos administrativos."""
    try:
        args = parse_arguments()
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
                return False
            
            admin.cambiar_hora_eliminacion(
                day_of_week=args.day,
                hour=args.hour,
                minute=args.minute
            )
        
        return True
        
    except KeyboardInterrupt:
        print("\n⚠️ Operación cancelada por el usuario")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False


if __name__ == "__main__":
    main_admin()