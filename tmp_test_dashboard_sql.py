
import os
import pymysql
import pymysql.cursors
from dotenv import load_dotenv

load_dotenv()

# Simulate get_db_connection
host = os.environ.get("DB_HOST", "127.0.0.1")
user = os.environ.get("DB_USER", "root")
password = os.environ.get("DB_PASS", "")
dbname = os.environ.get("DB_NAME", "inventario_prod")
port = int(os.environ.get("DB_PORT", "3306"))

conn_obj = pymysql.connect(
    host=host,
    user=user,
    password=password,
    database=dbname,
    port=port,
    charset="utf8mb4",
    cursorclass=pymysql.cursors.DictCursor
)

class DBConnectionWrapper:
    def __init__(self, conn): self.conn = conn; self.cur = None
    def execute(self, q, v=None):
        self.cur = self.conn.cursor()
        self.cur.execute(q, v)
        return self
    def fetchone(self): return self.cur.fetchone()
    def fetchall(self): return self.cur.fetchall()
    def close(self): self.conn.close()
    def __enter__(self): return self
    def __exit__(self, a, b, c): self.close()

def get_db_connection(): return DBConnectionWrapper(conn_obj)

# Part of bp_dashboard.dashboard logic
try:
    with get_db_connection() as conn:
        q = ""
        estado = "True"
        alerta = None
        os_param = None
        filter_tasks = None
        sort_by = "pc_name"
        order = "asc"
        
        filter_sql = ""
        filter_params = []
        
        if q:
            filter_sql += " AND (p.pc_name LIKE %s OR p.ip_address LIKE %s OR p.last_user LIKE %s OR p.os_name LIKE %s OR p.printer_model LIKE %s)"
            q_param = f"%{q}%"
            filter_params += [q_param]*5
            
        if estado in ("True", "False"):
            filter_sql += " AND p.is_active = %s"
            filter_params.append(estado)

        count_sql = """
            SELECT COUNT(*) as c 
            FROM pcs p 
            LEFT JOIN ad_users u ON (
                LOWER(SUBSTRING_INDEX(p.last_user, '\\\\', -1)) = u.username OR 
                LOWER(p.last_user) = LOWER(u.real_name)
            )
            WHERE 1=1
        """ + filter_sql
        
        print("Executing base query...")
        base_sql = """
            SELECT p.*, u.real_name as ad_real_name, u.phone as ad_phone
            FROM pcs p 
            LEFT JOIN ad_users u ON (
                LOWER(SUBSTRING_INDEX(p.last_user, '\\\\', -1)) = u.username OR 
                LOWER(p.last_user) = LOWER(u.real_name)
            )
            WHERE 1=1
        """ + filter_sql + " ORDER BY p.pc_name ASC LIMIT 25 OFFSET 0"
        
        pcs = conn.execute(base_sql, filter_params).fetchall()
        print(f"Result: {len(pcs)} items")
        for p in pcs:
            print(f" - {p['pc_name']}")

        
except Exception as e:
    import traceback
    traceback.print_exc()
