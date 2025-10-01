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