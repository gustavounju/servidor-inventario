from database.db_core import get_db_connection
import json

def search_pcs(patterns):
    with get_db_connection() as conn:
        for pat in patterns:
            print(f"\n--- BUSQUEDA PARA {pat} ---")
            rows = conn.execute("SELECT pc_name, printer_model, printer_port, printer_sn FROM pcs WHERE pc_name LIKE %s", (f"%{pat}%",)).fetchall()
            if rows:
                for row in rows:
                    print(f"PC: {row['pc_name']}")
                    print(f"  Modelo: {row['printer_model']}")
                    print(f"  Puerto: {row['printer_port']}")
                    print(f"  Serial: {row['printer_sn']}")
            else:
                print("No se encontraron coincidencias.")

if __name__ == "__main__":
    search_pcs(["JCC8SEC", "JUZMEN"])
