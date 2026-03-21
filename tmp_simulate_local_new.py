import requests, json
url = "http://localhost:5000/submit_inventory"
payload = {
    "PC_Nombre": "PC-SECRETARIA-B",
    "Usuario_Actual": "AreaA\\SecB",
    "Fecha_Reporte": "2026-03-21 01:55:00",
    "Printer_Model": "HP LaserJet P1102 (NUEVA LOCAL)",
    "Printer_Port": "USB001 (Local)",
    "Printer_SN": "XYZ-SERIE-PROPIA-77"
}
try:
    r = requests.post(url, json=payload)
    print(f"Status: {r.status_code}, Response: {r.text}")
except Exception as e:
    print(f"Error: {e}")
