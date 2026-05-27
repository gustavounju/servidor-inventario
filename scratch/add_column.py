from database.db_core import get_db_connection
with get_db_connection() as conn:
    try:
        conn.execute('ALTER TABLE tasks ADD COLUMN solucion TEXT AFTER descripcion')
        conn.commit()
        print("Column 'solucion' added successfully.")
    except Exception as e:
        print(f"Error: {e}")
