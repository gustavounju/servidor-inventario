
import sqlite3

try:
    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()
    
    print("--- Specific PCs ---")
    rows = cursor.execute("SELECT pc_name, last_user FROM pcs WHERE pc_name IN ('JCC8SEC1600006', 'JCC8SEC1600012')").fetchall()
    for r in rows:
        print(f"PC: '{r[0]}', LastUser: '{r[1]}', Hex: {r[1].encode('utf-8').hex() if r[1] else 'None'}")

    conn.close()
except Exception as e:
    print(e)
