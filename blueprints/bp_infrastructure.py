from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.db_core import get_db_connection
from datetime import datetime as dt
import requests
import asyncio
from pysnmp.hlapi.v3arch.asyncio import *
from utils.constants import FUERO_COLORS, FUERO_MAPPING

bp_infrastructure = Blueprint('infrastructure', __name__, url_prefix='/infra')

@bp_infrastructure.app_context_processor
def inject_infra_kpis():
    from utils.auth import allowed_module_links, auth_mode_label, available_roles, current_user, has_permission, is_authenticated, role_label, generate_csrf_token
    from utils.constants import APP_VERSION
    from utils.runtime_urls import get_public_app_base_url, get_public_script_fallback_url
    
    kpis = {}
    if is_authenticated():
        try:
            with get_db_connection() as conn:
                kpis['kpi_total_activas'] = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND pc_name NOT IN ('PC Generica', 'Infraestructura')").fetchone()["c"]
                kpis['kpi_total_graveyard'] = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'False'").fetchone()["c"]
                kpis['kpi_win7'] = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND os_name LIKE %s AND pc_name NOT IN ('PC Generica', 'Infraestructura')", ("%Windows 7%",)).fetchone()["c"]
                kpis['kpi_alerta_ram'] = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND alerta_ram_baja = 1 AND pc_name NOT IN ('PC Generica', 'Infraestructura')").fetchone()["c"]
                net_pr = conn.execute("SELECT COUNT(*) as c FROM network_printers").fetchone()["c"]
                loc_pr = conn.execute("""
                    SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' 
                    AND (printer_model IS NOT NULL AND printer_model != '' AND printer_model != 'N/A' AND UPPER(printer_model) NOT LIKE '%%SIN IMPRESORA%%')
                    AND (printer_port IS NULL OR printer_port NOT LIKE '\\\\\\\\%%') AND alerta_impresora_red = 0
                    AND pc_name NOT IN (SELECT pc_name FROM pc_network_printers)
                """).fetchone()["c"]
                kpis['kpi_total_impresoras'] = net_pr + loc_pr
                kpis['kpi_tareas_hoy'] = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE estado = 'Hecha' AND DATE(completed_at) = CURDATE()").fetchone()["c"]
                kpis['kpi_total_pendientes'] = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE estado != 'Hecha'").fetchone()["c"]
        except Exception as e:
            print(f"Error in context processor KPIs (Infra): {e}")

    return {
        'app_version': APP_VERSION,
        'csrf_token': generate_csrf_token,
        'is_authenticated': is_authenticated(),
        'current_user': current_user(),
        'auth_mode_label': auth_mode_label(),
        'has_access': has_permission,
        'module_access_links': allowed_module_links(),
        'current_role_label': role_label(),
        'available_roles': available_roles(),
        'client_script_base_url': get_public_app_base_url(),
        'client_script_fallback_url': get_public_script_fallback_url(),
        **kpis 
    }

@bp_infrastructure.route('/')
def index():
    """Muestra el panel principal de Infraestructura: Baterías y UPS"""
    with get_db_connection() as conn:
        ups_list = conn.execute('''
            SELECT u.*, b.serial_number as battery_code, p.last_user, p.fuero,
                   usr.real_name as ad_real_name
            FROM ups_inventory u 
            LEFT JOIN components b ON u.assigned_battery_id = b.id
            LEFT JOIN pcs p ON u.assigned_pc = p.pc_name
            LEFT JOIN ad_users usr ON LOWER(SUBSTRING_INDEX(p.last_user, '\\\\', -1)) = usr.username
            ORDER BY u.created_at DESC
        ''').fetchall()
        
        # Baterias disponibles para el modal de asignacion
        # Baterias disponibles para el modal de asignacion
        baterias_disponibles = conn.execute("SELECT id, serial_number as code, brand_model FROM components WHERE component_type LIKE 'Bat%' AND status = 'Stock'").fetchall()
        
        # PCs disponibles
        pcs_disponibles = conn.execute("""
            SELECT p.pc_name, p.fuero, p.last_user, u.real_name as ad_real_name 
            FROM pcs p 
            LEFT JOIN ad_users u ON LOWER(SUBSTRING_INDEX(p.last_user, '\\\\', -1)) = u.username 
            WHERE p.is_active = 'True' 
            ORDER BY p.pc_name
        """).fetchall()
        
        # Componentes generales
        components = conn.execute('''
            SELECT c.*, p.fuero as pc_fuero, p.last_user,
                   parent.serial_number as parent_serial,
                   parent.component_type as parent_type,
                   u.code as ups_code,
                   u.assigned_pc as ups_assigned_pc
            FROM components c
            LEFT JOIN pcs p ON c.assigned_pc = p.pc_name
            LEFT JOIN components parent ON c.assigned_to_component_id = parent.id
            LEFT JOIN ups_inventory u ON u.assigned_battery_id = c.id
            ORDER BY c.created_at DESC
        ''').fetchall()

        # Impresoras de Red y sus asignaciones
        network_printers_raw = conn.execute("SELECT * FROM network_printers ORDER BY created_at DESC").fetchall()
        network_printers = []
        for printer in network_printers_raw:
            p_dict = dict(printer)
            # Obtener las PCs asignadas a esta impresora
            assigned = conn.execute("SELECT pc_name FROM pc_network_printers WHERE printer_id = %s", (printer["id"],)).fetchall()
            p_dict["assigned_pcs"] = [a["pc_name"] for a in assigned]
            network_printers.append(p_dict)

        # Historial de Infraestructura
        infra_logs = conn.execute("SELECT * FROM audit_logs WHERE pc_name = 'Infraestructura' ORDER BY changed_at DESC").fetchall()

    return render_template(
        'infrastructure.html', 
        ups_list=ups_list,
        baterias_disponibles=baterias_disponibles,
        pcs_disponibles=pcs_disponibles,
        components=components,
        network_printers=network_printers,
        infra_logs=infra_logs,
        fuero_colors=FUERO_COLORS
    )

@bp_infrastructure.route('/ups/add', methods=['POST'])
def add_ups():
    code = request.form.get('code', '').strip()
    model = request.form.get('model', 'LYONN CTB-800V').strip()
    supplier = request.form.get('supplier', '').strip()
    invoice_number = request.form.get('invoice_number', '').strip()
    
    if not code:
        flash("El código/serial de la UPS es obligatorio.", "error")
        return redirect(url_for('infrastructure.index'))
        
    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO ups_inventory (code, model, supplier, invoice_number) VALUES (%s, %s, %s, %s)",
                (code, model, supplier, invoice_number)
            )
            conn.commit()
        flash(f"UPS {code} agregada exitosamente.", "success")
    except Exception as e:
        flash(f"Error al agregar UPS (¿código duplicado%s): {e}", "error")
        
    return redirect(url_for('infrastructure.index'))

@bp_infrastructure.route('/ups/<int:ups_id>/assign_battery', methods=['POST'])
def assign_battery_to_ups(ups_id):
    battery_id = request.form.get('battery_id')
    
    try:
        with get_db_connection() as conn:
            # Get current UPS to see if it already has a battery
            ups = conn.execute("SELECT assigned_battery_id, code FROM ups_inventory WHERE id = %s", (ups_id,)).fetchone()
            if not ups:
                flash("UPS no encontrada", "error")
                return redirect(url_for('infrastructure.index'))
                
            old_battery_id = ups['assigned_battery_id']
            
            # If removing battery or changing it, set old battery back to Stock
            if old_battery_id:
                old_bat_data = conn.execute("SELECT serial_number FROM components WHERE id = %s", (old_battery_id,)).fetchone()
                old_bat_sn = old_bat_data['serial_number'] if old_bat_data else str(old_battery_id)
                conn.execute("UPDATE components SET status = 'Stock' WHERE id = %s", (old_battery_id,))
                conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (%s, %s, %s, %s)", 
                             (f"UPS:{ups['code']}", "Bateria Retirada", old_bat_sn, "None"))
                
            # If assigning a new battery
            if battery_id:
                new_bat_data = conn.execute("SELECT serial_number FROM components WHERE id = %s", (battery_id,)).fetchone()
                new_bat_sn = new_bat_data['serial_number'] if new_bat_data else str(battery_id)
                conn.execute("UPDATE ups_inventory SET assigned_battery_id = %s WHERE id = %s", (battery_id, ups_id))
                conn.execute("UPDATE components SET status = 'Instalado' WHERE id = %s", (battery_id,))
                conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (%s, %s, %s, %s)", 
                             (f"UPS:{ups['code']}", "Bateria RAM", "None", new_bat_sn))
            else:
                # Just removing
                conn.execute("UPDATE ups_inventory SET assigned_battery_id = NULL WHERE id = %s", (ups_id,))
                
            conn.commit()
            flash("Asignación de batería actualizada.", "success")
    except Exception as e:
        flash(f"Error asignando batería: {e}", "error")
        
    # Redirect back to where they came from (could be infrastructure page or PC detail page)
    return redirect(request.referrer or url_for('infrastructure.index'))

@bp_infrastructure.route('/ups/<int:ups_id>/assign_pc', methods=['POST'])
def assign_ups_to_pc(ups_id):
    pc_name = request.form.get('pc_name')
    
    try:
        with get_db_connection() as conn:
            ups = conn.execute("SELECT assigned_pc, code FROM ups_inventory WHERE id = %s", (ups_id,)).fetchone()
            if not ups: return redirect(url_for('infrastructure.index'))
            
            old_pc = ups['assigned_pc']
            
            if pc_name:
                conn.execute("UPDATE ups_inventory SET assigned_pc = %s WHERE id = %s", (pc_name, ups_id))
                conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (%s, %s, %s, %s)", 
                             (pc_name, "UPS Asignada", str(old_pc), f"{ups['code']}"))
            else:
                conn.execute("UPDATE ups_inventory SET assigned_pc = NULL WHERE id = %s", (ups_id,))
                if old_pc:
                    conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (%s, %s, %s, %s)", 
                                 (old_pc, "UPS Retirada", f"{ups['code']}", "None"))
            
            conn.commit()
            flash("Asignación de equipo actualizada.", "success")
    except Exception as e:
        flash(f"Error vinculando UPS: {e}", "error")
        
    return redirect(request.referrer or url_for('infrastructure.index'))

@bp_infrastructure.route('/status_check')
def status_check():
    """Verifica el estado del sistema SIGJ"""
    url = "https://sigj.justiciajujuy.gov.ar/mentradas/sesiones/login"
    try:
        # Usamos un timeout corto para no bloquear demasiado si el sitio está caído
        response = requests.get(url, timeout=5, verify=False)
        if response.status_code == 200:
            return {"status": "online", "code": response.status_code}
        else:
            return {"status": "offline", "code": response.status_code}
    except Exception as e:
        return {"status": "offline", "error": str(e)}

@bp_infrastructure.route('/ups/<int:id>/delete', methods=['POST'])
def delete_ups(id):
    try:
        with get_db_connection() as conn:
            ups = conn.execute("SELECT code, assigned_pc, assigned_battery_id FROM ups_inventory WHERE id = %s", (id,)).fetchone()
            if not ups:
                return redirect(url_for('infrastructure.index'))
            
            if ups['assigned_pc']:
                flash(f"No se puede eliminar: La UPS {ups['code']} está asignada a la PC '{ups['assigned_pc']}'. Desvincúlela primero.", "error")
                return redirect(url_for('infrastructure.index'))
                
            if ups['assigned_battery_id']:
                # Liberar bateria
                conn.execute("UPDATE components SET status = 'Stock' WHERE id = %s", (ups['assigned_battery_id'],))
            
            conn.execute("DELETE FROM ups_inventory WHERE id = %s", (id,))
            conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES ('Infraestructura', 'UPS Eliminada', %s, 'DELETED')", (ups['code'],))
            conn.commit()
            flash("UPS eliminada y registrada en el historial de infraestructura.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for('infrastructure.index'))

@bp_infrastructure.route('/components/add', methods=['POST'])
def add_component():
    serial_number = request.form.get('serial_number', '').strip()
    component_type = request.form.get('component_type', '').strip()
    brand_model = request.form.get('brand_model', '').strip()
    supplier_name = request.form.get('supplier', '').strip()
    remito_number = request.form.get('invoice_number', '').strip()
    
    if not serial_number or not component_type:
        flash("El número de serie y el tipo son obligatorios.", "error")
        return redirect(url_for('infrastructure.index'))
        
    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO components (serial_number, component_type, brand_model, supplier, invoice_number) VALUES (%s, %s, %s, %s, %s)",
                (serial_number, component_type, brand_model, supplier_name, remito_number)
            )
            conn.commit()
        flash(f"Componente {component_type} ({serial_number}) registrado exitosamente.", "success")
    except Exception as e:
        flash(f"Error al agregar componente (¿serie duplicada%s): {e}", "error")
        
    return redirect(url_for('infrastructure.index'))

@bp_infrastructure.route('/components/<int:component_id>/assign_pc', methods=['POST'])
def assign_component_to_pc(component_id):
    pc_name = request.form.get('pc_name')
    
    try:
        with get_db_connection() as conn:
            comp = conn.execute("SELECT assigned_pc, serial_number, component_type FROM components WHERE id = %s", (component_id,)).fetchone()
            if not comp: return redirect(url_for('infrastructure.index'))
            
            old_pc = comp['assigned_pc']
            
            if pc_name:
                conn.execute("UPDATE components SET assigned_pc = %s, assigned_to_component_id = NULL, status = 'Instalado' WHERE id = %s", (pc_name, component_id))
                conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (%s, %s, %s, %s)", 
                             (pc_name, f"{comp['component_type']} Asignado", str(old_pc), comp['serial_number']))
            else:
                conn.execute("UPDATE components SET assigned_pc = NULL, status = 'Stock' WHERE id = %s", (component_id,))
                if old_pc:
                    conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (%s, %s, %s, %s)", 
                                 (old_pc, f"{comp['component_type']} Retirado", comp['serial_number'], "None"))
            
            conn.commit()
            flash("Asignación de componente a PC actualizada.", "success")
    except Exception as e:
        flash(f"Error vinculando componente: {e}", "error")
        
    return redirect(request.referrer or url_for('infrastructure.index'))

@bp_infrastructure.route('/components/<int:component_id>/assign_component', methods=['POST'])
def assign_component_to_component(component_id):
    parent_id = request.form.get('parent_component_id')
    
    try:
        with get_db_connection() as conn:
            comp = conn.execute("SELECT assigned_to_component_id, serial_number, component_type FROM components WHERE id = %s", (component_id,)).fetchone()
            if not comp: return redirect(url_for('infrastructure.index'))
            
            if parent_id:
                # Get parent details for log
                parent = conn.execute("SELECT serial_number, component_type, assigned_pc FROM components WHERE id = %s", (parent_id,)).fetchone()
                
                conn.execute("UPDATE components SET assigned_to_component_id = %s, assigned_pc = %s, status = 'Instalado' WHERE id = %s", 
                             (parent_id, parent['assigned_pc'], component_id))
                
                pc_context = parent["assigned_pc"] or f"COMP:{parent['serial_number']}"
                conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (%s, %s, %s, %s)", 
                             (pc_context, f"Sub-componente {comp['component_type']} Asignado a {parent['component_type']}", "None", comp['serial_number']))
            else:
                conn.execute("UPDATE components SET assigned_to_component_id = NULL, assigned_pc = NULL, status = 'Stock' WHERE id = %s", (component_id,))
            
            conn.commit()
            flash("Asignación interna de componente actualizada.", "success")
    except Exception as e:
        flash(f"Error vinculando sub-componente: {e}", "error")
        
    return redirect(request.referrer or url_for('infrastructure.index'))

@bp_infrastructure.route('/components/<int:id>/delete', methods=['POST'])
def delete_component(id):
    try:
        with get_db_connection() as conn:
            comp = conn.execute("SELECT serial_number, component_type, status FROM components WHERE id = %s", (id,)).fetchone()
            if not comp:
                return redirect(url_for('infrastructure.index'))
                
            if comp['status'] != 'Stock':
                flash(f"No se puede eliminar: El componente {comp['component_type']} ({comp['serial_number']}) se encuentra En Uso. Desvincúlelo primero.", "error")
                return redirect(url_for('infrastructure.index'))
                
            # Check if it is a battery assigned to a UPS and unassign it to avoid foreign key/logic errors
            conn.execute("UPDATE ups_inventory SET assigned_battery_id = NULL WHERE assigned_battery_id = %s", (id,))
            
            # Check if there are sub-components and release them to stock
            conn.execute("UPDATE components SET assigned_to_component_id = NULL, status = 'Stock' WHERE assigned_to_component_id = %s", (id,))
            
            # Now delete the component
            conn.execute("DELETE FROM components WHERE id = %s", (id,))
            conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES ('Infraestructura', %s, %s, 'DELETED')", 
                         (f"Componente Eliminado ({comp['component_type']})", comp['serial_number']))
            conn.commit()
            flash("Componente eliminado del inventario y registrado en el historial.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for('infrastructure.index'))

@bp_infrastructure.route('/network_printers/add', methods=['POST'])
def add_network_printer():
    ip_address = request.form.get('ip_address', '').strip()
    serial_number = request.form.get('serial_number', '').strip()
    brand_model = request.form.get('brand_model', '').strip()
    assigned_pc_name = request.form.get('assigned_pc_name', '').strip()
    
    if not serial_number or not ip_address:
        flash("La Dirección IP y el Número de Serie son obligatorios.", "error")
        return redirect(request.referrer or url_for('infrastructure.index'))
    
    # Limpiar IP antes de guardar
    ip_address = ip_address.strip().split(' ')[0]
        
    try:
        with get_db_connection() as conn:
            # 1. Verificar si ya existe por SERIAL NUMBER
            existing = conn.execute(
                "SELECT id FROM network_printers WHERE serial_number = %s", (serial_number,)
            ).fetchone()
            
            if existing:
                printer_id = existing['id']
                # Actualizar IP y Modelo si ya existía (por si cambiaron)
                conn.execute(
                    "UPDATE network_printers SET ip_address = %s, brand_model = %s WHERE id = %s",
                    (ip_address, brand_model, printer_id)
                )
            else:
                # 2. Si no existe, insertar nueva y obtener ID
                cursor = conn.execute(
                    "INSERT INTO network_printers (ip_address, serial_number, brand_model) VALUES (%s, %s, %s)",
                    (ip_address, serial_number, brand_model)
                )
                printer_id = cursor.lastrowid
            
            # 3. Vincular a la PC si se especificó
            if assigned_pc_name:
                # Evitar duplicidad en la asignación
                assigned_existing = conn.execute(
                    "SELECT id FROM pc_network_printers WHERE pc_name = %s AND printer_id = %s",
                    (assigned_pc_name, printer_id)
                ).fetchone()
                
                if not assigned_existing:
                    conn.execute(
                        "INSERT INTO pc_network_printers (pc_name, printer_id) VALUES (%s, %s)",
                        (assigned_pc_name, printer_id)
                    )
                    conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (%s, %s, %s, %s)", 
                                 (assigned_pc_name, "Impresora Red Vinculada (Promoción)", "None", ip_address))
                    flash(f"Impresora {ip_address} ({serial_number}) vinculada correctamente a {assigned_pc_name}.", "success")
                else:
                    flash(f"La impresora {ip_address} ya estaba vinculada a {assigned_pc_name}.", "info")
            else:
                flash(f"Datos de impresora de red ({ip_address}) actualizados/registrados.", "success")
                
            conn.commit()
    except Exception as e:
        flash(f"Error procesando impresora de red: {e}", "error")
        
    return redirect(request.referrer or url_for('infrastructure.index'))

@bp_infrastructure.route('/network_printers/<int:id>/delete', methods=['POST'])
def delete_network_printer(id):
    try:
        with get_db_connection() as conn:
            printer = conn.execute("SELECT ip_address, brand_model FROM network_printers WHERE id = %s", (id,)).fetchone()
            if not printer:
                return redirect(url_for('infrastructure.index'))
                
            # Verificar si está en uso en pc_network_printers
            used_pcs = conn.execute("SELECT pc_name FROM pc_network_printers WHERE printer_id = %s", (id,)).fetchall()
            if used_pcs:
                pc_names = ", ".join([p["pc_name"] for p in used_pcs])
                flash(f"No se puede eliminar: La impresora ({printer['ip_address']}) está actualmente asignada a: {pc_names}. Desvincúlela primero.", "error")
                return redirect(url_for('infrastructure.index'))
                
            conn.execute("DELETE FROM network_printers WHERE id = %s", (id,))
            conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES ('Infraestructura', 'Impresora de Red Eliminada', %s, 'DELETED')", 
                         (printer['ip_address'],))
            conn.commit()
            flash("Impresora de red eliminada del catálogo y registrada en el historial.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for('infrastructure.index'))

@bp_infrastructure.route('/network_printers/<int:printer_id>/assign_pc', methods=['POST'])
def assign_network_printer(printer_id):
    pc_name = request.form.get('pc_name', '').strip()
    if not pc_name:
        flash("Debe seleccionar una PC válida.", "error")
        return redirect(request.referrer or url_for('infrastructure.index'))
        
    try:
        with get_db_connection() as conn:
            # Check if printer exists
            printer = conn.execute("SELECT ip_address FROM network_printers WHERE id = %s", (printer_id,)).fetchone()
            if not printer:
                flash("Impresora no encontrada.", "error")
                return redirect(request.referrer or url_for('infrastructure.index'))
                
            # Check if already assigned
            existing = conn.execute("SELECT id FROM pc_network_printers WHERE printer_id = %s AND pc_name = %s", (printer_id, pc_name)).fetchone()
            if existing:
                flash(f"La impresora {printer['ip_address']} ya estaba asignada a {pc_name}.", "info")
                return redirect(request.referrer or url_for('infrastructure.index'))
                
            conn.execute("INSERT INTO pc_network_printers (pc_name, printer_id) VALUES (%s, %s)", (pc_name, printer_id))
            conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (%s, %s, %s, %s)", 
                         (pc_name, "Impresora Red Asignada", "None", printer['ip_address']))
            conn.commit()
            flash(f"Impresora {printer['ip_address']} asignada a {pc_name} exitosamente.", "success")
    except Exception as e:
        flash(f"Error al asignar impresora: {e}", "error")
        
    return redirect(request.referrer or url_for('infrastructure.index'))

@bp_infrastructure.route('/network_printers/<int:printer_id>/unassign_pc', methods=['POST'])
def unassign_network_printer(printer_id):
    pc_name = request.form.get('pc_name', '').strip()
    
    try:
        with get_db_connection() as conn:
            printer = conn.execute("SELECT ip_address FROM network_printers WHERE id = %s", (printer_id,)).fetchone()
            if not printer:
                return redirect(request.referrer or url_for('infrastructure.index'))
                
            conn.execute("DELETE FROM pc_network_printers WHERE printer_id = %s AND pc_name = %s", (printer_id, pc_name))
            conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (%s, %s, %s, %s)", 
                         (pc_name, "Impresora Red Desvinculada", printer['ip_address'], "None"))
            conn.commit()
            flash(f"Impresora {printer['ip_address']} desvinculada de {pc_name}.", "success")
    except Exception as e:
        flash(f"Error al desvincular impresora: {e}", "error")
        
    return redirect(request.referrer or url_for('infrastructure.index'))

@bp_infrastructure.route('/api/snmp_printer')
def snmp_printer():
    ip = request.args.get('ip')
    if not ip:
        return {"error": "No IP provided"}, 400
    
    # Limpiar IP por si viene con texto extra (ej: "192.168.1.9 (Red)")
    ip = ip.strip().split(' ')[0]
    
    try:
        data = asyncio.run(snmp_fetch(ip))
        return data
    except Exception as e:
        return {"error": str(e)}, 500

async def snmp_fetch(ip):
    snmp_engine = SnmpEngine()
    result = {
        "brand_model": "",
        "serial_number": "",
        "mac_address": ""
    }
    try:
        transport = await UdpTransportTarget.create((ip, 161), timeout=2.0, retries=1)
        
        # 1. Fetch sysDescr (Model)
        errorIndication, errorStatus, errorIndex, varBindTable = await get_cmd(
            snmp_engine,
            CommunityData('public', mpModel=0),
            transport,
            ContextData(),
            ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0'))
        )
        if not errorIndication and not errorStatus and varBindTable:
            val = varBindTable[0][1].prettyPrint()
            result["brand_model"] = val.split('/')[0].strip() if '/' in val else val.strip()
            
        # 2. Fetch MAC (ifPhysAddress)
        async for errorIndication, errorStatus, errorIndex, varBinds in walk_cmd(
            snmp_engine,
            CommunityData('public', mpModel=0),
            transport,
            ContextData(),
            ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.6')),
            lexicographicMode=False
        ):
            if not errorIndication and not errorStatus and varBinds:
                val = varBinds[0][1]
                if val.prettyPrint().startswith('0x'):
                    mac_hex = val.prettyPrint()[2:]
                    if len(mac_hex) == 12:
                        mac_str = ':'.join(mac_hex[i:i+2] for i in range(0, 12, 2)).upper()
                        if not result["mac_address"] and mac_str != "00:00:00:00:00:00":
                            result["mac_address"] = mac_str

        # 3. Fetch Serial Number (prtGeneralSerialNumber)
        async for errorIndication, errorStatus, errorIndex, varBinds in walk_cmd(
            snmp_engine,
            CommunityData('public', mpModel=0),
            transport,
            ContextData(),
            ObjectType(ObjectIdentity('1.3.6.1.2.1.43.5.1.1.17')),
            lexicographicMode=False
        ):
            if not errorIndication and not errorStatus and varBinds:
                val = varBinds[0][1].prettyPrint()
                if val and val != "No Such Instance currently exists at this OID":
                    result["serial_number"] = val
                    break
                    
    except Exception as e:
        print(f"SNMP Error: {e}")
    finally:
        snmp_engine.close_dispatcher()
        
    return result
