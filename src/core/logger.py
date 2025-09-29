import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_file: str = "logs/browser-data-control.log", level: str = "INFO"):
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("browser_data_control")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not logger.handlers:
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")

        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        logger.addHandler(ch)

        fh = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger
