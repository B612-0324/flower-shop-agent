"""统一日志配置：同时输出到控制台和文件。
配置 root logger，所有子 logger（Agent 名）自动传播上来。"""
import logging
import os


def setup_logger(log_dir="data"):
    os.makedirs(log_dir, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    fmt = logging.Formatter("%(asctime)s [%(name)s] %(message)s",
                           datefmt="%H:%M:%S")
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    root.addHandler(sh)

    fh = logging.FileHandler(os.path.join(log_dir, "simulation.log"),
                            encoding="utf-8")
    fh.setFormatter(fmt)
    root.addHandler(fh)
    return root
