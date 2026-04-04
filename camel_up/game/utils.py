import logging
import traceback
from logging.handlers import RotatingFileHandler


def setup_logging():
    logger = logging.getLogger('camel_up')
    logger.setLevel(logging.ERROR)
    handler = RotatingFileHandler('errors.log', maxBytes=1_000_000, backupCount=3)
    handler.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)
    return logger


def log_exception(logger, exc, context=""):
    msg = f"{context}: {exc}" if context else str(exc)
    logger.error("%s\n%s", msg, traceback.format_exc())


def coin_str(n):
    return f"{n} coin" if n == 1 else f"{n} coins"


def format_camel_name(color: str):
    return color.capitalize()


def clamp(value, min_val, max_val):
    return max(min_val, min(max_val, value))


def lerp(a, b, t):
    return a + (b - a) * t


def camel_color_to_rgb(color: str) -> tuple:
    mapping = {
        'blue':   (46, 109, 180),
        'green':  (58, 140, 63),
        'orange': (232, 117, 26),
        'yellow': (212, 192, 32),
        'white':  (240, 237, 224),
    }
    return mapping.get(color, (128, 128, 128))
