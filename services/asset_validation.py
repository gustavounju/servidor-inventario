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
        cpu_asset = conn.execute(
            """
            SELECT brand_model, serial_number
            FROM components
            WHERE LOWER(TRIM(assigned_pc)) = LOWER(TRIM(%s))
              AND LOWER(TRIM(component_type)) IN ('cpu', 'gabinete', 'computadora', 'pc')
              AND status NOT IN ('Retirado', 'Scrap')
            LIMIT 1
            """,
            (pc_name,)
        ).fetchone()

        if not cpu_asset:
            # Sin activo patrimonial asignado → todavía no tiene gemelo
            return "sin_gemelo"

        # 2. ¿La PC ya reportó desde el script?
        pc_data = conn.execute(
            "SELECT processor, motherboard_model, last_report FROM pcs WHERE pc_name = %s",
            (pc_name,)
        ).fetchone()

        if not pc_data or not pc_data.get("last_report"):
            # Activo asignado pero el script no corrió aún
            return "pendiente"

        # 3. Comparar hardware del activo vs. lo que reportó el script
        #    Usamos la misma lógica ya existente en bp_api.py:246-254
        asset_model = cpu_asset.get("brand_model") or ""
        script_processor = pc_data.get("processor") or ""
        script_motherboard = pc_data.get("motherboard_model") or ""

        # Si el modelo del activo coincide con procesador O motherboard reportados,
        # consideramos que el hardware es el mismo.
        processor_match = _hw_tokens_match(asset_model, script_processor)
        motherboard_match = _hw_tokens_match(asset_model, script_motherboard)

        # Consideramos "validado" si hay coincidencia en al menos uno de los dos campos
        # (el brand_model del activo puede ser el modelo del gabinete o del CPU indistintamente).
        if processor_match or motherboard_match:
            return "validado"

        # Si ninguno coincide pero el activo existe, puede ser una discrepancia real
        # o simplemente que el brand_model del activo es el nombre comercial del gabinete
        # y no el modelo del CPU. Para evitar falsos positivos, solo marcamos discrepancia
        # si AMBOS campos del script son no-vacíos y no-genéricos.
        if (script_processor and script_processor not in ("N/A", "") and
                script_motherboard and script_motherboard not in ("N/A", "")):
            return "discrepancia"

        # Datos de script insuficientes para comparar → considerar validado con reserva
        return "validado"

    except Exception as exc:
        logger.warning(
            "compute_validation_status(%s): error calculando estado — %s",
            pc_name, exc
        )
        # En caso de error no bloqueamos el flujo principal; retornamos estado conservador
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
