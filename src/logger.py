import logging
import os

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def _setup() -> None:
    _root = logging.getLogger()
    if _root.handlers:
        return
    _root.setLevel(LOG_LEVEL)
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
    _root.addHandler(_handler)

_setup()

def get_logger(name: str) -> logging.Logger:
    """Return a logger for *name* (pass __name__ from the calling module)."""
    return logging.getLogger(name)
