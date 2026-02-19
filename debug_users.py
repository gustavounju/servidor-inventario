
import sqlite3

try:
    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()
    
    print("--- AD Users (Sample) ---")
    rows = cursor.execute("SELECT username, real_name FROM ad_users WHERE username LIKE '%aldonate%' OR username LIKE '%canizares%'").fetchall()
    for r in rows:
        print(f"User: '{r[0]}', Real: '{r[1]}'")
        
    print("\n--- PCs (Sample) ---")
    rows = cursor.execute("SELECT pc_name, last_user FROM pcs WHERE last_user LIKE '%aldonate%' OR last_user LIKE '%canizares%'").fetchall()
    for r in rows:
        print(f"PC: '{r[0]}', LastUser: '{r[1]}'")

    conn.close()
except Exception as e:
    print(e)
