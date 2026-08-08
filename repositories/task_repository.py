from database.db_core import get_db_connection
import logging

logger = logging.getLogger(__name__)

class TaskRepository:
    """
    Repositorio desacoplado para gestionar la persisicencia de la tabla 'tasks'.
    """

    @staticmethod
    def get_task_by_id(task_id: int) -> dict:
        """Obtiene una tarea por su ID."""
        try:
            with get_db_connection() as conn:
                return conn.execute("SELECT * FROM tasks WHERE id = %s", (task_id,)).fetchone()
        except Exception as e:
            logger.error(f"Error en TaskRepository.get_task_by_id({task_id}): {e}")
            return None

    @staticmethod
    def get_tasks_by_status(status: str, limit: int = 100) -> list:
        """Obtiene una lista de tareas filtradas por estado."""
        try:
            with get_db_connection() as conn:
                return conn.execute(
                    "SELECT * FROM tasks WHERE estado = %s ORDER BY id DESC LIMIT %s",
                    (status, limit)
                ).fetchall() or []
        except Exception as e:
            logger.error(f"Error en TaskRepository.get_tasks_by_status({status}): {e}")
            return []

    @staticmethod
    def update_task_status(task_id: int, new_status: str, solucion: str = None) -> bool:
        """Actualiza el estado y opcionalmente la solución de una tarea."""
        try:
            with get_db_connection() as conn:
                if solucion is not None:
                    res = conn.execute(
                        "UPDATE tasks SET estado = %s, solucion = %s WHERE id = %s",
                        (new_status, solucion, task_id)
                    )
                else:
                    res = conn.execute(
                        "UPDATE tasks SET estado = %s WHERE id = %s",
                        (new_status, task_id)
                    )
                conn.commit()
                return res.rowcount > 0
        except Exception as e:
            logger.error(f"Error en TaskRepository.update_task_status({task_id}): {e}")
            return False
