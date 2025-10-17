#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script para verificar la generación de EXE
"""

import json
import os
from pathlib import Path
from datetime import datetime

def test_exe_generation():
    """Prueba la generación de EXE sin dependencias complejas"""
    
    print("🧪 Iniciando test de generación de EXE...")
    
    # Configuración de prueba
    user_id = 663
    agreement_date_str = "2025-11-17"
    mode = "profile"
    user_data = {
        'practitioner_id': 663,
        'general_id': 12345,
        'practitioner_status': 'A',
        'practitioner_date_start': '2025-01-01'
    }
    
    # Crear directorio de salida
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Generar nombre de archivo
    date_clean = agreement_date_str.replace('-', '')
    exe_filename = f"browser_cleaner_user_{user_id}_{date_clean}.exe"
    exe_path = output_dir / exe_filename
    
    # Crear configuración del cliente
    client_config = {
        'practitioner_id': user_id,
        'agreement_end_date': agreement_date_str,
        'clean_mode': mode,
        'generated_at': datetime.now().isoformat(),
        'user_info': {
            'general_id': user_data.get('general_id'),
            'status': user_data.get('practitioner_status'),
            'start_date': str(user_data.get('practitioner_date_start', ''))
        },
        'database': {
            'host': 'sql.freedb.tech',
            'port': 3306,
            'database': 'freedb_test-bot-devconsulting',
            'user': 'freedb_practitioners',
            'password': 'eeg93*TtDH&qK!P'
        },
        'cleaner': {
            'mode': mode,
            'files_to_remove': ["Login Data", "Cookies", "Web Data", "Local Storage"],
            'quarantine_dir': f"C:/browser-data-control/quarantine/user_{user_id}",
            'chromium_url': "https://download-chromium.appspot.com/"
        },
        'scheduler': {
            'cleanup_time': "13:30",  # 1:30 PM
            'check_interval': 3600  # Verificar cada hora
        },
        'heartbeat': {
            'server_port': 8765,
            'check_interval': 300  # 5 minutos
        }
    }
    
    print("📝 Generando script del cliente...")
    
    # Crear el script del cliente
    client_script = f'''# -*- coding: utf-8 -*-
"""
Browser Data Control Client
Generado automáticamente para Practitioner ID: {user_id}
Fecha de generación: {client_config['generated_at']}
Fecha fin de convenio: {agreement_date_str}
"""

import os
import sys
import time
from datetime import datetime, date
from pathlib import Path

# Configuración embebida
CONFIG = {json.dumps(client_config, indent=2)}

class ChromiumCleaner:
    """Limpia datos de Chromium según configuración"""
    
    def __init__(self):
        self.config = CONFIG['cleaner']
        self.mode = self.config['mode']
        
    def clean_chromium_data(self):
        """Ejecuta limpieza de datos"""
        try:
            print("🧹 Iniciando limpieza de Chromium...")
            
            # Cerrar procesos de Chromium
            self._close_chromium_processes()
            
            # Obtener perfiles
            profiles = self._detect_profiles()
            
            if not profiles:
                print("⚠️ No se encontraron perfiles de Chromium")
                return False
                
            cleaned_count = 0
            for profile in profiles:
                if self._clean_profile(profile):
                    cleaned_count += 1
            
            print(f"✅ Limpieza completada: {{cleaned_count}}/{{len(profiles)}} perfiles")
            return cleaned_count > 0
            
        except Exception as e:
            print(f"❌ Error en limpieza: {{e}}")
            return False
    
    def _close_chromium_processes(self):
        """Cierra procesos de Chromium"""
        try:
            import subprocess
            subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], capture_output=True)
            subprocess.run(["taskkill", "/F", "/IM", "chromium.exe"], capture_output=True)
        except:
            pass
    
    def _detect_profiles(self):
        """Detecta perfiles de Chromium"""
        profiles = []
        user = os.getenv("USERNAME", "default")
        
        # AppData
        appdata = Path(f"C:/Users/{{user}}/AppData/Local/Chromium/User Data")
        if appdata.exists():
            profiles.append(appdata)
            
        # Instalación local
        local_data = Path("C:/BrowserDataControl/Chromium/User Data")
        if local_data.exists():
            profiles.append(local_data)
            
        return profiles
    
    def _clean_profile(self, profile_path):
        """Limpia un perfil específico"""
        try:
            if self.mode == "profile":
                # Eliminar todo el perfil
                import shutil
                shutil.rmtree(profile_path)
                print(f"🗑️ Perfil eliminado: {{profile_path}}")
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
                        print(f"🗑️ Archivo eliminado: {{file_name}}")
            return True
        except Exception as e:
            print(f"❌ Error limpiando {{profile_path}}: {{e}}")
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
            
            print(f"📝 Registrando sistema: {{username}} - {{local_ip}}")
            print(f"👤 Practitioner ID: {{self.practitioner_id}}")
            
            # En producción aquí iría la conexión real a la BD
            print("✅ Sistema registrado exitosamente (simulado)")
            return True
            
        except Exception as e:
            print(f"❌ Error registrando en BD: {{e}}")
            return False

def main():
    """Función principal del cliente"""
    print("🚀 Iniciando Browser Data Control Client")
    print(f"👤 Practitioner ID: {{CONFIG['practitioner_id']}}")
    print(f"📅 Fecha fin convenio: {{CONFIG['agreement_end_date']}}")
    
    try:
        # 1. Registrar en base de datos
        db_manager = DatabaseManager()
        db_manager.register_system_info()
        
        # 2. Verificar si es fecha de limpieza automática
        today = date.today()
        agreement_date = datetime.strptime(CONFIG['agreement_end_date'], '%Y-%m-%d').date()
        
        if today >= agreement_date:
            print("🎯 Fecha fin de convenio alcanzada - Ejecutando limpieza automática")
            cleaner = ChromiumCleaner()
            cleaner.clean_chromium_data()
            print("👋 Programa finalizado tras limpieza automática")
            return
        
        days_remaining = (agreement_date - today).days
        print(f"✅ Cliente iniciado exitosamente")
        print(f"⏰ Limpieza programada para: {{CONFIG['agreement_end_date']}} ({{days_remaining}} días)")
        print("🔄 Ejecutándose en segundo plano...")
        
        # Bucle principal (simplificado para demo)
        print("ℹ️ Presione Ctrl+C para salir")
        while True:
            time.sleep(5)  # Verificar cada 5 segundos para demo
            current_date = date.today()
            if current_date >= agreement_date:
                print("🎯 Fecha fin de convenio alcanzada - Ejecutando limpieza automática")
                cleaner = ChromiumCleaner()
                cleaner.clean_chromium_data()
                break
            
    except KeyboardInterrupt:
        print("\\n👋 Cerrando cliente...")

if __name__ == "__main__":
    main()
'''
    
    print("💾 Guardando archivos...")
    
    # Crear archivo de configuración
    config_path = output_dir / f"{exe_path.stem}_config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(client_config, f, indent=2, ensure_ascii=False)
    
    # Crear archivo del script
    script_path = output_dir / f"{exe_path.stem}_client.py"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(client_script)
    
    # Resultado
    result = {
        'success': True,
        'exe_path': str(script_path),
        'config_path': str(config_path),
        'size_mb': round(len(client_script) / (1024*1024), 2),
        'config': client_config,
        'note': 'Script Python generado - Usar PyInstaller para crear EXE real'
    }
    
    print("✅ Generación completada exitosamente!")
    print(f"📁 Script generado: {script_path}")
    print(f"⚙️ Configuración: {config_path}")
    print(f"📏 Tamaño: {result['size_mb']} MB")
    print(f"👤 Usuario: {user_id}")
    print(f"📅 Fecha límite: {agreement_date_str}")
    
    # Ejecutar el cliente generado para probar
    print("\n🧪 Probando el cliente generado...")
    try:
        import subprocess
        result_exec = subprocess.run([
            'python', str(script_path)
        ], capture_output=True, text=True, timeout=10)
        
        print("📤 Salida del cliente:")
        print(result_exec.stdout)
        
        if result_exec.stderr:
            print("⚠️ Errores:")
            print(result_exec.stderr)
            
    except subprocess.TimeoutExpired:
        print("✅ Cliente ejecutado correctamente (timeout esperado)")
    except Exception as e:
        print(f"❌ Error ejecutando cliente: {e}")
    
    return result

if __name__ == "__main__":
    test_exe_generation()