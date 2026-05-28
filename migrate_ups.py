import os
import sys
from dotenv import load_dotenv
import pymysql

# Cargar variables de entorno para la base de datos
load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASS', '')
DB_NAME = os.getenv('DB_NAME', 'inventory_db')

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

def migrate_ups():
    print("Iniciando migración de UPS mal categorizadas...")
    migradas = 0
    errores = 0

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Buscar todos los componentes guardados como 'UPS' o similar en la tabla de componentes genérica
            cursor.execute("SELECT * FROM components WHERE component_type LIKE '%UPS%' AND component_type != 'Batería UPS'")
            ups_components = cursor.fetchall()
            
            if not ups_components:
                print("No se encontraron UPS mal categorizadas en la tabla 'components'.")
                return

            print(f"Se encontraron {len(ups_components)} equipos UPS para migrar.")

            for comp in ups_components:
                code = comp['serial_number']
                model = comp['brand_model']
                supplier = comp['supplier']
                invoice = comp['invoice_number']
                comp_id = comp['id']
                
                # Asumimos que si tiene assigned_pc es que estaba instalado, pero 'status' en la tabla
                # components era 'Stock', 'Installed', etc.
                assigned_pc = comp['assigned_pc'] if comp['status'] == 'Installed' else None

                print(f"  -> Migrando S/N: {code} | Modelo: {model}")
                try:
                    # 1. Insertar en ups_inventory
                    cursor.execute("""
                        INSERT IGNORE INTO ups_inventory (code, model, supplier, invoice_number, assigned_pc)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (code, model, supplier, invoice, assigned_pc))
                    
                    # 2. Borrar de components
                    cursor.execute("DELETE FROM components WHERE id = %s", (comp_id,))
                    migradas += 1
                except Exception as e:
                    print(f"    [Error] No se pudo migrar {code}: {str(e)}")
                    errores += 1

            conn.commit()
            print(f"Migración completada. Éxitos: {migradas}, Errores: {errores}.")
    except Exception as e:
        print(f"Error crítico conectando a la BD: {str(e)}")
    finally:
        if 'conn' in locals() and conn.open:
            conn.close()

if __name__ == '__main__':
    migrate_ups()
