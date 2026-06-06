"""Structured logging configuration."""
import logging
import sys
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


def setup_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "echo_emotion.log"),
    ]
    for h in handlers:
        h.setFormatter(logging.Formatter(fmt, datefmt))

    logging.basicConfig(level=level, handlers=handlers, force=True)

    # Silence noisy libs
    for noisy in ("httpx", "multipart", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


logger = logging.getLogger("echo_emotion")
