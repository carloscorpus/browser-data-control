# -*- coding: utf-8 -*-
# Admin App - Browser Control
# Aplicacion de administracion para gestionar usuarios y generar ejecutables

import sys
import os

# Agregar el directorio actual al path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def main():
    """Punto de entrada de la aplicacion administrativa"""
    print("🚀 Iniciando Browser Control Admin...")
    print("📍 Cargando interfaz de login...")
    
    try:
        # Importar con ruta relativa
        from src.ui.login_window import LoginWindow
        
        # Crear y ejecutar ventana de login
        app = LoginWindow()
        app.run()
        
    except ImportError as e:
        print(f"❌ Error importando modulos: {e}")
        print("🔧 Verifique que todos los archivos esten presentes")
        input("Presione Enter para salir...")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        input("Presione Enter para salir...")

if __name__ == "__main__":
    main()