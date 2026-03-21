import requests, json, time
from database.db_core import get_db_connection

url = "http://localhost:5000/submit_inventory"
pc_name = "PC-AUDITORIA-X"
sn_fake = f"SERIE-{int(time.time())}"

# 1. PC tiene impresora física
payload_ini = {
    "PC_Nombre": pc_name,
    "Usuario_Actual": "Auditoria\\Admin",
    "OS_Nombre": "Windows 11",
    "Printer_Model": "Samsung Xpress M2020 (STOCK)",
    "Printer_Port": "USB005",
    "Printer_SN": sn_fake
}
requests.post(url, json=payload_ini)
with get_db_connection() as conn:
    row = conn.execute("SELECT printer_sn FROM pcs WHERE pc_name = %s", (pc_name,)).fetchone()
    print(f"DEBUG: SN en PCS tras paso 1: {row['printer_sn']}")

# 2. PROMOVER MANUALMENTE AL CATÁLOGO
with get_db_connection() as conn:
    conn.execute("INSERT INTO network_printers (ip_address, brand_model, serial_number) VALUES (%s, %s, %s)",
                 ("USB005", "Samsung Xpress M2020 (STOCK)", sn_fake))
    pid = conn.execute("SELECT id FROM network_printers WHERE serial_number = %s", (sn_fake,)).fetchone()['id']
    conn.execute("INSERT INTO pc_network_printers (pc_name, printer_id) VALUES (%s, %s)", (pc_name, pid))
    conn.commit()
print("2. Impresora PROMOVIDA al catálogo.")

# 3. PC PIERDE LA IMPRESORA
payload_off = {
    "PC_Nombre": pc_name,
    "Printer_Model": "SIN IMPRESORA",
    "Printer_Port": "N/A",
    "Printer_SN": "N/A"
}
requests.post(url, json=payload_off)
print("3. PC informa SIN IMPRESORA.")

# 4. VERIFICAR
with get_db_connection() as conn:
    exists = conn.execute("SELECT COUNT(*) as c FROM network_printers WHERE serial_number = %s", (sn_fake,)).fetchone()['c']
    if exists == 0:
        print("RESULTADO: ¡ÉXITO! La impresora fue eliminada.")
    else:
        # Ver que hay en la tabla
        debug = conn.execute("SELECT * FROM network_printers WHERE serial_number = %s", (sn_fake,)).fetchone()
        print(f"RESULTADO: FALLO - Data en catálogo: {debug}")
