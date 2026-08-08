import os
import tempfile
import unittest
import gzip
from services.audit_service import AuditService
from scripts.backup_db import verify_backup_integrity
from database.db_core import get_db_connection

class TestPhase4Observability(unittest.TestCase):

    def test_audit_service_log_action_and_query(self):
        """Verifica que AuditService.log_action inserte un registro en audit_logs y que get_recent_logs lo recupere."""
        success = AuditService.log_action(
            pc_name="TEST_PC_PHASE4",
            field="ESTADO",
            old_value="OPERATIVO",
            new_value="REPARACION",
            user_name="TECNICO_TEST",
            action_type="UPDATE_TEST"
        )
        self.assertTrue(success, "AuditService.log_action debería devolver True al insertar correctamente")

        logs = AuditService.get_recent_logs(limit=10)
        self.assertIsInstance(logs, list)
        
        # Buscar la entrada recién insertada
        inserted = None
        for log in logs:
            if isinstance(log, dict):
                pc = log.get('pc_name')
            else:
                pc = log[1]
            if pc == "TEST_PC_PHASE4":
                inserted = log
                break
                
        self.assertIsNotNone(inserted, "Debería encontrar la entrada auditada para TEST_PC_PHASE4")

    def test_audit_service_log_security_event(self):
        """Verifica que AuditService.log_security_event registre eventos globales de seguridad."""
        success = AuditService.log_security_event(
            event_name="VAULT_TEST_EVENT",
            details="Intento de acceso a recurso protegido en test",
            user_name="TEST_USER"
        )
        self.assertTrue(success)

    def test_backup_integrity_valid_file(self):
        """Verifica que verify_backup_integrity acepte un archivo .sql.gz válido."""
        with tempfile.NamedTemporaryFile(suffix=".sql.gz", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            sql_content = b"-- MySQL dump 10.13\nCREATE TABLE test (id INT);\nINSERT INTO test VALUES (1);\n"
            with gzip.open(tmp_path, 'wb') as gz:
                gz.write(sql_content * 10)  # Generar suficiente contenido (> 100 bytes)
                
            self.assertTrue(verify_backup_integrity(tmp_path, min_bytes=50))
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_backup_integrity_nonexistent_file(self):
        """Verifica que verify_backup_integrity retorne False para un archivo inexistente."""
        self.assertFalse(verify_backup_integrity("/path/nonexistent/backup.sql.gz"))

    def test_backup_integrity_corrupt_file(self):
        """Verifica que verify_backup_integrity retorne False para un archivo corrupto."""
        with tempfile.NamedTemporaryFile(suffix=".sql.gz", delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(b"ESTO NO ES UN ARCHIVO GZIP VALIDO" * 10)

        try:
            self.assertFalse(verify_backup_integrity(tmp_path, min_bytes=10))
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_backup_integrity_non_sql_gzip(self):
        """Verifica que verify_backup_integrity retorne False si el gzip no contiene SQL."""
        with tempfile.NamedTemporaryFile(suffix=".sql.gz", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with gzip.open(tmp_path, 'wb') as gz:
                gz.write(b"FOOBAR HELLO WORLD RANDOM CONTENT 1234567890 BLA BLA " * 10)

            self.assertFalse(verify_backup_integrity(tmp_path, min_bytes=50))
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

if __name__ == '__main__':
    unittest.main()
