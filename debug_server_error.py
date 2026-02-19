
import sqlite3
from flask import Flask, render_template
import os

# Mock Flask app context if needed or just test the logic safely
try:
    conn = sqlite3.connect("inventario.db")
    conn.row_factory = sqlite3.Row
    
    # 1. Simulate Missing Table by renaming
    # We check if ad_users exists first
    exists = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ad_users'").fetchone()
    if exists:
        conn.execute("ALTER TABLE ad_users RENAME TO ad_users_backup_test")
        print("Renamed ad_users to ad_users_backup_test")
    
    # 2. Run the Query
    try:
        base_sql = """
            SELECT
                p.*,
                u.real_name as ad_real_name,
                (SELECT COUNT(*) FROM tasks t WHERE t.pc_name = p.pc_name AND t.estado != 'Hecha') AS tareas_pendientes
            FROM pcs p
            LEFT JOIN ad_users u ON LOWER(p.last_user) = u.username
            WHERE 1=1
        """
        rows = conn.execute(base_sql).fetchall()
        print("Query successful (Unexpected if table missing)")
    except Exception as e:
        print(f"Caught expected error: {e}")
        # This matches the catch block in servidor.py
        
    # 3. Restore Table
    if exists:
        conn.execute("ALTER TABLE ad_users_backup_test RENAME TO ad_users")
        print("Restored ad_users")
        
    conn.close()

except Exception as e:
    print(f"Critical Error: {e}")
