import pymysql
import pymysql.cursors
import os
import logging
from dotenv import load_dotenv
from utils.constants import DEFAULT_FUERO_MAPPING
try:
    from dbutils.pooled_db import PooledDB
except ImportError:
    from DBUtils.PooledDB import PooledDB

load_dotenv()


class DBConnectionWrapper:
    def __init__(self, conn):
        self.conn = conn
        self._cursor = None

    def execute(self, query, vars=None):
        if self._cursor is not None:
            try:
                self._cursor.close()
            except Exception:
                pass
        self._cursor = self.conn.cursor()
        self._cursor.execute(query, vars)
        return self._cursor

    @property
    def cursor(self):
        """Acceso directo al último cursor (para lastrowid, rowcount, etc.)."""
        return self._cursor

    def fetchone(self):
        return self._cursor.fetchone() if self._cursor else None

    def fetchall(self):
        return self._cursor.fetchall() if self._cursor else []

    def commit(self):
        self.conn.commit()
        try:
            from servidor import invalidate_global_cache
            invalidate_global_cache()
        except ImportError:
            pass

    def rollback(self):
        self.conn.rollback()

    def close(self):
        if self._cursor is not None:
            try:
                self._cursor.close()
            except Exception:
                pass
        try:
            self.conn.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.close()


_DB_POOL = None

def _get_pool():
    global _DB_POOL
    if _DB_POOL is not None:
        return _DB_POOL
    host = os.environ.get("DB_HOST", "127.0.0.1")
    user = os.environ.get("DB_USER", "root")
    password = os.environ.get("DB_PASS", "")
    dbname = os.environ.get("DB_NAME", "inventario_dev")
    port = int(os.environ.get("DB_PORT", "3306"))
    session_time_zone = os.environ.get("DB_TIME_ZONE", "-03:00")

    _DB_POOL = PooledDB(
        creator=pymysql,
        mincached=2,
        maxcached=10,
        maxconnections=20,
        blocking=True,
        host=host,
        user=user,
        password=password,
        database=dbname,
        port=port,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        connect_timeout=10,
        init_command=f"SET time_zone = '{session_time_zone}'"
    )
    return _DB_POOL

def get_db_connection():
    """Obtiene una conexión del pool. Siempre usar con 'with': with get_db_connection() as conn."""
    conn = _get_pool().connection()
    return DBConnectionWrapper(conn)


def init_db():
    print("Inicializando base de datos MySQL mediante migraciones versionadas...")
    try:
        from database.migrator import run_migrations
        run_migrations()
        print("Base de datos lista y estructura verificada (Migraciones exitosas).")
    except Exception as e:
        print(f"Error crítico inicializando base de datos: {e}")
        logging.error(f"Error inicializando base de datos con migrator: {e}")

