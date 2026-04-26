from database.db_core import get_db_connection
from utils.auth import current_username
from services.audit import log_audit_event

LOCAL_PRINTER_PREFIXES = ("USB", "LPT", "COM", "DOT4", "FILE:", "PORTPROMPT:", "NUL:")


def _is_network_or_shared_printer(printer_port):
    port = (printer_port or "").strip().upper()
    if not port or port == "N/A":
        return False
    if port.startswith("\\\\"):
        return True
    if "WSD" in port or "IP_" in port:
        return True
    if "." in port and not port.startswith(LOCAL_PRINTER_PREFIXES):
        return True
    return False


def _build_shared_printer_patterns(pc_name, ip_address):
    patterns = [f"%\\\\\\\\{pc_name.upper()}\\\\%"]
    if ip_address and ip_address != "N/A":
        patterns.append(f"%\\\\\\\\{ip_address}\\\\%")
    return patterns


def _release_local_printer_components(conn, pc_name, printer_sn, request_ip):
    component_ids = set()
    local_components = conn.execute(
        """
        SELECT id, serial_number, brand_model
        FROM components
        WHERE component_type LIKE 'Imp%%' AND assigned_pc = %s
        """,
        (pc_name,),
    ).fetchall()
    for row in local_components:
        component_ids.add(row["id"])

    if printer_sn and printer_sn != "N/A":
        serial_match = conn.execute(
            """
            SELECT id, serial_number, brand_model
            FROM components
            WHERE component_type LIKE 'Imp%%' AND serial_number = %s
            """,
            (printer_sn,),
        ).fetchall()
        for row in serial_match:
            component_ids.add(row["id"])

    if not component_ids:
        return 0

    placeholders = ",".join(["%s"] * len(component_ids))
    conn.execute(
        f"""
        UPDATE components
        SET assigned_pc = NULL, status = 'Stock'
        WHERE id IN ({placeholders})
        """,
        tuple(component_ids),
    )

    for row in local_components:
        log_audit_event(
            conn,
            pc_name=pc_name,
            field="LOCAL_PRINTER_RELEASE",
            old_value=row["serial_number"] or row["brand_model"] or row["id"],
            new_value="Stock",
            actor=current_username(),
            action_type="GESTION_EQUIPOS",
            request_ip=request_ip,
        )

    return len(component_ids)


def _cleanup_shared_printer_clients(conn, pc_name, ip_address, request_ip):
    patterns = _build_shared_printer_patterns(pc_name, ip_address)
    where_clause = " OR ".join(["UPPER(printer_port) LIKE %s" for _ in patterns])
    clients = conn.execute(
        f"""
        SELECT pc_name, printer_model, printer_port, printer_sn
        FROM pcs
        WHERE is_active = 'True'
          AND pc_name != %s
          AND ({where_clause})
        """,
        tuple([pc_name] + patterns),
    ).fetchall()

    if not clients:
        return 0

    for client in clients:
        client_name = client["pc_name"]
        conn.execute(
            """
            UPDATE pcs
            SET printer_model = 'SIN IMPRESORA',
                printer_port = 'N/A',
                printer_sn = 'N/A',
                alerta_sin_impresora = 1,
                alerta_impresora_red = 0
            WHERE pc_name = %s
            """,
            (client_name,),
        )
        conn.execute("DELETE FROM pc_detected_printers WHERE pc_name = %s", (client_name,))

        network_rows = conn.execute(
            f"""
            SELECT pnp.printer_id
            FROM pc_network_printers pnp
            JOIN network_printers np ON np.id = pnp.printer_id
            WHERE pnp.pc_name = %s
              AND ({' OR '.join(['UPPER(np.ip_address) LIKE %s' for _ in patterns])})
            """,
            tuple([client_name] + patterns),
        ).fetchall()
        for row in network_rows:
            conn.execute(
                "DELETE FROM pc_network_printers WHERE pc_name = %s AND printer_id = %s",
                (client_name, row["printer_id"]),
            )

        log_audit_event(
            conn,
            pc_name=client_name,
            field="SHARED_PRINTER_HOST_REMOVED",
            old_value=client["printer_port"] or client["printer_model"] or "Compartida",
            new_value="SIN IMPRESORA",
            actor=current_username(),
            action_type="GESTION_EQUIPOS",
            request_ip=request_ip,
        )

    return len(clients)


def _cleanup_pc_printer_state(conn, pc_name, request_ip):
    pc = conn.execute(
        """
        SELECT pc_name, ip_address, printer_model, printer_port, printer_sn
        FROM pcs
        WHERE pc_name = %s
        """,
        (pc_name,),
    ).fetchone()
    if not pc:
        return

    had_network_assignment = conn.execute(
        "SELECT COUNT(*) AS c FROM pc_network_printers WHERE pc_name = %s",
        (pc_name,),
    ).fetchone()["c"] > 0
    had_network_or_shared_port = _is_network_or_shared_printer(pc.get("printer_port"))

    _release_local_printer_components(conn, pc_name, pc.get("printer_sn"), request_ip)

    if had_network_assignment:
        conn.execute("DELETE FROM pc_network_printers WHERE pc_name = %s", (pc_name,))
        log_audit_event(
            conn,
            pc_name=pc_name,
            field="NETWORK_PRINTER_UNASSIGN",
            old_value="Asignaciones de red activas",
            new_value="Sin asignaciones",
            actor=current_username(),
            action_type="GESTION_EQUIPOS",
            request_ip=request_ip,
        )

    conn.execute("DELETE FROM pc_detected_printers WHERE pc_name = %s", (pc_name,))
    conn.execute(
        """
        UPDATE pcs
        SET printer_model = 'SIN IMPRESORA',
            printer_port = 'N/A',
            printer_sn = 'N/A',
            alerta_sin_impresora = 1,
            alerta_impresora_red = 0
        WHERE pc_name = %s
        """,
        (pc_name,),
    )

    if had_network_or_shared_port or had_network_assignment:
        log_audit_event(
            conn,
            pc_name=pc_name,
            field="PC_PRINTER_RESET",
            old_value=pc.get("printer_port") or pc.get("printer_model") or "Impresora configurada",
            new_value="SIN IMPRESORA",
            actor=current_username(),
            action_type="GESTION_EQUIPOS",
            request_ip=request_ip,
        )

    _cleanup_shared_printer_clients(conn, pc_name, pc.get("ip_address"), request_ip)


def decommission_pc_service(pc_name, request_ip):
    """Mueve una PC al cementerio (is_active='False')."""
    try:
        with get_db_connection() as conn:
            _cleanup_pc_printer_state(conn, pc_name, request_ip)
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
                actor=current_username(),
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
                actor=current_username(),
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
                            actor=current_username(),
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
            _cleanup_pc_printer_state(conn, pc_name, request_ip)
            conn.execute("DELETE FROM tasks WHERE pc_name = %s", (pc_name,))
            conn.execute("DELETE FROM pcs WHERE pc_name = %s", (pc_name,))
            log_audit_event(
                conn,
                pc_name=pc_name,
                field="PERMANENT_DELETE",
                old_value="Exists",
                new_value="DELETED",
                actor=current_username(),
                action_type="BORRADO_PERMANENTE",
                request_ip=request_ip,
            )
            conn.commit()
            return True
    except Exception as exc:
        print(f"Error deleting PC {pc_name}: {exc}")
        return False
