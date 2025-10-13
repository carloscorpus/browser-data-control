@echo off
REM Script para ejecutar Browser Control Admin
REM Activa el entorno virtual y ejecuta la aplicacion

echo 🚀 Iniciando Browser Control Admin...
echo 📍 Activando entorno virtual...

cd /d "%~dp0.."
call .venv\Scripts\activate

echo ✅ Entorno activado
echo 📍 Ejecutando aplicacion...

cd admin_app
python main.py

echo 🔚 Aplicacion cerrada
pause