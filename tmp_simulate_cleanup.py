import requests, json
from database.db_core import get_db_connection

pc_name = "PC-SIMULA-LIMPIEZA"
url = "http://localhost:5000/submit_inventory"

# 1. Preparar: Crear PC y asignar impresora en DB (Supongamos IP 192.168.1.9 que es la Brother)
with get_db_connection() as conn:
    # Asegurar que la PC existe
    conn.execute("INSERT IGNORE INTO pcs (pc_name, is_active) VALUES (%s, 'True')", (pc_name,))
    # Obtener ID de la impresora Brother (1.9)
    printer = conn.execute("SELECT id FROM network_printers WHERE ip_address = '192.168.1.9'").fetchone()
    if printer:
        printer_id = printer['id']
        # Forzar asignación previa
        conn.execute("DELETE FROM pc_network_printers WHERE pc_name = %s", (pc_name,))
        conn.execute("INSERT INTO pc_network_printers (pc_name, printer_id) VALUES (%s, %s)", (pc_name, printer_id))
        print(f"Paso 1: PC {pc_name} tiene asignada la impresora ID {printer_id} (192.168.1.9)")
    conn.commit()

# 2. Simular Inventario SIN IMPRESORA
payload = {
    "PC_Nombre": pc_name,
    "Usuario_Actual": "Tecnico\\Limpieza",
    "Printer_Model": "SIN IMPRESORA",
    "Printer_Port": "N/A"
}
r = requests.post(url, json=payload)
print(f"Paso 2: Inventario 'Limpio' enviado. Status: {r.status_code}")

# 3. Verificar si se desvinculo
with get_db_connection() as conn:
    check = conn.execute("SELECT * FROM pc_network_printers WHERE pc_name = %s", (pc_name,)).fetchall()
    if not check:
        print(f"Paso 3: ¡ÉXITO! PC {pc_name} ya no tiene impresoras asignadas.")
    else:
        print(f"Paso 3: FALLO. Aun tiene asignadas: {len(check)}")
