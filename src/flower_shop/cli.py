"""统一命令行入口，所有产物路径均可指定。"""
import argparse
import json
from dataclasses import asdict
from pathlib import Path
from .services.config_loader import load_config
from .services.logger import setup_logger
from .services.repository import OrderRepository
from .services.dashboard import generate_dashboard
from .core.state import ShopState
from .core.exceptions import InvalidConfigError
from .simulation import Simulation


def positive(value):
    result = int(value)
    if result <= 0:
        raise argparse.ArgumentTypeError('模拟天数必须大于0')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description='花店七Agent规则驱动离线模拟（非LLM）')
    parser.add_argument('--days', type=positive, default=7)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--config', help='默认使用包内配置')
    parser.add_argument('--output-dir', default='data')
    parser.add_argument('--db', help='默认output-dir/shop.db')
    parser.add_argument('--csv', help='默认output-dir/orders.csv')
    parser.add_argument('--summary', help='默认output-dir/summary.json')
    parser.add_argument('--dashboard', help='默认output-dir/dashboard.html')
    parser.add_argument('--no-dashboard', action='store_true')
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
    except InvalidConfigError as exc:
        parser.error(str(exc))
    output = Path(args.output_dir)
    setup_logger(str(output))
    state = ShopState(config)
    repo = OrderRepository(args.db or output / 'shop.db')
    simulation = Simulation(state, repo, args.seed, output)
    result = simulation.run(args.days)
    csv_path = simulation.report.export_orders_csv(args.csv or output / 'orders.csv')
    dashboard = None if args.no_dashboard else generate_dashboard(
        state, args.dashboard or output / 'dashboard.html')
    summary = dict(**asdict(result), seed=args.seed, run_id=repo.run_id, agent_count=7,
                   agent_type='规则驱动（非LLM）', cash=state.cash,
                   total_cost=state.total_cost, sales_cost=round(state.total_cost-state.spoilage_loss,2),
                   spoilage_loss=state.spoilage_loss, purchase_spend=state.purchase_spend,
                   inventory={k.value: v.stock for k,v in state.inventory.items()},
                   daily=state.daily_metrics, timeline_events=len(state.timeline),
                   files=dict(database=str(repo.db_path.resolve()), csv=str(csv_path.resolve()),
                              dashboard=str(dashboard) if dashboard else None))
    path = Path(args.summary or output / 'summary.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    (output / 'timeline.json').write_text(json.dumps(state.timeline, ensure_ascii=False, indent=2),
                                          encoding='utf-8')
    print(f'汇总：{result.days}天 {result.total_orders}单，完成{result.completed}/拒绝{result.refused}，'
          f'营收{result.revenue:.2f}，利润{result.profit:.2f}；summary={path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
