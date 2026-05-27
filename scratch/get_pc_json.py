from database.db_core import get_db_connection
import json
import sys

def get_pc_json(pc_name):
    try:
        with get_db_connection() as conn:
            row = conn.execute("SELECT full_json_data FROM pcs WHERE pc_name = %s", (pc_name,)).fetchone()
            if row and row['full_json_data']:
                return row['full_json_data']
            else:
                return None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    pc = "SISTEMAS-105"
    data = get_pc_json(pc)
    if data:
        print(data)
    else:
        print(f"No se encontró información para la PC: {pc}")
