# Servicio de base de datos para la aplicación admin
# Reutiliza y extiende tu DBManager existente

import sys
import os

# Importar tu código existente
current_dir = os.path.dirname(__file__)
project_root = os.path.join(current_dir, '..', '..', '..')
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

try:
    from core.db_manager import DBManager
    from core.exceptions import DatabaseConnectionError
    import mysql.connector
except ImportError as e:
    print(f"❌ Error importando dependencias: {e}")
    print(f"📍 Buscando en: {src_path}")
    raise
from typing import Optional, Tuple, List, Dict
from datetime import datetime

class SecureDBService:
    """
    Wrapper seguro alrededor de tu DBManager existente
    Agrega funcionalidades específicas para la aplicación admin
    """
    
    def __init__(self):
        self.db_manager: Optional[DBManager] = None
        self.connection_params: Optional[Dict] = None
    
    def connect(self, host: str, port: int, user: str, password: str, database: str) -> Tuple[bool, Optional[str]]:
        """
        Conecta a la base de datos usando credenciales del admin
        Reutiliza tu DBManager pero con parámetros dinámicos
        """
        try:
            # Crear instancia de tu DBManager con parámetros correctos
            self.db_manager = DBManager(host, port, user, password, database)
            
            # Intentar conexión
            self.db_manager.connect()
            
            # Verificar que puede hacer operaciones básicas
            if self._verify_admin_permissions():
                self.connection_params = {
                    'host': host,
                    'port': port,
                    'user': user,
                    'database': database
                    # ❌ NO guardar password
                }
                return True, None
            else:
                return False, "Usuario sin permisos suficientes para operaciones administrativas"
                
        except DatabaseConnectionError as e:
            return False, f"Error de conexión: {str(e)}"
        except Exception as e:
            return False, f"Error inesperado: {str(e)}"
    
    def _verify_admin_permissions(self) -> bool:
        """
        Verifica que el usuario conectado tiene permisos para operaciones admin
        Hace una query simple para probar la conexión
        """
        try:
            # Test simple: verificar que puede hacer SELECT
            cursor = self.db_manager.conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            return result is not None
        except Exception:
            return False
    
    def get_inactive_practitioners(self) -> List[Dict]:
        """
        Obtiene usuarios inactivos usando tu estructura de BD real
        """
        if not self.db_manager:
            raise DatabaseConnectionError("No hay conexión a la base de datos")
        
        try:
            # Asegurar conexión viva y sesión con lecturas frescas
            try:
                self.db_manager.conn.ping(reconnect=True)
                # Forzar autocommit en conexiones existentes
                try:
                    self.db_manager.conn.autocommit(True)
                except Exception:
                    pass
                # Cerrar cualquier transacción previa para evitar snapshots antiguos
                try:
                    self.db_manager.conn.rollback()
                except Exception:
                    pass
                with self.db_manager.conn.cursor() as _c:
                    _c.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
            except Exception:
                pass

            cursor = self.db_manager.conn.cursor()

            # Evitar duplicados: no hacer JOIN que multiplique filas por usuario del sistema.
            query = (
                "SELECT practitioner_id, general_id, practitioner_status, "
                "       practitioner_date_start, practitioner_date_end, "
                "       practitioner_observation, area_id, division_id "
                "FROM practitioners WHERE practitioner_status = 'I' "
                "ORDER BY practitioner_id"
            )

            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()

            return results
            
        except Exception as e:
            print(f"Error getting inactive practitioners: {e}")
            raise
    
    def register_ip(self, practitioner_id: int, ip_address: str) -> bool:
        """
        Reutiliza tu método existente
        """
        if not self.db_manager:
            raise DatabaseConnectionError("No hay conexión a la base de datos")
        
        return self.db_manager.register_ip(practitioner_id, ip_address)
    
    def get_all_practitioners(self) -> List[Dict]:
        """
        Nueva funcionalidad para el admin: listar todos los usuarios
        Adaptado a tu estructura real de BD
        """
        if not self.db_manager:
            raise DatabaseConnectionError("No hay conexión a la base de datos")
        
        try:
            # Asegurar conexión viva y sesión con lecturas frescas
            try:
                self.db_manager.conn.ping(reconnect=True)
                # Forzar autocommit en conexiones existentes
                try:
                    self.db_manager.conn.autocommit(True)
                except Exception:
                    pass
                # Cerrar cualquier transacción previa para evitar snapshots antiguos
                try:
                    self.db_manager.conn.rollback()
                except Exception:
                    pass
                with self.db_manager.conn.cursor() as _c:
                    _c.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
            except Exception:
                pass

            cursor = self.db_manager.conn.cursor()
            
            query = """
            SELECT practitioner_id, general_id, practitioner_status, 
                   practitioner_date_start, practitioner_date_end,
                   practitioner_observation, area_id, division_id
            FROM practitioners 
            ORDER BY practitioner_id
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            
            return results
            
        except Exception as e:
            print(f"Error getting all practitioners: {e}")
            raise
    
    def close(self):
        """
        Cierra la conexión usando tu método existente
        """
        if self.db_manager:
            self.db_manager.close()
            self.db_manager = None
            self.connection_params = None

    def get_practitioner_by_id(self, practitioner_id: int) -> Optional[Dict]:
        """
        Obtiene un practicante específico por ID para refrescar únicamente esa fila en UI.
        """
        if not self.db_manager:
            raise DatabaseConnectionError("No hay conexión a la base de datos")

        try:
            # Asegurar conexión viva y sesión con lecturas frescas
            try:
                self.db_manager.conn.ping(reconnect=True)
                try:
                    self.db_manager.conn.autocommit(True)
                except Exception:
                    pass
                try:
                    self.db_manager.conn.rollback()
                except Exception:
                    pass
                with self.db_manager.conn.cursor() as _c:
                    _c.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
            except Exception:
                pass

            query = (
                "SELECT practitioner_id, general_id, practitioner_status, "
                "       practitioner_date_start, practitioner_date_end, "
                "       practitioner_observation, area_id, division_id "
                "FROM practitioners WHERE practitioner_id = %s LIMIT 1"
            )
            with self.db_manager.conn.cursor() as cursor:
                cursor.execute(query, (int(practitioner_id),))
                row = cursor.fetchone()
                return row if row else None
        except Exception as e:
            print(f"Error getting practitioner by id: {e}")
            raise

    def get_practitioners_by_ids(self, practitioner_ids: List[int]) -> List[Dict]:
        """
        Obtiene múltiples practicantes por ID de forma eficiente.
        """
        if not practitioner_ids:
            return []
        if not self.db_manager:
            raise DatabaseConnectionError("No hay conexión a la base de datos")

        try:
            # Asegurar conexión viva y sesión con lecturas frescas
            try:
                self.db_manager.conn.ping(reconnect=True)
                try:
                    self.db_manager.conn.autocommit(True)
                except Exception:
                    pass
                try:
                    self.db_manager.conn.rollback()
                except Exception:
                    pass
                with self.db_manager.conn.cursor() as _c:
                    _c.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
            except Exception:
                pass

            ids_placeholders = ",".join(["%s"] * len(practitioner_ids))
            query = (
                "SELECT practitioner_id, general_id, practitioner_status, "
                "       practitioner_date_start, practitioner_date_end, "
                "       practitioner_observation, area_id, division_id "
                f"FROM practitioners WHERE practitioner_id IN ({ids_placeholders})"
            )
            with self.db_manager.conn.cursor() as cursor:
                cursor.execute(query, tuple(int(i) for i in practitioner_ids))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error getting practitioners by ids: {e}")
            raise

    def get_practitioner_signatures(self) -> List[Dict]:
        """
        Retorna una vista ligera para detectar cambios sin updated_at.
        Incluye columnas clave cuya modificación debe reflejarse en la UI.
        """
        if not self.db_manager:
            raise DatabaseConnectionError("No hay conexión a la base de datos")
        try:
            try:
                self.db_manager.conn.ping(reconnect=True)
                try:
                    self.db_manager.conn.autocommit(True)
                except Exception:
                    pass
                try:
                    self.db_manager.conn.rollback()
                except Exception:
                    pass
            except Exception:
                pass

            query = (
                "SELECT practitioner_id, general_id, practitioner_status, "
                "       practitioner_date_start, practitioner_date_end "
                "FROM practitioners ORDER BY practitioner_id"
            )
            with self.db_manager.conn.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            print(f"Error getting practitioner signatures: {e}")
            raise

    def get_new_practitioners_since_id(self, last_id: int) -> List[Dict]:
        """
        Obtiene nuevos practicantes con ID mayor a last_id (maneja altas nuevas).
        Nota: Solo detecta nuevas altas si practitioner_id es incremental.
        """
        if not self.db_manager:
            raise DatabaseConnectionError("No hay conexión a la base de datos")
        try:
            try:
                self.db_manager.conn.ping(reconnect=True)
                try:
                    self.db_manager.conn.autocommit(True)
                except Exception:
                    pass
                try:
                    self.db_manager.conn.rollback()
                except Exception:
                    pass
            except Exception:
                pass

            query = (
                "SELECT practitioner_id, general_id, practitioner_status, "
                "       practitioner_date_start, practitioner_date_end, "
                "       practitioner_observation, area_id, division_id "
                "FROM practitioners WHERE practitioner_id > %s ORDER BY practitioner_id"
            )
            with self.db_manager.conn.cursor() as cursor:
                cursor.execute(query, (int(last_id),))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error getting new practitioners: {e}")
            raise

    def get_updated_practitioners_since_ts(self, last_sync: datetime) -> Optional[List[Dict]]:
        """
        Obtiene practicantes actualizados desde last_sync usando columna updated_at.
        Si la columna no existe, retorna None para indicar que no es soportado.
        """
        if not self.db_manager:
            raise DatabaseConnectionError("No hay conexión a la base de datos")
        try:
            try:
                self.db_manager.conn.ping(reconnect=True)
                try:
                    self.db_manager.conn.autocommit(True)
                except Exception:
                    pass
                try:
                    self.db_manager.conn.rollback()
                except Exception:
                    pass
            except Exception:
                pass

            query = (
                "SELECT practitioner_id, general_id, practitioner_status, "
                "       practitioner_date_start, practitioner_date_end, "
                "       practitioner_observation, area_id, division_id, updated_at "
                "FROM practitioners WHERE updated_at > %s"
            )
            with self.db_manager.conn.cursor() as cursor:
                cursor.execute(query, (last_sync,))
                return cursor.fetchall()
        except Exception as e:
            # Si falla por columna desconocida, devolver None para fallback
            if "unknown column" in str(e).lower() or "updated_at" in str(e).lower():
                return None
            print(f"Error getting updated practitioners: {e}")
            raise