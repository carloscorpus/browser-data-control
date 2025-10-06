# Comandos Administrativos - Browser Data Control

Este documento describe los comandos administrativos disponibles en el sistema Browser Data Control.

## 📋 Comandos Disponibles

### 1. Consultar Usuarios Inhabilitados

```bash
python main.py --consultar-inhabilitados
```

**Descripción**: Muestra una lista de todos los usuarios que tienen status 'I' (Inactivo/Inhabilitado) en la base de datos.

**Ejemplo de salida**:

```
📋 USUARIOS INHABILITADOS (3 encontrados):
==================================================
ID         STATUS
--------------------------------------------------
428        I
663        I
678        I
==================================================
```

### 2. Limpiar Datos de un Usuario Específico

```bash
python main.py --eliminar-un-usuario <ID>
```

**Descripción**: Limpia todos los datos de Chromium/Chrome de un usuario específico mediante su ID, independientemente de si está inhabilitado o no. **NO elimina el usuario de la base de datos**.

**Ejemplo**:

```bash
python main.py --eliminar-un-usuario 428
```

**Proceso**:

1. Verifica que el usuario existe en la base de datos
2. Muestra la información del usuario
3. Solicita confirmación (s/N)
4. Ejecuta limpieza de datos de navegador (perfiles, cookies, etc.)
5. Los datos se mueven a cuarentena o se eliminan según configuración

**Importante**: Esta operación limpia datos de navegador, no elimina registros de la base de datos.

### 3. Limpiar Datos de Varios Usuarios (Inhabilitados)

```bash
python main.py --eliminar-varios-usuarios
```

**Descripción**: Limpia los datos de Chromium/Chrome de todos los usuarios que tengan status 'I' (Inhabilitado) de una sola vez. **NO elimina usuarios de la base de datos**.

**Proceso**:

1. Consulta automáticamente los usuarios inhabilitados
2. Muestra cuántos usuarios serán afectados y qué se hará
3. Solicita confirmación
4. Realiza la limpieza masiva de datos de navegador
5. Reporta el resultado de la operación

**Importante**:

-   Solo limpia datos de navegador, preserva registros en la base de datos
-   Afecta a todos los perfiles de Chromium detectados en el sistema
-   Los datos se procesan según la configuración de cuarentena

```bash
python main.py --eliminar-varios-usuarios
```

**Descripción**: Elimina todos los usuarios que tengan status 'I' (Inhabilitado) de una sola vez.

**Proceso**:

1. Consulta automáticamente los usuarios inhabilitados
2. Muestra cuántos usuarios se eliminarán
3. Solicita confirmación
4. Realiza la eliminación masiva

### 4. Cambiar Hora de Eliminación

```bash
python main.py --cambiar-hora-de-eliminacion --day "<día>" --hour <hora> --minute <minuto>
```

**Descripción**: Modifica dinámicamente la configuración del scheduler en el archivo `config.json`.

**Parámetros**:

-   `--day`: Día de la semana ("\*" para todos los días, "0"=Domingo, "1"=Lunes, etc.)
-   `--hour`: Hora en formato 24h (0-23)
-   `--minute`: Minuto (0-59)

**Ejemplos**:

```bash
# Cambiar solo la hora
python main.py --cambiar-hora-de-eliminacion --hour 20

# Cambiar hora y minutos
python main.py --cambiar-hora-de-eliminacion --hour 18 --minute 30

# Cambiar todo (ejecutar solo los lunes a las 14:15)
python main.py --cambiar-hora-de-eliminacion --day "1" --hour 14 --minute 15

# Ejecutar todos los días a las 23:59
python main.py --cambiar-hora-de-eliminacion --day "*" --hour 23 --minute 59
```

## 🔒 Seguridad y Confirmaciones

-   **Eliminaciones**: Todos los comandos de eliminación requieren confirmación explícita
-   **Validaciones**: Se validan rangos de hora (0-23) y minutos (0-59)
-   **Logging**: Todas las operaciones quedan registradas en el log del sistema
-   **Rollback**: Los cambios de configuración muestran antes/después para verificación

## 💡 Casos de Uso Típicos

### Mantenimiento Diario

1. Consultar usuarios inhabilitados
2. Revisar si hay usuarios que deban eliminarse
3. Eliminar usuarios específicos si es necesario

### Configuración de Horarios

-   Cambiar horario de limpieza según necesidades del negocio
-   Configurar ejecución en horarios de menor uso
-   Adaptar horarios según zona horaria

### Limpieza Masiva

-   Eliminar todos los usuarios inhabilitados de una vez
-   Útil para limpieza periódica de la base de datos

## 🚀 Integración con el Sistema Principal

Los comandos administrativos son completamente independientes del modo normal de operación:

```bash
# Modo normal (monitoreo continuo)
python main.py

# Modo administrativo (comandos puntuales)
python main.py --consultar-inhabilitados
```

## 📊 Resultados y Logging

Todos los comandos administrativos:

-   ✅ Proporcionan feedback visual inmediato
-   📝 Registran operaciones en el log del sistema
-   🔍 Muestran información detallada antes de acciones destructivas
-   ⚠️ Manejan errores de manera amigable

## 🛠️ Implementación Técnica

-   **Módulo**: `admin_commands.py`
-   **Base de datos**: Utiliza el mismo `DBManager` que el sistema principal
-   **Configuración**: Modifica directamente `config/config.json`
-   **Logging**: Integrado con el sistema de logging existente
