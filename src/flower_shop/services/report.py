"""报表生成：日报、CSV 导出。"""
from __future__ import annotations

import csv
from pathlib import Path

from ..core.enums import OrderStatus
from ..core.state import ShopState


class ReportService:
    def __init__(self, state: ShopState, csv_dir: str = "data") -> None:
        self.state = state
        self.csv_dir = Path(csv_dir)
        self.csv_dir.mkdir(parents=True, exist_ok=True)

    def daily_report(self) -> str:
        s = self.state
        profit = s.profit
        margin = (profit / s.revenue * 100) if s.revenue > 0 else 0
        done = sum(1 for o in s.orders.values() if o.status == OrderStatus.COMPLETED)
        refused = sum(1 for o in s.orders.values() if o.status == OrderStatus.REFUSED)

        lines = [
            "=" * 60,
            f"  第 {s.day} 日营业日报",
            "=" * 60,
            f"  营收：{s.revenue:>10.2f} 元   成本：{s.total_cost:>10.2f} 元",
            f"  利润：{profit:>10.2f} 元   毛利率：{margin:.1f}%",
            f"  报损：{s.spoilage_loss:>10.2f} 元（累计）",
            f"  现金：{s.cash:>10.2f} 元",
            f"  订单：{len(s.orders)}（完成 {done} / 拒绝 {refused}）",
            "",
            "  订单明细：",
            f"  {'单号':<12}{'客户':<8}{'金额':>8}  状态",
        ]
        for o in s.orders.values():
            reason = f"({o.refuse_reason})" if o.refuse_reason else ""
            lines.append(
                f"  {o.order_id:<12}{o.customer.name:<8}"
                f"{o.total_price:>8.2f}  {o.status.label}{reason}"
            )
        if s.refuse_stats:
            lines.append("")
            lines.append("  拒单原因：")
            for reason, cnt in s.refuse_stats.items():
                lines.append(f"    {reason}：{cnt} 单")
        lines.append("=" * 60)
        return "\n".join(lines)

    def export_orders_csv(self, path: str | Path | None = None) -> Path:
        path = Path(path) if path else self.csv_dir / "orders.csv"
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["单号", "日期", "客户", "VIP", "花材", "金额", "成本", "状态", "备注"])
            for o in self.state.orders.values():
                items = ";".join(f"{k.label}x{v}" for k, v in o.items.items())
                w.writerow([
                    o.order_id, o.day, o.customer.name, o.customer.vip_level,
                    items, o.total_price, o.cost, o.status.label, o.note,
                ])
        return path
