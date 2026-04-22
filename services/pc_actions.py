from database.db_core import get_db_connection
from utils.auth import current_username
from services.audit import log_audit_event

def decommission_pc_service(pc_name, request_ip):
    """Mueve una PC al cementerio (is_active='False')."""
    try:
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE pcs SET is_active = 'False' WHERE pc_name = %s",
                (pc_name,),
            )
            log_audit_event(
                conn,
                pc_name=pc_name,
                field="STATUS",
                old_value="Active",
                new_value="DECOMMISSIONED (Cementerio)",
                user_name=current_username(),
                action_type="GESTION_EQUIPOS",
                request_ip=request_ip,
            )
            conn.commit()
            return True
    except Exception as exc:
        print(f"Error decommissioning PC {pc_name}: {exc}")
        return False

def reactivate_pc_service(pc_name, request_ip):
    """Saca una PC del cementerio."""
    try:
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE pcs SET is_active = 'True' WHERE pc_name = %s",
                (pc_name,),
            )
            log_audit_event(
                conn,
                pc_name=pc_name,
                field="STATUS",
                old_value="Inactive",
                new_value="REACTIVATED",
                user_name=current_username(),
                action_type="GESTION_EQUIPOS",
                request_ip=request_ip,
            )
            conn.commit()
            return True
    except Exception as exc:
        print(f"Error reactivating PC {pc_name}: {exc}")
        return False

def update_pc_infrastructure_service(pc_name, infra_data, request_ip):
    """Actualiza datos de red y ubicación de la PC."""
    try:
        with get_db_connection() as conn:
            old_pc = conn.execute("SELECT * FROM pcs WHERE pc_name = %s", (pc_name,)).fetchone()
            conn.execute(
                """UPDATE pcs SET building = %s, floor = %s, switch_name = %s, switch_port = %s, pachera_name = %s, pachera_port = %s WHERE pc_name = %s""",
                (infra_data['building'], infra_data['floor'], infra_data['switch_name'], 
                 infra_data['switch_port'], infra_data['pachera_name'], infra_data['pachera_port'], pc_name)
            )
            if old_pc:
                changes = [
                    ("building", old_pc["building"], infra_data['building']), 
                    ("floor", old_pc["floor"], infra_data['floor']),
                    ("switch_name", old_pc["switch_name"], infra_data['switch_name']), 
                    ("switch_port", old_pc["switch_port"], infra_data['switch_port']),
                    ("pachera_name", old_pc["pachera_name"], infra_data['pachera_name']), 
                    ("pachera_port", old_pc["pachera_port"], infra_data['pachera_port'])
                ]
                for field, old, new in changes:
                    if str(old or "") != str(new or ""):
                        log_audit_event(
                            conn,
                            pc_name=pc_name,
                            field=field,
                            old_value=str(old or ""),
                            new_value=str(new or ""),
                            user_name=current_username(),
                            action_type="EDICION_INFRAESTRUCTURA",
                            request_ip=request_ip,
                        )
            conn.commit()
            return True
    except Exception as e:
        print(f"Error updating infrastructure: {e}")
        return False

def delete_permanent_pc_service(pc_name, request_ip):
    """Borrado total de PC y sus tareas."""
    try:
        with get_db_connection() as conn:
            conn.execute("DELETE FROM tasks WHERE pc_name = %s", (pc_name,))
            conn.execute("DELETE FROM pcs WHERE pc_name = %s", (pc_name,))
            log_audit_event(
                conn,
                pc_name=pc_name,
                field="PERMANENT_DELETE",
                old_value="Exists",
                new_value="DELETED",
                user_name=current_username(),
                action_type="BORRADO_PERMANENTE",
                request_ip=request_ip,
            )
            conn.commit()
            return True
    except Exception as exc:
        print(f"Error deleting PC {pc_name}: {exc}")
        return False
