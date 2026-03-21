import requests, json
url = "http://localhost:5000/submit_inventory"
payload = {
    "PC_Nombre": "PC-GUSTAVO-LOCAL",
    "Usuario_Actual": "Gustavo\\Pruebas",
    "Fecha_Reporte": "2026-03-21 01:15:00",
    "Printer_Model": "Samsung Xpress M2020 (SIMULADA)",
    "Printer_Port": "USB001 (Local)",
    "Printer_SN": "Z780B34L900123"
}
try:
    r = requests.post(url, json=payload)
    print(f"Status: {r.status_code}, Response: {r.text}")
except Exception as e:
    print(f"Error: {e}")
