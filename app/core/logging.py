import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime
from logging.config import dictConfig
from typing import Any

from app.core.config import Settings

request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)

LOG_EXTRA_FIELDS = (
    "request_id",
    "method",
    "path",
    "status_code",
    "duration_ms",
)


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = request_id_context.get() or "-"
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        event: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in LOG_EXTRA_FIELDS:
            value = getattr(record, field, None)
            if value is not None and value != "-":
                event[field] = value
        if record.exc_info is not None:
            event["exception"] = self.formatException(record.exc_info)
        return json.dumps(event, ensure_ascii=False, default=str)


def configure_logging(settings: Settings) -> None:
    formatter = "json" if settings.log_format == "json" else "console"
    configuration: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {"request_context": {"()": RequestContextFilter}},
        "formatters": {
            "console": {
                "format": (
                    "%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s %(message)s"
                )
            },
            "json": {"()": JsonFormatter},
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": formatter,
                "filters": ["request_context"],
                "stream": "ext://sys.stdout",
            }
        },
        "root": {"handlers": ["default"], "level": settings.log_level},
    }
    dictConfig(configuration)
