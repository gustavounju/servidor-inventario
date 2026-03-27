from database.db_core import get_db_connection

def perform_cleanup():
    try:
        with get_db_connection() as conn:
            # 1. Borrar todos los usuarios del sistema excepto administrador
            conn.execute("DELETE FROM app_users WHERE username != 'administrador'")
            print("Cleanup: app_users cleaned (only admin remains).")
            
            # 2. Borrar todos los usuarios del directorio
            conn.execute("DELETE FROM ad_users")
            print("Cleanup: ad_users deleted.")
            
            # 3. Borrar todas las PCs
            conn.execute("DELETE FROM pcs")
            print("Cleanup: pcs deleted.")
            
            # 4. Insertar PCs nuevas con nombres sin espacios
            conn.execute("""
                INSERT INTO pcs (pc_name, fuero, last_user, is_active, ip_address, os_name) 
                VALUES ('PC-AUDITORIA-01', 'Penal', 'carlosruiz', 'True', '192.168.1.10', 'Windows 10 Pro')
            """)
            conn.execute("""
                INSERT INTO pcs (pc_name, fuero, last_user, is_active, ip_address, os_name) 
                VALUES ('PC-SECRETARIA-02', 'Contencioso', 'analopez', 'True', '192.168.1.20', 'Windows 10 Pro')
            """)
            print("Cleanup: Added 2 test PCs (carlosruiz, analopez).")
            
            conn.commit()
            print("Cleanup: Commit succesful.")
    except Exception as e:
        print(f"Cleanup Error: {e}")

if __name__ == "__main__":
    perform_cleanup()
