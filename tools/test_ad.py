import os
import sys
from dotenv import load_dotenv

# Asegurar que encuentre el .env del proyecto (cámbialo si lo mueves a otra carpeta)
project_path = r"g:\unju2025\google gravity\ServidorInventario"
sys.path.insert(0, project_path)
load_dotenv(os.path.join(project_path, ".env"))

try:
    from ldap3 import Server, Connection, ALL, SUBTREE, SIMPLE
except ImportError:
    print("Error: No se encontró la librería 'ldap3'.")
    print("Asegúrate de correr este script con el Python del entorno virtual (.venv).")
    sys.exit(1)

def test_ad_connection():
    ad_server = os.environ.get("AD_SERVER", "")
    use_ssl = os.environ.get("AD_USE_SSL", "false").strip().lower() == "true"
    base_dn = os.environ.get("AD_BASE_DN", "").strip()
    
    if not ad_server:
        print("ERROR: AD_SERVER no está configurado en tu archivo .env")
        return

    print(f"[*] Iniciando prueba de conexión AD...")
    print(f"[*] Servidor: {ad_server} (SSL: {use_ssl})")
    print(f"[*] Base DN : {base_dn}")
    
    username = input("Ingresa tu usuario de AD (ej. gmurad): ").strip()
    password = input("Ingresa tu contraseña de red: ").strip()
    
    domain = os.environ.get("AD_DOMAIN", "podjudsp.local").strip()
    bind_user = f"{username}@{domain}" if domain else username
    
    print(f"[*] Intentando bind con: {bind_user}")
    
    try:
        server = Server(ad_server, use_ssl=use_ssl, get_info=ALL, connect_timeout=5)
        conn = Connection(server, user=bind_user, password=password, authentication=SIMPLE, auto_bind=True)
        print("[+] ¡Conexión exitosa! Tu usuario tiene permisos para loguearse.")
        
        print("\n[*] Probando permiso de lectura de estructura de Computadoras...")
        search_filter = "(objectCategory=computer)"
        print(f"[*] Buscando computadoras en: {base_dn}")
        
        attributes = ["sAMAccountName", "distinguishedName", "description"]
        
        conn.search(search_base=base_dn, 
                    search_filter=search_filter, 
                    search_scope=SUBTREE, 
                    attributes=attributes)
        
        if not conn.entries:
            print("[-] No se encontraron computadoras. Posibles causas:")
            print("    1. El Base DN solo incluye Usuarios y no Computadoras.")
            print("    2. Faltan permisos de lectura en la OU de Computadoras.")
        else:
            print(f"[+] ¡Éxito! Se detectaron {len(conn.entries)} computadoras.")
            print("[*] Muestra de 5 computadoras:")
            for entry in conn.entries[:5]:
                print("    ----------------------------------")
                print(f"    Nombre PC : {getattr(entry, 'sAMAccountName', 'N/A')}")
                print(f"    OU / Ruta : {getattr(entry, 'distinguishedName', 'N/A')}")
                print(f"    Descrip   : {getattr(entry, 'description', 'N/A')}")
            
            print("\n[INFO] El servidor podrá deducir automáticamente el Fuero de cada PC usando estos datos.")
        
        conn.unbind()
        
    except Exception as e:
        print(f"\n[X] Error durante la prueba:")
        print(e)

if __name__ == "__main__":
    test_ad_connection()
