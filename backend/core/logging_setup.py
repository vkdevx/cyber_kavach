import logging
import json
import time
from typing import Optional, Dict, Any
from config.settings import settings


class AuditJSONFormatter(logging.Formatter):
    """Custom logging formatter outputting structured audit logs in JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }

        # Include custom audit attributes if attached
        if hasattr(record, "event_type"):
            log_obj["event_type"] = record.event_type
        if hasattr(record, "src_ip"):
            log_obj["src_ip"] = record.src_ip
        if hasattr(record, "correlation_id"):
            log_obj["correlation_id"] = record.correlation_id
        if hasattr(record, "user_id"):
            log_obj["user_id"] = record.user_id
        if hasattr(record, "details"):
            log_obj["details"] = record.details

        return json.dumps(log_obj)


def setup_logging():
    """Initializes cybersecurity audit logging configuration."""
    logger = logging.getLogger("oneway_sentinel")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(AuditJSONFormatter())
        logger.addHandler(handler)

    return logger


audit_logger = setup_logging()


def log_security_event(
    event_type: str,
    message: str,
    src_ip: Optional[str] = "127.0.0.1",
    user_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    level: int = logging.INFO
):
    """Logs a structured security audit event."""
    extra = {
        "event_type": event_type,
        "src_ip": src_ip,
        "user_id": user_id,
        "correlation_id": correlation_id,
        "details": details or {}
    }
    audit_logger.log(level, message, extra=extra)
