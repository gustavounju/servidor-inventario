import requests
import time
import sys

BASE_URL = "http://127.0.0.1:5000/submit_inventory"

# 1. PC HOST (Con impresora USB y Serial real)
host_data = {
    "PC_Nombre": "HOST-TEST-01",
    "Usuario_Actual": "Tecnico_Ejemplo",
    "Sistema": {
        "OsName": "Windows 10 Pro",
        "Procesador": "Intel Core i5",
        "RAM (GB)": 16
    },
    "Red": [{"IPAddress": "10.0.0.100"}],
    "Printer_Model": "HP LaserJet P1102",
    "Printer_Port": "USB001",
    "Printer_SN": "SN-ABC-123456789"
}

# 2. PC CLIENTE (Imprime en la compartida del HOST)
client_data = {
    "PC_Nombre": "CLIENTE-TEST-02",
    "Usuario_Actual": "Usuario_Remoto",
    "Sistema": {
        "OsName": "Windows 11 Home",
        "Procesador": "Intel Core i3",
        "RAM (GB)": 8
    },
    "Red": [{"IPAddress": "10.0.0.101"}],
    "Printer_Model": "HP LaserJet P1102 (vía red)",
    "Printer_Port": "\\\\HOST-TEST-01\\HP1102",
    "Printer_SN": "N/A" # Debería heredar de HOST-TEST-01
}

def simulate():
    try:
        print("--- PASO 1: Reporte del HOST ---")
        print(f"Enviando reporte para {host_data['PC_Nombre']} con Serial {host_data['Printer_SN']}...")
        r1 = requests.post(BASE_URL, json=host_data)
        print(f"Resultado HOST: {r1.status_code} - {r1.text}")

        time.sleep(2) # Esperar un poco para que se procese y se vea el delay

        print("\n--- PASO 2: Reporte del CLIENTE ---")
        print(f"Enviando reporte para {client_data['PC_Nombre']} apuntando a {client_data['Printer_Port']}...")
        r2 = requests.post(BASE_URL, json=client_data)
        print(f"Resultado CLIENTE: {r2.status_code} - {r2.text}")
        
        print("\n--- ¡SIMULACIÓN COMPLETADA! ---")
        print("Acceda al dashboard del servidor para ver los resultados en las fichas correspondientes.")
    except Exception as e:
        print(f"Error en la simulación: {e}")
        sys.exit(1)

if __name__ == "__main__":
    simulate()
