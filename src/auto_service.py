# src/auto_service.py
"""
Servicio de limpieza automática para Browser Data Control
Este servicio debe ejecutarse como un servicio de Windows o proceso en segundo plano
para manejar las limpiezas automáticas programadas.
"""

import sys
import os
import signal
import time
from pathlib import Path

# Agregar src al path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from core.config_loader import ConfigLoader
from core.auto_scheduler import AutoScheduler
from core.logger import get_logger

class AutoService:
    """
    Servicio principal para limpieza automática
    """
    
    def __init__(self):
        self.config = None
        self.scheduler = None
        self.logger = get_logger()
        self.running = False
        
    def start(self):
        """Inicia el servicio automático"""
        try:
            self.logger.info("🚀 Iniciando Browser Data Control Auto Service")
            
            # Cargar configuración
            config_path = current_dir / "config" / "config.json"
            self.config = ConfigLoader(str(config_path))
            self.logger.info("✅ Configuración cargada")
            
            # Crear y iniciar scheduler
            self.scheduler = AutoScheduler(self.config)
            self.scheduler.start_scheduler()
            
            # Configurar manejadores de señales para cierre limpio
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            self.running = True
            self.logger.info("✅ Auto Service iniciado exitosamente")
            
            # Bucle principal
            self._main_loop()
            
        except Exception as e:
            self.logger.error(f"❌ Error iniciando servicio: {e}")
            raise
    
    def stop(self):
        """Detiene el servicio"""
        self.logger.info("🛑 Deteniendo Auto Service...")
        self.running = False
        
        if self.scheduler:
            self.scheduler.stop_scheduler()
        
        self.logger.info("✅ Auto Service detenido")
    
    def _signal_handler(self, signum, frame):
        """Maneja señales de sistema para cierre limpio"""
        self.logger.info(f"📨 Recibida señal {signum} - Cerrando servicio...")
        self.stop()
    
    def _main_loop(self):
        """Bucle principal del servicio"""
        try:
            while self.running:
                # Monitorear estado del scheduler
                status = self.scheduler.get_scheduler_status()
                
                if not status['running'] or not status['thread_alive']:
                    self.logger.error("⚠️ Scheduler no está funcionando - Reiniciando...")
                    try:
                        self.scheduler.stop_scheduler()
                        self.scheduler.start_scheduler()
                    except Exception as e:
                        self.logger.error(f"❌ Error reiniciando scheduler: {e}")
                
                # Log periódico de estado (cada 30 minutos)
                current_minute = int(time.time()) // 60
                if current_minute % 30 == 0:
                    self.logger.info(f"💓 Auto Service funcionando - Próxima limpieza: {status['next_cleanup']}")
                
                time.sleep(60)  # Verificar cada minuto
                
        except KeyboardInterrupt:
            self.logger.info("⌨️ Interrupción por teclado - Cerrando...")
        except Exception as e:
            self.logger.error(f"❌ Error en bucle principal: {e}")
        finally:
            self.stop()

def main():
    """Función principal"""
    print("=" * 60)
    print("🤖 Browser Data Control - Auto Service")
    print("=" * 60)
    
    service = AutoService()
    
    try:
        service.start()
    except KeyboardInterrupt:
        print("\n⌨️ Interrumpido por usuario")
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()