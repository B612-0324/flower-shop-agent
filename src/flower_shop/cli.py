"""命令行入口：python -m flower_shop.cli --days 7 --config config/shop_config.json"""
from __future__ import annotations

import argparse
import sys

from .services.config_loader import load_config
from .services.logger import setup_logger
from .services.repository import OrderRepository
from .core.state import ShopState
from .simulation import Simulation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="花店多 Agent 协作运营模拟系统")
    parser.add_argument("--days", type=int, default=3, help="模拟天数")
    parser.add_argument("--config", default="config/shop_config.json", help="配置文件路径")
    parser.add_argument("--db", default="data/shop.db", help="SQLite 路径")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    args = parser.parse_args(argv)

    setup_logger()
    cfg = load_config(args.config)
    state = ShopState(cfg)
    repo = OrderRepository(args.db)
    sim = Simulation(state, repo=repo, seed=args.seed)
    result = sim.run(days=args.days)

    print(f"\n[汇总] {result.days} 天共 {result.total_orders} 单，"
          f"完成 {result.completed} / 拒绝 {result.refused}，"
          f"营收 {result.revenue:.2f}，利润 {result.profit:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
