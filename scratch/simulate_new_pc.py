import requests
import json
import datetime

def simulate_new_pc():
    url = "http://localhost:5000/submit_inventory"
    
    data = {
        "PC_Nombre": "PC-TEST-OFFICE",
        "Usuario_Actual": "ELIAS\\Gustavo",
        "Fecha_Reporte": str(datetime.datetime.now()),
        "Sistema": {
            "OsName": "Microsoft Windows 11 Pro",
            "Procesador": "Intel Core i7-12700K",
            "RAM (GB)": 16.0,
            "Office": "Microsoft Office Professional Plus 2021"
        },
        "Red": [{"IPAddress": "192.168.1.100"}],
        "RAM_Detalles": "16GB @ 3200MHz",
        "Disk_Models": "Samsung SSD 980 1TB",
        "Disk_Speeds_RPM": "SSD",
        "Motherboard_Model": "ASUSTeK PRIME Z690-P",
        "Printer_Model": "HP LaserJet Pro M404n",
        "Printer_Port": "192.168.1.50",
        "Printer_SN": "PHC3X42010",
        "Salud": {
            "Uptime_Dias": 2.5,
            "Discos_SMART": [{"Model": "Samsung SSD 980", "Status": "OK", "DeviceID": "0"}],
            "Discos_Espacio": [{"Letter": "C:", "FreeGB": 450, "TotalGB": 1000, "PctFree": 45}],
            "Eventos_Criticos": []
        },
        "Seguridad_Extra": {
            "Antivirus": "Windows Defender",
            "Startup": [{"Name": "OneDrive", "Command": "C:\\Program Files\\Microsoft OneDrive\\OneDrive.exe /background"}]
        }
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print("PC-TEST-OFFICE simulada con éxito!")
            print("Visita el Dashboard para verla.")
        else:
            print(f"Error al simular: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"No se pudo conectar al servidor: {e}")
        print("Asegúrate de que el servidor Flask esté corriendo en http://localhost:5000")

if __name__ == "__main__":
    simulate_new_pc()
