from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.db_core import get_db_connection
from datetime import datetime as dt
import requests
from utils.constants import FUERO_COLORS, FUERO_MAPPING

bp_infrastructure = Blueprint('infrastructure', __name__, url_prefix='/infra')

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
                   parent.component_type as parent_type
            FROM components c
            LEFT JOIN pcs p ON c.assigned_pc = p.pc_name
            LEFT JOIN components parent ON c.assigned_to_component_id = parent.id
            ORDER BY c.created_at DESC
        ''').fetchall()

    return render_template(
        'infrastructure.html', 
        ups_list=ups_list,
        baterias_disponibles=baterias_disponibles,
        pcs_disponibles=pcs_disponibles,
        components=components,
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

@bp_infrastructure.route('/ups/<int:id>/delete')
def delete_ups(id):
    try:
        with get_db_connection() as conn:
            ups = conn.execute("SELECT assigned_battery_id FROM ups_inventory WHERE id = %s", (id,)).fetchone()
            if ups and ups['assigned_battery_id']:
                # Liberar bateria
                conn.execute("UPDATE components SET status = 'Stock' WHERE id = %s", (ups['assigned_battery_id'],))
            conn.execute("DELETE FROM ups_inventory WHERE id = %s", (id,))
            conn.commit()
            flash("UPS eliminada.", "success")
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

@bp_infrastructure.route('/components/<int:id>/delete')
def delete_component(id):
    try:
        with get_db_connection() as conn:
            # First, check if there are sub-components and release them to stock
            conn.execute("UPDATE components SET assigned_to_component_id = NULL, status = 'Stock' WHERE assigned_to_component_id = %s", (id,))
            
            # Now delete the component
            conn.execute("DELETE FROM components WHERE id = %s", (id,))
            conn.commit()
            flash("Componente eliminado del inventario.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for('infrastructure.index'))
