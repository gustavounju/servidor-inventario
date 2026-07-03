import os
from database.db_core import get_db_connection

def apply_patch():
    try:
        with get_db_connection() as conn:
            # Check if columns exist first
            result = conn.execute("SHOW COLUMNS FROM tech_messages LIKE 'sender'").fetchone()
            if not result:
                print("Adding column sender...")
                conn.execute("ALTER TABLE tech_messages ADD COLUMN sender VARCHAR(100) DEFAULT 'Sistema' AFTER technician_name")
            
            result = conn.execute("SHOW COLUMNS FROM tech_messages LIKE 'task_id'").fetchone()
            if not result:
                print("Adding column task_id...")
                conn.execute("ALTER TABLE tech_messages ADD COLUMN task_id INT DEFAULT NULL AFTER sender")

            result = conn.execute("SHOW COLUMNS FROM tech_messages LIKE 'msg_type'").fetchone()
            if not result:
                print("Adding column msg_type...")
                conn.execute("ALTER TABLE tech_messages ADD COLUMN msg_type VARCHAR(50) DEFAULT 'direct' AFTER task_id")
                
            conn.commit()
            print("Patch aplicado con exito.")
    except Exception as e:
        print(f"Error aplicando parche: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    apply_patch()
