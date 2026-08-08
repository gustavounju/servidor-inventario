from database.db_core import get_db_connection
import logging

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
            if assigned_to is not None:
                res = conn.execute(
                    "UPDATE components SET status = %s, assigned_user = %s WHERE id = %s",
                    (new_status, assigned_to, comp_id)
                )
            else:
                res = conn.execute(
                    "UPDATE components SET status = %s WHERE id = %s",
                    (new_status, comp_id)
                )
            conn.commit()
            return res.rowcount > 0

    @staticmethod
    def decommission_component(comp_id: int, reason: str = "Baja por Falla") -> bool:
        """Da de baja un componente a estado 'Retirado'."""
        with get_db_connection() as conn:
            res = conn.execute(
                "UPDATE components SET status = 'Retirado' WHERE id = %s",
                (comp_id,)
            )
            conn.commit()
            return res.rowcount > 0
