
import sqlite3

try:
    conn = sqlite3.connect("inventario.db")
    conn.row_factory = sqlite3.Row
    
    # Enable case-insensitive LIKE if needed, but we used LOWER()
    
    base_sql = """
        SELECT
            p.pc_name,
            p.last_user,
            u.username as ad_username,
            u.real_name as ad_real_name
        FROM pcs p
        LEFT JOIN ad_users u ON LOWER(p.last_user) = u.username
        WHERE p.pc_name = 'SISTEMAS-105'
    """
    
    print("--- Executing Query ---")
    rows = conn.execute(base_sql).fetchall()
    
    for row in rows:
        r = dict(row)
        print(f"PC: {r['pc_name']}")
        print(f"Last User (PCS): '{r['last_user']}'")
        print(f"Matched User (AD): '{r['ad_username']}'")
        print(f"Real Name (AD): '{r['ad_real_name']}'")
        
        # Check for whitespace/hidden chars
        if r['last_user']:
            print(f"Last User Hex: {r['last_user'].encode('utf-8').hex()}")
        
    # Check ad_users for gmurad
    print("\n--- Checking ad_users for 'gmurad' ---")
    u_rows = conn.execute("SELECT username, real_name FROM ad_users WHERE username LIKE '%gmurad%'").fetchall()
    for row in u_rows:
        print(dict(row))

    conn.close()
except Exception as e:
    print(f"Error: {e}")
