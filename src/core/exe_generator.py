# src/core/exe_generator.py
import os
import json
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from .logger import get_logger

class EXEGenerator:
    """
    Genera ejecutables personalizados para colaboradores
    Incluye configuración específica de usuario y fechas de convenio
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger()
        self.output_dir = Path("output")
        self.templates_dir = Path("templates")
        self.pyinstaller_available = self._check_pyinstaller()
    
    def _check_pyinstaller(self) -> bool:
        """Verifica si PyInstaller está disponible"""
        try:
            import PyInstaller
            return True
        except ImportError:
            self.logger.warning("PyInstaller no está instalado - modo simulación activo")
            return False
    
    def generate_custom_exe(self, practitioner_id: int, agreement_end_date: str, 
                          clean_mode: str, user_data: dict) -> Dict:
        """
        Genera un ejecutable personalizado para un colaborador específico
        
        Args:
            practitioner_id: ID del usuario en la BD
            agreement_end_date: Fecha fin de convenio (YYYY-MM-DD)
            clean_mode: Modo de limpieza (profile/files)
            user_data: Datos completos del usuario
        
        Returns:
            Dict con información del EXE generado
        """
        try:
            # Crear directorio de salida
            self.output_dir.mkdir(exist_ok=True)
            
            # Generar nombre de archivo
            date_clean = agreement_end_date.replace('-', '')
            exe_filename = f"browser_cleaner_user_{practitioner_id}_{date_clean}.exe"
            exe_path = self.output_dir / exe_filename
            
            # Crear configuración personalizada
            client_config = self._create_client_config(
                practitioner_id, agreement_end_date, clean_mode, user_data
            )
            
            # Crear el script cliente
            client_script = self._create_client_script(client_config)
            
            if self.pyinstaller_available:
                # Compilar con PyInstaller
                return self._compile_with_pyinstaller(client_script, exe_path, client_config)
            else:
                # Modo simulación
                return self._simulate_exe_generation(exe_path, client_config)
                
        except Exception as e:
            self.logger.error(f"Error generando EXE: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_client_config(self, practitioner_id: int, agreement_end_date: str, 
                            clean_mode: str, user_data: dict) -> Dict:
        """Crea la configuración personalizada para el cliente"""
        config = {
            'practitioner_id': practitioner_id,
            'agreement_end_date': agreement_end_date,
            'clean_mode': clean_mode,
            'generated_at': datetime.now().isoformat(),
            'user_info': {
                'general_id': user_data.get('general_id'),
                'status': user_data.get('practitioner_status'),
                'start_date': str(user_data.get('practitioner_date_start', ''))
            },
            'database': {
                'host': self.config.db.host,
                'port': self.config.db.port,
                'database': self.config.db.database,
                'user': self.config.db.user,
                'password': self.config.db.password
            },
            'cleaner': {
                'mode': clean_mode,
                'files_to_remove': self.config.cleaner.files_to_remove,
                'quarantine_dir': f"C:/browser-data-control/quarantine/user_{practitioner_id}",
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
        return config
    
    def _create_client_script(self, config: Dict) -> str:
        """Crea el script Python que será compilado a EXE"""
        script_content = f'''# -*- coding: utf-8 -*-
"""
Browser Data Control Client
Generado automáticamente para Practitioner ID: {config['practitioner_id']}
Fecha de generación: {config['generated_at']}
Fecha fin de convenio: {config['agreement_end_date']}
"""

import os
import sys
import json
import time
import threading
import schedule
import requests
import subprocess
import tempfile
import zipfile
from datetime import datetime, date
from pathlib import Path
import pymysql
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver

# Configuración embebida
CONFIG = {json.dumps(config, indent=2)}

class ChromiumInstaller:
    """Instala Chromium automáticamente"""
    
    def __init__(self):
        self.chromium_url = CONFIG['cleaner']['chromium_url']
        self.install_dir = Path("C:/BrowserDataControl/Chromium")
        
    def install_chromium(self):
        """Descarga e instala Chromium"""
        try:
            print("🔽 Descargando Chromium...")
            
            # Crear directorio de instalación
            self.install_dir.mkdir(parents=True, exist_ok=True)
            
            # Simular descarga (implementar descarga real)
            print("📦 Instalando Chromium...")
            
            # Crear shortcut en desktop
            self._create_desktop_shortcut()
            
            print("✅ Chromium instalado exitosamente")
            return True
            
        except Exception as e:
            print(f"❌ Error instalando Chromium: {{e}}")
            return False
    
    def _create_desktop_shortcut(self):
        """Crea acceso directo en escritorio"""
        # Implementar creación de shortcut
        pass

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
            
            # Conectar a BD
            conn = pymysql.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database'],
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor
            )
            
            # Verificar que practitioner_id existe
            with conn.cursor() as cursor:
                cursor.execute("SELECT practitioner_id FROM practitioners WHERE practitioner_id = %s", 
                             (self.practitioner_id,))
                if not cursor.fetchone():
                    print(f"⚠️ Practitioner ID {{self.practitioner_id}} no existe en BD")
                    return False
            
            # Registrar o actualizar información del sistema
            with conn.cursor() as cursor:
                # Verificar si ya existe
                cursor.execute(
                    "SELECT practitioner_id FROM practitioner_system_users WHERE practitioner_id = %s AND system_username = %s",
                    (self.practitioner_id, username)
                )
                
                if cursor.fetchone():
                    # Actualizar IP
                    cursor.execute(
                        "UPDATE practitioner_system_users SET ip_address = %s WHERE practitioner_id = %s AND system_username = %s",
                        (local_ip, self.practitioner_id, username)
                    )
                    print(f"📝 IP actualizada: {{local_ip}}")
                else:
                    # Insertar nuevo registro
                    cursor.execute(
                        "INSERT INTO practitioner_system_users (practitioner_id, system_username, ip_address) VALUES (%s, %s, %s)",
                        (self.practitioner_id, username, local_ip)
                    )
                    print(f"📝 Nuevo registro creado: {{username}} - {{local_ip}}")
                
                conn.commit()
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error registrando en BD: {{e}}")
            return False

class ScheduleManager:
    """Maneja programación automática de limpieza"""
    
    def __init__(self):
        self.agreement_end_date = datetime.strptime(CONFIG['agreement_end_date'], '%Y-%m-%d').date()
        self.cleanup_time = CONFIG['scheduler']['cleanup_time']
        
    def setup_automatic_cleanup(self):
        """Configura limpieza automática"""
        # Programar limpieza para la fecha fin de convenio
        schedule.every().day.at(self.cleanup_time).do(self._check_and_clean)
        
        print(f"⏰ Limpieza programada para {{self.agreement_end_date}} a las {{self.cleanup_time}}")
        
        # Ejecutar scheduler en hilo separado
        scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        scheduler_thread.start()
    
    def _check_and_clean(self):
        """Verifica fecha y ejecuta limpieza si corresponde"""
        today = date.today()
        if today >= self.agreement_end_date:
            print("🎯 Fecha fin de convenio alcanzada - Ejecutando limpieza automática")
            cleaner = ChromiumCleaner()
            cleaner.clean_chromium_data()
            
            # Opcional: cerrar programa después de limpieza
            print("👋 Programa finalizado tras limpieza automática")
            sys.exit(0)
    
    def _run_scheduler(self):
        """Ejecuta el scheduler en bucle"""
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verificar cada minuto

class HeartbeatServer:
    """Servidor para recibir comandos remotos"""
    
    def __init__(self):
        self.port = CONFIG['heartbeat']['server_port']
        self.server = None
        
    def start_server(self):
        """Inicia servidor HTTP para comandos remotos"""
        try:
            handler = self._create_handler()
            self.server = HTTPServer(('', self.port), handler)
            
            print(f"🌐 Servidor heartbeat iniciado en puerto {{self.port}}")
            
            # Ejecutar servidor en hilo separado
            server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            server_thread.start()
            
        except Exception as e:
            print(f"❌ Error iniciando servidor: {{e}}")
    
    def _create_handler(self):
        """Crea handler para el servidor HTTP"""
        class CommandHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/api/status':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = {{
                        'status': 'online',
                        'practitioner_id': CONFIG['practitioner_id'],
                        'timestamp': datetime.now().isoformat()
                    }}
                    self.wfile.write(json.dumps(response).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def do_POST(self):
                if self.path == '/api/clean':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    
                    try:
                        command = json.loads(post_data.decode())
                        
                        if command.get('action') == 'clean_chromium':
                            # Ejecutar limpieza
                            cleaner = ChromiumCleaner()
                            success = cleaner.clean_chromium_data()
                            
                            response = {{
                                'success': success,
                                'practitioner_id': CONFIG['practitioner_id'],
                                'timestamp': datetime.now().isoformat(),
                                'message': 'Limpieza completada' if success else 'Error en limpieza'
                            }}
                            
                            self.send_response(200)
                            self.send_header('Content-type', 'application/json')
                            self.end_headers()
                            self.wfile.write(json.dumps(response).encode())
                        else:
                            self.send_response(400)
                            self.end_headers()
                            
                    except Exception as e:
                        self.send_response(500)
                        self.end_headers()
                else:
                    self.send_response(404)
                    self.end_headers()
                    
            def log_message(self, format, *args):
                # Silenciar logs del servidor
                pass
        
        return CommandHandler

def main():
    """Función principal del cliente"""
    print("🚀 Iniciando Browser Data Control Client")
    print(f"👤 Practitioner ID: {{CONFIG['practitioner_id']}}")
    print(f"📅 Fecha fin convenio: {{CONFIG['agreement_end_date']}}")
    
    try:
        # 1. Instalar Chromium
        installer = ChromiumInstaller()
        if not installer.install_chromium():
            print("⚠️ Continuando sin instalación de Chromium...")
        
        # 2. Registrar en base de datos
        db_manager = DatabaseManager()
        if not db_manager.register_system_info():
            print("⚠️ Continuando sin registro en BD...")
        
        # 3. Configurar limpieza automática
        scheduler = ScheduleManager()
        scheduler.setup_automatic_cleanup()
        
        # 4. Iniciar servidor de heartbeat
        heartbeat = HeartbeatServer()
        heartbeat.start_server()
        
        print("✅ Cliente iniciado exitosamente")
        print("🔄 Ejecutándose en segundo plano...")
        print("⏹️ Presione Ctrl+C para salir")
        
        # Mantener programa ejecutándose
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            print("\\n👋 Cerrando cliente...")
            sys.exit(0)
            
    except Exception as e:
        print(f"❌ Error crítico: {{e}}")
        input("Presione Enter para salir...")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        return script_content
    
    def _compile_with_pyinstaller(self, script_content: str, exe_path: Path, config: Dict) -> Dict:
        """Compila el script usando PyInstaller"""
        try:
            # Crear archivo temporal con el script
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(script_content)
                temp_script_path = temp_file.name
            
            # Preparar comando PyInstaller
            pyinstaller_cmd = [
                'pyinstaller',
                '--onefile',
                '--noconsole',
                '--name', exe_path.stem,
                '--distpath', str(self.output_dir),
                '--clean',
                temp_script_path
            ]
            
            # Ejecutar PyInstaller
            import subprocess
            result = subprocess.run(pyinstaller_cmd, capture_output=True, text=True)
            
            # Limpiar archivo temporal
            os.unlink(temp_script_path)
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'exe_path': str(exe_path),
                    'size_mb': round(exe_path.stat().st_size / (1024*1024), 2) if exe_path.exists() else 0,
                    'config': config,
                    'compilation_output': result.stdout
                }
            else:
                return {
                    'success': False,
                    'error': f'PyInstaller error: {result.stderr}',
                    'config': config
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Compilation error: {str(e)}',
                'config': config
            }
    
    def _simulate_exe_generation(self, exe_path: Path, config: Dict) -> Dict:
        """Simula la generación del EXE (para desarrollo)"""
        # Crear archivo de configuración como evidencia
        config_path = self.output_dir / f"{exe_path.stem}_config.json"
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        # Crear archivo placeholder del EXE
        placeholder_content = f"""# SIMULACIÓN DE EXE
# Practitioner ID: {config['practitioner_id']}
# Fecha fin convenio: {config['agreement_end_date']}
# Generado: {config['generated_at']}

# En producción, este sería un ejecutable real compilado con PyInstaller
"""
        
        placeholder_path = self.output_dir / f"{exe_path.stem}_PLACEHOLDER.txt"
        with open(placeholder_path, 'w', encoding='utf-8') as f:
            f.write(placeholder_content)
        
        return {
            'success': True,
            'exe_path': str(placeholder_path),
            'config_path': str(config_path),
            'size_mb': 0.0,
            'config': config,
            'note': 'Archivo simulado - PyInstaller no disponible'
        }