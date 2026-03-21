import requests, json
url = "http://localhost:5000/submit_inventory"

def send_pc(name, user, model, port, sn="N/A"):
    payload = {
        "PC_Nombre": name,
        "Usuario_Actual": user,
        "OS_Nombre": "Windows 10 Pro",
        "RAM_GB": 8,
        "Printer_Model": model,
        "Printer_Port": port,
        "Printer_SN": sn
    }
    requests.post(url, json=payload)

# 1. Ambos tienen la impresora (Situación normal)
send_pc("PC-DESPACHO-A", "AreaA\\Jefe", "HP LaserJet M15w", "USB001", "HP-USB-M15-99")
send_pc("PC-SECRETARIA-B", "AreaA\\SecB", "HP LaserJet M15w", "\\\\PC-DESPACHO-A\\HP_LaserJet", "HP-USB-M15-99")

print("Stage 1: Both assigned. Now Host reports SIN IMPRESORA.")

# 2. Host se queda SIN IMPRESORA
send_pc("PC-DESPACHO-A", "AreaA\\Jefe", "SIN IMPRESORA", "N/A", "N/A")

print("Simulation Stage 2 finished. PC-SECRETARIA-B should be AUTOMATICALLY UNASSIGNED now.")
