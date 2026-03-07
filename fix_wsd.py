import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database.db_core import get_db_connection

def fix_wsd():
    try:
        with get_db_connection() as conn:
            pcs = conn.execute("SELECT pc_name, printer_port FROM pcs WHERE printer_port LIKE 'WSD%'").fetchall()
            count = 0
            for pc in pcs:
                conn.execute("UPDATE pcs SET printer_port = 'Red' WHERE pc_name = %s", (pc["pc_name"],))
                count += 1
            conn.commit()
            print(f"Hecho: {count} PCs actualizadas exitosamente.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_wsd()
