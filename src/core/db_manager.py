# src/core/db_manager.py
import pymysql
from typing import List, Tuple
from .exceptions import DatabaseConnectionError


class DBManager:
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.conn = None

    def connect(self):
        try:
            self.conn = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
            # Intentar bajar el aislamiento para lecturas más frescas
            try:
                with self.conn.cursor() as cursor:
                    cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
            except Exception:
                # Si no se puede cambiar el nivel, continuar con autocommit
                pass
        except Exception as e:
            raise DatabaseConnectionError(f"Error al conectar a la BD: {e}")

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def get_inactive_practitioners(self) -> List[Tuple[int, str]]:
        """
        Retorna lista de tuples con (practitioner_id, practitioner_status)
        para todos los inactivos (status = 'I').
        """
        if not self.conn:
            self.connect()

        query = "SELECT practitioner_id, practitioner_status FROM practitioners WHERE practitioner_status = 'I';"
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                return [(row["practitioner_id"], row["practitioner_status"]) for row in results]
        except Exception as e:
            raise DatabaseConnectionError(f"Error ejecutando query: {e}")

    def get_inactive_for_user(self, system_username: str):
        """
        Retorna los practitioners inactivos asociados a un usuario específico del sistema.
        """
        query = """
        SELECT p.practitioner_id, p.practitioner_status, u.system_username
        FROM practitioners p
        JOIN practitioner_system_users u
          ON p.practitioner_id = u.practitioner_id
        WHERE p.practitioner_status = 'I'
          AND u.system_username = %s;
        """
        if not self.conn:
            self.connect()
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (system_username,))
                return cursor.fetchall()
        except Exception as e:
            raise DatabaseConnectionError(f"Error ejecutando query: {e}")

    def register_ip(self, practitioner_id: int, ip_address: str, system_username: str = None) -> bool:
        """
        Registra o actualiza la información del usuario en practitioner_system_users.
        Si el practitioner_id existe en practitioners, entonces:
        - Si ya existe en practitioner_system_users: actualiza system_username e ip_address
        - Si no existe: lo inserta
        Si el practitioner_id no existe en practitioners: no hace nada
        """
        if not self.conn:
            self.connect()

        try:
            # 1. Verificar que el practitioner_id existe en la tabla practitioners
            check_query = "SELECT practitioner_id FROM practitioners WHERE practitioner_id = %s LIMIT 1"
            with self.conn.cursor() as cursor:
                cursor.execute(check_query, (practitioner_id,))
                if not cursor.fetchone():
                    print(f"Practitioner ID {practitioner_id} no existe en tabla practitioners")
                    return False

            # 2. Obtener system_username si no se proporciona
            if not system_username:
                import os
                system_username = os.getenv("USERNAME", "unknown_user")

            # 3. Verificar si ya existe el registro en practitioner_system_users
            check_user_query = """
            SELECT practitioner_id FROM practitioner_system_users 
            WHERE practitioner_id = %s AND system_username = %s LIMIT 1
            """
            with self.conn.cursor() as cursor:
                cursor.execute(check_user_query, (practitioner_id, system_username))
                existing = cursor.fetchone()

            if existing:
                # 4. Actualizar IP si ya existe
                update_query = """
                UPDATE practitioner_system_users 
                SET ip_address = %s 
                WHERE practitioner_id = %s AND system_username = %s
                """
                with self.conn.cursor() as cursor:
                    cursor.execute(update_query, (ip_address, practitioner_id, system_username))
                    print(f"IP actualizada para practitioner {practitioner_id}, user {system_username}")
            else:
                # 5. Insertar nuevo registro
                insert_query = """
                INSERT INTO practitioner_system_users (practitioner_id, system_username, ip_address)
                VALUES (%s, %s, %s)
                """
                with self.conn.cursor() as cursor:
                    cursor.execute(insert_query, (practitioner_id, system_username, ip_address))
                    print(f"Nuevo registro creado para practitioner {practitioner_id}, user {system_username}")

            return True

        except Exception as e:
            print(f"Error registrando IP: {e}")
            raise DatabaseConnectionError(f"Error registrando IP: {e}")

    def get_practitioner_system_users(self, practitioner_id: int) -> List[dict]:
        """
        Obtiene todos los usuarios del sistema asociados a un practitioner
        Tabla: practitioner_system_users (practitioner_id, system_username, ip_address)
        """
        if not self.conn:
            self.connect()

        query = """
        SELECT practitioner_id, system_username, ip_address
        FROM practitioner_system_users 
        WHERE practitioner_id = %s
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (practitioner_id,))
                results = cursor.fetchall()
                print(f"[DEBUG] Encontrados {len(results)} registros para practitioner {practitioner_id}")
                return results
        except Exception as e:
            print(f"[ERROR] Error consultando practitioner_system_users: {e}")
            raise DatabaseConnectionError(f"Error ejecutando query: {e}")

    def cleanup_inactive_practitioners(self) -> List[dict]:
        """
        Obtiene información completa de usuarios inactivos con sus datos del sistema
        para realizar limpieza remota
        """
        if not self.conn:
            self.connect()

        query = """
        SELECT p.practitioner_id, p.practitioner_status, p.practitioner_date_end,
               u.system_username, u.ip_address
        FROM practitioners p
        LEFT JOIN practitioner_system_users u ON p.practitioner_id = u.practitioner_id
        WHERE p.practitioner_status = 'I'
        ORDER BY p.practitioner_id
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            raise DatabaseConnectionError(f"Error ejecutando query: {e}")
