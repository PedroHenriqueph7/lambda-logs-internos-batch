import json
from typing import Any, Iterable

from adapter.postgres_repo import ExecutionLogRepository
from aws_lambda_powertools import Logger

logger = Logger(service="lambda-logs-internos-batch", child=True)


class LogProcessorService:
    def __init__(self, repository: ExecutionLogRepository):
        self._repository = repository

    @staticmethod
    def _to_row(body: dict[str, Any]) -> tuple:
        if not isinstance(body, dict):
            raise ValueError(f"Payload inválido: esperado dict, recebido {type(body).__name__}")

        timestamp = body.get("timestamp") or body.get("created_at")
        correlation_id = body.get("correlation_id") or body.get("correlationId") or body.get("trace_id")
        module = body.get("module")
        level = body.get("level") or body.get("log_level")
        logger_name = body.get("logger_name") or body.get("loggerName")

        message = body.get("message")
        if isinstance(message, (dict, list)):
            message = json.dumps(message, ensure_ascii=False)
        elif message is not None:
            message = str(message)

        stack_trace = body.get("stack_trace") or body.get("stackTrace")
        if isinstance(stack_trace, list):
            stack_trace = "\n".join(str(s) for s in stack_trace)
        elif isinstance(stack_trace, dict):
            stack_trace = json.dumps(stack_trace, ensure_ascii=False)
        elif stack_trace is not None:
            stack_trace = str(stack_trace)

        return (
            timestamp,
            correlation_id,
            module,
            level,
            logger_name,
            message,
            stack_trace,
        )

    def process(self, logs: Iterable[dict[str, Any]]) -> int:
        rows = [self._to_row(log) for log in logs]
        
        if not rows:
            logger.info("Nenhum registro para processar")
            return 0

        inserted = self._repository.bulk_insert(rows)
        logger.info("Logs inseridos no banco de dados", extra={"inserted_count": inserted})
        return inserted
