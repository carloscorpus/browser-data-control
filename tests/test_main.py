import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import pytest
from unittest.mock import patch, MagicMock

def test_main_integration_success():
    """Test de integración básico cuando todo funciona correctamente."""
    with patch('core.config_loader.load_config') as mock_config, \
         patch('core.db_manager.DBManager') as mock_db_class, \
         patch('core.logger.setup_logging') as mock_logger, \
         patch('core.ip_utils.get_public_ip', return_value='192.168.1.100'), \
         patch('builtins.input', return_value='678'), \
         patch('os.getenv', return_value='testuser'), \
         patch('core.scheduler.TaskScheduler') as mock_scheduler_class:
        
        # Configurar mocks básicos
        mock_log = MagicMock()
        mock_logger.return_value = mock_log
        
        mock_config_obj = MagicMock()
        mock_config.return_value = mock_config_obj
        
        mock_db = MagicMock()
        mock_db.conn = None  
        mock_db_class.return_value = mock_db
        
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        # Simular conexión exitosa
        def mock_connect():
            mock_db.conn = MagicMock()
            mock_cursor = MagicMock()
            mock_db.conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        mock_db.connect.side_effect = mock_connect
        
        # Importar y ejecutar main
        import main
        main.main()
        
        # Verificaciones básicas
        assert mock_log.info.called  # Se ejecutó el logging
        assert mock_scheduler.start.called  # Se inició el scheduler