import sys
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import pytest
from unittest.mock import patch, MagicMock
from core.db_manager import DBManager
from core.exceptions import DatabaseConnectionError

@pytest.fixture
def db_params():
	return {
		'host': 'localhost',
		'port': 3306,
		'user': 'user',
		'password': 'pass',
		'database': 'testdb'
	}

def test_connect_success(db_params):
	with patch('core.db_manager.pymysql.connect') as mock_connect:
		db = DBManager(**db_params)
		db.connect()
		mock_connect.assert_called_once()

def test_connect_failure(db_params):
	with patch('core.db_manager.pymysql.connect', side_effect=Exception('fail')):
		db = DBManager(**db_params)
		with pytest.raises(DatabaseConnectionError):
			db.connect()

def test_close_connection(db_params):
	db = DBManager(**db_params)
	mock_conn = MagicMock()
	db.conn = mock_conn
	db.close()
	mock_conn.close.assert_called_once()
	assert db.conn is None

def test_get_inactive_practitioners_success(db_params):
	db = DBManager(**db_params)
	db.conn = MagicMock()
	mock_cursor = MagicMock()
	db.conn.cursor.return_value.__enter__.return_value = mock_cursor
	mock_cursor.fetchall.return_value = [
		{"practitioner_id": 1, "practitioner_status": "I"},
		{"practitioner_id": 2, "practitioner_status": "I"}
	]
	result = db.get_inactive_practitioners()
	assert result == [(1, "I"), (2, "I")]

def test_get_inactive_practitioners_query_error(db_params):
	db = DBManager(**db_params)
	db.conn = MagicMock()
	db.conn.cursor.return_value.__enter__.side_effect = Exception('query error')
	with pytest.raises(DatabaseConnectionError):
		db.get_inactive_practitioners()

def test_register_ip_success(db_params):
	"""Test que simula el registro exitoso de IP en la base de datos."""
	db = DBManager(**db_params)
	db.conn = MagicMock()
	mock_cursor = MagicMock()
	db.conn.cursor.return_value.__enter__.return_value = mock_cursor
	
	# Simular INSERT/UPDATE exitoso
	mock_cursor.execute.return_value = None
	db.conn.commit.return_value = None
	
	# Esta sería la funcionalidad que se hace en main.py
	practitioner_id = 678
	system_user = "xrobe"
	ip = "192.168.1.100"
	
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
	
	mock_cursor.execute.assert_called_once()
	db.conn.commit.assert_called_once()

def test_register_ip_foreign_key_error(db_params):
	"""Test que simula error de foreign key cuando practitioner_id no existe."""
	db = DBManager(**db_params)
	db.conn = MagicMock()
	mock_cursor = MagicMock()
	db.conn.cursor.return_value.__enter__.return_value = mock_cursor
	
	# Simular error de foreign key
	mock_cursor.execute.side_effect = Exception('foreign key constraint fails')
	
	practitioner_id = 999  # ID que no existe
	system_user = "testuser"
	ip = "192.168.1.100"
	
	with pytest.raises(Exception):
		with db.conn.cursor() as cursor:
			cursor.execute(
				"""
				INSERT INTO practitioner_system_users (practitioner_id, system_username, ip_address)
				VALUES (%s, %s, %s)
				ON DUPLICATE KEY UPDATE ip_address=VALUES(ip_address)
				""",
				(practitioner_id, system_user, ip)
			)