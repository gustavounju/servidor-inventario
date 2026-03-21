import requests, json
url = "http://localhost:5000/submit_inventory"
payload = {
    "PC_Nombre": "PC-TEST-SIMULADA",
    "Usuario_Actual": "Tecnico\\Simulacion",
    "Fecha_Reporte": "2026-03-21 00:30:00",
    "Sistema": {
        "OsName": "Windows 10 Pro",
        "Procesador": "Intel i5-12400",
        "RAM (GB)": 16.0
    },
    "Red": [{"IPAddress": "10.0.0.123"}],
    "Printer_Model": "Brother HL-L2350DW (SIMULADA)",
    "Printer_Port": "192.168.1.50 (Red)",
    "Salud": {
        "Uptime_Dias": 1.2,
        "Discos_SMART": [{"Model": "NVMe SSD", "Status": "OK"}]
    }
}
try:
    r = requests.post(url, json=payload)
    print(f"Status: {r.status_code}, Response: {r.text}")
except Exception as e:
    print(f"Error: {e}")
