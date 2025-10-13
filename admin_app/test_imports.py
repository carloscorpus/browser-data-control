# -*- coding: utf-8 -*-
# Test simple para verificar imports
import sys
import os

print("🧪 Test de importacion...")
print(f"📍 Directorio actual: {os.getcwd()}")

# Agregar path actual
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print(f"📍 Paths en sys.path:")
for i, path in enumerate(sys.path[:5]):
    print(f"  {i}: {path}")

try:
    print("\n🔄 Probando importar SecureDBService...")
    from src.services.db_service import SecureDBService
    print("✅ SecureDBService importado correctamente")
    
    print("\n🔄 Probando importar LoginWindow...")
    from src.ui.login_window import LoginWindow
    print("✅ LoginWindow importado correctamente")
    
    print("\n🔄 Probando crear instancia de LoginWindow...")
    # Solo crear la instancia, no ejecutar
    app = LoginWindow()
    print("✅ LoginWindow creado correctamente")
    print("✅ Todos los tests pasaron!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

input("Presione Enter para salir...")