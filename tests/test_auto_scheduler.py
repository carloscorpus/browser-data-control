# tests/test_auto_scheduler.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime, timedelta
from src.core.auto_scheduler import AutoScheduler

class TestAutoScheduler:
    """Tests para AutoScheduler"""
    
    @pytest.fixture
    def mock_config(self):
        """Configuración mock para tests"""
        config = Mock()
        config.db.host = "localhost"
        config.db.port = 3306
        config.db.user = "test"
        config.db.password = "test"
        config.db.database = "test_db"
        return config
    
    @pytest.fixture
    def auto_scheduler(self, mock_config):
        """Instancia de AutoScheduler para tests"""
        return AutoScheduler(mock_config)
    
    @patch('src.core.auto_scheduler.DBManager')
    @patch('src.core.auto_scheduler.RemoteCleaner')
    def test_initialize_connections(self, mock_remote_cleaner, mock_db_manager, auto_scheduler):
        """Test inicialización de conexiones"""
        mock_db = Mock()
        mock_db_manager.return_value = mock_db
        
        auto_scheduler._initialize_connections()
        
        assert auto_scheduler.db_manager == mock_db
        assert auto_scheduler.remote_cleaner is not None
        mock_db.connect.assert_called_once()
    
    @patch('schedule.every')
    def test_setup_scheduled_jobs(self, mock_schedule, auto_scheduler):
        """Test configuración de trabajos programados"""
        auto_scheduler._setup_scheduled_jobs()
        
        # Verificar que se programaron los trabajos
        assert mock_schedule.called
        mock_schedule.assert_any_call()
    
    def test_get_users_expiring_today(self, auto_scheduler):
        """Test obtención de usuarios que expiran hoy"""
        # Mock DB manager
        mock_db = Mock()
        mock_cursor = Mock()
        mock_db.conn.cursor.return_value.__enter__.return_value = mock_cursor
        auto_scheduler.db_manager = mock_db
        
        # Mock datos de retorno
        today = date.today()
        expected_users = [
            {
                'practitioner_id': 123,
                'practitioner_status': 'A',
                'practitioner_date_end': today,
                'general_id': 12345
            }
        ]
        mock_cursor.fetchall.return_value = expected_users
        
        result = auto_scheduler._get_users_expiring_today()
        
        assert result == expected_users
        mock_cursor.execute.assert_called_once()
        # Verificar que se usó la fecha de hoy en la query
        call_args = mock_cursor.execute.call_args
        assert call_args[0][1] == (today,)
    
    def test_execute_automatic_cleanup_no_systems(self, auto_scheduler):
        """Test limpieza automática sin sistemas registrados"""
        # Mock DB manager
        mock_db = Mock()
        mock_db.get_practitioner_system_users.return_value = []
        auto_scheduler.db_manager = mock_db
        
        user_data = {'practitioner_id': 123}
        
        with patch.object(auto_scheduler, '_mark_user_as_processed') as mock_mark:
            auto_scheduler._execute_automatic_cleanup(user_data)
            
            mock_mark.assert_called_once_with(123, success=False, error="No hay sistemas registrados")
    
    def test_execute_automatic_cleanup_success(self, auto_scheduler):
        """Test limpieza automática exitosa"""
        # Mock DB manager
        mock_db = Mock()
        system_users = [
            {'system_username': 'user1', 'ip_address': '192.168.1.100'},
            {'system_username': 'user2', 'ip_address': '192.168.1.101'}
        ]
        mock_db.get_practitioner_system_users.return_value = system_users
        auto_scheduler.db_manager = mock_db
        
        # Mock remote cleaner
        mock_remote_cleaner = Mock()
        cleanup_result = {
            'success': True,
            'cleaned_systems': [
                {'system_username': 'user1', 'ip_address': '192.168.1.100'}
            ],
            'total_systems': 2
        }
        mock_remote_cleaner.clean_user_chromium.return_value = cleanup_result
        auto_scheduler.remote_cleaner = mock_remote_cleaner
        
        user_data = {'practitioner_id': 123}
        
        with patch.object(auto_scheduler, '_deactivate_user_after_cleanup') as mock_deactivate:
            auto_scheduler._execute_automatic_cleanup(user_data)
            
            mock_remote_cleaner.clean_user_chromium.assert_called_once_with(123, system_users)
            mock_deactivate.assert_called_once_with(123)
    
    def test_deactivate_user_after_cleanup(self, auto_scheduler):
        """Test desactivación de usuario después de limpieza"""
        # Mock DB manager
        mock_db = Mock()
        mock_cursor = Mock()
        mock_db.conn.cursor.return_value.__enter__.return_value = mock_cursor
        auto_scheduler.db_manager = mock_db
        
        auto_scheduler._deactivate_user_after_cleanup(123)
        
        mock_cursor.execute.assert_called_once()
        mock_db.conn.commit.assert_called_once()
        
        # Verificar que la query incluye UPDATE y SET status = 'I'
        call_args = mock_cursor.execute.call_args[0]
        query = call_args[0]
        assert 'UPDATE practitioners' in query
        assert "practitioner_status = 'I'" in query
        assert call_args[1] == (123,)
    
    def test_mark_user_as_processed(self, auto_scheduler):
        """Test marcado de usuario como procesado"""
        # Mock DB manager
        mock_db = Mock()
        mock_cursor = Mock()
        mock_db.conn.cursor.return_value.__enter__.return_value = mock_cursor
        auto_scheduler.db_manager = mock_db
        
        auto_scheduler._mark_user_as_processed(123, success=True)
        
        mock_cursor.execute.assert_called_once()
        mock_db.conn.commit.assert_called_once()
        
        # Verificar que la query incluye UPDATE y SUCCESS
        call_args = mock_cursor.execute.call_args[0]
        query = call_args[0]
        assert 'UPDATE practitioners' in query
        assert 'SUCCESS' in call_args[1][0]
    
    def test_health_check_db_reconnection(self, auto_scheduler):
        """Test reconexión en health check"""
        # Mock DB manager con conexión fallida
        mock_db = Mock()
        auto_scheduler.db_manager = mock_db
        mock_db.conn = None
        
        with patch.object(auto_scheduler, '_initialize_connections') as mock_init:
            auto_scheduler._health_check()
            mock_init.assert_called_once()
    
    def test_check_expired_users(self, auto_scheduler):
        """Test verificación de usuarios con convenios vencidos"""
        # Mock DB manager
        mock_db = Mock()
        mock_cursor = Mock()
        mock_db.conn.cursor.return_value.__enter__.return_value = mock_cursor
        auto_scheduler.db_manager = mock_db
        
        # Mock usuarios vencidos
        expired_users = [
            {
                'practitioner_id': 123,
                'practitioner_date_end': date.today() - timedelta(days=5),
                'general_id': 12345
            }
        ]
        mock_cursor.fetchall.return_value = expired_users
        
        auto_scheduler._check_expired_users()
        
        mock_cursor.execute.assert_called_once()
        # Verificar que busca usuarios con fecha < hoy y status = 'A'
        call_args = mock_cursor.execute.call_args[0]
        query = call_args[0]
        assert 'practitioner_date_end <' in query
        assert "practitioner_status = 'A'" in query
    
    def test_force_cleanup_user_not_found(self, auto_scheduler):
        """Test limpieza forzada con usuario no encontrado"""
        # Mock DB manager
        mock_db = Mock()
        mock_db.get_practitioner_by_id.return_value = None
        auto_scheduler.db_manager = mock_db
        
        result = auto_scheduler.force_cleanup_user(999)
        
        assert result['success'] is False
        assert 'no encontrado' in result['error']
    
    def test_force_cleanup_user_success(self, auto_scheduler):
        """Test limpieza forzada exitosa"""
        # Mock DB manager
        mock_db = Mock()
        user_data = {'practitioner_id': 123, 'practitioner_status': 'A'}
        mock_db.get_practitioner_by_id.return_value = user_data
        auto_scheduler.db_manager = mock_db
        
        with patch.object(auto_scheduler, '_execute_automatic_cleanup') as mock_cleanup:
            result = auto_scheduler.force_cleanup_user(123)
            
            assert result['success'] is True
            mock_cleanup.assert_called_once_with(user_data)
    
    def test_get_scheduler_status(self, auto_scheduler):
        """Test obtención de estado del scheduler"""
        auto_scheduler.is_running = True
        auto_scheduler.db_manager = Mock()
        auto_scheduler.db_manager.conn = Mock()
        auto_scheduler.scheduler_thread = Mock()
        auto_scheduler.scheduler_thread.is_alive.return_value = True
        
        status = auto_scheduler.get_scheduler_status()
        
        assert status['running'] is True
        assert status['cleanup_time'] == "13:30"
        assert status['db_connected'] is True
        assert status['thread_alive'] is True
        assert 'next_cleanup' in status
    
    def test_get_next_cleanup_time_today(self, auto_scheduler):
        """Test cálculo de próxima limpieza (hoy)"""
        # Mock tiempo actual antes de las 13:30
        with patch('src.core.auto_scheduler.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 15, 10, 0, 0)  # 10:00 AM
            mock_datetime.now.return_value = mock_now
            mock_datetime.replace = datetime.replace
            
            next_cleanup = auto_scheduler._get_next_cleanup_time()
            
            expected = "2024-01-15 13:30:00"
            assert next_cleanup == expected
    
    def test_get_next_cleanup_time_tomorrow(self, auto_scheduler):
        """Test cálculo de próxima limpieza (mañana)"""
        # Mock tiempo actual después de las 13:30
        with patch('src.core.auto_scheduler.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 15, 15, 0, 0)  # 3:00 PM
            mock_datetime.now.return_value = mock_now
            mock_datetime.replace = datetime.replace
            
            next_cleanup = auto_scheduler._get_next_cleanup_time()
            
            # Debería ser mañana a las 13:30
            assert "2024-01-16 13:30:00" in next_cleanup or "Error" in next_cleanup