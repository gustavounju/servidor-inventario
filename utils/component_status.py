STATUS_STOCK = "Stock"
STATUS_RESERVED = "Reservado"
STATUS_INSTALLED = "Installed"
STATUS_RETIRED = "Retirado"
STATUS_REPAIR = "En Reparacion"

LIFECYCLE_STOCK = "stock"
LIFECYCLE_IN_ASSEMBLY = "en_armado"
LIFECYCLE_DEPLOYED = "desplegado"
LIFECYCLE_REPAIR = "en_reparacion"
LIFECYCLE_RETIRED = "retirado"
LIFECYCLE_SCRAP = "scrap"


def stock_component_state() -> tuple[str, str]:
    return STATUS_STOCK, LIFECYCLE_STOCK


def reserved_component_state() -> tuple[str, str]:
    return STATUS_RESERVED, LIFECYCLE_IN_ASSEMBLY


def deployed_component_state() -> tuple[str, str]:
    return STATUS_INSTALLED, LIFECYCLE_DEPLOYED


def retired_component_state(*, scrap=False) -> tuple[str, str]:
    return STATUS_RETIRED, (LIFECYCLE_SCRAP if scrap else LIFECYCLE_RETIRED)


def repair_component_state() -> tuple[str, str]:
    return STATUS_REPAIR, LIFECYCLE_REPAIR


def assignment_component_state(
    *,
    assigned_pc=None,
    assigned_user=None,
    assigned_fuero=None,
    assigned_to_component_id=None,
    build_order_id=None,
) -> tuple[str, str]:
    if assigned_pc or assigned_user or assigned_fuero or assigned_to_component_id:
        return deployed_component_state()
    if build_order_id:
        return reserved_component_state()
    return stock_component_state()
