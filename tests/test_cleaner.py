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
