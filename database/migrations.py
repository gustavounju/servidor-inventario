from database.db_core import get_db_connection

def migrate_db_v11():
    """Migración V11: Crear tabla components."""
    print("Verificando migración de DB v11...")
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                serial_number TEXT UNIQUE,
                component_type TEXT NOT NULL,
                brand_model TEXT,
                status TEXT DEFAULT 'Stock', 
                assigned_pc TEXT,
                created_at TEXT DEFAULT (datetime('now', '-3 hours')),
                FOREIGN KEY (assigned_pc) REFERENCES pcs(pc_name)
            )
            """
        )
        conn.commit()
    print("Migración V11 verificada.")

def migrate_db_v2():
    """Migra la tabla tasks para permitir pc_name NULL y agregar solicitante."""
    print("Verificando migración de DB v2...")
    with get_db_connection() as conn:
        cursor = conn.execute("PRAGMA table_info(tasks)")
        columns = [row["name"] for row in cursor.fetchall()]
        if "solicitante" in columns:
            print("DB ya está en v2.")
            return

        print("Migrando DB a v2...")
        try:
            conn.execute("ALTER TABLE tasks RENAME TO tasks_old")
            conn.execute(
                """
                CREATE TABLE tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pc_name TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now', '-3 hours')),
                    descripcion TEXT NOT NULL,
                    estado TEXT NOT NULL DEFAULT 'Pendiente',
                    solicitante TEXT,
                    FOREIGN KEY (pc_name) REFERENCES pcs(pc_name)
                )
                """
            )
            conn.execute(
                """
                INSERT INTO tasks (id, pc_name, created_at, descripcion, estado)
                SELECT id, pc_name, created_at, descripcion, estado FROM tasks_old
                """
            )
            conn.execute("DROP TABLE tasks_old")
            conn.commit()
            print("Migración v2 completada con éxito.")
        except Exception as e:
            print(f"Error en migración v2: {e}")
            conn.rollback()

def migrate_db_v3():
    """Migra BD a v3: tabla technicians y columnas completed_by/at en tasks."""
    print("Verificando migración de DB v3...")
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='technicians'")
        if not cursor.fetchone():
            print("Creando tabla technicians...")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS technicians (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
                """
            )
        
        cursor = conn.execute("PRAGMA table_info(tasks)")
        columns = [row["name"] for row in cursor.fetchall()]
        
        if "completed_by" not in columns:
            print("Agregando col completed_by a tasks...")
            try:
                conn.execute("ALTER TABLE tasks ADD COLUMN completed_by TEXT")
            except Exception as e: print(f"Error add completed_by: {e}")

        if "completed_at" not in columns:
            print("Agregando col completed_at a tasks...")
            try:
                conn.execute("ALTER TABLE tasks ADD COLUMN completed_at TEXT")
            except Exception as e: print(f"Error add completed_at: {e}")
            
        conn.commit()
    print("Migración v3 verificada.")

def migrate_db_v4():
    """Migra BD a v4: agregar columna categoria a tasks."""
    print("Verificando migración de DB v4...")
    with get_db_connection() as conn:
        cursor = conn.execute("PRAGMA table_info(tasks)")
        columns = [row["name"] for row in cursor.fetchall()]
        
        if "categoria" not in columns:
            print("Agregando col categoria a tasks...")
            try:
                conn.execute("ALTER TABLE tasks ADD COLUMN categoria TEXT")
                conn.commit()
            except Exception as e: print(f"Error add categoria: {e}")
            
    print("Migración v4 verificada.")

def migrate_db_v5():
    """Migra BD a v5: crear tabla audit_logs para historial de cambios."""
    print("Verificando migración de DB v5...")
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pc_name TEXT,
                field TEXT,
                old_value TEXT,
                new_value TEXT,
                changed_at DATETIME DEFAULT (datetime('now', '-3 hours'))
            )
            """
        )
    print("Migración v5 verificada.")

def migrate_db_v6():
    """Migración V6: Agregar columna 'assigned_to' a la tabla 'tasks'."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'assigned_to' not in columns:
            print("Aplicando migración V6: Agregando 'assigned_to' a tasks...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN assigned_to TEXT")
            conn.commit()
        else:
            print("Migración V6 verificada.")

def migrate_db_v7():
    """Migración V7: Agregar columna 'fuero' a la tabla 'pcs'."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(pcs)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'fuero' not in columns:
            print("Aplicando migración V7: Agregando 'fuero' a pcs...")
            cursor.execute("ALTER TABLE pcs ADD COLUMN fuero TEXT")
            conn.commit()
        else:
            print("Migración V7 verificada.")

def migrate_db_v8():
    """Migración V8: Agregar columna 'fuero' a la tabla 'tasks'."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'fuero' not in columns:
            print("Aplicando migración V8: Agregando 'fuero' a tasks...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN fuero TEXT")
            conn.commit()
        else:
            print("Migración V8 verificada.")

def migrate_db_v9():
    """Migración V9: Agregar columnas de infraestructura de red y ubicación a 'pcs'."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(pcs)")
        columns = [info[1] for info in cursor.fetchall()]
        
        new_columns = {
            "switch_name": "TEXT",
            "switch_port": "TEXT",
            "pachera_name": "TEXT",
            "pachera_port": "TEXT",
            "building": "TEXT",
            "floor": "TEXT"
        }
        
        for col, dtype in new_columns.items():
            if col not in columns:
                print(f"Aplicando migración V9: Agregando '{col}' a pcs...")
                try:
                    cursor.execute(f"ALTER TABLE pcs ADD COLUMN {col} {dtype}")
                except Exception as e:
                    print(f"Error agregando columna {col}: {e}")
        
        conn.commit()
    print("Migración V9 verificada.")

def migrate_db_v10():
    """Migración V10: Agregar columnas de alerta de salud a 'pcs'."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(pcs)")
        columns = [info[1] for info in cursor.fetchall()]
        
        new_columns = {
            "alerta_disco": "INTEGER DEFAULT 0",
            "alerta_uptime": "INTEGER DEFAULT 0"
        }
        
        for col, dtype in new_columns.items():
            if col not in columns:
                print(f"Aplicando migración V10: Agregando '{col}' a pcs...")
                try:
                    cursor.execute(f"ALTER TABLE pcs ADD COLUMN {col} {dtype}")
                except Exception as e:
                    print(f"Error agregando columna {col}: {e}")
        
        conn.commit()
    print("Migración V10 verificada.")

def migrate_db_v11():
    """Migración V11: Crear tabla components."""
    print("Verificando migración de DB v11...")
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                serial_number TEXT UNIQUE,
                component_type TEXT NOT NULL,
                brand_model TEXT,
                status TEXT DEFAULT 'Stock', 
                assigned_pc TEXT,
                created_at TEXT DEFAULT (datetime('now', '-3 hours')),
                FOREIGN KEY (assigned_pc) REFERENCES pcs(pc_name)
            )
            """
        )
        conn.commit()
    print("Migración V11 verificada.")

def migrate_db_v12():
    """Migración V12: Agregar columna 'assigned_to_component_id' a la tabla 'components'."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(components)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'assigned_to_component_id' not in columns:
            print("Aplicando migración V12: Agregando 'assigned_to_component_id' a components...")
            cursor.execute("ALTER TABLE components ADD COLUMN assigned_to_component_id INTEGER REFERENCES components(id)")
            conn.commit()
        else:
            print("Migración V12 verificada.")

def migrate_db_v13():
    """Migración V13: Añadir supplier e invoice_number a ups_inventory y components, unificar bateria_stock en components."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Agregar columnas a ups_inventory y components
        for table in ['components', 'ups_inventory']:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [info[1] for info in cursor.fetchall()]
            
            if 'supplier' not in columns:
                print(f"Aplicando migración V13: Agregando 'supplier' e 'invoice_number' a {table}...")
                try:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN supplier TEXT")
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN invoice_number TEXT")
                except Exception as e:
                    print(f"Error agregando columnas a {table}: {e}")

        # 2. Volcar baterias_stock en components
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='baterias_stock'")
        if cursor.fetchone():
            print("Aplicando migración V13: Migrando tabla baterias_stock hacia components...")
            cursor.execute("SELECT id, code, brand_model, status, created_at FROM baterias_stock")
            baterias = cursor.fetchall()
            
            status_map = {'Stock': 'Stock', 'Asignada': 'Instalado', 'Descartada': 'Retirado'}
            
            for bat in baterias:
                cursor.execute("SELECT id FROM components WHERE component_type='Batería UPS' AND serial_number=?", (bat['code'],))
                existing_comp = cursor.fetchone()
                
                if existing_comp:
                    new_comp_id = existing_comp['id']
                else:
                    mapped_status = status_map.get(bat['status'], 'Stock')
                    cursor.execute("""
                        INSERT INTO components (serial_number, component_type, brand_model, status, created_at)
                        VALUES (?, 'Batería UPS', ?, ?, ?)
                    """, (bat['code'], bat['brand_model'], mapped_status, bat['created_at']))
                    new_comp_id = cursor.lastrowid
                
                # 3. Actualizar la foreign key en ups_inventory
                cursor.execute("""
                    UPDATE ups_inventory 
                    SET assigned_battery_id = ? 
                    WHERE assigned_battery_id = ?
                """, (new_comp_id, bat['id']))
            
            # Renombrar tabla antigua
            try:
                cursor.execute("ALTER TABLE baterias_stock RENAME TO baterias_stock_old")
            except Exception as e:
                pass
                
        conn.commit()
    print("Migración V13 verificada.")

def run_all_migrations():
    """Ejecuta todas las migraciones en orden."""
    migrate_db_v2()
    migrate_db_v3()
    migrate_db_v4()
    migrate_db_v5()
    migrate_db_v6()
    migrate_db_v7()
    migrate_db_v8()
    migrate_db_v9()
    migrate_db_v10()
    migrate_db_v11()
    migrate_db_v12()
    migrate_db_v13()
