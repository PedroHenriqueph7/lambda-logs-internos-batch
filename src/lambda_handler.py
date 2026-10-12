import json
from typing import Any

from aws_lambda_powertools import Logger, Metrics
from aws_lambda_powertools.metrics import MetricUnit

from adapter.postgres_repo import ExecutionLogRepository
from config import load_database_settings
from service.processor import LogProcessorService

logger = Logger(service="lambda-logs-internos-batch")
metrics = Metrics(namespace="LogsInternos")

# Montado fora do handler: reaproveitado em execuções "warm" e falha cedo se faltar configuração
_service = LogProcessorService(ExecutionLogRepository(load_database_settings()))


@logger.inject_lambda_context
@metrics.log_metrics(capture_cold_start_metric=True, raise_on_empty_metrics=False)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:

    records = event.get("Records", [])
    failed_ids: list[dict[str, str]] = []
    valid_records: list[tuple[str, dict[str, Any]]] = []

    # 1. Parse e validação inicial de cada mensagem do SQS
    for record in records:
        msg_id = record.get("messageId", "")
        try:
            body = json.loads(record.get("body", "{}"))

            if not isinstance(body, dict):
                raise ValueError("O corpo da mensagem não é um objeto JSON válido")
            valid_records.append((msg_id, body))
            
        except Exception:
            logger.exception("Falha ao desserializar mensagem do SQS", extra={"message_id": msg_id})
            if msg_id:
                failed_ids.append({"itemIdentifier": msg_id})

    # 2. Inserção em lote (Bulk) com fallback individual para isolamento de erros
    total_inserted = 0
    if valid_records:
        try:
            total_inserted = _service.process([body for _, body in valid_records])
        except Exception:
            logger.warning(
                "Falha na inserção em lote completa. Executando fallback individual para isolar mensagens com erro."
            )
            for msg_id, body in valid_records:
                try:
                    _service.process([body])
                    total_inserted += 1
                except Exception:
                    logger.exception("Falha ao processar mensagem individual", extra={"message_id": msg_id})
                    if msg_id:
                        failed_ids.append({"itemIdentifier": msg_id})

    # 3. Registro de métricas da execução
    if total_inserted > 0:
        metrics.add_metric(name="LogsInserted", unit=MetricUnit.Count, value=total_inserted)
    if failed_ids:
        metrics.add_metric(name="LogsFailed", unit=MetricUnit.Count, value=len(failed_ids))

    logger.info(
        "Processamento do lote finalizado",
        extra={
            "total_records": len(records),
            "inserted": total_inserted,
            "failed": len(failed_ids),
        },
    )

    # SQS deleta apenas os sucessos; falhas retornam para retry/DLQ
    return {"batchItemFailures": failed_ids}
