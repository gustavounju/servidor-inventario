from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.db_core import get_db_connection
from datetime import datetime as dt
from utils.constants import FUERO_COLORS, FUERO_MAPPING

bp_infrastructure = Blueprint('infrastructure', __name__, url_prefix='/infra')

@bp_infrastructure.route('/')
def index():
    """Muestra el panel principal de Infraestructura: Baterías y UPS"""
    with get_db_connection() as conn:
        baterias = conn.execute("SELECT * FROM baterias_stock ORDER BY created_at DESC").fetchall()
        ups_list = conn.execute('''
            SELECT u.*, b.code as battery_code, p.last_user, p.fuero 
            FROM ups_inventory u 
            LEFT JOIN baterias_stock b ON u.assigned_battery_id = b.id
            LEFT JOIN pcs p ON u.assigned_pc = p.pc_name
            ORDER BY u.created_at DESC
        ''').fetchall()
        
        # Baterias disponibles para el modal de asignacion
        baterias_disponibles = conn.execute("SELECT id, code, brand_model FROM baterias_stock WHERE status = 'Stock'").fetchall()
        
        # PCs disponibles
        pcs_disponibles = conn.execute("SELECT pc_name, fuero FROM pcs WHERE is_active = 'True' ORDER BY pc_name").fetchall()

    return render_template(
        'infrastructure.html', 
        baterias=baterias, 
        ups_list=ups_list,
        baterias_disponibles=baterias_disponibles,
        pcs_disponibles=pcs_disponibles,
        fuero_colors=FUERO_COLORS
    )

@bp_infrastructure.route('/battery/add', methods=['POST'])
def add_battery():
    code = request.form.get('code', '').strip()
    brand_model = request.form.get('brand_model', '').strip()
    
    if not code:
        flash("El código de la batería es obligatorio.", "error")
        return redirect(url_for('infrastructure.index'))
        
    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO baterias_stock (code, brand_model) VALUES (?, ?)",
                (code, brand_model)
            )
            conn.commit()
        flash(f"Batería {code} agregada exitosamente.", "success")
    except Exception as e:
        flash(f"Error al agregar batería (¿código duplicado?): {e}", "error")
        
    return redirect(url_for('infrastructure.index'))

@bp_infrastructure.route('/battery/<int:id>/delete')
def delete_battery(id):
    try:
        with get_db_connection() as conn:
            # Check if assigned
            b = conn.execute("SELECT status FROM baterias_stock WHERE id = ?", (id,)).fetchone()
            if b and b['status'] == 'Asignada':
                flash("No se puede eliminar una batería que está asignada a una UPS.", "error")
            else:
                conn.execute("DELETE FROM baterias_stock WHERE id = ?", (id,))
                conn.commit()
                flash("Batería eliminada.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for('infrastructure.index'))

@bp_infrastructure.route('/ups/add', methods=['POST'])
def add_ups():
    code = request.form.get('code', '').strip()
    model = request.form.get('model', 'LYONN CTB-800V').strip()
    
    if not code:
        flash("El código/serial de la UPS es obligatorio.", "error")
        return redirect(url_for('infrastructure.index'))
        
    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO ups_inventory (code, model) VALUES (?, ?)",
                (code, model)
            )
            conn.commit()
        flash(f"UPS {code} agregada exitosamente.", "success")
    except Exception as e:
        flash(f"Error al agregar UPS (¿código duplicado?): {e}", "error")
        
    return redirect(url_for('infrastructure.index'))

@bp_infrastructure.route('/ups/<int:ups_id>/assign_battery', methods=['POST'])
def assign_battery_to_ups(ups_id):
    battery_id = request.form.get('battery_id')
    
    try:
        with get_db_connection() as conn:
            # Get current UPS to see if it already has a battery
            ups = conn.execute("SELECT assigned_battery_id, code FROM ups_inventory WHERE id = ?", (ups_id,)).fetchone()
            if not ups:
                flash("UPS no encontrada", "error")
                return redirect(url_for('infrastructure.index'))
                
            old_battery_id = ups['assigned_battery_id']
            
            # If removing battery or changing it, set old battery back to Stock
            if old_battery_id:
                conn.execute("UPDATE baterias_stock SET status = 'Stock' WHERE id = ?", (old_battery_id,))
                conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (?, ?, ?, ?)", 
                             (f"UPS:{ups['code']}", "Bateria Retirada", str(old_battery_id), "None"))
                
            # If assigning a new battery
            if battery_id:
                conn.execute("UPDATE ups_inventory SET assigned_battery_id = ? WHERE id = ?", (battery_id, ups_id))
                conn.execute("UPDATE baterias_stock SET status = 'Asignada' WHERE id = ?", (battery_id,))
                conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (?, ?, ?, ?)", 
                             (f"UPS:{ups['code']}", "Bateria RAM", "None", str(battery_id)))
            else:
                # Just removing
                conn.execute("UPDATE ups_inventory SET assigned_battery_id = NULL WHERE id = ?", (ups_id,))
                
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
            ups = conn.execute("SELECT assigned_pc, code FROM ups_inventory WHERE id = ?", (ups_id,)).fetchone()
            if not ups: return redirect(url_for('infrastructure.index'))
            
            old_pc = ups['assigned_pc']
            
            if pc_name:
                conn.execute("UPDATE ups_inventory SET assigned_pc = ? WHERE id = ?", (pc_name, ups_id))
                conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (?, ?, ?, ?)", 
                             (pc_name, "UPS Asignada", str(old_pc), f"{ups['code']}"))
            else:
                conn.execute("UPDATE ups_inventory SET assigned_pc = NULL WHERE id = ?", (ups_id,))
                if old_pc:
                    conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (?, ?, ?, ?)", 
                                 (old_pc, "UPS Retirada", f"{ups['code']}", "None"))
            
            conn.commit()
            flash("Asignación de equipo actualizada.", "success")
    except Exception as e:
        flash(f"Error vinculando UPS: {e}", "error")
        
    return redirect(request.referrer or url_for('infrastructure.index'))

@bp_infrastructure.route('/ups/<int:id>/delete')
def delete_ups(id):
    try:
        with get_db_connection() as conn:
            ups = conn.execute("SELECT assigned_battery_id FROM ups_inventory WHERE id = ?", (id,)).fetchone()
            if ups and ups['assigned_battery_id']:
                # Liberar bateria
                conn.execute("UPDATE baterias_stock SET status = 'Stock' WHERE id = ?", (ups['assigned_battery_id'],))
            conn.execute("DELETE FROM ups_inventory WHERE id = ?", (id,))
            conn.commit()
            flash("UPS eliminada.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for('infrastructure.index'))
