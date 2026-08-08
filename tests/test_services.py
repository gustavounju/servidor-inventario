import os
import tempfile
import unittest
from services.vault_service import VaultService
from services.stock_service import StockService
from services.task_service import TaskService
from database.db_core import get_db_connection

class TestServicesLayer(unittest.TestCase):

    def test_vault_service_file_operations(self):
        """Verifica las operaciones del VaultService (cálculo de tamaño y eliminación de archivos)."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = os.path.join(tmp_dir, "test.txt")
            with open(test_file, "w") as f:
                f.write("A" * 1000)

            size = VaultService.calculate_folder_size(tmp_dir)
            self.assertGreaterEqual(size, 1000)

            ok, msg = VaultService.delete_file(tmp_dir, "test.txt", "TEST_USER")
            self.assertTrue(ok)
            self.assertFalse(os.path.exists(test_file))

    def test_stock_service_replacement(self):
        """Verifica la sustitución atómica de componentes en StockService."""
        with get_db_connection() as conn:
            res1 = conn.execute("INSERT INTO components (serial_number, component_type, status) VALUES ('SN_FAULTY_99', 'RAM', 'Asignado') ON DUPLICATE KEY UPDATE status='Asignado'")
            res2 = conn.execute("INSERT INTO components (serial_number, component_type, status) VALUES ('SN_REPLACEMENT_99', 'RAM', 'Stock') ON DUPLICATE KEY UPDATE status='Stock'")
            conn.commit()
            faulty_comp = conn.execute("SELECT id FROM components WHERE serial_number='SN_FAULTY_99'").fetchone()
            replacement_comp = conn.execute("SELECT id FROM components WHERE serial_number='SN_REPLACEMENT_99'").fetchone()
            faulty_id = faulty_comp['id']
            replacement_id = replacement_comp['id']

        ok, msg = StockService.replace_failed_component(faulty_id, replacement_id, "PC_TEST_DESTINO", "TEST_TECH")
        self.assertTrue(ok, f"Error devuelto por StockService: {msg}")

        with get_db_connection() as conn:
            c1 = conn.execute("SELECT status FROM components WHERE id = %s", (faulty_id,)).fetchone()
            c2 = conn.execute("SELECT status, assigned_user FROM components WHERE id = %s", (replacement_id,)).fetchone()
            self.assertEqual(c1['status'], 'Retirado')
            self.assertEqual(c2['status'], 'Asignado')
            self.assertEqual(c2['assigned_user'], 'PC_TEST_DESTINO')

    def test_task_service_resolve(self):
        """Verifica la resolución de tareas en TaskService."""
        with get_db_connection() as conn:
            res = conn.execute("INSERT INTO tasks (solicitante, descripcion, estado) VALUES ('USER_X', 'Desc', 'pendiente')")
            conn.commit()
            task_id = res.lastrowid

        ok, msg = TaskService.resolve_task(task_id, "Problema resuelto con cambio de cable", "TECH_Y")
        self.assertTrue(ok)

        with get_db_connection() as conn:
            t = conn.execute("SELECT estado, solucion FROM tasks WHERE id = %s", (task_id,)).fetchone()
            self.assertEqual(t['estado'], 'hecha')
            self.assertEqual(t['solucion'], 'Problema resuelto con cambio de cable')

if __name__ == '__main__':
    unittest.main()
