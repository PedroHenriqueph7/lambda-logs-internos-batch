import logging
from typing import Any, Iterable

from adapter.postgres_repo import ExecutionLogRepository

logger = logging.getLogger(__name__)


class LogProcessorService:
    def __init__(self, repository: ExecutionLogRepository):
        self._repository = repository

    @staticmethod
    def _to_row(body: dict[str, Any]) -> tuple:
        # Ordem alinhada às colunas do INSERT (created_at primeiro)
        return (
            body.get("timestamp"),
            body.get("correlation_id"),
            body.get("module"),
            body.get("level"),
            body.get("logger_name"),
            body.get("message"),
            body.get("stack_trace"),
        )

    def process(self, logs: Iterable[dict[str, Any]]) -> int:
        rows = [self._to_row(log) for log in logs]
        if not rows:
            logger.info("Nenhum registro para processar")
            return 0

        inserted = self._repository.bulk_insert(rows)
        logger.info("%d logs inseridos no banco de dados", inserted)
        return inserted
