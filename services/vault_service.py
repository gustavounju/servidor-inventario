import os
from werkzeug.utils import secure_filename
from services.audit_service import AuditService
import logging

logger = logging.getLogger(__name__)

DEFAULT_LIMIT_MB = 1000

class VaultService:
    """
    Servicio para orquestar las operaciones del Vault (gestión de archivos y cuotas).
    """

    @staticmethod
    def calculate_folder_size(directory_path: str) -> int:
        """Calcula el tamaño total en bytes de un directorio."""
        total_size = 0
        if not os.path.exists(directory_path):
            return 0
        for dirpath, dirnames, filenames in os.walk(directory_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.isfile(fp):
                    total_size += os.path.getsize(fp)
        return total_size

    @staticmethod
    def save_file(vault_path: str, file_obj, current_limit_mb: int, user_name: str) -> tuple[bool, str]:
        """
        Guarda un archivo en el Vault verificando que no exceda el límite de espacio.
        Retorna (exito: bool, mensaje: str).
        """
        if not file_obj or not file_obj.filename:
            return False, "Archivo no proporcionado o sin nombre."

        safe_filename = secure_filename(file_obj.filename)
        if not safe_filename:
            return False, "Nombre de archivo inválido."

        os.makedirs(vault_path, exist_ok=True)
        file_path = os.path.join(vault_path, safe_filename)
        file_obj.save(file_path)

        limit_bytes = current_limit_mb * 1024 * 1024
        if VaultService.calculate_folder_size(vault_path) > limit_bytes:
            if os.path.exists(file_path):
                os.remove(file_path)
            return False, "El archivo excede el límite de espacio disponible."

        AuditService.log_security_event(
            event_name="VAULT_UPLOAD",
            details=f"Archivo subido al Vault: {safe_filename}",
            user_name=user_name
        )
        return True, f"Archivo '{safe_filename}' subido correctamente."

    @staticmethod
    def delete_file(vault_path: str, filename: str, user_name: str) -> tuple[bool, str]:
        """
        Elimina de manera segura un archivo del Vault.
        """
        safe_filename = secure_filename(filename)
        file_path = os.path.join(vault_path, safe_filename)

        if os.path.exists(file_path) and os.path.isfile(file_path):
            os.remove(file_path)
            AuditService.log_security_event(
                event_name="VAULT_DELETE",
                details=f"Archivo eliminado del Vault: {safe_filename}",
                user_name=user_name
            )
            return True, f"Archivo '{safe_filename}' eliminado."
        return False, "El archivo especificado no existe."
