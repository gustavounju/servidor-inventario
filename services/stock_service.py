from repositories.stock_repository import StockRepository
from services.audit_service import AuditService
import logging

logger = logging.getLogger(__name__)

class StockService:
    """
    Servicio para orquestar la lógica de negocio del módulo de Stock (asignaciones, bajas, reemplazos).
    """

    @staticmethod
    def assign_component(comp_id: int, target_user_or_pc: str, actor_user: str) -> tuple[bool, str]:
        """Asigna un componente del stock a un usuario o PC."""
        comp = StockRepository.get_component_by_id(comp_id)
        if not comp:
            return False, "Componente no encontrado."

        old_status = comp.get('status', 'Desconocido')
        success = StockRepository.update_component_status(comp_id, 'Asignado', target_user_or_pc)
        if success:
            AuditService.log_action(
                pc_name=f"STOCK:{comp_id}",
                field="Asignación",
                old_value=f"Estado: {old_status}",
                new_value=f"Asignado a {target_user_or_pc}",
                user_name=actor_user,
                action_type="STOCK_ASSIGNMENT"
            )
            return True, f"Componente ID {comp_id} asignado exitosamente a {target_user_or_pc}."
        return False, "Error al actualizar la base de datos."

    @staticmethod
    def replace_failed_component(faulty_comp_id: int, replacement_comp_id: int, target_pc: str, actor_user: str) -> tuple[bool, str]:
        """
        Realiza la sustitución atómica de un componente fallado por un repuesto del stock.
        """
        faulty = StockRepository.get_component_by_id(faulty_comp_id)
        replacement = StockRepository.get_component_by_id(replacement_comp_id)

        if not faulty or not replacement:
            return False, "Uno o ambos componentes especificados no existen."

        # 1. Dar de baja el fallado
        decommission_ok = StockRepository.decommission_component(faulty_comp_id, f"Sustituido por {replacement_comp_id}")
        if not decommission_ok:
            return False, "Fallo al dar de baja el componente averiado."

        # 2. Asignar el repuesto
        assign_ok = StockRepository.update_component_status(replacement_comp_id, 'Asignado', target_pc)
        if not assign_ok:
            return False, "Fallo al asignar el nuevo componente de repuesto."

        AuditService.log_action(
            pc_name=target_pc,
            field="Sustitución por Falla",
            old_value=f"Componente Retirado: ID {faulty_comp_id}",
            new_value=f"Nuevo Componente: ID {replacement_comp_id}",
            user_name=actor_user,
            action_type="STOCK_REPLACEMENT"
        )
        return True, f"Sustitución completada. Componente {faulty_comp_id} retirado y {replacement_comp_id} instalado en {target_pc}."
