
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
    # List of Fueros to bulk delete ENTIRELY
    FUEROS_TO_DELETE = [
        "Cámara Gesell",
        "Sala IV Laboral",
        "Tribunal de Juicio",
        "Violencia de Género 5"
    ]

    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print(f"--- Bulk Deleting Specific PCs ({len(PCS_TO_DELETE)}) ---")
        deleted_count = 0
        skipped_count = 0
        
        print(f"{'PC NAME':<20} | {'REASON':<20} | {'STATUS':<15}")
        print("-" * 65)

        # 1. Delete by Specific Name
        for pc in PCS_TO_DELETE:
            exists = cursor.execute("SELECT pc_name FROM pcs WHERE pc_name = ?", (pc,)).fetchone()
            
            if not exists:
                print(f"{pc:<20} | {'Manual List':<20} | ALREADY GONE")
                skipped_count += 1
                continue
                
            cursor.execute("DELETE FROM pcs WHERE pc_name = ?", (pc,))
            cursor.execute("DELETE FROM tasks WHERE pc_name = ?", (pc,))
            cursor.execute(
                "INSERT INTO audit_logs (pc_name, field, old_value, new_value, changed_at) VALUES (?, ?, ?, ?, datetime('now', '-3 hours'))",
                (pc, "STATUS", "Active/Cementerio", "DELETED (Manual)",)
            )
            print(f"{pc:<20} | {'Manual List':<20} | DELETED NOW")
            deleted_count += 1

        print("-" * 65)

        # 2. Delete by Fuero
        print(f"--- Bulk Deleting by Fuero ({len(FUEROS_TO_DELETE)} Fueros) ---")
        fuero_deleted_count = 0
        
        for fuero in FUEROS_TO_DELETE:
            # Find PCs in this Fuero
            pcs_in_fuero = cursor.execute("SELECT pc_name FROM pcs WHERE fuero = ?", (fuero,)).fetchall()
            
            if not pcs_in_fuero:
                 print(f"No PCs found for Fuero: '{fuero}'")
                 continue
                 
            for row in pcs_in_fuero:
                pc = row["pc_name"]
                
                # Check if we already deleted it in the manual list loop (though strictly it's gone now)
                # But good to be safe if list overlaps
                
                cursor.execute("DELETE FROM pcs WHERE pc_name = ?", (pc,))
                cursor.execute("DELETE FROM tasks WHERE pc_name = ?", (pc,))
                cursor.execute(
                    "INSERT INTO audit_logs (pc_name, field, old_value, new_value, changed_at) VALUES (?, ?, ?, ?, datetime('now', '-3 hours'))",
                    (pc, "STATUS", f"Fuero: {fuero}", "DELETED (Fuero)",)
                )
                print(f"{pc:<20} | {fuero[:20]:<20} | DELETED NOW")
                fuero_deleted_count += 1

        conn.commit()
        conn.close()
        print("-" * 65)
        print(f"SUMMARY:")
        print(f"  Manual List Deleted: {deleted_count}")
        print(f"  Manual List Skipped: {skipped_count}")
        print(f"  Fuero Bulk Deleted:  {fuero_deleted_count}")
        print(f"  TOTAL DELETED:       {deleted_count + fuero_deleted_count}")
        print("Deletion complete.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    delete_pcs()
