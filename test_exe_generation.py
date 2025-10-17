#!/usr/bin/env python3
"""
Test script para verificar generación EXE desde admin panel
"""

import os
import subprocess
import sys
from pathlib import Path

def test_exe_generation():
    print("🔍 Probando generación EXE...")
    
    # Directorio de trabajo
    output_dir = Path("c:/Users/xrobe/OneDrive/Desktop/browser-data-control/admin_app/output")
    script_file = output_dir / "browser_cleaner_user_663_20251117_client.py"
    
    if not script_file.exists():
        print(f"❌ No existe el archivo: {script_file}")
        return False
    
    # Comando PyInstaller
    cmd = [
        "pyinstaller",
        "--onefile",
        "--noconsole", 
        "--name", "browser_cleaner_user_663_20251117",
        str(script_file)
    ]
    
    print(f"🚀 Ejecutando: {' '.join(cmd)}")
    print(f"📁 Directorio: {output_dir}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(output_dir),
            capture_output=True,
            text=True,
            timeout=120  # 2 minutos timeout
        )
        
        print(f"📊 Return code: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ PyInstaller ejecutado exitosamente!")
            
            # Verificar si se creó el EXE
            exe_file = output_dir / "dist" / "browser_cleaner_user_663_20251117.exe"
            if exe_file.exists():
                print(f"✅ EXE generado: {exe_file}")
                print(f"📏 Tamaño: {exe_file.stat().st_size / (1024*1024):.2f} MB")
                return True
            else:
                print(f"❌ EXE no encontrado en: {exe_file}")
                return False
        else:
            print("❌ PyInstaller falló!")
            print("STDOUT:", result.stdout[:500])
            print("STDERR:", result.stderr[:500])
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Timeout - PyInstaller tomó demasiado tiempo")
        return False
    except Exception as e:
        print(f"💥 Error ejecutando PyInstaller: {e}")
        return False

if __name__ == "__main__":
    success = test_exe_generation()
    sys.exit(0 if success else 1)