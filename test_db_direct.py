#!/usr/bin/env python3
"""
Test directo de conexión a base de datos
"""

import pymysql
import socket
import os

# Configuración de BD
DB_CONFIG = {
    'host': 'sql.freedb.tech',
    'user': 'freedb_practitioners',
    'password': 'eeg93*TtDH&qK!P',
    'database': 'freedb_test-bot-devconsulting'
}

def test_database_connection():
    """Prueba conexión directa a BD"""
    try:
        print("🔍 Probando conexión a base de datos...")
        print(f"Host: {DB_CONFIG['host']}")
        print(f"Database: {DB_CONFIG['database']}")
        print(f"User: {DB_CONFIG['user']}")
        
        # Obtener info del sistema
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        username = os.getenv("USERNAME", "unknown")
        practitioner_id = 663  # ID de prueba
        
        print(f"\nInfo del sistema:")
        print(f"- Usuario: {username}")
        print(f"- IP: {local_ip}")
        print(f"- Hostname: {hostname}")
        print(f"- Practitioner ID: {practitioner_id}")
        
        # Conectar
        print("\n📡 Conectando...")
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'], 
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10
        )
        
        print("✅ Conexión exitosa!")
        
        with conn.cursor() as cursor:
            # Verificar tabla
            cursor.execute("SHOW TABLES LIKE 'practitioner_system_users'")
            table_exists = cursor.fetchone()
            
            if table_exists:
                print("✅ Tabla practitioner_system_users existe")
                
                # Verificar estructura
                cursor.execute("DESCRIBE practitioner_system_users")
                columns = cursor.fetchall()
                print("\n📋 Estructura de tabla:")
                for col in columns:
                    print(f"  - {col['Field']}: {col['Type']}")
                
                # Verificar registros existentes
                cursor.execute("SELECT COUNT(*) as total FROM practitioner_system_users")
                count = cursor.fetchone()
                print(f"\n📊 Registros existentes: {count['total']}")
                
                # Intentar insertar registro de prueba
                print(f"\n💾 Insertando registro de prueba...")
                
                # Verificar si ya existe
                sql_check = """
                    SELECT practitioner_id FROM practitioner_system_users 
                    WHERE practitioner_id = %s AND system_username = %s
                """
                cursor.execute(sql_check, (practitioner_id, username))
                existing = cursor.fetchone()
                
                if existing:
                    print(f"🔄 Registro existe, actualizando...")
                    sql_update = """
                        UPDATE practitioner_system_users 
                        SET ip_address = %s
                        WHERE practitioner_id = %s AND system_username = %s
                    """
                    cursor.execute(sql_update, (local_ip, practitioner_id, username))
                    print("✅ Registro actualizado")
                else:
                    print(f"➕ Creando nuevo registro...")
                    sql_insert = """
                        INSERT INTO practitioner_system_users 
                        (practitioner_id, system_username, ip_address)
                        VALUES (%s, %s, %s)
                    """
                    cursor.execute(sql_insert, (practitioner_id, username, local_ip))
                    print("✅ Registro creado")
                
                conn.commit()
                print("💾 Cambios guardados")
                
                # Verificar resultado
                cursor.execute("SELECT * FROM practitioner_system_users WHERE practitioner_id = %s", (practitioner_id,))
                records = cursor.fetchall()
                print(f"\n📋 Registros para practitioner {practitioner_id}:")
                for record in records:
                    print(f"  Usuario: {record['system_username']}, IP: {record['ip_address']}")
                
            else:
                print("❌ Tabla practitioner_system_users NO existe")
        
        conn.close()
        print("\n🎉 Test completado exitosamente!")
        return True
        
    except Exception as e:
        print(f"\n💥 Error: {e}")
        print(f"Tipo: {type(e).__name__}")
        return False

if __name__ == "__main__":
    test_database_connection()
    input("\nPresiona Enter para cerrar...")