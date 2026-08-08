from database.db_core import get_db_connection

class PcRepository:
    """
    Repositorio para gestionar el acceso a datos de la tabla 'pcs'.
    """

    @staticmethod
    def get_pc_by_name(pc_name: str) -> dict:
        """Obtiene un PC por su nombre (PRIMARY KEY)."""
        with get_db_connection() as conn:
            return conn.execute("SELECT * FROM pcs WHERE pc_name = %s", (pc_name,)).fetchone()

    @staticmethod
    def get_pc_by_name_or_ip(pc_ref: str) -> dict:
        """Busca una PC por nombre o dirección IP."""
        with get_db_connection() as conn:
            return conn.execute(
                "SELECT * FROM pcs WHERE pc_name = %s OR ip_address = %s LIMIT 1", 
                (pc_ref, pc_ref)
            ).fetchone()

    @staticmethod
    def get_all_active_pcs() -> list:
        """Obtiene una lista de todos los PCs activos."""
        with get_db_connection() as conn:
            return conn.execute("SELECT * FROM pcs WHERE is_active = 1").fetchall()

    @staticmethod
    def delete_pc(pc_name: str) -> bool:
        """Borra lógicamente un PC marcándolo como inactivo."""
        with get_db_connection() as conn:
            res = conn.execute("UPDATE pcs SET is_active = 0 WHERE pc_name = %s", (pc_name,))
            conn.commit()
            return res.rowcount > 0

    @staticmethod
    def reactivate_pc(pc_name: str) -> bool:
        """Reactiva un PC marcándolo como activo."""
        with get_db_connection() as conn:
            res = conn.execute("UPDATE pcs SET is_active = 1 WHERE pc_name = %s", (pc_name,))
            conn.commit()
            return res.rowcount > 0
