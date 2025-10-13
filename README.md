# Browser Data Control

Sistema administrativo profesional para el control y limpieza automatizada de datos de navegador Chromium/Chrome. Incluye interfaz gráfica de administración, gestión de usuarios con base de datos MySQL, y generación de EXE personalizados.

## ✨ **Características Principales**

-   🖥️ **Interfaz Administrativa Profesional** - GUI moderna con Tkinter para gestión completa
-   🔐 **Sistema de Autenticación** - Login seguro con validación de credenciales en base de datos
-   👥 **Gestión de Usuarios** - Visualización, búsqueda y administración de practitioners
-   📦 **Generación de EXE Personalizados** - Creación de ejecutables específicos por usuario
-   📅 **Fechas Automáticas** - Lectura automática de fechas de fin de convenio desde BD
-   🔍 **Validación en Tiempo Real** - Verificación inmediata de IDs y estados de usuario
-   🗄️ **Integración MySQL** - Conexión directa con base de datos de producción
-   🧹 **Limpieza Automatizada** - Limpieza programada de datos de navegador Chromium/Chrome

---

## 📋 **Requisitos del Sistema**

-   **Sistema Operativo:** Windows 10/11
-   **Python:** 3.13+ (recomendado)
-   **Base de Datos:** MySQL Server
-   **Navegador:** Chromium/Chrome instalado
-   **Dependencias:** Ver `requirements.txt`

---

## ⚙️ **Instalación y Configuración**

### 1. **Configuración del Entorno**

```bash
# Clonar repositorio
git clone [repo-url]
cd browser-data-control

# Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. **Configuración de Base de Datos**

Editar `src/config/config.json`:

```json
{
	"db": {
		"host": "sql.freedb.tech",
		"port": 3306,
		"user": "tu_usuario",
		"password": "tu_contraseña",
		"database": "tu_base_datos"
	}
}
```

### 3. **Estructura de Base de Datos Requerida**

```sql
-- Tabla practitioners (requerida)
CREATE TABLE practitioners (
    practitioner_id INT PRIMARY KEY,
    practitioner_status CHAR(1), -- 'A' = Activo, 'I' = Inactivo
    practitioner_date_end DATE   -- Fecha fin de convenio (campo virtual generado)
);

-- Tabla admin_users (para login)
CREATE TABLE admin_users (
    username VARCHAR(50) PRIMARY KEY,
    password_hash VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE
);
```

---

## 🚀 **Uso de la Aplicación**

### **Ejecutar Interfaz Administrativa**

```bash
# Activar entorno
.venv\Scripts\activate

# Ejecutar aplicación admin
python admin_app/main.py
```

### **Flujo de Trabajo Principal**

1. **🔑 Login Administrativo**

    - Ingresar credenciales de administrador
    - Validación automática con base de datos

2. **👥 Gestión de Usuarios**

    - Ver lista completa de practitioners
    - Buscar por ID, nombre o estado
    - Visualizar detalles completos de usuario
    - Ejecutar limpieza manual por usuario

3. **📦 Generación de EXE**
    - Ingresar ID de practitioner objetivo
    - Validar usuario con botón "🔍 Validar"
    - Verificar fecha de fin de convenio automática
    - Validar configuración completa
    - Generar EXE personalizado

### **Controles Principales**

-   **🔍 Validar:** Verifica ID de usuario y muestra información
-   **🔍 Validar Configuración:** Confirma que todos los datos son correctos
-   **🚀 Generar EXE Personalizado:** Crea ejecutable específico para el usuario
-   **🧹 Limpiar Usuario:** Ejecuta limpieza inmediata de datos del navegador

---

## 🛠️ **Configuración Avanzada**

### **Modos de Limpieza**

-   **`profile`:** Elimina perfil completo de usuario
-   **`files`:** Elimina archivos específicos (cookies, historial, etc.)

### **Opciones de Seguridad**

```json
{
	"safety": {
		"dry_run": false, // true = simulación, false = ejecución real
		"allow_permanent_delete": false, // true = borrado permanente
		"quarantine_dir": "C:/browser-data-control/quarantine"
	}
}
```

### **Archivos de Limpieza Específica**

```json
{
	"cleaner": {
		"files_to_remove": [
			"Login Data", // Contraseñas guardadas
			"Cookies", // Cookies de sitios web
			"Web Data", // Datos de formularios
			"Local Storage", // Almacenamiento local
			"History" // Historial de navegación
		]
	}
}
```

---

## 🔧 **Línea de Comandos (Legacy)**

> **Nota:** La interfaz gráfica es la forma recomendada de usar el sistema. Los comandos CLI siguen disponibles para automatización.

```bash
# Consultar usuarios inactivos
python src/main.py --consultar-inhabilitados

# Limpiar usuario específico
python src/main.py --eliminar-un-usuario 123

# Limpiar todos los usuarios inactivos
python src/main.py --eliminar-varios-usuarios

# Cambiar horario de limpieza automática
python src/main.py --cambiar-hora-de-eliminacion --hour 20 --minute 0
```

---

## 🧪 **Testing y Calidad**

### **Ejecutar Tests Automáticos**

```bash
# Tests completos
pytest -v

# Tests específicos por módulo
pytest tests/test_db_manager.py -v
pytest tests/test_cleaner.py -v
pytest tests/test_scheduler.py -v
```

### **Cobertura de Testing**

-   ✅ Conexión y operaciones de base de datos
-   ✅ Limpieza de perfiles Chromium
-   ✅ Validación de usuarios y fechas
-   ✅ Sistema de programación de tareas
-   ✅ Manejo de errores y excepciones

---

## 📊 **Estructura del Proyecto**

```
browser-data-control/
├── admin_app/                 # Interfaz administrativa (GUI)
│   ├── main.py               # Punto de entrada de la aplicación
│   ├── src/
│   │   ├── ui/
│   │   │   ├── login_window.py    # Ventana de login
│   │   │   └── main_window.py     # Interfaz principal
│   │   └── services/
│   │       ├── db_service.py      # Servicios de base de datos
│   │       └── user_service.py    # Gestión de usuarios
├── src/                      # Core del sistema (CLI)
│   ├── main.py              # Script principal CLI
│   ├── config/              # Archivos de configuración
│   └── core/                # Módulos principales
├── tests/                   # Tests automáticos
└── logs/                    # Archivos de log
```

---

## 🚨 **Notas Importantes de Seguridad**

-   ⚠️ **Respaldos:** Siempre hacer backup antes de limpiezas masivas
-   🔒 **Credenciales:** No compartir credenciales de base de datos
-   🛡️ **Permisos:** Ejecutar con permisos administrativos cuando sea necesario
-   📝 **Logs:** Revisar logs regularmente para detectar anomalías
-   🔍 **Validación:** Siempre validar IDs antes de ejecutar limpiezas

---

## 📈 **Próximas Funcionalidades**

-   🔄 **Sistema Heartbeat:** Validación automática en tiempo real
-   🏗️ **PyInstaller:** Generación real de ejecutables standalone
-   📊 **Dashboard:** Métricas y estadísticas de uso
-   🔔 **Notificaciones:** Alertas automáticas de eventos importantes

---

## 🆘 **Soporte y Mantenimiento**

### **Logs del Sistema**

-   **Ubicación:** `logs/browser-data-control.log`
-   **Nivel:** INFO, DEBUG, WARNING, ERROR
-   **Rotación:** Automática por tamaño

### **Resolución de Problemas Comunes**

| Problema              | Causa                      | Solución                    |
| --------------------- | -------------------------- | --------------------------- |
| Error de conexión DB  | Credenciales incorrectas   | Verificar `config.json`     |
| Usuario no encontrado | ID inexistente             | Validar ID en base de datos |
| Error de permisos     | Falta acceso administrador | Ejecutar como administrador |
| Chromium en uso       | Navegador abierto          | Cerrar todas las ventanas   |

### **Contacto**

-   **Desarrollador:** [Nombre del desarrollador]
-   **Repositorio:** [URL del repositorio]
-   **Documentación:** Ver archivos `/docs` para detalles técnicos
