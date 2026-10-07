import logging
from typing import Sequence

import psycopg2
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

    def _connect(self):
        s = self._settings
        return psycopg2.connect(
            host=s.host,
            port=s.port,
            dbname=s.name,
            user=s.user,
            password=s.password,
            connect_timeout=s.connect_timeout,
        )

    def bulk_insert(self, rows: Sequence[tuple]) -> int:
        """Insere as linhas em uma única transação. Ordem: created_at, correlation_id,
        module, log_level, logger_name, message, stack_trace."""
        if not rows:
            return 0

        conn = self._connect()
        try:
            with conn.cursor() as cursor:
                execute_values(cursor, INSERT_QUERY, rows)
            conn.commit()
            return len(rows)
        except Exception:
            conn.rollback()
            logger.exception("Falha no bulk insert; rollback executado")
            raise
        finally:
            conn.close()
