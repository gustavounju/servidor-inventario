
import sqlite3

# List of PCs identified from screenshots to delete
# Verified from images: 
# 1. CGESE-0002 (Grey)
# 2. SIVL-0017 (Grey)
# 3. TJO1-0004 (Grey - Note the 'O' instead of '0', likely a typo in hostname)
# 4. VG5-0003 (Grey)
# 5. VGS-0006 (Grey)

PCS_TO_DELETE = [
    "CGESE-0002",
    "SIVL-0017",
    "TJO1-0004", 
    "VG5-0003",
    "VGS-0006",
    # Added in second batch
    "VG5-0018",
    "VGS-0009",
    # Added in third batch
    "SIVL-0003",
    "VG5-0015",
    "VG5-0017",
    "TJ01-0003",
    # Added in fourth batch
    "VGS-0016",
    "VG5-0014",
    "VG5-0005"
]

DB_FILE = "inventario.db"

def delete_pcs():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        print(f"--- Bulk Deleting {len(PCS_TO_DELETE)} PCs ---")
        
        for pc in PCS_TO_DELETE:
            # check if exists
            exists = cursor.execute("SELECT pc_name FROM pcs WHERE pc_name = ?", (pc,)).fetchone()
            if not exists:
                print(f"Skipping {pc}: Not found in DB.")
                continue
                
            # Delete from pcs
            cursor.execute("DELETE FROM pcs WHERE pc_name = ?", (pc,))
            
            # Delete associated tasks (optional, but cleaner)
            cursor.execute("DELETE FROM tasks WHERE pc_name = ?", (pc,))
            
            # Log audit
            cursor.execute(
                "INSERT INTO audit_logs (pc_name, field, old_value, new_value, changed_at) VALUES (?, ?, ?, ?, datetime('now', '-3 hours'))",
                (pc, "STATUS", "Active/Cementerio", "DELETED FOREVER",)
            )
            
            print(f"Deleted: {pc}")
            
        conn.commit()
        conn.close()
        print("\nDeletion complete.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    delete_pcs()
