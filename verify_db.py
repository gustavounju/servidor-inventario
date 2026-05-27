import os
from dotenv import load_dotenv
import pymysql.cursors

load_dotenv()

def verify():
    # Conectarse localmente a la DB para verificar
    connection = pymysql.connect(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASS', 'tdg729tdg'),
        database=os.getenv('DB_NAME', 'inventario_dev'),
        port=int(os.getenv('DB_PORT', 3306)),
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        with connection.cursor() as cursor:
            # 1. Host
            cursor.execute("SELECT pc_name, printer_sn FROM pcs WHERE pc_name = %s", ('HOST-TEST-01',))
            host = cursor.fetchone()
            print(f"HOST-TEST-01: Serial={host['printer_sn']}")

            # 2. Cliente
            cursor.execute("SELECT pc_name, printer_sn, printer_port FROM pcs WHERE pc_name = %s", ('CLIENTE-TEST-02',))
            client = cursor.fetchone()
            print(f"CLIENTE-TEST-02: Port={client['printer_port']} Serial={client['printer_sn']}")

            if host['printer_sn'] == client['printer_sn']:
                print("\n✅ EXITO: El cliente heredó el serial correctamente.")
            else:
                print("\n❌ FALLO: El serial no coincide.")

    finally:
        connection.close()

if __name__ == "__main__":
    verify()
