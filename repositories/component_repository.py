from database.db_core import get_db_connection

class ComponentRepository:
    """
    Repositorio para gestionar el acceso a datos de la tabla 'components' y stock.
    """

    @staticmethod
    def get_component_by_serial(serial_number: str) -> dict:
        """Obtiene un componente por su número de serie."""
        with get_db_connection() as conn:
            return conn.execute("SELECT * FROM components WHERE serial_number = %s", (serial_number,)).fetchone()

    @staticmethod
    def get_components_by_status(status: str) -> list:
        """Obtiene una lista de componentes por estado (ej: 'Stock', 'Asignado')."""
        with get_db_connection() as conn:
            return conn.execute("SELECT * FROM components WHERE status = %s", (status,)).fetchall()
