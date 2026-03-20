
import sys
import os
from datetime import datetime

# Añadir el directorio actual al path para importar database.db_core
sys.path.append(os.getcwd())

from database.db_core import get_db_connection

mock_pcs = [
    {
        "pc_name": "TEC-ADMIN-01",
        "last_user": "Ana Lopez",
        "fuero": "Contencioso",
        "ip_address": "192.168.10.11",
        "os_name": "Windows 10 Pro",
        "ram_gb": 8.0,
        "processor": "Intel Core i5-8500"
    },
    {
        "pc_name": "TEC-ADMIN-02",
        "last_user": "Luis Gomez",
        "fuero": "Laboral",
        "ip_address": "192.168.10.12",
        "os_name": "Windows 11 Pro",
        "ram_gb": 16.0,
        "processor": "AMD Ryzen 5 5600X"
    },
    {
        "pc_name": "PENAL-SEC-03",
        "last_user": "Marcos Paz",
        "fuero": "Penal",
        "ip_address": "192.168.20.15",
        "os_name": "Windows 7 Professional",
        "ram_gb": 4.0,
        "processor": "Intel Core i3-4160"
    },
    {
        "pc_name": "CIVIL-MESA-04",
        "last_user": "Julia Perez",
        "fuero": "Civil",
        "ip_address": "192.168.30.22",
        "os_name": "Windows 10 Home",
        "ram_gb": 8.0,
        "processor": "Intel Core i5-7400"
    },
    {
        "pc_name": "SOPORTE-NOTE-05",
        "last_user": "Carlos Ruiz",
        "fuero": "Soporte",
        "ip_address": "192.168.50.100",
        "os_name": "Windows 10 Pro",
        "ram_gb": 12.0,
        "processor": "Intel Core i7-10510U"
    }
]

def seed():
    try:
        with get_db_connection() as conn:
            now_dt = datetime.now()
            for pc in mock_pcs:
                print(f"Insertando {pc['pc_name']}...")
                query = """
                    INSERT INTO pcs (pc_name, last_user, fuero, ip_address, os_name, ram_gb, processor, is_active, last_report)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'True', %s)
                    ON DUPLICATE KEY UPDATE 
                        last_user=%s, fuero=%s, ip_address=%s, os_name=%s, ram_gb=%s, processor=%s, last_report=%s
                """
                params = (
                    pc['pc_name'], pc['last_user'], pc['fuero'], pc['ip_address'], pc['os_name'], pc['ram_gb'], pc['processor'], now_dt,
                    pc['last_user'], pc['fuero'], pc['ip_address'], pc['os_name'], pc['ram_gb'], pc['processor'], now_dt
                )
                conn.execute(query, params)
            print("Siembra completada con éxito.")
    except Exception as e:
        print(f"Error al sembrar: {e}")

if __name__ == "__main__":
    seed()
