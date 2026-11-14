"""
Central logging configuration for playwright-server-native.
Provides console and file handlers with timestamps and log levels.
"""
import logging
import sys
from config.config import Config


def get_logger(name: str = "playwright-framework") -> logging.Logger:
    """
    Returns a configured logger instance writing to console and logs/framework.log.
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers if already configured
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler in logs/framework.log
        log_file = Config.LOGS_DIR / "framework.log"
        file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
