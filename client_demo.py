#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del cliente generado sin emojis para compatibilidad Windows
"""

import json
import os
import sys
import time
from datetime import datetime, date
from pathlib import Path

# Configuración embebida (se reemplazaría por la configuración real)
CONFIG = {
    'practitioner_id': 663,
    'agreement_end_date': '2025-11-17',
    'clean_mode': 'profile',
    'generated_at': '2025-10-16T12:00:00',
    'database': {
        'host': 'sql.freedb.tech',
        'port': 3306,
        'database': 'freedb_test-bot-devconsulting',
        'user': 'freedb_practitioners',
        'password': 'eeg93*TtDH&qK!P'
    },
    'cleaner': {
        'mode': 'profile',
        'files_to_remove': ["Login Data", "Cookies", "Web Data", "Local Storage"]
    }
}

class ChromiumCleaner:
    """Limpia datos de Chromium según configuración"""
    
    def __init__(self):
        self.config = CONFIG['cleaner']
        self.mode = self.config['mode']
        
    def clean_chromium_data(self):
        """Ejecuta limpieza de datos"""
        try:
            print("[INFO] Iniciando limpieza de Chromium...")
            
            # Cerrar procesos de Chromium
            self._close_chromium_processes()
            
            # Obtener perfiles
            profiles = self._detect_profiles()
            
            if not profiles:
                print("[WARNING] No se encontraron perfiles de Chromium")
                return False
                
            cleaned_count = 0
            for profile in profiles:
                if self._clean_profile(profile):
                    cleaned_count += 1
            
            print(f"[SUCCESS] Limpieza completada: {cleaned_count}/{len(profiles)} perfiles")
            return cleaned_count > 0
            
        except Exception as e:
            print(f"[ERROR] Error en limpieza: {e}")
            return False
    
    def _close_chromium_processes(self):
        """Cierra procesos de Chromium"""
        try:
            import subprocess
            subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], capture_output=True)
            subprocess.run(["taskkill", "/F", "/IM", "chromium.exe"], capture_output=True)
            print("[INFO] Procesos de Chromium finalizados")
        except:
            pass
    
    def _detect_profiles(self):
        """Detecta perfiles de Chromium"""
        profiles = []
        user = os.getenv("USERNAME", "default")
        
        # AppData
        appdata = Path(f"C:/Users/{user}/AppData/Local/Chromium/User Data")
        if appdata.exists():
            profiles.append(appdata)
            print(f"[INFO] Perfil encontrado: {appdata}")
            
        # Instalación local
        local_data = Path("C:/BrowserDataControl/Chromium/User Data")
        if local_data.exists():
            profiles.append(local_data)
            print(f"[INFO] Perfil encontrado: {local_data}")
            
        return profiles
    
    def _clean_profile(self, profile_path):
        """Limpia un perfil específico"""
        try:
            if self.mode == "profile":
                # Eliminar todo el perfil
                import shutil
                shutil.rmtree(profile_path)
                print(f"[INFO] Perfil eliminado: {profile_path}")
            elif self.mode == "files":
                # Eliminar archivos específicos
                for file_name in self.config['files_to_remove']:
                    file_path = profile_path / "Default" / file_name
                    if file_path.exists():
                        if file_path.is_dir():
                            import shutil
                            shutil.rmtree(file_path)
                        else:
                            file_path.unlink()
                        print(f"[INFO] Archivo eliminado: {file_name}")
            return True
        except Exception as e:
            print(f"[ERROR] Error limpiando {profile_path}: {e}")
            return False

class DatabaseManager:
    """Maneja conexión a base de datos"""
    
    def __init__(self):
        self.db_config = CONFIG['database']
        self.practitioner_id = CONFIG['practitioner_id']
        
    def register_system_info(self):
        """Registra información del sistema en la BD"""
        try:
            # Obtener información del sistema
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            username = os.getenv("USERNAME", "unknown")
            
            print(f"[INFO] Registrando sistema: {username} - {local_ip}")
            print(f"[INFO] Practitioner ID: {self.practitioner_id}")
            
            # En producción aquí iría la conexión real a pymysql
            print("[SUCCESS] Sistema registrado exitosamente (simulado)")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error registrando en BD: {e}")
            return False

def main():
    """Función principal del cliente"""
    print("=" * 50)
    print("Browser Data Control Client")
    print("=" * 50)
    print(f"Practitioner ID: {CONFIG['practitioner_id']}")
    print(f"Fecha fin convenio: {CONFIG['agreement_end_date']}")
    print(f"Modo limpieza: {CONFIG['clean_mode']}")
    
    try:
        # 1. Registrar en base de datos
        print("\n[STEP 1] Registrando sistema en base de datos...")
        db_manager = DatabaseManager()
        db_manager.register_system_info()
        
        # 2. Verificar si es fecha de limpieza automática
        print("\n[STEP 2] Verificando fecha de convenio...")
        today = date.today()
        agreement_date = datetime.strptime(CONFIG['agreement_end_date'], '%Y-%m-%d').date()
        
        if today >= agreement_date:
            print("[ALERT] Fecha fin de convenio alcanzada - Ejecutando limpieza automatica")
            cleaner = ChromiumCleaner()
            cleaner.clean_chromium_data()
            print("[INFO] Programa finalizado tras limpieza automatica")
            return
        
        days_remaining = (agreement_date - today).days
        print(f"[SUCCESS] Cliente iniciado exitosamente")
        print(f"[INFO] Limpieza programada para: {CONFIG['agreement_end_date']} ({days_remaining} dias)")
        print("[INFO] Ejecutandose en segundo plano...")
        
        # Bucle principal (simplificado para demo)
        print("\n[INFO] Presione Ctrl+C para salir")
        print("[INFO] Verificando fecha cada 5 segundos...")
        
        for i in range(6):  # Solo 6 iteraciones para demo (30 segundos)
            time.sleep(5)
            print(f"[HEARTBEAT] Verificacion {i+1}/6 - Estado: OK")
            current_date = date.today()
            if current_date >= agreement_date:
                print("[ALERT] Fecha fin de convenio alcanzada - Ejecutando limpieza automatica")
                cleaner = ChromiumCleaner()
                cleaner.clean_chromium_data()
                break
        
        print("[INFO] Demo completada - En produccion continuaria ejecutandose")
        
    except KeyboardInterrupt:
        print("\n[INFO] Cerrando cliente...")

if __name__ == "__main__":
    main()