import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import pytest
from unittest.mock import patch, MagicMock, mock_open
import json
from admin_commands import AdminCommands

def test_consultar_inhabilitados_success():
    """Test que verifica la consulta exitosa de usuarios inhabilitados."""
    with patch('admin_commands.load_config') as mock_config, \
         patch('admin_commands.setup_logging') as mock_logger, \
         patch('admin_commands.DBManager') as mock_db_class:
        
        # Configurar mocks
        mock_log = MagicMock()
        mock_logger.return_value = mock_log
        
        mock_config_obj = MagicMock()
        mock_config.return_value = mock_config_obj
        
        mock_db = MagicMock()
        mock_db.conn = None
        mock_db_class.return_value = mock_db
        
        # Simular datos de usuarios inhabilitados
        mock_cursor = MagicMock()
        mock_db.conn = MagicMock()
        mock_db.conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Datos de prueba - deben ser diccionarios como retorna el cursor real
        test_data = [
            {'practitioner_id': 1, 'practitioner_status': 'I'},
            {'practitioner_id': 2, 'practitioner_status': 'I'}
        ]
        mock_cursor.fetchall.return_value = test_data
        
        # Ejecutar
        admin = AdminCommands()
        resultado = admin.consultar_inhabilitados()
        
        # Verificaciones
        assert len(resultado) == 2
        assert resultado[0]['id'] == 1
        assert resultado[0]['status'] == 'I'
        assert resultado[1]['id'] == 2
        assert resultado[1]['status'] == 'I'
        
        mock_cursor.execute.assert_called_once()
        mock_db.close.assert_called_once()

def test_consultar_inhabilitados_empty():
    """Test que verifica el comportamiento cuando no hay usuarios inhabilitados."""
    with patch('admin_commands.load_config') as mock_config, \
         patch('admin_commands.setup_logging') as mock_logger, \
         patch('admin_commands.DBManager') as mock_db_class:
        
        # Configurar mocks
        mock_log = MagicMock()
        mock_logger.return_value = mock_log
        
        mock_config_obj = MagicMock()
        mock_config.return_value = mock_config_obj
        
        mock_db = MagicMock()
        mock_db.conn = None
        mock_db_class.return_value = mock_db
        
        # Simular respuesta vacía
        mock_cursor = MagicMock()
        mock_db.conn = MagicMock()
        mock_db.conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        
        # Ejecutar
        admin = AdminCommands()
        resultado = admin.consultar_inhabilitados()
        
        # Verificaciones
        assert resultado == []
        mock_log.info.assert_called_with("📋 No hay usuarios inhabilitados en el sistema")

def test_eliminar_un_usuario_success():
    """Test que verifica la limpieza exitosa de datos de un usuario."""
    with patch('admin_commands.load_config') as mock_config, \
         patch('admin_commands.setup_logging') as mock_logger, \
         patch('admin_commands.DBManager') as mock_db_class, \
         patch('core.chromium_cleaner.ChromiumCleaner') as mock_cleaner_class, \
         patch('builtins.input', return_value='s'):
        
        # Configurar mocks
        mock_log = MagicMock()
        mock_logger.return_value = mock_log
        
        mock_config_obj = MagicMock()
        mock_config.return_value = mock_config_obj
        
        mock_db = MagicMock()
        mock_db.conn = None
        mock_db_class.return_value = mock_db
        
        # Simular usuario existente
        mock_cursor = MagicMock()
        mock_db.conn = MagicMock()
        mock_db.conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Simular usuario encontrado
        mock_cursor.fetchone.side_effect = [
            {'practitioner_id': 123, 'practitioner_status': 'A'},  # Primera consulta
            {'system_username': 'testuser'}  # Segunda consulta
        ]
        
        # Simular limpieza exitosa
        mock_cleaner = MagicMock()
        mock_cleaner.clean_profiles.return_value = True
        mock_cleaner_class.return_value = mock_cleaner
        
        # Ejecutar
        admin = AdminCommands()
        resultado = admin.eliminar_un_usuario(123)
        
        # Verificaciones
        assert resultado == True
        mock_cleaner.clean_profiles.assert_called_once()
        mock_log.info.assert_called_with("Datos de Chromium del usuario 123 limpiados exitosamente")

def test_eliminar_un_usuario_not_found():
    """Test que verifica el comportamiento cuando el usuario no existe."""
    with patch('admin_commands.load_config') as mock_config, \
         patch('admin_commands.setup_logging') as mock_logger, \
         patch('admin_commands.DBManager') as mock_db_class:
        
        # Configurar mocks
        mock_log = MagicMock()
        mock_logger.return_value = mock_log
        
        mock_config_obj = MagicMock()
        mock_config.return_value = mock_config_obj
        
        mock_db = MagicMock()
        mock_db.conn = None
        mock_db_class.return_value = mock_db
        
        # Simular usuario no encontrado
        mock_cursor = MagicMock()
        mock_db.conn = MagicMock()
        mock_db.conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        # Ejecutar
        admin = AdminCommands()
        resultado = admin.eliminar_un_usuario(999)
        
        # Verificaciones
        assert resultado == False
        mock_log.warning.assert_called_with("Usuario con ID 999 no encontrado")

def test_cambiar_hora_eliminacion_success():
    """Test que verifica el cambio exitoso de hora de eliminación."""
    # Configuración de prueba
    config_original = {
        "scheduler": {
            "cron": {
                "day_of_week": "*",
                "hour": 16,
                "minute": 7
            }
        }
    }
    
    with patch('admin_commands.load_config') as mock_config, \
         patch('admin_commands.setup_logging') as mock_logger, \
         patch('admin_commands.DBManager') as mock_db_class, \
         patch('os.path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=json.dumps(config_original))) as mock_file:
        
        # Configurar mocks
        mock_log = MagicMock()
        mock_logger.return_value = mock_log
        
        mock_config_obj = MagicMock()
        mock_config.return_value = mock_config_obj
        
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        
        # Ejecutar
        admin = AdminCommands()
        resultado = admin.cambiar_hora_eliminacion(hour=20, minute=30)
        
        # Verificaciones
        assert resultado == True
        # Verificar que se intentó escribir el archivo
        mock_file.assert_called()
        mock_log.info.assert_called_with("Configuración de horario actualizada exitosamente")

def test_cambiar_hora_eliminacion_invalid_hour():
    """Test que verifica el manejo de horas inválidas."""
    with patch('admin_commands.load_config') as mock_config, \
         patch('admin_commands.setup_logging') as mock_logger, \
         patch('admin_commands.DBManager') as mock_db_class:
        
        # Configurar mocks
        mock_log = MagicMock()
        mock_logger.return_value = mock_log
        
        mock_config_obj = MagicMock()
        mock_config.return_value = mock_config_obj
        
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        
        # Ejecutar con hora inválida
        admin = AdminCommands()
        resultado = admin.cambiar_hora_eliminacion(hour=25)  # Hora inválida
        
        # Verificaciones
        assert resultado == False