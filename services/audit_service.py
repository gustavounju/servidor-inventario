from flask import request, has_request_context
from database.db_core import get_db_connection
import logging

logger = logging.getLogger(__name__)

class AuditService:
    """
    Servicio centralizado para registrar eventos de auditoría y operaciones críticas.
    Reemplaza los inserts manuales esparcidos por el código.
    """

    @staticmethod
    def log_action(
        pc_name: str,
        field: str,
        old_value: str,
        new_value: str,
        user_name: str = 'SISTEMA',
        action_type: str = 'UPDATE',
        ip_address: str = None
    ) -> bool:
        """
        Registra una acción en la tabla audit_logs.
        """
        if ip_address:
            client_ip = ip_address
        else:
            client_ip = request.remote_addr if has_request_context() else '127.0.0.1'

        try:
            with get_db_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO audit_logs 
                    (pc_name, field, old_value, new_value, user_name, action_type, ip_address) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (pc_name, field, old_value, new_value, user_name, action_type, client_ip)
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Fallo al registrar auditoría para {pc_name} (Acción: {action_type}): {e}")
            return False

    @staticmethod
    def log_security_event(
        event_name: str,
        details: str,
        user_name: str,
        action_type: str = 'SECURITY_ALERT',
        ip_address: str = None
    ) -> bool:
        """
        Registra eventos que no están necesariamente ligados a una 'pc_name', como intentos fallidos de login o uso de Vault.
        Utiliza 'SISTEMA_GLOBAL' como pc_name para indicar que es un evento general.
        """
        return AuditService.log_action(
            pc_name='SISTEMA_GLOBAL',
            field=event_name,
            old_value='N/A',
            new_value=details,
            user_name=user_name,
            action_type=action_type,
            ip_address=ip_address
        )

    @staticmethod
    def log_user_event(
        event_name: str,
        target_user: str,
        details: str,
        actor_user: str,
        action_type: str = 'USER_MANAGEMENT',
        ip_address: str = None
    ) -> bool:
        """
        Registra eventos de gestión de usuarios (creación, edición, cambio de rol, baja).
        """
        return AuditService.log_action(
            pc_name=f"USER:{target_user}",
            field=event_name,
            old_value='N/A',
            new_value=details,
            user_name=actor_user,
            action_type=action_type,
            ip_address=ip_address
        )

    @staticmethod
    def get_recent_logs(limit: int = 50) -> list:
        """
        Obtiene los últimos N registros de auditoría ordenados por fecha descendente.
        """
        try:
            with get_db_connection() as conn:
                res = conn.execute(
                    """
                    SELECT id, pc_name, field, old_value, new_value, user_name, action_type, changed_at AS timestamp, ip_address
                    FROM audit_logs
                    ORDER BY id DESC
                    LIMIT %s
                    """,
                    (limit,)
                )
                return res.fetchall() or []
        except Exception as e:
            logger.error(f"Fallo al consultar logs de auditoría: {e}")
            return []

