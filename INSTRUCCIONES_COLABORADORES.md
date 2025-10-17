# 📋 Instrucciones para Colaboradores - Browser Data Control

## 🚀 **Instrucciones de Instalación y Uso**

### **PASO 1: Descargar Chromium** 🌐

1. Ve a: **https://download-chromium.appspot.com/**
2. Haz click en **"Download Chromium"**
3. Se descargará un archivo ZIP llamado `chrome-win.zip`

### **PASO 2: Instalar Chromium** 📁

1. **Extrae** el archivo `chrome-win.zip`
2. Se creará una carpeta llamada `chrome-win`
3. **Mueve** esta carpeta a una ubicación permanente:
    - Recomendado: `C:\chrome-win\` (raíz del disco C)
    - Alternativa: Mantener en `Downloads` o `Desktop`

### **PASO 3: Ejecutar el Cliente** ⚡

1. **Recibe** el archivo EXE personalizado de tu supervisor:

    - Ejemplo: `browser_cleaner_user_663_20251117.exe`

2. **Ejecuta** el archivo haciendo doble-click

3. **Verifica** la salida en consola (se abrirá una ventana negra):

    ```
    ============================================================
    Browser Data Control Client
    ============================================================
    Practitioner ID: 663
    Fecha fin convenio: 2025-11-17

    [STEP 1] Registrando sistema en base de datos...
    [INFO] Conectando a BD: sql.freedb.tech
    [INFO] Registrando sistema: usuario123 - 192.168.1.100
    [SUCCESS] Sistema registrado en BD

    [STEP 2] Verificando fecha de convenio...
    [INFO] Perfil Chromium encontrado: C:\chrome-win\User Data
    [SUCCESS] Cliente iniciado exitosamente
    [INFO] Limpieza programada para: 2025-11-17 (32 dias)
    [INFO] Ejecutandose en segundo plano...
    ```

### **PASO 4: Uso Normal** 🖥️

1. **Abre Chromium** desde `C:\chrome-win\chrome.exe`
2. **Navega normalmente** - crea bookmarks, historial, etc.
3. **El cliente corre en segundo plano** automáticamente
4. **Mantén abierta** la ventana de consola negra (NO la cierres)

> **⚠️ IMPORTANTE**: La ventana de consola negra debe permanecer abierta. Si la cierras, el cliente dejará de funcionar.

### **PASO 5: Limpieza Automática** 🧹

-   **Fecha programada**: Se ejecuta automáticamente en la fecha de fin de convenio
-   **Proceso automático**:
    1. Cierra Chromium si está abierto
    2. Elimina todos los datos de navegación
    3. El cliente se cierra automáticamente

## 🔍 **Ubicaciones de Chromium Detectadas**

El sistema buscará Chromium en estas ubicaciones:

### **Instalaciones Manuales** (Recomendadas)

-   `C:\chrome-win\User Data` ⭐
-   `C:\Users\[usuario]\Downloads\chrome-win\User Data`
-   `C:\Users\[usuario]\Desktop\chrome-win\User Data`

### **Instalaciones Estándar**

-   `C:\Users\[usuario]\AppData\Local\Chromium\User Data`
-   `C:\Users\[usuario]\AppData\Local\Google\Chrome\User Data`
-   `C:\Program Files\Chromium\User Data`

## ⚠️ **Importante**

1. **NO muevas** la carpeta `chrome-win` después de instalar
2. **Mantén abierto** el cliente todo el tiempo
3. **No elimines** archivos del sistema manualmente
4. **El proceso es automático** - no requiere intervención

## 🆘 **Solución de Problemas**

### **Error: "No se encontraron perfiles de Chromium"**

-   ✅ Verifica que Chromium esté instalado en `C:\chrome-win\`
-   ✅ Ejecuta Chromium al menos una vez para crear el perfil
-   ✅ Verifica que existe la carpeta `User Data`

### **Error: "Error registrando en BD"**

-   ✅ Verifica conexión a Internet
-   ✅ El sistema continuará funcionando sin registro
-   ✅ Contacta al supervisor si persiste

### **Cliente no responde**

-   ✅ Cierra y vuelve a abrir el cliente
-   ✅ Verifica que no hay múltiples copias ejecutándose
-   ✅ Contacta soporte técnico

## 📞 **Soporte**

Para dudas o problemas contactar al administrador del sistema.

---

**Versión**: 1.0  
**Fecha**: 2025-10-16
