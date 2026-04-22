ALERTA_ALIASES = {
    "sinimp": "sin_impresora_alerta",
    "sin_impresora": "sin_impresora_inventario",
}

ALLOWED_SORT_COLUMNS = {
    "pc_name": "p.pc_name",
    "last_user": "p.last_user",
    "fuero": "p.fuero",
    "motherboard_model": "p.motherboard_model",
    "os_name": "p.os_name",
    "processor": "p.processor",
    "ram_gb": "p.ram_gb",
    "ram_detalles": "p.ram_detalles",
    "disk_models": "p.disk_models",
    "printer_model": "p.printer_model",
    "monitors": "p.monitors",
    "ip_address": "p.ip_address",
}

CANONICAL_ALERTA_VALUES = {
    "",
    "ram",
    "sin_impresora_alerta",
    "sin_impresora_inventario",
    "red",
    "critica",
    "media",
    "ninguna",
}


def normalize_alerta(value):
    cleaned = (value or "").strip()
    return ALERTA_ALIASES.get(cleaned, cleaned)


def sanitize_sort_column(sort_by):
    return ALLOWED_SORT_COLUMNS.get((sort_by or "").strip(), "p.pc_name")


def sanitize_sort_direction(order):
    return "DESC" if (order or "").strip().lower() == "desc" else "ASC"
