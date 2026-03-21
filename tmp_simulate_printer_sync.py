import requests, json
url = "http://localhost:5000/submit_inventory"
payload = {
    "PC_Nombre": "PC-AUTO-SYNC-TEST",
    "Usuario_Actual": "Tecnico\\Simulacion",
    "Fecha_Reporte": "2026-03-21 00:33:00",
    "Red": [{"IPAddress": "10.0.0.124"}],
    "Printer_Model": "Brother HL-2270DW (EXISTENTE)",
    "Printer_Port": "192.168.1.9 (Red)"
}
r = requests.post(url, json=payload)
print(f"Status: {r.status_code}, Response: {r.text}")
