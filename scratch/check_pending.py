import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def check_pending():
    conn = pymysql.connect(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASS', ''),
        database=os.getenv('DB_NAME', 'inventario_dev'),
        port=int(os.getenv('DB_PORT', 3306)),
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with conn.cursor() as cursor:
            # Check Tasks
            cursor.execute("SELECT * FROM tasks WHERE estado != 'Hecha'")
            tasks = cursor.fetchall()
            
            # Check Pending Users (is_active = 0)
            cursor.execute("SELECT * FROM app_users WHERE is_active = 0")
            users = cursor.fetchall()
            
            print(f"--- PENDING TASKS ({len(tasks)}) ---")
            for t in tasks:
                print(f"ID: {t['id']} | PC: {t['pc_name']} | Desc: {t['descripcion']} | Estado: {t['estado']}")
            
            print(f"\n--- PENDING USERS ({len(users)}) ---")
            for u in users:
                print(f"ID: {u['id']} | Username: {u['username']} | Display: {u['display_name']}")
    finally:
        conn.close()

if __name__ == '__main__':
    check_pending()
