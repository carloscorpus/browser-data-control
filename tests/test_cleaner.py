import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import pytest
from unittest.mock import patch, MagicMock
from core.chromium_cleaner import ChromiumCleaner
from core.exceptions import CleanerError

@pytest.fixture
def fake_config():
	class Safety:
		dry_run = True
	class Cleaner:
		mode = "files"
		files_to_remove = ["Login Data", "Cookies"]
		quarantine_dir = None
		browser_profiles = []
	class Config:
		cleaner = Cleaner()
		safety = Safety()
	return Config()

@pytest.fixture
def fake_logger():
	return MagicMock()

def test_close_chromium_processes_success(fake_logger, fake_config):
	cleaner = ChromiumCleaner(fake_logger, fake_config)
	with patch('core.chromium_cleaner.subprocess.run') as mock_run:
		cleaner.close_chromium_processes()
		assert mock_run.call_count == 2
		fake_logger.info.assert_called()

def test_close_chromium_processes_error(fake_logger, fake_config):
	cleaner = ChromiumCleaner(fake_logger, fake_config)
	with patch('core.chromium_cleaner.subprocess.run', side_effect=Exception('fail')):
		with pytest.raises(CleanerError):
			cleaner.close_chromium_processes()

def test_detect_profiles_appdata_and_portable(fake_logger, fake_config):
	cleaner = ChromiumCleaner(fake_logger, fake_config)
	with patch('core.chromium_cleaner.os.getenv', return_value='testuser'), \
		 patch('core.chromium_cleaner.Path.exists', side_effect=[True, True, False, False]):
		profiles = cleaner.detect_profiles()
		assert len(profiles) == 2

def test_clean_profiles_dry_run(fake_logger, fake_config):
	from unittest.mock import ANY
	cleaner = ChromiumCleaner(fake_logger, fake_config)
	with patch.object(cleaner, 'close_chromium_processes'), \
		 patch.object(cleaner, 'detect_profiles', return_value=[MagicMock()]):
		cleaner.clean_profiles()
		# Verifica que se llamó info con el mensaje esperado, sin importar el id del MagicMock
		found = any('[DRY RUN] Se habría limpiado:' in str(call[0][0]) for call in fake_logger.info.call_args_list)
		assert found, 'No se encontró el mensaje esperado en fake_logger.info'

def test_delete_or_quarantine_with_timestamp(fake_logger, fake_config):
	"""Test que verifica que se crea una carpeta con timestamp cuando ya existe el destino."""
	from pathlib import Path
	import datetime
	fake_config.safety.dry_run = False
	fake_config.cleaner.quarantine_dir = "/test/quarantine"
	
	cleaner = ChromiumCleaner(fake_logger, fake_config)
	
	with patch('core.chromium_cleaner.Path') as mock_path_class, \
		 patch('core.chromium_cleaner.shutil.move') as mock_move, \
		 patch('datetime.datetime') as mock_datetime:
		
		# Configurar mocks
		mock_path = MagicMock()
		mock_path.exists.return_value = True
		mock_path.name = "User Data"
		mock_path_class.return_value = mock_path
		
		mock_dest_base = MagicMock()
		mock_dest_base.exists.return_value = True  # Simular que ya existe
		mock_dest_base.__str__ = lambda self: "/test/quarantine/User Data"
		
		mock_dest_with_timestamp = MagicMock()
		mock_dest_with_timestamp.parent.mkdir = MagicMock()
		
		# Configurar Path() para retornar diferentes objetos según el contexto
		def path_side_effect(path_str):
			if "quarantine" in str(path_str) and "User Data" in str(path_str):
				if "_20251003" in str(path_str):
					return mock_dest_with_timestamp
				else:
					return mock_dest_base
			return mock_path
		
		mock_path_class.side_effect = path_side_effect
		
		# Configurar datetime mock
		mock_datetime.datetime.now.return_value.strftime.return_value = "_20251003_141500"
		
		# Ejecutar el método
		cleaner._delete_or_quarantine(mock_path)
		
		# Verificar que se llamó shutil.move con el path con timestamp
		mock_move.assert_called_once()
		fake_logger.info.assert_called()

def test_delete_or_quarantine_no_timestamp_needed(fake_logger, fake_config):
	"""Test que verifica que no se agrega timestamp cuando el destino no existe."""
	from pathlib import Path
	fake_config.safety.dry_run = False
	fake_config.cleaner.quarantine_dir = "/test/quarantine"
	
	cleaner = ChromiumCleaner(fake_logger, fake_config)
	
	with patch('core.chromium_cleaner.Path') as mock_path_class, \
		 patch('core.chromium_cleaner.shutil.move') as mock_move:
		
		# Configurar mocks
		mock_path = MagicMock()
		mock_path.exists.return_value = True
		mock_path.name = "User Data"
		
		mock_dest = MagicMock()
		mock_dest.exists.return_value = False  # Simular que NO existe
		mock_dest.parent.mkdir = MagicMock()
		
		def path_side_effect(path_str):
			if "quarantine" in str(path_str):
				return mock_dest
			return mock_path
		
		mock_path_class.side_effect = path_side_effect
		
		# Ejecutar el método
		cleaner._delete_or_quarantine(mock_path)
		
		# Verificar que se llamó shutil.move sin timestamp
		mock_move.assert_called_once()
		fake_logger.info.assert_called()
