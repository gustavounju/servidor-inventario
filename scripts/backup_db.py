import os
import sys
import subprocess
import time
import gzip
from datetime import datetime
from dotenv import load_dotenv

def verify_backup_integrity(backup_path: str, min_bytes: int = 100) -> bool:
    """
    Verifica la integridad de un archivo de respaldo .sql.gz.
    Retorna True si el archivo existe, supera el tamaño mínimo, es descompresible y contiene sentencias SQL válidas.
    """
    if not os.path.exists(backup_path):
        print(f"[X] Verificación fallida: El archivo '{backup_path}' no existe.")
        return False

    file_size = os.path.getsize(backup_path)
    if file_size < min_bytes:
        print(f"[X] Verificación fallida: El archivo '{backup_path}' es demasiado pequeño ({file_size} bytes < {min_bytes} bytes).")
        return False

    try:
        with gzip.open(backup_path, 'rb') as gz:
            # Leer una porción del contenido para verificar validez GZip y SQL
            header_sample = gz.read(4096)
            if not header_sample:
                print(f"[X] Verificación fallida: El archivo descompreso está vacío.")
                return False

            sample_text = header_sample.decode('utf-8', errors='ignore').upper()
            # Comprobar indicadores típicos de un mysqldump SQL válido
            sql_keywords = ["MYSQL", "DUMP", "CREATE", "INSERT", "TABLE", "DATABASE", "USE"]
            if not any(keyword in sample_text for keyword in sql_keywords):
                print(f"[X] Verificación fallida: El archivo no parece ser un dump SQL válido.")
                return False

            # Leer el resto del archivo para asegurar que no hay truncamiento/corrupción intermedia
            while chunk := gz.read(65536):
                pass

        print(f"[+] Verificación de integridad OK: '{os.path.basename(backup_path)}' ({file_size / 1024:.2f} KB).")
        return True

    except (gzip.BadGzipFile, EOFError, OSError) as e:
        print(f"[X] Error de integridad GZip en '{backup_path}': {e}")
        return False
    except Exception as e:
        print(f"[X] Error inesperado verificando integridad de '{backup_path}': {e}")
        return False


def run_backup():
    """
    Ejecuta mysqldump para realizar un backup de la base de datos,
    comprime el resultado, verifica su integridad y elimina backups antiguos (más de 7 días).
    """
    # Cargar .env
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(base_dir, '.env'))
    
    db_host = os.environ.get("DB_HOST", "127.0.0.1")
    db_user = os.environ.get("DB_USER", "root")
    db_pass = os.environ.get("DB_PASS", "")
    db_name = os.environ.get("DB_NAME", "inventario_jujuy")
    
    backups_dir = os.path.join(base_dir, "backups")
    os.makedirs(backups_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backups_dir, f"{db_name}_backup_{timestamp}.sql.gz")
    
    print(f"[*] Iniciando backup de '{db_name}' en '{db_host}'...")
    
    # Construir comando (mysqldump debe estar en el PATH)
    cmd = [
        "mysqldump",
        f"-h{db_host}",
        f"-u{db_user}",
    ]
    if db_pass:
        cmd.append(f"-p{db_pass}")
    cmd.append(db_name)
    
    try:
        # Ejecutar mysqldump y comprimir al vuelo
        with open(backup_file, 'wb') as f:
            with gzip.GzipFile(fileobj=f, mode='wb') as gz:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    print(f"[X] Error en mysqldump: {stderr.decode('utf-8', errors='ignore')}")
                    if os.path.exists(backup_file):
                        os.remove(backup_file)
                    return False
                
                gz.write(stdout)
                
        # Verificar la integridad del backup recién generado
        if not verify_backup_integrity(backup_file):
            print(f"[X] El backup generado no superó la prueba de integridad. Eliminando...")
            if os.path.exists(backup_file):
                os.remove(backup_file)
            return False

        file_size_kb = os.path.getsize(backup_file) / 1024
        print(f"[+] Backup exitoso e íntegro: {backup_file} ({file_size_kb:.2f} KB)")
        
        # Limpieza de backups antiguos (mayores a 7 días)
        clean_old_backups(backups_dir, days_to_keep=7)
        return True
        
    except Exception as e:
        print(f"[X] Excepción durante el backup: {e}")
        return False

def clean_old_backups(backups_dir, days_to_keep=7):
    """Elimina archivos de backup más antiguos de 'days_to_keep' días."""
    now = time.time()
    for filename in os.listdir(backups_dir):
        filepath = os.path.join(backups_dir, filename)
        if os.path.isfile(filepath) and filename.endswith(".sql.gz"):
            file_mtime = os.stat(filepath).st_mtime
            if (now - file_mtime) > (days_to_keep * 86400):
                os.remove(filepath)
                print(f"[*] Backup antiguo eliminado: {filename}")

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--verify":
        target = sys.argv[2]
        ok = verify_backup_integrity(target)
        sys.exit(0 if ok else 1)
    else:
        success = run_backup()
        sys.exit(0 if success else 1)

