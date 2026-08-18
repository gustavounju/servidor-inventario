from database.db_core import get_db_connection
import logging
from utils.component_status import assignment_component_state, retired_component_state

logger = logging.getLogger(__name__)

class StockRepository:
    """
    Repositorio para gestionar la persistencia de componentes, remitos y stock.
    """

    @staticmethod
    def get_component_by_id(comp_id: int) -> dict:
        """Obtiene un componente por su ID primario."""
        with get_db_connection() as conn:
            return conn.execute("SELECT * FROM components WHERE id = %s", (comp_id,)).fetchone()

    @staticmethod
    def update_component_status(comp_id: int, new_status: str, assigned_to: str = None) -> bool:
        """Actualiza el estado y asignación de un componente."""
        with get_db_connection() as conn:
            lifecycle_status = assignment_component_state(
                assigned_user=assigned_to if assigned_to is not None else None
            )[1]
            if assigned_to is not None:
                res = conn.execute(
                    "UPDATE components SET status = %s, lifecycle_status = %s, assigned_user = %s WHERE id = %s",
                    (new_status, lifecycle_status, assigned_to, comp_id)
                )
            else:
                res = conn.execute(
                    "UPDATE components SET status = %s, lifecycle_status = %s WHERE id = %s",
                    (new_status, lifecycle_status, comp_id)
                )
            conn.commit()
            return res.rowcount > 0

    @staticmethod
    def decommission_component(comp_id: int, reason: str = "Baja por Falla") -> bool:
        """Da de baja un componente a estado 'Retirado'."""
        with get_db_connection() as conn:
            status, lifecycle_status = retired_component_state()
            res = conn.execute(
                "UPDATE components SET status = %s, lifecycle_status = %s WHERE id = %s",
                (status, lifecycle_status, comp_id)
            )
            conn.commit()
            return res.rowcount > 0
