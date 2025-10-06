# Browser Data Control

Automatiza la limpieza de perfiles y datos sensibles de Chromium/Chrome en Windows, con soporte para tareas programadas y respaldo en cuarentena.

---

## Requisitos previos

-   Python 3.8+
-   Windows
-   Tener instalado Chromium/Chrome (para limpieza de perfiles)
-   (Opcional) MySQL si quieres usar la funcionalidad de base de datos

## Instalación y setup del entorno

1. Clona el repositorio y entra a la carpeta del proyecto.
2. Crea y activa el entorno virtual:
    ```bash
    python -m venv .venv
    source .venv/Scripts/activate
    ```
3. Instala las dependencias:
    ```bash
    pip install -r requirements.txt
    ```

## Configuración del archivo `config.json`

El archivo `src/config/config.json` controla el comportamiento de la aplicación. A continuación se describen sus secciones y opciones principales:

### Estructura y opciones

```json
{
	"db": {
		"host": "", // Dirección del servidor de base de datos MySQL
		"port": , // Puerto de conexión
		"user": "", // Usuario de la base de datos
		"password": "", // Contraseña del usuario
		"database": "", // Nombre de la base de datos
		"status_query": "" // Consulta SQL para obtener practitioners inactivos
	},
	"scheduler": {
		"type": "cron", // Tipo de programación (por ahora solo 'cron')
		"cron": {
			"day_of_week": "*", // Días de la semana para ejecutar (ej: "mon", "tue", "*")
			"hour": 13, // Hora de ejecución (0-23)
			"minute": 26 // Minuto de ejecución (0-59)
		}
	},
	"cleaner": {
		"mode": "profile", // "profile" para borrar el perfil completo, "files" para borrar archivos específicos
		"files_to_remove": ["Login Data", "Cookies", "Web Data", "Local Storage"], // Archivos a eliminar si el modo es "files"
		"allow_permanent_delete": false, // Si es true, borra permanentemente; si es false, mueve a cuarentena
		"quarantine_dir": "C:/browser-data-control/quarantine", // Carpeta donde se moverán los archivos en cuarentena
		"browser_profiles": [] // Rutas adicionales de perfiles de Chromium a limpiar (opcional)
	},
	"logging": {
		"level": "INFO", // Nivel de logs: "DEBUG", "INFO", "WARNING", "ERROR"
		"log_file": "logs/browser-data-control.log" // Ruta del archivo de logs
	},
	"safety": {
		"dry_run": true // Si es true, solo simula la limpieza (no borra nada realmente)
	}
}
```

### Notas importantes

-   **dry_run**: Si está en `true`, la limpieza solo se simula. Para borrar realmente, ponlo en `false`.
-   **mode**:
    -   `"profile"` borra todo el perfil de usuario de Chromium.
    -   `"files"` solo borra los archivos listados en `files_to_remove`.
-   **quarantine_dir**: Si `allow_permanent_delete` es `false`, los archivos se moverán aquí en vez de borrarse.
-   **browser_profiles**: Puedes agregar rutas personalizadas de perfiles Chromium si no quieres usar solo las rutas por defecto.

---

## Ejecución del script principal

1. Activa el entorno virtual:
    ```bash
    source .venv/Scripts/activate
    ```
2. Ejecuta el script (se quedará corriendo):
    ```bash
    python src/main.py
    ```

### Comandos administrativos

El sistema incluye comandos administrativos para gestión manual:

```bash
# Consultar usuarios inhabilitados
python src/main.py --consultar-inhabilitados

# Limpiar datos de Chromium de un usuario específico
python src/main.py --eliminar-un-usuario 123

# Limpiar datos de Chromium de todos los usuarios inhabilitados
python src/main.py --eliminar-varios-usuarios

# Cambiar horario de ejecución automática
python src/main.py --cambiar-hora-de-eliminacion --hour 20 --minute 0
```

**Nota importante**: Los comandos de "eliminación" **NO borran usuarios de la base de datos**, sino que **limpian sus datos de navegador** (perfiles, cookies, historial, etc.). Ver [COMANDOS_ADMINISTRATIVOS.md](COMANDOS_ADMINISTRATIVOS.md) para documentación completa.

---

## Pruebas automáticas (tests)

El proyecto incluye tests automáticos para asegurar la funcionalidad y robustez del código.

### ¿Cómo ejecutar los tests?

1. Activa el entorno virtual:
    ```bash
    source .venv/Scripts/activate
    ```
2. Ejecuta todos los tests con:
    ```bash
    pytest -v
    ```
    - El parámetro `-v` muestra el detalle de cada test.
    - Si todo está correcto, verás que todos los tests pasan (`PASSED`).

### ¿Qué cubren los tests?

-   Conexión y manejo de errores de la base de datos.
-   Limpieza de perfiles y archivos de Chromium.
-   Programación y ejecución de tareas automáticas.
-   Validación de la configuración y logging.

### ¿Qué hacer si agregas nuevas funciones?

-   Crea un nuevo archivo de test en la carpeta `tests/` o agrega funciones a los existentes.
-   Usa el patrón `test_*.py` y funciones que comiencen con `test_`.
-   Ejecuta `pytest -v` para verificar que todo sigue funcionando.

**Consejo:** Ejecuta los tests antes y después de hacer cambios importantes para asegurarte de que no se rompe nada.

---

## Pruebas manuales de limpieza de Chromium

Puedes probar la funcionalidad de limpieza de perfiles Chromium siguiendo estos pasos:

1. Configura el archivo `config.json`
    - Asegúrate de que la sección `cleaner` tenga:
        - `"mode": "profile"` para borrar el perfil completo, o `"files"` para borrar archivos específicos.
        - `"dry_run": false` en la sección `safety` para que la limpieza sea real (si solo quieres simular, déjalo en `true`).
        - `"quarantine_dir"` debe existir o ser una ruta válida si no quieres borrar permanentemente.
2. Cierra todas las ventanas de Chromium/Chrome
    - El script intentará cerrarlas, pero es mejor cerrarlas manualmente para evitar conflictos.
3. Ejecuta el script principal
    ```bash
    python src/main.py
    ```
    - Observa los logs en consola y en el archivo de logs para ver el resultado de la limpieza.
4. Verifica la carpeta de cuarentena
    - Si usas cuarentena, revisa que los perfiles o archivos hayan sido movidos correctamente a la ruta indicada.
5. Repite la prueba cambiando parámetros
    - Puedes cambiar `mode`, `files_to_remove`, o activar/desactivar `dry_run` para probar diferentes escenarios.

**Nota:** Si ves errores de "Destination path ... already exists", elimina manualmente la carpeta de cuarentena correspondiente antes de volver a ejecutar la prueba, o pide ayuda para automatizar el manejo de duplicados.

---

## Notas y recomendaciones

-   Revisa los logs para cualquier advertencia o error.
-   Haz respaldos antes de limpiar perfiles reales.
-   Si tienes dudas sobre la configuración, revisa la sección correspondiente arriba.
