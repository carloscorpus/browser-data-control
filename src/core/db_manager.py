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
                cursorclass=pymysql.cursors.DictCursor
            )
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
