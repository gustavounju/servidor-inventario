from database.db_core import get_db_connection
import json

def get_pc_json(pc_name):
    with get_db_connection() as conn:
        row = conn.execute("SELECT full_json_data FROM pcs WHERE pc_name = %s", (pc_name,)).fetchone()
        if row:
            data = json.loads(row['full_json_data'])
            print(json.dumps(data, indent=4))
        else:
            # Intentar búsqueda con wildcard por si acaso
            print(f"PC '{pc_name}' no encontrada exactamente. Buscando similares...")
            rows = conn.execute("SELECT pc_name FROM pcs WHERE pc_name LIKE %s", (f"%{pc_name}%",)).fetchall()
            for r in rows:
                print(f"Encontrada: {r['pc_name']}")

if __name__ == "__main__":
    get_pc_json("TTSIVVOC120007")
