# src/core/auto_scheduler.py
import schedule
import time
import threading
from datetime import datetime, date
from typing import List, Dict
from .logger import get_logger
from .db_manager import DBManager
from .remote_cleaner import RemoteCleaner

class AutoScheduler:
    """
    Sistema de limpieza automática programada
    Ejecuta limpiezas automáticas a la 1:30 PM del día fin de convenio
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger()
        self.db_manager = None
        self.remote_cleaner = None
        self.is_running = False
        self.scheduler_thread = None
        
        # Configuración de horarios
        self.cleanup_time = "13:30"  # 1:30 PM
        self.check_interval = 300    # 5 minutos entre verificaciones
        
    def start_scheduler(self):
        """Inicia el scheduler automático"""
        if self.is_running:
            self.logger.warning("Scheduler ya está ejecutándose")
            return
        
        try:
            # Inicializar conexiones
            self._initialize_connections()
            
            # Configurar trabajos programados
            self._setup_scheduled_jobs()
            
            # Iniciar hilo del scheduler
            self.is_running = True
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            
            self.logger.info("✅ Auto-scheduler iniciado exitosamente")
            
        except Exception as e:
            self.logger.error(f"❌ Error iniciando auto-scheduler: {e}")
            raise
    
    def stop_scheduler(self):
        """Detiene el scheduler"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        if self.db_manager:
            self.db_manager.close()
        
        self.logger.info("🛑 Auto-scheduler detenido")
    
    def _initialize_connections(self):
        """Inicializa conexiones a BD y servicios"""
        # Conexión a base de datos
        self.db_manager = DBManager(
            host=self.config.db.host,
            port=self.config.db.port,
            user=self.config.db.user,
            password=self.config.db.password,
            database=self.config.db.database
        )
        self.db_manager.connect()
        
        # Servicio de limpieza remota
        self.remote_cleaner = RemoteCleaner(self.config)
        
        self.logger.info("🔗 Conexiones inicializadas")
    
    def _setup_scheduled_jobs(self):
        """Configura los trabajos programados"""
        # Limpieza automática diaria a la 1:30 PM
        schedule.every().day.at(self.cleanup_time).do(self._daily_cleanup_check)
        
        # Verificación de estado cada 5 minutos
        schedule.every(5).minutes.do(self._health_check)
        
        # Verificación de usuarios expirados cada hora
        schedule.every().hour.do(self._check_expired_users)
        
        self.logger.info(f"📅 Trabajos programados configurados - Limpieza diaria a las {self.cleanup_time}")
    
    def _run_scheduler(self):
        """Ejecuta el scheduler en bucle"""
        self.logger.info("🔄 Scheduler iniciado en modo automático")
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Verificar cada minuto
                
            except Exception as e:
                self.logger.error(f"❌ Error en scheduler: {e}")
                time.sleep(60)  # Continuar después del error
    
    def _daily_cleanup_check(self):
        """Verificación diaria de limpiezas automáticas"""
        try:
            today = date.today()
            self.logger.info(f"🔍 Verificando limpiezas automáticas para {today}")
            
            # Obtener usuarios que expiran hoy
            expired_users = self._get_users_expiring_today()
            
            if not expired_users:
                self.logger.info("✅ No hay usuarios para limpieza automática hoy")
                return
            
            self.logger.info(f"🎯 Encontrados {len(expired_users)} usuarios para limpieza automática")
            
            # Ejecutar limpieza para cada usuario
            for user_data in expired_users:
                self._execute_automatic_cleanup(user_data)
            
        except Exception as e:
            self.logger.error(f"❌ Error en verificación diaria: {e}")
    
    def _get_users_expiring_today(self) -> List[Dict]:
        """Obtiene usuarios cuyo convenio expira hoy"""
        try:
            today = date.today()
            
            # Query para obtener usuarios que expiran hoy y están activos
            query = """
            SELECT p.practitioner_id, p.practitioner_status, p.practitioner_date_end,
                   p.general_id, p.practitioner_observation
            FROM practitioners p
            WHERE p.practitioner_date_end = %s 
            AND p.practitioner_status = 'A'
            ORDER BY p.practitioner_id
            """
            
            with self.db_manager.conn.cursor() as cursor:
                cursor.execute(query, (today,))
                return cursor.fetchall()
                
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo usuarios que expiran: {e}")
            return []
    
    def _execute_automatic_cleanup(self, user_data: Dict):
        """Ejecuta limpieza automática para un usuario específico"""
        practitioner_id = user_data['practitioner_id']
        
        try:
            self.logger.info(f"🧹 Iniciando limpieza automática para usuario {practitioner_id}")
            
            # Obtener sistemas registrados del usuario
            system_users = self.db_manager.get_practitioner_system_users(practitioner_id)
            
            if not system_users:
                self.logger.warning(f"⚠️ Usuario {practitioner_id} no tiene sistemas registrados")
                self._mark_user_as_processed(practitioner_id, success=False, 
                                           error="No hay sistemas registrados")
                return
            
            # Ejecutar limpieza remota
            cleanup_result = self.remote_cleaner.clean_user_chromium(practitioner_id, system_users)
            
            # Procesar resultado
            if cleanup_result['success']:
                cleaned_count = len(cleanup_result.get('cleaned_systems', []))
                total_count = cleanup_result.get('total_systems', 0)
                
                self.logger.info(f"✅ Limpieza automática exitosa para usuario {practitioner_id}: "
                               f"{cleaned_count}/{total_count} sistemas")
                
                # Marcar usuario como inactivo tras limpieza exitosa
                self._deactivate_user_after_cleanup(practitioner_id)
                
            else:
                error_msg = '; '.join(cleanup_result.get('errors', ['Error desconocido']))
                self.logger.error(f"❌ Fallo en limpieza automática para usuario {practitioner_id}: {error_msg}")
                
                self._mark_user_as_processed(practitioner_id, success=False, error=error_msg)
            
        except Exception as e:
            self.logger.error(f"❌ Error ejecutando limpieza automática para usuario {practitioner_id}: {e}")
            self._mark_user_as_processed(practitioner_id, success=False, error=str(e))
    
    def _deactivate_user_after_cleanup(self, practitioner_id: int):
        """Marca usuario como inactivo después de limpieza exitosa"""
        try:
            query = """
            UPDATE practitioners 
            SET practitioner_status = 'I',
                practitioner_observation = CONCAT(
                    COALESCE(practitioner_observation, ''), 
                    ' [AUTO-CLEANUP: ', NOW(), ']'
                )
            WHERE practitioner_id = %s AND practitioner_status = 'A'
            """
            
            with self.db_manager.conn.cursor() as cursor:
                cursor.execute(query, (practitioner_id,))
                self.db_manager.conn.commit()
            
            self.logger.info(f"👤 Usuario {practitioner_id} marcado como inactivo tras limpieza automática")
            
        except Exception as e:
            self.logger.error(f"❌ Error marcando usuario {practitioner_id} como inactivo: {e}")
    
    def _mark_user_as_processed(self, practitioner_id: int, success: bool, error: str = None):
        """Marca usuario como procesado en limpieza automática"""
        try:
            status_msg = "SUCCESS" if success else f"FAILED: {error}"
            observation_update = f" [AUTO-CLEANUP: {datetime.now()} - {status_msg}]"
            
            query = """
            UPDATE practitioners 
            SET practitioner_observation = CONCAT(
                COALESCE(practitioner_observation, ''), 
                %s
            )
            WHERE practitioner_id = %s
            """
            
            with self.db_manager.conn.cursor() as cursor:
                cursor.execute(query, (observation_update, practitioner_id))
                self.db_manager.conn.commit()
            
            self.logger.info(f"📝 Usuario {practitioner_id} marcado como procesado: {status_msg}")
            
        except Exception as e:
            self.logger.error(f"❌ Error marcando usuario {practitioner_id} como procesado: {e}")
    
    def _health_check(self):
        """Verificación de salud del sistema"""
        try:
            # Verificar conexión a BD
            if not self.db_manager or not self.db_manager.conn:
                self.logger.warning("⚠️ Reconectando a base de datos...")
                self._initialize_connections()
            
            # Ping a la BD
            with self.db_manager.conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            # Log periódico de estado
            current_time = datetime.now().strftime("%H:%M")
            if current_time.endswith("0"):  # Cada 10 minutos
                self.logger.info(f"💓 Auto-scheduler funcionando - {current_time}")
                
        except Exception as e:
            self.logger.error(f"❌ Error en health check: {e}")
            try:
                self._initialize_connections()
            except Exception as reconnect_error:
                self.logger.error(f"❌ Error reconectando: {reconnect_error}")
    
    def _check_expired_users(self):
        """Verificación cada hora de usuarios con convenios vencidos"""
        try:
            # Obtener usuarios con convenios vencidos que siguen activos
            today = date.today()
            
            query = """
            SELECT practitioner_id, practitioner_date_end, general_id
            FROM practitioners 
            WHERE practitioner_date_end < %s 
            AND practitioner_status = 'A'
            ORDER BY practitioner_date_end DESC
            LIMIT 10
            """
            
            with self.db_manager.conn.cursor() as cursor:
                cursor.execute(query, (today,))
                expired_users = cursor.fetchall()
            
            if expired_users:
                self.logger.warning(f"⚠️ Encontrados {len(expired_users)} usuarios con convenios vencidos aún activos")
                
                # Log de usuarios vencidos para seguimiento manual
                for user in expired_users:
                    days_expired = (today - user['practitioner_date_end']).days
                    self.logger.warning(f"📋 Usuario {user['practitioner_id']} "
                                      f"(General: {user['general_id']}) "
                                      f"vencido hace {days_expired} días")
            
        except Exception as e:
            self.logger.error(f"❌ Error verificando usuarios vencidos: {e}")
    
    def force_cleanup_user(self, practitioner_id: int) -> Dict:
        """Fuerza limpieza inmediata de un usuario específico"""
        try:
            self.logger.info(f"🔨 Forzando limpieza inmediata para usuario {practitioner_id}")
            
            # Obtener datos del usuario
            user_data = self.db_manager.get_practitioner_by_id(practitioner_id)
            if not user_data:
                return {
                    'success': False,
                    'error': f'Usuario {practitioner_id} no encontrado'
                }
            
            # Ejecutar limpieza
            self._execute_automatic_cleanup(user_data)
            
            return {
                'success': True,
                'message': f'Limpieza forzada ejecutada para usuario {practitioner_id}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error en limpieza forzada: {str(e)}'
            }
    
    def get_scheduler_status(self) -> Dict:
        """Obtiene estado actual del scheduler"""
        return {
            'running': self.is_running,
            'cleanup_time': self.cleanup_time,
            'check_interval': self.check_interval,
            'db_connected': bool(self.db_manager and self.db_manager.conn),
            'next_cleanup': self._get_next_cleanup_time(),
            'thread_alive': bool(self.scheduler_thread and self.scheduler_thread.is_alive())
        }
    
    def _get_next_cleanup_time(self) -> str:
        """Calcula próxima ejecución de limpieza"""
        try:
            today = datetime.now()
            cleanup_today = today.replace(hour=13, minute=30, second=0, microsecond=0)
            
            if today < cleanup_today:
                return cleanup_today.strftime("%Y-%m-%d %H:%M:%S")
            else:
                # Próximo día
                tomorrow = cleanup_today.replace(day=cleanup_today.day + 1)
                return tomorrow.strftime("%Y-%m-%d %H:%M:%S")
                
        except Exception:
            return "Error calculando próxima ejecución"