import sqlite3

try:
    conn = sqlite3.connect('inventario.db')
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM pcs WHERE pc_name = 'DESKTOP-BVVVOGR'").fetchone()
    if row:
        print(dict(row))
    else:
        print("NOT FOUND")
except Exception as e:
    print(f"ERROR: {e}")
finally:
    if 'conn' in locals():
        conn.close()
