"""
asset_validation.py — Servicio de validación del Gemelo Digital Patrimonial.

Lógica central del Sistema Patrimonial:
  - Dado un pc_name, determina si la PC reportada por el script .ps1
    tiene un activo registrado en components y si el hardware coincide.

Valores de validation_status:
  'sin_gemelo'   → El script reportó esta PC pero no hay componente CPU asignado.
  'pendiente'    → Se asignó un CPU (Build Order o asignación directa) pero el script
                   no ha reportado desde esa asignación (last_report vacío o None).
  'validado'     → El hardware reportado coincide con el activo registrado.
  'discrepancia' → El hardware cambió respecto al activo registrado (posible
                   reemplazo sin documentar).

Este módulo NO modifica la tabla pcs; solo calcula el estado.
La escritura la hace el caller (bp_api.py → process_inventory_data).
"""

import logging
import re

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers de normalización (locales para evitar importar bp_api)
# ─────────────────────────────────────────────────────────────────────────────

def _normalize_hw_token(value: str) -> str:
    """Limpia un string de hardware para comparación tolerante a cambios menores."""
    if not value:
        return ""
    v = value.strip().upper()
    # Eliminar sufijos de velocidad / revisiones que no identifican el modelo
    v = re.sub(r"\s*@\s*[\d.]+\s*GHZ", "", v)
    v = re.sub(r"\s+REV\s*[\d.]+", "", v)
    v = re.sub(r"\s+", " ", v)
    return v.strip()


def _hw_tokens_match(a: str, b: str) -> bool:
    """Compara dos strings de hardware normalizados."""
    na, nb = _normalize_hw_token(a), _normalize_hw_token(b)
    if not na or not nb:
        return False
    # Coincidencia exacta o una como substring de la otra (cubre modelos abreviados)
    return na == nb or na in nb or nb in na


# ─────────────────────────────────────────────────────────────────────────────
# Función principal
# ─────────────────────────────────────────────────────────────────────────────

def compute_validation_status(pc_name: str, conn) -> str:
    """
    Calcula el validation_status de una PC dado su nombre y una conexión activa.

    Se llama al final de process_inventory_data() en bp_api.py, con la misma
    conexión abierta del UPSERT, para garantizar que los datos ya están escritos.

    Parámetros:
        pc_name : Nombre de la PC (clave primaria en pcs).
        conn    : Conexión activa (DBConnectionWrapper) — ya dentro de un contexto with.

    Retorna:
        str : 'sin_gemelo' | 'pendiente' | 'validado' | 'discrepancia'
    """
    try:
        # 1. ¿Hay algún activo de tipo CPU asignado a esta PC?
        #    Filtra por lifecycle_status (Fase 3) con fallback a status original
        #    para compatibilidad con instalaciones que aún no corrieron V52.
        cpu_asset = conn.execute(
            """
            SELECT brand_model, serial_number
            FROM components
            WHERE LOWER(TRIM(assigned_pc)) = LOWER(TRIM(%s))
              AND LOWER(TRIM(component_type)) IN ('cpu', 'gabinete', 'computadora', 'pc')
              AND status NOT IN ('Retirado', 'Scrap')
              AND (lifecycle_status IS NULL OR lifecycle_status NOT IN ('retirado', 'scrap'))
            LIMIT 1
            """,
            (pc_name,)
        ).fetchone()

        if not cpu_asset:
            # Sin activo patrimonial asignado → todavía no tiene gemelo
            return "sin_gemelo"

        # 2. ¿La PC ya reportó desde el script?
        pc_data = conn.execute(
            "SELECT processor, motherboard_model, ram_gb, disk_models, last_report, telemetry_snapshot, full_json_data FROM pcs WHERE pc_name = %s",
            (pc_name,)
        ).fetchone()

        if not pc_data or not pc_data.get("last_report"):
            # Activo asignado pero el script no corrió aún
            return "pendiente"

        # 3. Obtener telemetría del script desde telemetry_snapshot o full_json_data
        telemetry_raw = pc_data.get("telemetry_snapshot") or pc_data.get("full_json_data")
        script_processor = pc_data.get("processor") or ""
        script_motherboard = pc_data.get("motherboard_model") or ""
        script_ram = pc_data.get("ram_gb") or 0.0
        script_disks = pc_data.get("disk_models") or ""

        if telemetry_raw:
            try:
                import json
                t_data = json.loads(telemetry_raw)
                sistema = t_data.get("Sistema", {})
                script_processor = sistema.get("Procesador") or script_processor
                script_ram = sistema.get("RAM (GB)") or script_ram
                script_disks = t_data.get("Disk_Models") or script_disks
                script_motherboard = t_data.get("Motherboard_Model") or script_motherboard
            except Exception:
                pass

        asset_model = cpu_asset.get("brand_model") or ""

        # Si el modelo del activo coincide con procesador O motherboard reportados,
        # consideramos que el hardware de CPU es compatible.
        processor_match = _hw_tokens_match(asset_model, script_processor)
        motherboard_match = _hw_tokens_match(asset_model, script_motherboard)

        # Si ninguno coincide pero el activo existe y hay telemetría limpia
        if not (processor_match or motherboard_match):
            if (script_processor and script_processor not in ("N/A", "") and
                    script_motherboard and script_motherboard not in ("N/A", "")):
                return "discrepancia"

        # 4. Verificar RAM registrada vs telemetría si existe registro previo
        reg_ram = pc_data.get("ram_gb")
        if reg_ram and reg_ram > 0 and script_ram and float(script_ram) > 0:
            try:
                diff = abs(float(reg_ram) - float(script_ram))
                # Si la diferencia de RAM es superior a 1 GB sin intervención registrada
                if diff > 1.0:
                    return "discrepancia"
            except Exception:
                pass

        return "validado"

    except Exception as exc:
        logger.warning(
            "compute_validation_status(%s): error calculando estado — %s",
            pc_name, exc
        )
        return "sin_gemelo"


# ─────────────────────────────────────────────────────────────────────────────
# Bulk recalculation (para usar desde panel de administración)
# ─────────────────────────────────────────────────────────────────────────────

def recalculate_all_validation_statuses() -> dict:
    """
    Recalcula el validation_status de TODAS las PCs activas.
    Se puede llamar desde un endpoint de administración para una pasada inicial
    después de la migración V49.

    Retorna un dict con conteos por estado para mostrar en la respuesta.
    """
    from database.db_core import get_db_connection

    counts = {"sin_gemelo": 0, "pendiente": 0, "validado": 0, "discrepancia": 0, "error": 0}

    try:
        with get_db_connection() as conn:
            pcs = conn.execute(
                "SELECT pc_name FROM pcs WHERE is_active = 1"
            ).fetchall()

            for row in pcs:
                pc_name = row["pc_name"]
                status = compute_validation_status(pc_name, conn)
                try:
                    conn.execute(
                        "UPDATE pcs SET validation_status = %s WHERE pc_name = %s",
                        (status, pc_name)
                    )
                    counts[status] = counts.get(status, 0) + 1
                except Exception as upd_exc:
                    logger.warning("Error actualizando validation_status para %s: %s", pc_name, upd_exc)
                    counts["error"] += 1

    except Exception as exc:
        logger.error("recalculate_all_validation_statuses: error general — %s", exc)

    logger.info("Recálculo validation_status completado: %s", counts)
    return counts


def get_pc_validation_comparison(pc_name: str, conn=None):
    """
    Construye una comparativa estructurada entre el Armado Patrimonial (componentes asignados)
    y la Telemetría Real reportada por el script .ps1.
    """
    close_conn = False
    if conn is None:
        from database.db_core import get_db_connection
        conn_ctx = get_db_connection()
        conn = conn_ctx.__enter__()
        close_conn = True

    try:
        pc = conn.execute("SELECT * FROM pcs WHERE pc_name = %s", (pc_name,)).fetchone()
        if not pc:
            return []

        comps = conn.execute(
            "SELECT serial_number, component_type, brand_model FROM components WHERE LOWER(TRIM(assigned_pc)) = LOWER(TRIM(%s)) AND status NOT IN ('Retirado', 'Scrap')",
            (pc_name,)
        ).fetchall()

        telemetry_raw = pc.get("telemetry_snapshot") or pc.get("full_json_data")
        script_data = {}
        if telemetry_raw:
            try:
                import json
                script_data = json.loads(telemetry_raw)
            except Exception:
                pass

        sistema = script_data.get("Sistema", {})
        script_proc = sistema.get("Procesador") or pc.get("processor") or "Sin reporte de script"
        script_ram = str(sistema.get("RAM (GB)") or pc.get("ram_gb") or "Sin reporte")
        script_mb = script_data.get("Motherboard_Model") or pc.get("motherboard_model") or "Sin reporte de script"
        script_disk = script_data.get("Disk_Models") or pc.get("disk_models") or "Sin reporte de script"

        comp_by_type = {}
        for c in comps:
            ctype = (c.get("component_type") or "Otro").strip().title()
            comp_by_type.setdefault(ctype, []).append(c)

        comparison = []

        # 1. Motherboard
        mb_comps = comp_by_type.get("Motherboard", [])
        reg_mb = ", ".join(f"{c['brand_model']} ({c['serial_number']})" for c in mb_comps) if mb_comps else "Sin registro de Placa"
        mb_match = _hw_tokens_match(reg_mb, script_mb) if mb_comps else True
        comparison.append({
            "component": "Motherboard",
            "registered": reg_mb,
            "telemetry": script_mb,
            "match": mb_match,
            "status_label": "Coincide OK" if mb_match else "Diferencia de Placa Madre"
        })

        # 2. Procesador
        cpu_comps = comp_by_type.get("Cpu", []) or comp_by_type.get("Gabinete", []) or comp_by_type.get("Pc", [])
        reg_cpu = ", ".join(f"{c['brand_model']} ({c['serial_number']})" for c in cpu_comps) if cpu_comps else "Sin registro CPU"
        proc_match = _hw_tokens_match(reg_cpu, script_proc) if cpu_comps else True
        comparison.append({
            "component": "Procesador (CPU)",
            "registered": reg_cpu,
            "telemetry": script_proc,
            "match": proc_match,
            "status_label": "Coincide OK" if proc_match else "Diferencia de Procesador"
        })

        # 3. Memoria RAM
        ram_comps = comp_by_type.get("Memoria Ram", []) or comp_by_type.get("Ram", [])
        reg_ram = ", ".join(f"{c['brand_model']} ({c['serial_number']})" for c in ram_comps) if ram_comps else "Sin registro RAM"
        ram_match = _hw_tokens_match(reg_ram, script_ram) if (ram_comps and script_ram != "Sin reporte") else True
        comparison.append({
            "component": "Memoria RAM",
            "registered": reg_ram,
            "telemetry": f"{script_ram} GB" if script_ram != "Sin reporte" else "Sin reporte",
            "match": ram_match,
            "status_label": "Coincide OK" if ram_match else "Diferencia de Capacidad RAM"
        })

        # 4. Almacenamiento (Disco)
        disk_comps = comp_by_type.get("Disco Rígido", []) or comp_by_type.get("Disco", [])
        reg_disk = ", ".join(f"{c['brand_model']} ({c['serial_number']})" for c in disk_comps) if disk_comps else "Sin registro Disco"
        disk_match = _hw_tokens_match(reg_disk, script_disk) if (disk_comps and script_disk != "Sin reporte de script") else True
        comparison.append({
            "component": "Almacenamiento (Disco)",
            "registered": reg_disk,
            "telemetry": script_disk,
            "match": disk_match,
            "status_label": "Coincide OK" if disk_match else "Diferencia de Disco"
        })

        return comparison
    finally:
        if close_conn:
            conn_ctx.__exit__(None, None, None)
