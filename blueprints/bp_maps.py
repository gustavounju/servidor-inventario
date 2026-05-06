from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import os
from database.db_core import get_db_connection
from utils.auth import current_username, auth_guard
from werkzeug.utils import secure_filename
from utils.constants import UPLOAD_FOLDER

bp_maps = Blueprint('maps', __name__, url_prefix='/planos')

@bp_maps.route('/')
def index():
    """Listado de planos disponibles."""
    try:
        with get_db_connection() as conn:
            maps = conn.execute("SELECT * FROM infrastructure_maps ORDER BY building, floor").fetchall()
        return render_template('maps_list.html', maps=maps)
    except Exception as e:
        return f"Error en Planos: {str(e)}", 500

@bp_maps.route('/add', methods=['POST'])
def add_map():
    """Sube un nuevo plano."""
    name = request.form.get('name')
    building = request.form.get('building')
    floor = request.form.get('floor')
    file = request.files.get('file')

    if not name or not file:
        flash("Nombre y archivo son obligatorios.", "error")
        return redirect(url_for('maps.index'))

    filename = secure_filename(file.filename)
    # Asegurar que el nombre de archivo sea único
    import time
    filename = f"{int(time.time())}_{filename}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    # La URL que usaremos en el frontend (ajustar si se usa otro método de servir estáticos)
    image_url = f"/uploads/{filename}"

    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO infrastructure_maps (name, image_url, building, floor) VALUES (%s, %s, %s, %s)",
            (name, image_url, building, floor)
        )
        conn.commit()

    flash("Plano subido exitosamente.", "success")
    return redirect(url_for('maps.index'))

@bp_maps.route('/view/<int:map_id>')
def view_map(map_id):
    """Visualización y editor de equipos sobre el plano."""
    try:
        with get_db_connection() as conn:
            map_data = conn.execute("SELECT * FROM infrastructure_maps WHERE id = %s", (map_id,)).fetchone()
            if not map_data:
                flash("Plano no encontrado.", "error")
                return redirect(url_for('maps.index'))

            pattern_gen = "%GENERICA%"
            pattern_infra = "%INFRAESTRUCTURA%"

            # Obtener PCs asignadas a este mapa (excluyendo auxiliares)
            pcs_on_map = conn.execute("""
                SELECT pc_name, x_pos, y_pos, fuero, last_user 
                FROM pcs 
                WHERE map_id = %s AND is_active = 'True' 
                AND pc_name NOT LIKE %s AND pc_name NOT LIKE %s
            """, (map_id, pattern_gen, pattern_infra)).fetchall()
            
            # Impresoras de red asignadas a este mapa
            printers_on_map = conn.execute("SELECT id, brand_model, x_pos, y_pos, fuero, ip_address FROM network_printers WHERE map_id = %s", (map_id,)).fetchall()
            
            # Usuarios asignados a este mapa
            users_on_map = conn.execute("SELECT username, display_name, x_pos, y_pos FROM ad_users WHERE map_id = %s", (map_id,)).fetchall()

            # Lista de activos disponibles para agregar al mapa
            available_pcs = conn.execute("""
                SELECT pc_name, fuero 
                FROM pcs 
                WHERE (map_id IS NULL OR map_id != %s) AND is_active = 'True' 
                AND pc_name NOT LIKE %s AND pc_name NOT LIKE %s
                ORDER BY pc_name
            """, (map_id, pattern_gen, pattern_infra)).fetchall()
            
            available_printers = conn.execute("SELECT id, brand_model, ip_address FROM network_printers WHERE (map_id IS NULL OR map_id != %s) ORDER BY brand_model", (map_id,)).fetchall()
            
            available_users = conn.execute("SELECT username, display_name FROM ad_users WHERE (map_id IS NULL OR map_id != %s) ORDER BY display_name", (map_id,)).fetchall()

        return render_template(
            'map_editor.html', 
            map=map_data, 
            pcs=pcs_on_map, 
            printers=printers_on_map,
            users=users_on_map,
            available_pcs=available_pcs,
            available_printers=available_printers,
            available_users=available_users
        )
    except Exception as e:
        # Si esto falla, es casi seguro que falta una columna en ad_users o similar
        return f"<h1>Error de Base de Datos</h1><p>Detalle: {str(e)}</p><p>Asegúrese de haber reiniciado el servicio para aplicar las migraciones.</p>", 500

@bp_maps.route('/api/update_position', methods=['POST'])
def update_position():
    """API para actualizar la posición de un activo (drag & drop)."""
    data = request.json
    asset_type = data.get('type') # 'pc' o 'printer'
    asset_id = data.get('id')     # pc_name o printer_id
    x = data.get('x')
    y = data.get('y')
    map_id = data.get('map_id')

    try:
        with get_db_connection() as conn:
            if asset_type == 'pc':
                conn.execute(
                    "UPDATE pcs SET x_pos = %s, y_pos = %s, map_id = %s WHERE pc_name = %s",
                    (x, y, map_id, asset_id)
                )
            elif asset_type == 'printer':
                conn.execute(
                    "UPDATE network_printers SET x_pos = %s, y_pos = %s, map_id = %s WHERE id = %s",
                    (x, y, map_id, asset_id)
                )
            elif asset_type == 'user':
                conn.execute(
                    "UPDATE ad_users SET x_pos = %s, y_pos = %s, map_id = %s WHERE username = %s",
                    (x, y, map_id, asset_id)
                )
            conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_maps.route('/api/remove_from_map', methods=['POST'])
def remove_from_map():
    """API para quitar un activo del mapa."""
    data = request.json
    asset_type = data.get('type')
    asset_id = data.get('id')

    try:
        with get_db_connection() as conn:
            if asset_type == 'pc':
                conn.execute("UPDATE pcs SET map_id = NULL, x_pos = 0, y_pos = 0 WHERE pc_name = %s", (asset_id,))
            elif asset_type == 'printer':
                conn.execute("UPDATE network_printers SET map_id = NULL, x_pos = 0, y_pos = 0 WHERE id = %s", (asset_id,))
            elif asset_type == 'user':
                conn.execute("UPDATE ad_users SET map_id = NULL, x_pos = 0, y_pos = 0 WHERE username = %s", (asset_id,))
            conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_maps.route('/delete/<int:map_id>', methods=['POST'])
def delete_map(map_id):
    """Elimina un plano y desvincula los activos."""
    try:
        with get_db_connection() as conn:
            conn.execute("UPDATE pcs SET map_id = NULL, x_pos = 0, y_pos = 0 WHERE map_id = %s", (map_id,))
            conn.execute("UPDATE network_printers SET map_id = NULL, x_pos = 0, y_pos = 0 WHERE map_id = %s", (map_id,))
            map_data = conn.execute("SELECT image_url FROM infrastructure_maps WHERE id = %s", (map_id,)).fetchone()
            if map_data:
                filename = map_data['image_url'].split('/')[-1]
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
            conn.execute("DELETE FROM infrastructure_maps WHERE id = %s", (map_id,))
            conn.commit()
        flash("Plano eliminado exitosamente.", "success")
    except Exception as e:
        flash(f"Error al eliminar plano: {str(e)}", "error")
    return redirect(url_for('maps.index'))


