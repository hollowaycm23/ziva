import logging
import json
import time
import threading
from datetime import datetime

_context = threading.local()


def set_request_id(request_id: str = None):
    if request_id is None:
        request_id = f"req_{int(time.time() * 1000000)}_{threading.get_ident()}"
    _context.request_id = request_id
    return request_id


def get_request_id() -> str:
    return getattr(_context, 'request_id', 'unknown')


def set_session_id(session_id):
    _context.session_id = session_id


def get_session_id():
    return getattr(_context, 'session_id', None)


class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": get_request_id(),
        }
        session_id = get_session_id()
        if session_id:
            log_entry["session_id"] = session_id
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(level=logging.INFO):
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    for logger_name in ('httpx', 'httpcore', 'urllib3', 'chardet'):
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def log_event(event_type: str, **kwargs):
    logger = logging.getLogger("ZivaEvent")
    extra = {"extra_fields": {"event_type": event_type, **kwargs}}
    logger.info(f"[{event_type}]", extra=extra)
