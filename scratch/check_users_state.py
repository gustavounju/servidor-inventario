
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

host = os.environ.get("DB_HOST", "127.0.0.1")
user = os.environ.get("DB_USER", "root")
password = os.environ.get("DB_PASS", "")
dbname = os.environ.get("DB_NAME", "inventario_prod")
port = int(os.environ.get("DB_PORT", "3306"))

try:
    conn = pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=dbname,
        port=port,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )
    
    with conn.cursor() as cursor:
        print("--- app_users ---")
        cursor.execute("SELECT id, username, display_name, role, is_superuser, is_active, technician_name, can_access_mobile FROM app_users")
        rows = cursor.fetchall()
        for r in rows:
            print(f"ID: {r['id']}, User: '{r['username']}', Name: '{r['display_name']}', Role: '{r['role']}', Super: {r['is_superuser']}, Active: {r['is_active']}, TechName: '{r['technician_name']}', Mobile: {r['can_access_mobile']}")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
