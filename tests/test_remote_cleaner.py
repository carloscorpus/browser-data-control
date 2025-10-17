# tests/test_remote_cleaner.py
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from src.core.remote_cleaner import RemoteCleaner
from src.core.exceptions import CleanerError

class TestRemoteCleaner:
    """Tests para RemoteCleaner"""
    
    @pytest.fixture
    def mock_config(self):
        """Configuración mock para tests"""
        config = Mock()
        config.cleaner.mode = "profile"
        return config
    
    @pytest.fixture
    def remote_cleaner(self, mock_config):
        """Instancia de RemoteCleaner para tests"""
        return RemoteCleaner(mock_config)
    
    def test_clean_user_chromium_no_systems(self, remote_cleaner):
        """Test cuando no hay sistemas registrados"""
        result = remote_cleaner.clean_user_chromium(123, [])
        
        assert result['success'] is False
        assert result['practitioner_id'] == 123
        assert result['total_systems'] == 0
        assert 'No hay sistemas registrados' in result['errors'][0]
    
    def test_clean_user_chromium_no_ip(self, remote_cleaner):
        """Test cuando sistema no tiene IP registrada"""
        system_users = [{
            'system_username': 'test_user',
            'ip_address': None
        }]
        
        result = remote_cleaner.clean_user_chromium(123, system_users)
        
        assert result['success'] is False
        assert len(result['failed_systems']) == 1
        assert 'Sin IP registrada' in result['failed_systems'][0]['error']
    
    @patch('requests.post')
    def test_http_clean_success(self, mock_post, remote_cleaner):
        """Test limpieza HTTP exitosa"""
        # Mock respuesta exitosa
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True, 'profiles_cleaned': 2}
        mock_post.return_value = mock_response
        
        system_users = [{
            'system_username': 'test_user',
            'ip_address': '192.168.1.100'
        }]
        
        result = remote_cleaner.clean_user_chromium(123, system_users)
        
        assert result['success'] is True
        assert len(result['cleaned_systems']) == 1
        assert result['cleaned_systems'][0]['ip_address'] == '192.168.1.100'
    
    @patch('requests.post')
    def test_http_clean_failure(self, mock_post, remote_cleaner):
        """Test fallo en limpieza HTTP"""
        # Mock respuesta de error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        system_users = [{
            'system_username': 'test_user',
            'ip_address': '192.168.1.100'
        }]
        
        # Mock TCP también falla para forzar simulación
        with patch('socket.socket') as mock_socket:
            mock_socket.return_value.connect.side_effect = ConnectionRefusedError()
            
            result = remote_cleaner.clean_user_chromium(123, system_users)
            
            # Debería fallar HTTP y TCP, pero éxito en simulación
            assert result['success'] is True  # Simulación exitosa
            assert len(result['cleaned_systems']) == 1
    
    @patch('socket.socket')
    def test_tcp_clean_success(self, mock_socket, remote_cleaner):
        """Test limpieza TCP exitosa"""
        # Mock socket TCP
        mock_sock = Mock()
        mock_socket.return_value = mock_sock
        mock_sock.recv.side_effect = [
            (4).to_bytes(4, byteorder='big'),  # Tamaño respuesta
            b'{"success": true, "profiles_cleaned": 1}'  # Respuesta JSON
        ]
        
        # Mock HTTP falla para forzar TCP
        with patch('requests.post', side_effect=ConnectionError()):
            system_users = [{
                'system_username': 'test_user',
                'ip_address': '192.168.1.100'
            }]
            
            result = remote_cleaner.clean_user_chromium(123, system_users)
            
            assert result['success'] is True
            assert len(result['cleaned_systems']) == 1
    
    @patch('requests.get')
    def test_check_client_status_online(self, mock_get, remote_cleaner):
        """Test verificación de cliente online"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'online', 'version': '1.0'}
        mock_get.return_value = mock_response
        
        result = remote_cleaner.check_client_status('192.168.1.100')
        
        assert result['online'] is True
        assert result['method'] == 'HTTP'
        assert result['response']['status'] == 'online'
    
    def test_simulate_clean(self, remote_cleaner):
        """Test simulación de limpieza"""
        result = remote_cleaner._simulate_clean('192.168.1.100', 'test_user', 123)
        
        assert result['success'] is True
        assert result['method'] == 'SIMULATION'
        assert 'profiles_cleaned' in result['response']
    
    def test_get_timestamp(self, remote_cleaner):
        """Test generación de timestamp"""
        timestamp = remote_cleaner._get_timestamp()
        
        assert isinstance(timestamp, str)
        assert 'T' in timestamp  # Formato ISO
        assert len(timestamp) > 15