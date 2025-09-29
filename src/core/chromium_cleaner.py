# src/core/chromium_cleaner.py
import os
import shutil
import subprocess
from pathlib import Path
from typing import List
from .exceptions import CleanerError


class ChromiumCleaner:
    def __init__(self, logger, config):
        self.logger = logger
        self.cfg = config.cleaner
        self.safety = config.safety

    def close_chromium_processes(self):
        """Intenta cerrar Chromium si está abierto."""
        try:
            subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], capture_output=True)
            subprocess.run(["taskkill", "/F", "/IM", "chromium.exe"], capture_output=True)
            self.logger.info("Procesos de Chromium finalizados (si estaban abiertos).")
        except Exception as e:
            raise CleanerError(f"Error cerrando Chromium: {e}")

    def detect_profiles(self) -> List[Path]:
        """Detecta rutas de perfiles Chromium (AppData + portable)."""
        user = os.getenv("USERNAME") or "default"
        profiles = []

        # AppData
        appdata = Path(f"C:/Users/{user}/AppData/Local/Chromium/User Data")
        if appdata.exists():
            profiles.append(appdata)

        # Portable (carpeta donde se ejecute el programa)
        portable = Path(__file__).resolve().parent.parent / "User Data"
        if portable.exists():
            profiles.append(portable)

        # Config extra (browser_profiles en config.json)
        for p in self.cfg.browser_profiles:
            path = Path(p)
            if path.exists():
                profiles.append(path)

        return profiles

    def clean_profiles(self):
        """Ejecuta limpieza de perfiles Chromium según configuración."""
        self.close_chromium_processes()
        profiles = self.detect_profiles()

        if not profiles:
            self.logger.warning("No se encontraron perfiles de Chromium para limpiar.")
            return

        for profile in profiles:
            if self.safety.dry_run:
                self.logger.info(f"[DRY RUN] Se habría limpiado: {profile}")
                continue

            if self.cfg.mode == "profile":
                self._delete_or_quarantine(profile)

            elif self.cfg.mode == "files":
                for file_name in self.cfg.files_to_remove:
                    target = profile / "Default" / file_name
                    if target.exists():
                        self._delete_or_quarantine(target)
                    else:
                        self.logger.info(f"No se encontró: {target}")

    def _delete_or_quarantine(self, path: Path):
        """Elimina o mueve un archivo/carpeta a cuarentena."""
        if not path.exists():
            self.logger.info(f"No existe: {path}")
            return

        try:
            if self.cfg.quarantine_dir:
                q_dir = Path(self.cfg.quarantine_dir)
                q_dir.mkdir(parents=True, exist_ok=True)
                dest = q_dir / path.name
                shutil.move(str(path), str(dest))
                self.logger.info(f"Movido a cuarentena: {path} -> {dest}")
            else:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                self.logger.info(f"Eliminado: {path}")
        except Exception as e:
            raise CleanerError(f"Error al limpiar {path}: {e}")
