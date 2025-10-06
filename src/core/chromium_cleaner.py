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
            return False

        profiles_cleaned = 0
        total_profiles = len(profiles)

        for profile in profiles:
            try:
                if self.safety.dry_run:
                    self.logger.info(f"[DRY RUN] Se habría limpiado: {profile}")
                    profiles_cleaned += 1
                    continue

                if self.cfg.mode == "profile":
                    self._delete_or_quarantine(profile)
                    profiles_cleaned += 1

                elif self.cfg.mode == "files":
                    files_cleaned = 0
                    for file_name in self.cfg.files_to_remove:
                        target = profile / "Default" / file_name
                        if target.exists():
                            self._delete_or_quarantine(target)
                            files_cleaned += 1
                        else:
                            self.logger.info(f"No se encontró: {target}")
                    
                    if files_cleaned > 0:
                        profiles_cleaned += 1

            except Exception as e:
                self.logger.error(f"Error limpiando perfil {profile}: {e}")
                # Continuamos con el siguiente perfil en lugar de fallar completamente

        # Retornar True si se limpió al menos un perfil exitosamente
        success = profiles_cleaned > 0
        if success:
            self.logger.info(f"Limpieza completada: {profiles_cleaned}/{total_profiles} perfiles procesados")
        else:
            self.logger.error(f"No se pudo limpiar ningún perfil de {total_profiles} encontrados")
        
        return success

    def _delete_or_quarantine(self, path: Path):
        """Elimina o mueve un archivo/carpeta a cuarentena."""
        if not path.exists():
            self.logger.info(f"No existe: {path}")
            return

        try:
            if self.cfg.quarantine_dir:
                import datetime
                q_dir = Path(self.cfg.quarantine_dir)
                q_dir.mkdir(parents=True, exist_ok=True)
                dest_base = q_dir / path.name
                dest = dest_base
                if dest.exists():
                    timestamp = datetime.datetime.now().strftime("_%Y%m%d_%H%M%S")
                    dest = Path(f"{str(dest_base)}{timestamp}")
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
