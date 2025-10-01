import sys
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import pytest
from unittest.mock import MagicMock, patch
from core.scheduler import TaskScheduler

@pytest.fixture
def fake_logger():
	return MagicMock()

def test_add_cron_job(fake_logger):
	scheduler = TaskScheduler(fake_logger)
	with patch('core.scheduler.CronTrigger') as mock_cron, \
		 patch.object(scheduler.scheduler, 'add_job') as mock_add_job:
		func = lambda: None
		scheduler.add_cron_job(func, 'mon', 10, 30)
		mock_cron.assert_called_once_with(day_of_week='mon', hour=10, minute=30)
		mock_add_job.assert_called_once()
		fake_logger.info.assert_called()

def test_start_and_shutdown(fake_logger):
	scheduler = TaskScheduler(fake_logger)
	with patch.object(scheduler.scheduler, 'start') as mock_start, \
		 patch('time.sleep', side_effect=KeyboardInterrupt), \
		 patch.object(scheduler.scheduler, 'shutdown') as mock_shutdown:
		scheduler.start()
		mock_start.assert_called_once()
		mock_shutdown.assert_called_once()
		fake_logger.info.assert_any_call('Scheduler detenido.')
