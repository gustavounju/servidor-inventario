from database.db_core import get_db_connection
import json

pc_name = "WIN7-PC-TEST"

print(f"Buscando datos en la DB para {pc_name}...")

try:
    with get_db_connection() as conn:
        pc = conn.execute("SELECT pc_name, printer_model, printer_sn, printer_port FROM pcs WHERE pc_name = %s", (pc_name,)).fetchone()
        
        if pc:
            print(f"PC encontrada: {pc['pc_name']}")
            print(f"Modelo Impresora: {pc['printer_model']}")
            print(f"Puerto Impresora: {pc['printer_port']}")
            print(f"Serial Impresora: {pc['printer_sn']}")
            
            expected_sn = "VNC3G05432"
            if pc['printer_sn'] == expected_sn:
                print("\n>>> PRUEBA EXITOSA: El serial se guardó correctamente en la base de datos.")
            else:
                print(f"\n>>> PRUEBA FALLIDA: El serial guardado ({pc['printer_sn']}) no coincide con el esperado ({expected_sn}).")
        else:
            print(f"PC {pc_name} no encontrada en la base de datos.")
            
except Exception as e:
    print(f"Error consultando la base de datos: {e}")
