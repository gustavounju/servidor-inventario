import os
from dotenv import load_dotenv
from database.db_core import get_db_connection

load_dotenv()

# Datos extraídos manualmente de las imágenes
# Formato: (PC_NAME, PACHERA_NAME, PACHERA_PORT, SWITCH_NAME, SWITCH_PORT, USUARIO_UBICACION)
# Nota: Si solo tenemos Pachera, Switch queda None. Si solo Switch, Pachera None.
# Edificio y Piso son constantes: "Edificio Central", "Piso 2"

# Modificado para incluir Usuario/Ubicación como 4to elemento en pacheras y swtichs
# Listas de tuplas: (PC_NAME, DEVICE_NAME, PORT, USER_LOCATION)

datos_pacheras = [
    # PACHERA 1
    ("SIVL-0001", "Pachera 1", "2", "TERRAZA GABRIEL"),
    ("CGESE-0002", "Pachera 1", "3", "CAMARA GESELL (PUESTO LIBRE)"),
    ("VGS-0004", "Pachera 1", "4", "LIC. GARNICA"),
    ("SIVL-0011", "Pachera 1", "5", "DRA. VERA"),
    ("TJO6-0002", "Pachera 1", "7", "DR. MARIO MOYANO"),
    ("SIVL-0003", "Pachera 1", "11", "SALA DE AUDIENCIA"),
    ("VGS-0002", "Pachera 1", "12", "LIC FAYOS (PUESTO LIBRE)"),
    ("VGS-0006", "Pachera 1", "13", "LIC AGUSTINA HEMULLER"),
    ("VGS-0016", "Pachera 1", "14", "NENA SANCHEZ DE BUSTAMANTE"),
    ("VGS-0009", "Pachera 1", "24", "PUESTO LIBRE"),
    ("SIVL-0002", "Pachera 1", "25", "DRA. QUINTOS"),

    # PACHERA 2
    ("CC1-0001", "Pachera 2", "1", "IMPRESORA EN RED"),
    ("CYC1-0004", "Pachera 2", "3", "AUXILIAR Mesa de Entradas"),
    ("TJO1-0001", "Pachera 2", "4", "DRA. ALICIA LORENTE"),
    ("VGS-0014", "Pachera 2", "5", "DRA. ALEMAN"),
    ("CC1-0018", "Pachera 2", "6", "PUESTO LIBRE DRA. MARIANA ABRAHAM"),
    ("VGS-0015", "Pachera 2", "7", "DRA. PELLEGRINI"),
    ("SIVL-0001", "Pachera 2", "8", "GUIDO FLORES"),
    ("VGS-0005", "Pachera 2", "9", "NAIR ARICA"),
    ("CYC1-0015", "Pachera 2", "10", "PUESTO LIBRE DRA. ALDONATE"),
    ("CGESE-0002", "Pachera 2", "11", "CAMARA GESELLE PUESTO LIBRE"),
    ("CYC1-0022", "Pachera 2", "13", "DRA VEGA"),
    ("SIVL-0012", "Pachera 2", "14", "DR. MASASSESI"),
    ("CYC1-0014", "Pachera 2", "15", "TELEFONO IP DRA. ROLDAN MARIANA"),
    ("SIVL-0002", "Pachera 2", "16", "DRA. GRISELDA ASMUZI"),
    ("CYC1-0003", "Pachera 2", "17", "PUESTO LIBRE Mesa de Entradas"),
    ("CGESE-0002", "Pachera 2", "18", "CAMARA GESELLE PUESTO LIBRE"), 
    ("CYC1-0003", "Pachera 2", "19", "ESTRELLA ANGEL"), 
    ("VGS-0001", "Pachera 2", "20", "FERNANDEZ BELEN"),
    ("TJO1-0001", "Pachera 2", "21", "DRA. ALICIA LORENTE"), 
    ("CYC1-2019", "Pachera 2", "22", "PUESTO LIBRE DR. NIETO"),
    ("CGESE-0001", "Pachera 2", "24", "EQUIPO DE GRABACION"),
    ("CYC1-0008", "Pachera 2", "25", "BELEN RIOS"),
    ("CYC1-0001", "Pachera 2", "26", "JORGELINA CANIZARES"),
    ("SIVL-0001", "Pachera 2", "27", "IMPRESORA EN RED MESA DE ENTRADAS GUIDO FLORES"), 
    ("SIVL-0001", "Pachera 2", "28", "SALA IV LABORAL PUESTO LIBRE"), 
    ("SIVL-0017", "Pachera 2", "29", "DRA. ANA GRANADO"),
    ("TJO1-0004", "Pachera 2", "30", "DR. SASASI"),
    ("VGS-0012", "Pachera 2", "32", "PUESTO LIBRE"),
    ("VGS-0008", "Pachera 2", "33", "PUESTO LIBRE"),
    ("CYC1-0005", "Pachera 2", "34", "SOLEDAD CORREA LASPIUR"),
    ("CYC1-0010", "Pachera 2", "35", "AGUSTIN TORRES"),
    ("VGS-0017", "Pachera 2", "36", "LIC. AVALOS"),
    ("CYC1-0013", "Pachera 2", "37", "CASASOLA HERNAN"),
    ("VGS-0009", "Pachera 2", "38", "DANIEL OVANDO RUIZ"),
    ("CYC1-0002", "Pachera 2", "40", "TELEFONO IP ELCIA PEREZ"),
    ("TJO1-0002", "Pachera 2", "41", "ESCRIBANO OTERO"),
    ("CYC1-0009", "Pachera 2", "42", "NATALIA SALAS"),
    ("CYC1-0011", "Pachera 2", "43", "PUESTO LIBRE"),
    ("CYC1-0017", "Pachera 2", "44", "TELEFONO IP DR. DAVILA"),
    ("CYC1-0007", "Pachera 2", "46", "REBECA TORRES"),
    ("CYC1-0020", "Pachera 2", "47", "DRA. FLORENCIA ARTAZA"),
    ("CGESE-0003", "Pachera 2", "48", "PUESTO LIBRE SALA DE TOMA DE AUDIENCIAS"),

    # PACHERA 3
    ("JCYC1-0011", "Pachera 3", "1", "DR. DARIO ROTONDO"),
    ("VG5-0001", "Pachera 3", "3", "GRACIELA FALKONIER"),
    ("VG5-0003", "Pachera 3", "4", "PUESTO LIBRE LIC. ONTIVEROS VIVIANAN"),
    ("VG5-0005", "Pachera 3", "7", "CARINA PICARDO"),
    ("JCYC1-0009", "Pachera 3", "8", "ANALIA CORRADO"),
    ("VG5-0007", "Pachera 3", "9", "DRA. ORELLANA"),
    ("JCYC1-0006", "Pachera 3", "10", "ARTURO PEREYRA"),
    ("JCYC1-0008", "Pachera 3", "11", "FOFI FOLKONIER"),
    ("JCYC1-0017", "Pachera 3", "12", "DR. DAVILA"),
    ("SIVL-0017", "Pachera 3", "13", "SALA IV LABORAL PUESTO LIBRE"), 
    ("JCYC1-0015", "Pachera 3", "14", "DRA. ALDONATE"),
    ("JCYC1-0019", "Pachera 3", "18", "PUESTO LIBRE"),
    ("JCYC1-0021", "Pachera 3", "19", "DRA. GARCIA"),
    ("CGESE-0002", "Pachera 3", "20", "CAMARA GESELLE PUESTO LIBRE"), 
    ("JCYC1-0018", "Pachera 3", "21", "DRA. MORIANA ABRAHAM"),
    ("JCYC1-0013", "Pachera 3", "22", "ROLANDO ROJAS"),
    ("JCYC1-0019", "Pachera 3", "23", "DR. NIETO"),
    ("TJ01-0004", "Pachera 3", "26", "DR. SASASI"), 
    ("SIVL-0011", "Pachera 3", "30", "DRA. VERA"), 
    ("TJ01-0001", "Pachera 3", "31", "DR. ALFARO"), 
    ("VG5-0012", "Pachera 3", "32", "PUESTO LIBRE"), 
    ("TJ01-0003", "Pachera 3", "33", "DR. JUAREZ ALMARAZ"),
    ("TJ01-0002", "Pachera 3", "36", "ESCRIBANO OTERO"), 
    ("TJ01-0001", "Pachera 3", "37", "TRIBUNAL DE JUICIO PUESTO LIBRE"), 
    ("SIVL-0001", "Pachera 3", "38", "CLAUDIO RAMOS MESA DE ENTRADAS"), 
    ("VG5-0018", "Pachera 3", "39", "VIOLENCIA DE GENERO COCINA"),
    ("JCYC1-0002", "Pachera 3", "41", "ELCIA PEREZ"),
    ("VG5-0014", "Pachera 3", "42", "DRA. ALEMAN"), 
    ("CYC1-0001", "Pachera 3", "43", "PUESTO LIBRE MESA DE ENTRADAS"), 
    ("SIVL-0002", "Pachera 3", "46", "DRA. GRISELDA ASMUZI"), 
    ("CGESE-0002", "Pachera 3", "47", "PUESTO LIBRE"), 
    ("VG5-0017", "Pachera 3", "48", "LIC. AVALOS") 
]

datos_switches = [
    # SWITCH 3
    ("CYC1-0009", "Switch 3", "17", "ELVA ZAMAR"),
    ("CYC1-0011", "Switch 3", "33", "ERNESTO ANGEL"),
    
    # SWITCH 4
    ("CYC1-0006", "Switch 4", "22", "ROMERO"),

    # SWITCH 6
    ("VGS-0003", "Switch 6", "31", "LIC. ONTIVEROS VIVIANAN")
]

def ensure_columns(conn):
    db_name = os.environ.get("DB_NAME", "inventario_dev")
    new_columns = {
        "switch_name": "TEXT",
        "switch_port": "TEXT",
        "pachera_name": "TEXT",
        "pachera_port": "TEXT",
        "building": "TEXT",
        "floor": "TEXT"
    }
    for col, dtype in new_columns.items():
        result = conn.execute(
            "SELECT COUNT(*) AS cnt FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA=%s AND TABLE_NAME='pcs' AND COLUMN_NAME=%s",
            (db_name, col)
        ).fetchone()
        if not result or result["cnt"] == 0:
            print(f"Agregando columna '{col}'...")
            try:
                conn.execute(f"ALTER TABLE pcs ADD COLUMN {col} {dtype}")
            except Exception as e:
                print(f"Error agregando columna {col}: {e}")

def importar():
    print("Iniciando importación de datos de red...")

    with get_db_connection() as conn:
        ensure_columns(conn)

        count_pachera = 0
        for pc, pachera, port, user_loc in datos_pacheras:
            conn.execute("""
                UPDATE pcs
                SET building = 'Edificio Central', floor = 'Piso 2', pachera_name = %s, pachera_port = %s,
                    last_user = CASE WHEN last_user IS NULL OR last_user = '' THEN %s ELSE last_user END
                WHERE pc_name = %s
            """, (pachera, port, user_loc, pc))

            if conn.cursor.rowcount == 0:
                print(f"Creando PC {pc} con datos de Pachera...")
                conn.execute("""
                    INSERT INTO pcs (pc_name, building, floor, pachera_name, pachera_port, last_user, is_active, os_name)
                    VALUES (%s, 'Edificio Central', 'Piso 2', %s, %s, %s, 'True', 'Desconocido')
                """, (pc, pachera, port, user_loc))
            count_pachera += 1

        count_switch = 0
        for pc, switch, port, user_loc in datos_switches:
            conn.execute("""
                UPDATE pcs
                SET building = 'Edificio Central', floor = 'Piso 2', switch_name = %s, switch_port = %s,
                    last_user = CASE WHEN last_user IS NULL OR last_user = '' THEN %s ELSE last_user END
                WHERE pc_name = %s
            """, (switch, port, user_loc, pc))

            if conn.cursor.rowcount > 0:
                count_switch += 1
            else:
                print(f"Creando PC {pc} con datos de Switch...")
                conn.execute("""
                    INSERT INTO pcs (pc_name, building, floor, switch_name, switch_port, last_user, is_active, os_name)
                    VALUES (%s, 'Edificio Central', 'Piso 2', %s, %s, %s, 'True', 'Desconocido')
                """, (pc, switch, port, user_loc))
                count_switch += 1

    print("Importación finalizada.")
    print(f"Se actualizaron/crearon datos de Pachera para {count_pachera} registros.")
    print(f"Se actualizaron/crearon datos de Switch para {count_switch} registros.")

if __name__ == "__main__":
    importar()
