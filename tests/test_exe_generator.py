# tests/test_exe_generator.py
import pytest
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from src.core.exe_generator import EXEGenerator

class TestEXEGenerator:
    """Tests para EXEGenerator"""
    
    @pytest.fixture
    def mock_config(self):
        """Configuración mock para tests"""
        config = Mock()
        config.db.host = "sql.freedb.tech"
        config.db.port = 3306
        config.db.database = "test_db"
        config.db.user = "test_user"
        config.db.password = "test_pass"
        config.cleaner.files_to_remove = ["Login Data", "Cookies"]
        return config
    
    @pytest.fixture
    def exe_generator(self, mock_config):
        """Instancia de EXEGenerator para tests"""
        with patch('src.core.exe_generator.EXEGenerator._check_pyinstaller', return_value=False):
            return EXEGenerator(mock_config)
    
    def test_check_pyinstaller_available(self):
        """Test verificación de PyInstaller disponible"""
        with patch('builtins.__import__', side_effect=lambda name: Mock() if name == 'PyInstaller' else __import__(name)):
            config = Mock()
            generator = EXEGenerator(config)
            assert generator.pyinstaller_available is True
    
    def test_check_pyinstaller_not_available(self):
        """Test verificación de PyInstaller no disponible"""
        with patch('builtins.__import__', side_effect=ImportError("No module named 'PyInstaller'")):
            config = Mock()
            generator = EXEGenerator(config)
            assert generator.pyinstaller_available is False
    
    def test_create_client_config(self, exe_generator):
        """Test creación de configuración del cliente"""
        user_data = {
            'general_id': 12345,
            'practitioner_status': 'A',
            'practitioner_date_start': '2024-01-01'
        }
        
        config = exe_generator._create_client_config(
            practitioner_id=123,
            agreement_end_date='2024-12-31',
            clean_mode='profile',
            user_data=user_data
        )
        
        assert config['practitioner_id'] == 123
        assert config['agreement_end_date'] == '2024-12-31'
        assert config['clean_mode'] == 'profile'
        assert config['user_info']['general_id'] == 12345
        assert config['database']['host'] == 'sql.freedb.tech'
        assert config['scheduler']['cleanup_time'] == '13:30'
        assert 'generated_at' in config
    
    def test_create_client_script(self, exe_generator):
        """Test creación del script del cliente"""
        config = {
            'practitioner_id': 123,
            'generated_at': '2024-01-01T12:00:00',
            'agreement_end_date': '2024-12-31'
        }
        
        script = exe_generator._create_client_script(config)
        
        assert isinstance(script, str)
        assert '# -*- coding: utf-8 -*-' in script
        assert 'Practitioner ID: 123' in script
        assert 'class ChromiumInstaller:' in script
        assert 'class ChromiumCleaner:' in script
        assert 'class DatabaseManager:' in script
        assert 'class ScheduleManager:' in script
        assert 'class HeartbeatServer:' in script
        assert 'def main():' in script
    
    @patch('pathlib.Path.mkdir')
    def test_simulate_exe_generation(self, mock_mkdir, exe_generator):
        """Test simulación de generación de EXE"""
        config = {
            'practitioner_id': 123,
            'agreement_end_date': '2024-12-31',
            'generated_at': '2024-01-01T12:00:00'
        }
        
        exe_path = Path("test_output/test.exe")
        
        with patch('builtins.open', create=True) as mock_open:
            result = exe_generator._simulate_exe_generation(exe_path, config)
        
        assert result['success'] is True
        assert 'test_PLACEHOLDER.txt' in result['exe_path']
        assert 'config_path' in result
        assert result['size_mb'] == 0.0
        assert 'PyInstaller no disponible' in result['note']
    
    def test_generate_custom_exe_simulation(self, exe_generator):
        """Test generación completa de EXE en modo simulación"""
        user_data = {
            'general_id': 12345,
            'practitioner_status': 'A',
            'practitioner_date_start': '2024-01-01'
        }
        
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', create=True):
            
            result = exe_generator.generate_custom_exe(
                practitioner_id=123,
                agreement_end_date='2024-12-31',
                clean_mode='profile',
                user_data=user_data
            )
        
        assert result['success'] is True
        assert result['config']['practitioner_id'] == 123
        assert result['config']['clean_mode'] == 'profile'
        assert 'exe_path' in result
    
    @patch('subprocess.run')
    @patch('tempfile.NamedTemporaryFile')
    @patch('pathlib.Path.stat')
    def test_compile_with_pyinstaller_success(self, mock_stat, mock_temp, mock_subprocess, mock_config):
        """Test compilación exitosa con PyInstaller"""
        # Mock PyInstaller disponible
        with patch('src.core.exe_generator.EXEGenerator._check_pyinstaller', return_value=True):
            generator = EXEGenerator(mock_config)
        
        # Mock archivo temporal
        mock_temp_file = Mock()
        mock_temp_file.name = '/tmp/test_script.py'
        mock_temp.return_value.__enter__.return_value = mock_temp_file
        
        # Mock subprocess exitoso
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Build successful"
        mock_subprocess.return_value = mock_result
        
        # Mock estadísticas del archivo
        mock_stat.return_value.st_size = 5 * 1024 * 1024  # 5 MB
        
        script_content = "print('test')"
        exe_path = Path("output/test.exe")
        config = {'test': 'config'}
        
        with patch('os.unlink'), \
             patch('pathlib.Path.exists', return_value=True):
            
            result = generator._compile_with_pyinstaller(script_content, exe_path, config)
        
        assert result['success'] is True
        assert result['size_mb'] == 5.0
        assert 'compilation_output' in result
    
    @patch('subprocess.run')
    @patch('tempfile.NamedTemporaryFile')
    def test_compile_with_pyinstaller_failure(self, mock_temp, mock_subprocess, mock_config):
        """Test fallo en compilación con PyInstaller"""
        # Mock PyInstaller disponible
        with patch('src.core.exe_generator.EXEGenerator._check_pyinstaller', return_value=True):
            generator = EXEGenerator(mock_config)
        
        # Mock archivo temporal
        mock_temp_file = Mock()
        mock_temp_file.name = '/tmp/test_script.py'
        mock_temp.return_value.__enter__.return_value = mock_temp_file
        
        # Mock subprocess con error
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "PyInstaller error: module not found"
        mock_subprocess.return_value = mock_result
        
        script_content = "print('test')"
        exe_path = Path("output/test.exe")
        config = {'test': 'config'}
        
        with patch('os.unlink'):
            result = generator._compile_with_pyinstaller(script_content, exe_path, config)
        
        assert result['success'] is False
        assert 'PyInstaller error' in result['error']
    
    def test_generate_exe_error_handling(self, exe_generator):
        """Test manejo de errores en generación de EXE"""
        user_data = {
            'general_id': 12345,
            'practitioner_status': 'A'
        }
        
        # Forzar error en creación de directorio
        with patch('pathlib.Path.mkdir', side_effect=OSError("Permission denied")):
            result = exe_generator.generate_custom_exe(
                practitioner_id=123,
                agreement_end_date='2024-12-31',
                clean_mode='profile',
                user_data=user_data
            )
        
        assert result['success'] is False
        assert 'Permission denied' in result['error']