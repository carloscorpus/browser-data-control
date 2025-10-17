# tests/test_integration.py
import pytest
from unittest.mock import Mock, patch
from src.core.db_manager import DBManager
from src.admin_app.src.services.db_service import SecureDBService

class TestIntegration:
    """Tests de integración para funcionalidades MVP"""
    
    def test_db_manager_register_ip_integration(self):
        """Test integración del registro de IP en DB Manager"""
        # Mock conexión a BD
        with patch('pymysql.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            
            # Mock respuestas de BD
            mock_cursor.fetchone.side_effect = [
                {'practitioner_id': 123},  # Usuario existe
                None  # No existe en system_users
            ]
            
            db_manager = DBManager("host", 3306, "user", "pass", "db")
            db_manager.conn = mock_conn
            
            result = db_manager.register_ip(123, "192.168.1.100", "test_user")
            
            assert result is True
            # Verificar que se ejecutaron las queries correctas
            assert mock_cursor.execute.call_count >= 2
    
    def test_secure_db_service_integration(self):
        """Test integración del servicio seguro de BD"""
        with patch('src.admin_app.src.services.db_service.DBManager') as mock_db_manager:
            mock_db = Mock()
            mock_db_manager.return_value = mock_db
            mock_db.connect.return_value = None
            
            # Mock verificación de permisos
            mock_cursor = Mock()
            mock_db.conn.cursor.return_value = mock_cursor
            mock_cursor.fetchone.return_value = [1]
            
            service = SecureDBService()
            success, error = service.connect("host", 3306, "user", "pass", "db")
            
            assert success is True
            assert error is None
            assert service.db_manager is not None
    
    @patch('src.core.remote_cleaner.requests.post')
    def test_remote_cleaning_workflow(self, mock_post):
        """Test workflow completo de limpieza remota"""
        from src.core.remote_cleaner import RemoteCleaner
        
        # Mock respuesta exitosa
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'profiles_cleaned': 2,
            'files_removed': 15
        }
        mock_post.return_value = mock_response
        
        # Mock config
        config = Mock()
        config.cleaner.mode = "profile"
        
        cleaner = RemoteCleaner(config)
        
        system_users = [
            {
                'system_username': 'colaborador1',
                'ip_address': '192.168.1.100'
            },
            {
                'system_username': 'colaborador2',
                'ip_address': '192.168.1.101'
            }
        ]
        
        result = cleaner.clean_user_chromium(123, system_users)
        
        # Verificar resultado exitoso
        assert result['success'] is True
        assert result['practitioner_id'] == 123
        assert len(result['cleaned_systems']) == 2
        assert result['total_systems'] == 2
        
        # Verificar que se hicieron las llamadas HTTP correctas
        assert mock_post.call_count == 2
        
        # Verificar payload de las llamadas
        for call in mock_post.call_args_list:
            payload = call[1]['json']
            assert payload['practitioner_id'] == 123
            assert payload['action'] == 'clean_chromium'
            assert payload['mode'] == 'profile'
    
    def test_exe_generation_workflow(self):
        """Test workflow completo de generación de EXE"""
        from src.core.exe_generator import EXEGenerator
        
        # Mock config
        config = Mock()
        config.db.host = "sql.freedb.tech"
        config.db.port = 3306
        config.db.database = "test_db"
        config.db.user = "test_user"
        config.db.password = "test_pass"
        config.cleaner.files_to_remove = ["Login Data", "Cookies"]
        
        with patch('src.core.exe_generator.EXEGenerator._check_pyinstaller', return_value=False):
            generator = EXEGenerator(config)
        
        user_data = {
            'practitioner_id': 123,
            'general_id': 12345,
            'practitioner_status': 'A',
            'practitioner_date_start': '2024-01-01'
        }
        
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', create=True):
            
            result = generator.generate_custom_exe(
                practitioner_id=123,
                agreement_end_date='2024-12-31',
                clean_mode='profile',
                user_data=user_data
            )
        
        # Verificar que el EXE se "generó" correctamente
        assert result['success'] is True
        assert result['config']['practitioner_id'] == 123
        assert result['config']['agreement_end_date'] == '2024-12-31'
        assert result['config']['clean_mode'] == 'profile'
        
        # Verificar configuración específica del cliente
        client_config = result['config']
        assert client_config['database']['host'] == 'sql.freedb.tech'
        assert client_config['scheduler']['cleanup_time'] == '13:30'
        assert client_config['heartbeat']['server_port'] == 8765
    
    def test_automatic_scheduling_workflow(self):
        """Test workflow completo de programación automática"""
        from src.core.auto_scheduler import AutoScheduler
        from datetime import date
        
        # Mock config
        config = Mock()
        config.db.host = "localhost"
        config.db.port = 3306
        config.db.user = "test"
        config.db.password = "test"
        config.db.database = "test_db"
        
        scheduler = AutoScheduler(config)
        
        # Mock DB manager
        mock_db = Mock()
        mock_cursor = Mock()
        mock_db.conn.cursor.return_value.__enter__.return_value = mock_cursor
        scheduler.db_manager = mock_db
        
        # Mock usuarios que expiran hoy
        today = date.today()
        expiring_users = [
            {
                'practitioner_id': 123,
                'practitioner_status': 'A',
                'practitioner_date_end': today,
                'general_id': 12345
            }
        ]
        mock_cursor.fetchall.return_value = expiring_users
        
        # Mock remote cleaner
        mock_remote_cleaner = Mock()
        cleanup_result = {
            'success': True,
            'cleaned_systems': [{'system_username': 'user1'}],
            'total_systems': 1
        }
        mock_remote_cleaner.clean_user_chromium.return_value = cleanup_result
        scheduler.remote_cleaner = mock_remote_cleaner
        
        # Mock system users
        system_users = [{'system_username': 'user1', 'ip_address': '192.168.1.100'}]
        mock_db.get_practitioner_system_users.return_value = system_users
        
        # Ejecutar verificación diaria
        with patch.object(scheduler, '_deactivate_user_after_cleanup') as mock_deactivate:
            scheduler._daily_cleanup_check()
            
            # Verificar que se ejecutó la limpieza
            mock_remote_cleaner.clean_user_chromium.assert_called_once_with(123, system_users)
            
            # Verificar que se desactivó el usuario
            mock_deactivate.assert_called_once_with(123)
    
    def test_full_mvp_workflow(self):
        """Test del workflow completo del MVP"""
        # Simular el flujo completo:
        # 1. Admin selecciona usuario
        # 2. Genera EXE personalizado
        # 3. Usuario ejecuta EXE y se registra en BD
        # 4. Al vencer convenio, se ejecuta limpieza automática
        
        # 1. Mock datos del usuario seleccionado
        selected_user = {
            'practitioner_id': 123,
            'general_id': 12345,
            'practitioner_status': 'A',
            'practitioner_date_start': '2024-01-01',
            'practitioner_date_end': '2024-12-31'
        }
        
        # 2. Generar EXE personalizado
        from src.core.exe_generator import EXEGenerator
        
        config = Mock()
        config.db.host = "sql.freedb.tech"
        config.db.port = 3306
        config.db.database = "freedb_test-bot-devconsulting"
        config.db.user = "freedb_practitioners"
        config.db.password = "eeg93*TtDH&qK!P"
        config.cleaner.files_to_remove = ["Login Data", "Cookies", "Web Data"]
        
        with patch('src.core.exe_generator.EXEGenerator._check_pyinstaller', return_value=False):
            generator = EXEGenerator(config)
        
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', create=True):
            
            exe_result = generator.generate_custom_exe(
                practitioner_id=123,
                agreement_end_date='2024-12-31',
                clean_mode='profile',
                user_data=selected_user
            )
        
        assert exe_result['success'] is True
        
        # 3. Simular registro en BD cuando usuario ejecuta EXE
        with patch('pymysql.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            
            # Mock usuario existe
            mock_cursor.fetchone.side_effect = [
                {'practitioner_id': 123},  # Usuario existe
                None  # No existe en system_users
            ]
            
            db_manager = DBManager("host", 3306, "user", "pass", "db")
            db_manager.conn = mock_conn
            
            register_result = db_manager.register_ip(123, "192.168.1.100", "colaborador")
            assert register_result is True
        
        # 4. Simular limpieza automática al vencer convenio
        from src.core.auto_scheduler import AutoScheduler
        from src.core.remote_cleaner import RemoteCleaner
        
        scheduler = AutoScheduler(config)
        
        # Mock remote cleaner exitoso
        with patch('src.core.remote_cleaner.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'success': True, 'profiles_cleaned': 1}
            mock_post.return_value = mock_response
            
            remote_cleaner = RemoteCleaner(config)
            system_users = [{'system_username': 'colaborador', 'ip_address': '192.168.1.100'}]
            
            cleanup_result = remote_cleaner.clean_user_chromium(123, system_users)
            
            assert cleanup_result['success'] is True
            assert len(cleanup_result['cleaned_systems']) == 1
        
        # Verificar que todo el workflow funcionó
        assert exe_result['success'] is True
        assert register_result is True
        assert cleanup_result['success'] is True