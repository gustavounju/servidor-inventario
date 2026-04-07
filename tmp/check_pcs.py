import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

host = os.environ.get("DB_HOST", "127.0.0.1")
user = os.environ.get("DB_USER", "root")
password = os.environ.get("DB_PASS", "")
port = int(os.environ.get("DB_PORT", "3306"))
dbname = "inventario_prod"

try:
    conn = pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=dbname,
        port=port,
        cursorclass=pymysql.cursors.DictCursor
    )
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM pcs")
        print(cursor.fetchone())
        
        cursor.execute("SELECT pc_name, last_report FROM pcs ORDER BY last_report DESC LIMIT 10")
        for row in cursor.fetchall():
            print(row)
    conn.close()
except Exception as e:
    print(f"Error: {e}")
