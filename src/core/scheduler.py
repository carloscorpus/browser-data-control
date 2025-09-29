from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import time

class TaskScheduler:
    def __init__(self, logger):
        self.logger = logger
        self.scheduler = BackgroundScheduler()

    def add_cron_job(self, func, day_of_week: str, hour: int, minute: int):
        trigger = CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)
        self.scheduler.add_job(func, trigger)
        self.logger.info(f"Tarea programada: {day_of_week} {hour}:{minute:02d}")

    def start(self):
        self.scheduler.start()
        self.logger.info("Scheduler iniciado. Esperando ejecuciones...")
        try:
            while True:
                time.sleep(60)  # mantener vivo el proceso
        except (KeyboardInterrupt, SystemExit):
            self.scheduler.shutdown()
            self.logger.info("Scheduler detenido.")
