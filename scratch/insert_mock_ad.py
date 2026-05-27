from database.db_core import get_db_connection
import sys

def insert_mock_ad():
    try:
        with get_db_connection() as conn:
            # Usuarios en el directorio AD (oficiales)
            mock_ad_directory = [
                ('gustavo.m', 'Gustavo Mock AD', '1234', 'Sistemas'),
                ('tecnico.pro', 'Tecnico Simulado AD', '5555', 'Mantenimiento'),
                ('admin.ad', 'Admin AD Simulation', '9999', 'Direccion'),
                ('usuario.nuevo', 'Nuevo Usuario Pendiente', '1111', 'Pendientes'),
                ('andrea', 'Andrea Gomez', '2222', 'Recursos Humanos'),
                ('pedro', 'Pedro Nuevo AD', '4444', 'Comunicaciones')
            ]

            
            for username, real_name, phone, fuero in mock_ad_directory:
                conn.execute("""
                    INSERT INTO ad_users (username, real_name, phone, fuero) 
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE real_name=VALUES(real_name), phone=VALUES(phone), fuero=VALUES(fuero)
                """, (username, real_name, phone, fuero))
                
                # Crear shadow user para los primeros dos (Activos)
                # Crear shadow user para 'usuario.nuevo' y 'andrea' (Inactivos)
                if username in ('gustavo.m', 'tecnico.pro'):
                    conn.execute("""
                        INSERT INTO app_users (username, display_name, role, is_active, can_access_mobile, password_hash)
                        VALUES (%s, %s, 'tecnico', 1, 1, 'mock_ad_pass')
                        ON DUPLICATE KEY UPDATE display_name=VALUES(display_name), is_active=1
                    """, (username, real_name))
                elif username in ('usuario.nuevo', 'andrea'):
                    conn.execute("""
                        INSERT INTO app_users (username, display_name, role, is_active, can_access_mobile, password_hash)
                        VALUES (%s, %s, 'tecnico', 0, 0, 'mock_ad_pass')
                        ON DUPLICATE KEY UPDATE display_name=VALUES(display_name), is_active=0
                    """, (username, real_name))


            
            conn.commit()
            print("Mock AD data inserted successfully.")
    except Exception as e:
        print(f"Error inserting mock data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    insert_mock_ad()
