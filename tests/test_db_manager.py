import pytest
from unittest.mock import Mock, patch, MagicMock, ANY
from core.db_manager import DBManager
from core.exceptions import DatabaseConnectionError

class TestDBManager:
    
    @pytest.fixture
    def db_manager(self):
        """Fixture que crea un DBManager para testing"""
        return DBManager(
            host="127.0.0.1",
            port=3306,
            user="root",
            password="",
            database="test-bot-devconsulting"
        )
    
    @patch('core.db_manager.pymysql.connect')
    def test_successful_connection(self, mock_connect, db_manager):
        """Test conexión exitosa a la base de datos"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        db_manager.connect()
        
        mock_connect.assert_called_once()
        assert db_manager.conn == mock_conn
    
    @patch('core.db_manager.pymysql.connect')
    def test_connection_failure(self, mock_connect, db_manager):
        """Test fallo en conexión a la base de datos"""
        mock_connect.side_effect = Exception("Connection failed")
        
        with pytest.raises((DatabaseConnectionError, Exception)):
            db_manager.connect()
    
    def test_get_inactive_practitioners_success(self, db_manager):
        """Test obtener practitioners inactivos exitosamente"""
        mock_conn = Mock()
        mock_cursor = MagicMock()
        
        # Configurar el context manager del cursor
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.__exit__.return_value = None
        
        # Mock de resultados como dict (lo que espera tu DBManager)
        mock_cursor.fetchall.return_value = [
            {"practitioner_id": 428, "practitioner_status": "I"},
            {"practitioner_id": 663, "practitioner_status": "I"},
            {"practitioner_id": 678, "practitioner_status": "I"}
        ]
        
        db_manager.conn = mock_conn
        
        result = db_manager.get_inactive_practitioners()
        
        # Esperamos tuples como resultado final
        expected = [(428, "I"), (663, "I"), (678, "I")]
        assert result == expected
        mock_cursor.execute.assert_called_once()
    
    def test_get_inactive_for_user_success(self, db_manager):
        """Test obtener practitioners inactivos para usuario específico"""
        mock_conn = Mock()
        mock_cursor = MagicMock()
        
        # Configurar el context manager del cursor
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.__exit__.return_value = None
        
        # Resultado como tu setup real con xrobe
        mock_cursor.fetchall.return_value = [
            {
                "practitioner_id": 678, 
                "practitioner_status": "I", 
                "system_username": "xrobe"
            }
        ]
        
        db_manager.conn = mock_conn
        
        result = db_manager.get_inactive_for_user("xrobe")
        
        assert len(result) == 1
        assert result[0]["practitioner_id"] == 678
        assert result[0]["system_username"] == "xrobe"
        
        # Verificar que se ejecutó con el parámetro correcto
        mock_cursor.execute.assert_called_with(
            ANY,  # El query SQL
            ("xrobe",)  # Los parámetros
        )
    
    def test_get_inactive_for_user_no_results(self, db_manager):
        """Test usuario activo o no registrado"""
        mock_conn = Mock()
        mock_cursor = MagicMock()
        
        # Configurar el context manager del cursor
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.__exit__.return_value = None
        
        mock_cursor.fetchall.return_value = []
        
        db_manager.conn = mock_conn
        
        result = db_manager.get_inactive_for_user("usuario_activo")
        
        assert result == []
    
    def test_database_connection_params(self, db_manager):
        """Test que los parámetros de conexión son correctos"""
        assert db_manager.host == "127.0.0.1"
        assert db_manager.port == 3306
        assert db_manager.user == "root"
        assert db_manager.password == ""
        assert db_manager.database == "test-bot-devconsulting"
    
    @patch('core.db_manager.pymysql.connect')
    def test_connection_with_real_params(self, mock_connect, db_manager):
        """Test que la conexión usa los parámetros correctos"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        db_manager.connect()
        
        # ✅ Incluir todos los parámetros que realmente usa tu DBManager
        mock_connect.assert_called_once_with(
            host="127.0.0.1",
            port=3306,
            user="root",
            password="",
            database="test-bot-devconsulting",
            charset='utf8mb4',  # ← Agregar este parámetro que faltaba
            cursorclass=ANY  # pymysql.cursors.DictCursor
        )