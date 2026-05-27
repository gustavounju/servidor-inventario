from database.db_core import get_db_connection
import json

def get_pcs_info(pc_names):
    with get_db_connection() as conn:
        for name in pc_names:
            print(f"\n--- INFO PARA {name} ---")
            row = conn.execute("SELECT pc_name, printer_model, printer_port, printer_sn, full_json_data FROM pcs WHERE pc_name = %s", (name,)).fetchone()
            if row:
                print(f"Modelo: {row['printer_model']}")
                print(f"Puerto: {row['printer_port']}")
                print(f"Serial en DB: {row['printer_sn']}")
                try:
                    data = json.loads(row['full_json_data'])
                    print("Seriales crudos en JSON:")
                    # Buscamos en el JSON original
                    print(f"  Printer_SN: {data.get('Printer_SN')}")
                except:
                    print("Error parsing JSON")
            else:
                print("No encontrada en DB")

if __name__ == "__main__":
    get_pcs_info(["JCC8SEC1500003", "JUZMEN20000009"])
