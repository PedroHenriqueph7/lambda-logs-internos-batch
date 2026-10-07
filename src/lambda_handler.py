import json
import logging

from adapter.postgres_repo import ExecutionLogRepository
from config import load_database_settings
from service.processor import LogProcessorService

logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)

# Montado fora do handler: reaproveitado em execuções "warm" e falha cedo se faltar configuração
_service = LogProcessorService(ExecutionLogRepository(load_database_settings()))


def lambda_handler(event, context):
    logs = [json.loads(record["body"]) for record in event.get("Records", [])]

    try:
        inserted = _service.process(logs)
    except Exception:
        logger.exception("Erro no processamento da Lambda")
        raise  # SQS não deleta o lote e aplica o retry

    return {"statusCode": 200, "body": f"{inserted} registros processados"}
