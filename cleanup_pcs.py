
import sqlite3

DB_FILE = "inventario.db"

def cleanup():
    print(f"Conectando a {DB_FILE}...")
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 1. Identificar candidatos
        query_select = """
        SELECT pc_name, fuero FROM pcs 
        WHERE (fuero = 'Desconocido' OR fuero IS NULL) 
        AND pc_name NOT IN ('PC Generica', 'Infraestructura')
        """
        
        cursor.execute(query_select)
        to_delete = cursor.fetchall()
        
        print(f"Encontradas {len(to_delete)} PCs para eliminar (Fuero Desconocido).")
            
        if len(to_delete) > 0:
            # 2. Eliminar
            query_delete = """
            DELETE FROM pcs 
            WHERE (fuero = 'Desconocido' OR fuero IS NULL) 
            AND pc_name NOT IN ('PC Generica', 'Infraestructura')
            """
            cursor.execute(query_delete)
            conn.commit()
            print(f"EXITO: {cursor.rowcount} PCs eliminadas correctamente.")
        else:
            print("No se encontraron PCs para eliminar.")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    cleanup()
