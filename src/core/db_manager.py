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
