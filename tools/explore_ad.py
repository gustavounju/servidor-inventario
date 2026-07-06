import os
import sys
from dotenv import load_dotenv

project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_path)
load_dotenv(os.path.join(project_path, ".env"))

try:
    from ldap3 import Server, Connection, ALL, SUBTREE, SIMPLE
except ImportError:
    print("Error: ldap3 no está instalado.")
    sys.exit(1)

def explore_ad():
    ad_server = os.environ.get("AD_SERVER", "")
    use_ssl = os.environ.get("AD_USE_SSL", "false").strip().lower() == "true"
    
    # Usaremos el dominio raíz en lugar del AD_BASE_DN restrictivo
    domain = os.environ.get("AD_DOMAIN", "podjudsp.local").strip()
    # Convertir "podjudsp.local" a "DC=podjudsp,DC=local"
    root_dn = ",".join([f"DC={part}" for part in domain.split(".")])

    print(f"[*] Conectando a {ad_server}...")
    username = input("Ingresa tu usuario de AD (ej. gmurad): ").strip()
    password = input("Ingresa tu contraseña de red: ").strip()
    
    bind_user = f"{username}@{domain}" if domain else username
    
    try:
        server = Server(ad_server, use_ssl=use_ssl, get_info=ALL, connect_timeout=5)
        conn = Connection(server, user=bind_user, password=password, authentication=SIMPLE, auto_bind=True)
        print("[+] Conexión exitosa.\n")
        
        print(f"[*] Explorando el árbol completo desde: {root_dn}")
        
        # Buscar todas las Unidades Organizativas (OUs)
        print("\n=== UNIDADES ORGANIZATIVAS (FUEROS/ÁREAS) ===")
        conn.search(search_base=root_dn, 
                    search_filter="(objectClass=organizationalUnit)", 
                    search_scope=SUBTREE, 
                    attributes=["ou", "distinguishedName"])
        
        ous = sorted([entry for entry in conn.entries], key=lambda x: str(x.distinguishedName))
        print(f"Se encontraron {len(ous)} OUs.")
        for ou in ous[:20]: # Mostramos las primeras 20 para no saturar
            print(f"  - {ou.distinguishedName}")
        if len(ous) > 20:
            print("  ... (mostrando solo 20)")

        # Buscar Computadoras
        print("\n=== COMPUTADORAS ===")
        conn.search(search_base=root_dn, 
                    search_filter="(objectCategory=computer)", 
                    search_scope=SUBTREE, 
                    attributes=["sAMAccountName", "distinguishedName", "description"])
        
        pcs = conn.entries
        print(f"Se encontraron {len(pcs)} computadoras.")
        for pc in pcs[:10]:
            print(f"  - PC: {getattr(pc, 'sAMAccountName', 'N/A')} | Ubicación: {getattr(pc, 'distinguishedName', 'N/A')}")
        if len(pcs) > 10:
            print("  ... (mostrando solo 10)")

        # Buscar Usuarios
        print("\n=== USUARIOS ===")
        conn.search(search_base=root_dn, 
                    search_filter="(&(objectCategory=person)(objectClass=user))", 
                    search_scope=SUBTREE, 
                    attributes=["sAMAccountName", "distinguishedName", "displayName"])
        
        users = conn.entries
        print(f"Se encontraron {len(users)} usuarios.")
        for user in users[:10]:
            print(f"  - Usuario: {getattr(user, 'sAMAccountName', 'N/A')} ({getattr(user, 'displayName', 'N/A')})")
        if len(users) > 10:
            print("  ... (mostrando solo 10)")

        conn.unbind()
        
    except Exception as e:
        print(f"\n[X] Error: {e}")

if __name__ == "__main__":
    explore_ad()
