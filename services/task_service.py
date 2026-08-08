from repositories.task_repository import TaskRepository
from services.audit_service import AuditService
import logging

logger = logging.getLogger(__name__)

class TaskService:
    """
    Servicio de capa de negocio para la gestión de tareas del Centro Judicial.
    """

    @staticmethod
    def resolve_task(task_id: int, solucion: str, actor_user: str) -> tuple[bool, str]:
        """Marca una tarea como hecha/resuelta guardando la solución."""
        task = TaskRepository.get_task_by_id(task_id)
        if not task:
            return False, "La tarea especificada no existe."

        old_status = task.get('estado', 'pendiente')
        success = TaskRepository.update_task_status(task_id, 'hecha', solucion)
        if success:
            AuditService.log_action(
                pc_name=f"TASK:{task_id}",
                field="Estado Tarea",
                old_value=old_status,
                new_value="hecha",
                user_name=actor_user,
                action_type="TASK_RESOLVE"
            )
            return True, f"Tarea #{task_id} marcada como realizada."
        return False, "Error al actualizar la tarea."
