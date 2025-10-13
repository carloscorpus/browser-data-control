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
            cursor = self.db_manager.conn.cursor()
            
            # Query para obtener usuarios inactivos (adaptada a tu BD real)
            query = """
            SELECT p.practitioner_id, p.general_id, p.practitioner_status, 
                   p.practitioner_date_start, p.practitioner_date_end,
                   p.practitioner_observation, p.area_id, p.division_id,
                   psu.system_username, psu.ip_address
            FROM practitioners p
            LEFT JOIN practitioner_system_users psu ON p.practitioner_id = psu.practitioner_id
            WHERE p.practitioner_status = 'I'
            ORDER BY p.practitioner_id
            """
            
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