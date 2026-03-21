import requests, json
url = "http://localhost:5000/submit_inventory"

# El Host desinstala la impresora
payload_host_offline = {
    "PC_Nombre": "PC-DESPACHO-A",
    "Usuario_Actual": "AreaA\\Jefe",
    "Fecha_Reporte": "2026-03-21 02:10:00",
    "Printer_Model": "SIN IMPRESORA",
    "Printer_Port": "N/A",
    "Printer_SN": "N/A"
}

try:
    r = requests.post(url, json=payload_host_offline)
    print(f"Host Offline Report: {r.status_code}")
except Exception as e:
    print(f"Error: {e}")
