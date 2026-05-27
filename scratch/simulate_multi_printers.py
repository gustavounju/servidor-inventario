import requests
import json
import datetime

url = "http://127.0.0.1:5000/submit_inventory"

# Payload simulando una PC con múltiples impresoras
payload = {
    "PC_Nombre": "PC-TEST-PRINTERS",
    "Usuario_Actual": "SimulatedUser",
    "Fecha_Reporte": str(datetime.datetime.now()),
    "Sistema": {
        "OsName": "Windows 10 Pro",
        "Procesador": "Intel Core i7-10700",
        "RAM (GB)": 16,
        "Office": "Office 2019"
    },
    "Red": [
        {
            "IPAddress": "192.168.1.100",
            "MACAddress": "AA:BB:CC:DD:EE:FF"
        }
    ],
    "RAM_Detalles": "16GB DDR4",
    "Disk_Models": "Samsung SSD 970 EVO 500GB",
    "Disk_Speeds_RPM": "SSD",
    "Motherboard_Model": "ASUS ROG STRIX Z490-E",
    
    # Impresora principal (la que detecta por defecto)
    "Printer_Model": "HP LaserJet Pro M404n",
    "Printer_Port": "USB001",
    "Printer_SN": "VNB3K12345",
    
    # NUEVA FUNCIONALIDAD: Impresoras extra detectadas
    "Printers_Extra": [
        {
            "Model": "HP LaserJet Pro M404n",
            "Port": "USB001",
            "SN": "VNB3K12345"
        },
        {
            "Model": "Epson L3110 Series",
            "Port": "USB002",
            "SN": "X4Y7000001"
        },
        {
            "Model": "Microsoft Print to PDF",
            "Port": "PORTPROMPT:",
            "SN": "N/A"
        },
        {
            "Model": "Fax (Useless Virtual)",
            "Port": "SHRFAX:",
            "SN": "N/A"
        },
        {
            "Model": "OneNote (Desktop)",
            "Port": "nul:",
            "SN": "N/A"
        }
    ],
    
    "Salud": {
        "Discos_SMART": [{"Status": "OK"}],
        "Discos_Espacio": [{"Drive": "C:", "FreeGB": 250}],
        "Uptime_Dias": 1.5
    }
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
