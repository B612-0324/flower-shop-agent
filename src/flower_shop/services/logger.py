"""日志配置：同时输出到控制台和 logs/flower_shop.log。"""
from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(log_dir: str = "logs", level: int = logging.INFO) -> logging.Logger:
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger("flower_shop")
    logger.setLevel(level)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()
    logger.propagate = False

    fmt = logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    fh = RotatingFileHandler(
        os.path.join(log_dir, "flower_shop.log"),
        maxBytes=1_000_000, backupCount=3, encoding="utf-8",
    )
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger
