import unittest
from repositories.pc_repository import PcRepository
from repositories.component_repository import ComponentRepository
from repositories.task_repository import TaskRepository
from repositories.user_repository import UserRepository
from database.db_core import get_db_connection

class TestRepositories(unittest.TestCase):

    def test_pc_repository_get_and_reactivate(self):
        """Verifica que PcRepository pueda consultar y actualizar el estado de una PC."""
        pc_name = "TEST_REPO_PC"
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO pcs (pc_name, ip_address, is_active) VALUES (%s, '10.15.99.99', 1) ON DUPLICATE KEY UPDATE is_active=1",
                (pc_name,)
            )
            conn.commit()

        pc = PcRepository.get_pc_by_name(pc_name)
        self.assertIsNotNone(pc)
        self.assertEqual(pc.get('pc_name'), pc_name)

        deleted = PcRepository.delete_pc(pc_name)
        self.assertTrue(deleted)

        reactivated = PcRepository.reactivate_pc(pc_name)
        self.assertTrue(reactivated)

    def test_component_repository(self):
        """Verifica consultas de ComponentRepository."""
        sn = "TEST_SN_12345"
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO components (serial_number, component_type, status) VALUES (%s, 'CPU', 'Stock') ON DUPLICATE KEY UPDATE status='Stock'",
                (sn,)
            )
            conn.commit()

        comp = ComponentRepository.get_component_by_serial(sn)
        self.assertIsNotNone(comp)
        self.assertEqual(comp.get('serial_number'), sn)

        stock_comps = ComponentRepository.get_components_by_status('Stock')
        self.assertIsInstance(stock_comps, list)

    def test_task_repository(self):
        """Verifica que TaskRepository gestione la tabla tasks."""
        with get_db_connection() as conn:
            res = conn.execute(
                "INSERT INTO tasks (solicitante, descripcion, estado) VALUES ('TEST_USER', 'Prueba de repositorio', 'pendiente')"
            )
            conn.commit()
            task_id = res.lastrowid

        task = TaskRepository.get_task_by_id(task_id)
        self.assertIsNotNone(task)
        self.assertEqual(task.get('estado'), 'pendiente')

        updated = TaskRepository.update_task_status(task_id, 'resuelto', 'Solución de prueba')
        self.assertTrue(updated)

        task_after = TaskRepository.get_task_by_id(task_id)
        self.assertEqual(task_after.get('estado'), 'resuelto')

    def test_user_repository(self):
        """Verifica que UserRepository gestione la tabla app_users."""
        username = "test_repo_user"
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO app_users (username, password_hash, role) VALUES (%s, 'hash', 'Técnico') ON DUPLICATE KEY UPDATE role='Técnico'",
                (username,)
            )
            conn.commit()

        user = UserRepository.get_user_by_username(username)
        self.assertIsNotNone(user)
        self.assertEqual(user.get('username'), username)

        updated = UserRepository.update_user_role(username, "Administrador")
        self.assertTrue(updated)

        users = UserRepository.get_all_users()
        self.assertIsInstance(users, list)

        deleted = UserRepository.delete_user(username)
        self.assertTrue(deleted)

if __name__ == '__main__':
    unittest.main()
