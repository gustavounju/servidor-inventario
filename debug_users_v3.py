
import sqlite3
import os

print(f"CWD: {os.getcwd()}")
print(f"DB Exists: {os.path.exists('inventario.db')}")

try:
    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()
    
    print("\n--- Tables ---")
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    for t in tables:
        print(t[0])
        
    print("\n--- Count PCs ---")
    count = cursor.execute("SELECT COUNT(*) FROM pcs").fetchone()[0]
    print(f"Total PCs: {count}")

    print("\n--- Sample PCs ---")
    rows = cursor.execute("SELECT pc_name, last_user FROM pcs LIMIT 5").fetchall()
    for r in rows:
        print(r)

    conn.close()
except Exception as e:
    print(e)
