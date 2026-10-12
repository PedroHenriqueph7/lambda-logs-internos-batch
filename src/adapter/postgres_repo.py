import logging
from typing import Sequence

from psycopg2 import pool
from psycopg2.extras import execute_values

from config import DatabaseSettings


logger = logging.getLogger(__name__)


INSERT_QUERY = """
    INSERT INTO tb_execution_logs
    (created_at, correlation_id, module, log_level, logger_name, message, stack_trace)
    VALUES %s
"""


class ExecutionLogRepository:
    
    def __init__(self, settings: DatabaseSettings):
        self._settings = settings
        self._pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            host=settings.host,
            port=settings.port,
            dbname=settings.name,
            user=settings.user,
            password=settings.password,
            connect_timeout=settings.connect_timeout,
            sslmode=settings.sslmode,
        )

    def _get_connection(self):
        conn = self._pool.getconn()
        if conn.closed:
            self._pool.putconn(conn, close=True)
            conn = self._pool.getconn()
        return conn

    def bulk_insert(self, rows: Sequence[tuple]) -> int:
        """Insere as linhas em uma única transação. Ordem: created_at, correlation_id,
        module, log_level, logger_name, message, stack_trace."""
        if not rows:
            return 0

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                execute_values(cur, INSERT_QUERY, rows)
            conn.commit()
            return len(rows)
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.exception("Falha no bulk insert; rollback executado")
            raise
        finally:
            self._pool.putconn(conn, close=bool(conn.closed))
