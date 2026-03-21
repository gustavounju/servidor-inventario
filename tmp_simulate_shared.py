import requests, json
url = "http://localhost:5000/submit_inventory"

# 1. Host - PHYSICAL (USB)
payload_host = {
    "PC_Nombre": "PC-DESPACHO-A",
    "Usuario_Actual": "AreaA\\Jefe",
    "Fecha_Reporte": "2026-03-21 01:40:00",
    "Printer_Model": "HP LaserJet M15w (SIMULADA)",
    "Printer_Port": "USB001 (Local)",
    "Printer_SN": "HP-USB-M15-99"
}

# 2. Client - NETWORK (SHARED)
payload_client = {
    "PC_Nombre": "PC-SECRETARIA-B",
    "Usuario_Actual": "AreaA\\SecB",
    "Fecha_Reporte": "2026-03-21 01:42:00",
    "Printer_Model": "HP LaserJet M15w (SIMULADA-NETWORK)",
    "Printer_Port": "\\\\PC-DESPACHO-A\\HP_LaserJet",
    "Printer_SN": "HP-USB-M15-99" # A veces Windows lo reporta, a veces no. Lo incluimos para que la auto-sincronización lo capture.
}

try:
    r1 = requests.post(url, json=payload_host)
    print(f"Host: {r1.status_code}")
    r2 = requests.post(url, json=payload_client)
    print(f"Client: {r2.status_code}")
except Exception as e:
    print(f"Error: {e}")
