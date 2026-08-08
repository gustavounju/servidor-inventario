from database.db_core import get_db_connection
import logging

logger = logging.getLogger(__name__)

class UserRepository:
    """
    Repositorio desacoplado para gestionar el acceso a datos de la tabla 'app_users'.
    """

    @staticmethod
    def get_user_by_username(username: str) -> dict:
        """Obtiene los datos de un usuario por su nombre de usuario (LOWER case)."""
        if not username:
            return None
        try:
            with get_db_connection() as conn:
                return conn.execute(
                    "SELECT * FROM app_users WHERE LOWER(username) = LOWER(%s) LIMIT 1",
                    (username.strip(),)
                ).fetchone()
        except Exception as e:
            logger.error(f"Error en UserRepository.get_user_by_username({username}): {e}")
            return None

    @staticmethod
    def get_all_users() -> list:
        """Obtiene la lista de todos los usuarios registrados."""
        try:
            with get_db_connection() as conn:
                return conn.execute(
                    "SELECT id, username, display_name, role, can_manage_stock, created_at FROM app_users ORDER BY username ASC"
                ).fetchall() or []
        except Exception as e:
            logger.error(f"Error en UserRepository.get_all_users(): {e}")
            return []

    @staticmethod
    def update_user_role(username: str, new_role: str) -> bool:
        """Actualiza el rol de un usuario."""
        try:
            with get_db_connection() as conn:
                res = conn.execute(
                    "UPDATE app_users SET role = %s WHERE LOWER(username) = LOWER(%s)",
                    (new_role, username.strip())
                )
                conn.commit()
                return res.rowcount > 0
        except Exception as e:
            logger.error(f"Error en UserRepository.update_user_role({username}): {e}")
            return False

    @staticmethod
    def delete_user(username: str) -> bool:
        """Elimina un usuario por su username."""
        try:
            with get_db_connection() as conn:
                res = conn.execute(
                    "DELETE FROM app_users WHERE LOWER(username) = LOWER(%s)",
                    (username.strip(),)
                )
                conn.commit()
                return res.rowcount > 0
        except Exception as e:
            logger.error(f"Error en UserRepository.delete_user({username}): {e}")
            return False
