import os
from flask import current_app
from database.db_core import get_db_connection
from utils.auth import _ad_default_domain
from dotenv import load_dotenv

def sync_ad_users():
    load_dotenv(override=True)
    
    ad_server = os.environ.get("AD_SERVER", "").strip()
    if not ad_server:
        return {"status": "error", "message": "AD_SERVER no está configurado."}

    sync_user = os.environ.get("AD_SYNC_USER", "").strip()
    sync_password = os.environ.get("AD_SYNC_PASSWORD", "")
    
    if not sync_user or not sync_password:
        return {"status": "error", "message": "Faltan credenciales de sincronización (AD_SYNC_USER / AD_SYNC_PASSWORD)."}

    try:
        from ldap3 import ALL, NONE, NTLM, SIMPLE, Connection, Server, SUBTREE
    except Exception as exc:
        return {"status": "error", "message": f"ldap3 no disponible: {exc}"}

    use_ssl = os.environ.get("AD_USE_SSL", "false").strip().lower() == "true"
    connect_timeout = int(os.environ.get("AD_CONNECT_TIMEOUT", "5"))
    base_dn = os.environ.get("AD_BASE_DN", "").strip()
    domain = _ad_default_domain()

    if not base_dn:
        return {"status": "error", "message": "AD_BASE_DN no está configurado."}

    server = Server(ad_server, use_ssl=use_ssl, get_info=NONE, connect_timeout=connect_timeout)
    
    bind_user = f"{sync_user}@{domain}" if domain and "\\" not in sync_user and "@" not in sync_user else sync_user

    try:
        conn = Connection(server, user=bind_user, password=sync_password, authentication=SIMPLE, auto_bind=True)
    except Exception as e:
        return {"status": "error", "message": f"Error al conectar con AD: {e}"}

    # Búsqueda de todos los usuarios
    search_filter = "(&(objectClass=user)(objectCategory=person)(sAMAccountName=*))"
    attributes = ["sAMAccountName", "displayName", "telephoneNumber", "department"]
    
    try:
        conn.search(base_dn, search_filter, search_scope=SUBTREE, attributes=attributes)
    except Exception as e:
        conn.unbind()
        return {"status": "error", "message": f"Error en la búsqueda LDAP: {e}"}

    users_synced = 0
    with get_db_connection() as db_conn:
        for entry in conn.entries:
            username = getattr(entry, "sAMAccountName", None)
            display_name = getattr(entry, "displayName", None)
            
            if not username or not display_name:
                continue
                
            username = str(getattr(username, "value", username) or "").strip().lower()
            display_name = str(getattr(display_name, "value", display_name) or "").strip()
            
            if not username or not display_name:
                continue
                
            phone_attr = getattr(entry, "telephoneNumber", None)
            department_attr = getattr(entry, "department", None)
            
            phone = str(getattr(phone_attr, "value", phone_attr) or "")
            fuero = str(getattr(department_attr, "value", department_attr) or "")

            db_conn.execute(
                """
                INSERT INTO ad_users (username, real_name, phone, fuero)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    real_name = VALUES(real_name),
                    phone = IF(phone IS NULL OR phone = '', VALUES(phone), phone),
                    fuero = IF(fuero IS NULL OR fuero = '', VALUES(fuero), fuero)
                """,
                (username, display_name, phone, fuero)
            )
            users_synced += 1
        
        db_conn.commit()

    conn.unbind()
    
    return {"status": "success", "message": f"Sincronización completada. Se procesaron {users_synced} usuarios."}

def sync_computers_from_ad():
    load_dotenv(override=True)
    
    ad_server = os.environ.get("AD_SERVER", "").strip()
    if not ad_server:
        return {"status": "error", "message": "AD_SERVER no está configurado."}

    sync_user = os.environ.get("AD_SYNC_USER", "").strip()
    sync_password = os.environ.get("AD_SYNC_PASSWORD", "")
    
    if not sync_user or not sync_password:
        return {"status": "error", "message": "Faltan credenciales de sincronización (AD_SYNC_USER / AD_SYNC_PASSWORD)."}

    try:
        from ldap3 import ALL, NONE, NTLM, SIMPLE, Connection, Server, SUBTREE
    except Exception as exc:
        return {"status": "error", "message": f"ldap3 no disponible: {exc}"}

    use_ssl = os.environ.get("AD_USE_SSL", "false").strip().lower() == "true"
    connect_timeout = int(os.environ.get("AD_CONNECT_TIMEOUT", "5"))
    domain = os.environ.get("AD_DOMAIN", "podjudsp.local").strip()
    root_dn = ",".join([f"DC={part}" for part in domain.split(".")])

    server = Server(ad_server, use_ssl=use_ssl, get_info=NONE, connect_timeout=connect_timeout)
    bind_user = f"{sync_user}@{domain}" if domain and "\\" not in sync_user and "@" not in sync_user else sync_user

    try:
        conn = Connection(server, user=bind_user, password=sync_password, authentication=SIMPLE, auto_bind=True)
    except Exception as e:
        return {"status": "error", "message": f"Error al conectar con AD: {e}"}

    # Búsqueda de todas las computadoras
    search_filter = "(objectCategory=computer)"
    attributes = ["sAMAccountName", "distinguishedName"]
    
    try:
        conn.search(root_dn, search_filter, search_scope=SUBTREE, attributes=attributes)
    except Exception as e:
        conn.unbind()
        return {"status": "error", "message": f"Error en la búsqueda LDAP: {e}"}

    pcs_synced = 0
    with get_db_connection() as db_conn:
        for entry in conn.entries:
            sam_account = getattr(entry, "sAMAccountName", None)
            distinguished_name = getattr(entry, "distinguishedName", None)
            
            if not sam_account or not distinguished_name:
                continue
                
            pc_name = str(getattr(sam_account, "value", sam_account) or "").strip()
            if pc_name.endswith("$"):
                pc_name = pc_name[:-1]
                
            dn = str(getattr(distinguished_name, "value", distinguished_name) or "").strip()
            
            # Extraer las OUs del DN para armar el Fuero
            parts = dn.split(",")
            ous = [p.replace("OU=", "") for p in parts if p.startswith("OU=")]
            # Invertimos para que quede general a específico (ej: Tribunal de Trabajo -> Sala IV)
            # Ignoraremos "EQUIPOS" o "USUARIOS" o "PODJUDSP" que son genéricos
            ignored_ous = {"EQUIPOS", "USUARIOS", "PODJUDSP"}
            filtered_ous = [ou for ou in reversed(ous) if ou.upper() not in ignored_ous]
            
            fuero_label = " - ".join(filtered_ous) if filtered_ous else None
            
            if fuero_label:
                # Actualizar en la DB local si existe la PC
                db_conn.execute(
                    """
                    UPDATE pcs 
                    SET fuero = %s 
                    WHERE pc_name = %s OR pc_name = %s
                    """,
                    (fuero_label, pc_name, pc_name.upper())
                )
                if db_conn.cursor.rowcount > 0:
                    pcs_synced += 1
        
        db_conn.commit()

    conn.unbind()
    
    return {"status": "success", "message": f"Sincronización completada. Se actualizaron {pcs_synced} PCs."}
