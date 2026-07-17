import sys
import os
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from database.db_core import get_db_connection

try:
    with get_db_connection() as conn:
        print("=== DETALLES DE SISTEMAS-112 ===")
        row = conn.execute("SELECT * FROM pcs WHERE pc_name = 'SISTEMAS-112'").fetchone()
        if row:
            for k, v in dict(row).items():
                if k != 'full_json_data':
                    print(f"{k}: {v}")
        else:
            print("SISTEMAS-112 no encontrada en la tabla pcs.")

        print("\n=== HISTORIAL DE LOGS DE SISTEMAS-112 ===")
        logs = conn.execute("SELECT * FROM audit_logs WHERE pc_name = 'SISTEMAS-112' ORDER BY changed_at DESC LIMIT 10").fetchall()
        for log in logs:
            print(f"{log['changed_at']} | Campo: {log['field']} | '{log['old_value']}' -> '{log['new_value']}' | User: {log['user_name']}")

        print("\n=== MAPEOS DE FUEROS EN LA BASE DE DATOS ===")
        mappings = conn.execute("SELECT * FROM fuero_mappings").fetchall()
        for m in mappings:
            print(f"Prefix: {m['prefix_code']:<15} | Label: {m['fuero_label']:<35} | Active: {m['is_active']}")
except Exception as e:
    print("Error:", e)
