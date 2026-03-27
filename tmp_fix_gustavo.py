from database.db_core import get_db_connection
from utils.auth import hash_password

def fix_user():
    with get_db_connection() as conn:
        print("Restoring 'gustavo' as superuser...")
        conn.execute("""
            UPDATE app_users 
            SET is_superuser = 1, 
                role = 'administrador',
                is_active = 1,
                can_access_dashboard = 1,
                can_access_mobile = 1,
                can_access_infrastructure = 1,
                can_access_reports = 1
            WHERE username = 'gustavo'
        """)
        conn.commit()
        print("Done.")

if __name__ == "__main__":
    fix_user()
