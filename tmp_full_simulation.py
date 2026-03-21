import requests, json
url = "http://localhost:5000/submit_inventory"

# Simulation with FULL payload to avoid NULL issues
def send_pc(name, user, model, port, sn, os="Windows 10 Pro"):
    payload = {
        "PC_Nombre": name,
        "Usuario_Actual": user,
        "OS_Nombre": os,
        "Procesador": "Intel Core i5-10400",
        "RAM_GB": 16,
        "IP": "172.16.0." + str(hash(name) % 254),
        "Motherboard": "ASUS H410M",
        "Discos": [{"Model": "SSD 480GB", "Size": "480 GB"}],
        "Monitores": ["Samsung 19\""],
        "Printer_Model": model,
        "Printer_Port": port,
        "Printer_SN": sn,
        "Salud": {"Uptime_Dias": 1, "Discos_SMART": [{"Model": "SSD", "Status": "OK"}], "Discos_Espacio": [{"Drive": "C:", "FreeGB": 100}]}
    }
    r = requests.post(url, json=payload)
    print(f"Sent {name}: {r.status_code}")

# 1. Reset Host to OFFLINE (for testing warning)
send_pc("PC-DESPACHO-A", "AreaA\\Jefe", "SIN IMPRESORA", "N/A", "N/A")

# 2. Re-send Client (Shared to A)
send_pc("PC-SECRETARIA-B", "AreaA\\SecB", "HP LaserJet M15w (SIMULADA)", "\\\\PC-DESPACHO-A\\HP_LaserJet", "HP-USB-M15-99")

print("Simulation finished. Check Dashboard for PC-DESPACHO-A (No printer) and PC-SECRETARIA-B (Host Offline warning).")
