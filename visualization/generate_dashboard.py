# -*- coding: utf-8 -*-
"""
把 ShopState 的统计结果渲染成一个独立的 HTML 仪表盘。
无外部依赖：纯 HTML + 内联 CSS，用 div 画柱状图，浏览器直接打开即可。
"""
import os
from collections import defaultdict
from core.enums import OrderStatus


def generate_dashboard(state, output_path="data/dashboard.html"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # ---- 统计 ----
    total_orders = len(state.orders)
    done = sum(1 for o in state.orders.values() if o.status == OrderStatus.COMPLETED)
    refused = total_orders - done
    revenue = state.revenue
    cost = state.total_cost
    profit = revenue - cost
    margin = (profit / revenue * 100) if revenue > 0 else 0

    # 按客户统计消费
    cust_spend = defaultdict(float)
    for o in state.orders.values():
        if o.status == OrderStatus.COMPLETED:
            cust_spend[o.customer.name] += o.total_price

    # 按花材品类统计销量
    flower_qty = defaultdict(int)
    for o in state.orders.values():
        if o.status == OrderStatus.COMPLETED:
            for ftype, qty in o.items.items():
                flower_qty[ftype.value] += qty

    # 当前库存
    inv_rows = []
    max_stock = max((it.stock for it in state.inventory.values()), default=1)
    for ftype, it in state.inventory.items():
        pct = int(it.stock / max_stock * 100) if max_stock else 0
        warn = " ⚠ 低库存" if it.is_low() else ""
        inv_rows.append(
            f'<div class="bar-row"><span class="label">{ftype.value}{warn}</span>'
            f'<div class="bar-bg"><div class="bar-fill" style="width:{pct}%"></div></div>'
            f'<span class="num">{it.stock} 枝</span></div>'
        )

    # 花材销量柱状图
    max_qty = max(flower_qty.values()) if flower_qty else 1
    flower_bars = []
    for name, qty in sorted(flower_qty.items(), key=lambda x: -x[1]):
        pct = int(qty / max_qty * 100)
        flower_bars.append(
            f'<div class="bar-row"><span class="label">{name}</span>'
            f'<div class="bar-bg"><div class="bar-fill" style="width:{pct}%;background:#e91e63"></div></div>'
            f'<span class="num">{qty} 枝</span></div>'
        )

    # 客户消费 TOP
    max_cust = max(cust_spend.values()) if cust_spend else 1
    cust_bars = []
    for name, amt in sorted(cust_spend.items(), key=lambda x: -x[1])[:6]:
        pct = int(amt / max_cust * 100)
        cust_bars.append(
            f'<div class="bar-row"><span class="label">{name}</span>'
            f'<div class="bar-bg"><div class="bar-fill" style="width:{pct}%;background:#4caf50"></div></div>'
            f'<span class="num">¥{amt:.0f}</span></div>'
        )

    # 订单明细表格
    order_rows = []
    for o in state.orders.values():
        items_str = ", ".join(f"{k.value}×{v}" for k, v in o.items.items())
        color = "#4caf50" if o.status == OrderStatus.COMPLETED else "#f44336"
        order_rows.append(
            f"<tr><td>{o.order_id}</td><td>{o.customer.name}</td>"
            f"<td>{items_str}</td><td>¥{o.total_price:.2f}</td>"
            f'<td style="color:{color};font-weight:bold">{o.status.value}</td></tr>'
        )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>花店运营仪表盘</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
         background: #f5f7fa; padding: 24px; color: #333; }}
  h1 {{ font-size: 22px; margin-bottom: 20px; color: #2c3e50; }}
  .cards {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }}
  .card {{ background: #fff; border-radius: 10px; padding: 18px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
  .card .v {{ font-size: 24px; font-weight: bold; color: #2c3e50; margin-top: 6px; }}
  .card .l {{ font-size: 13px; color: #888; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
  .panel {{ background: #fff; border-radius: 10px; padding: 20px;
           box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 16px; }}
  .panel h3 {{ font-size: 15px; margin-bottom: 14px; color: #2c3e50; }}
  .bar-row {{ display: flex; align-items: center; margin-bottom: 8px; font-size: 13px; }}
  .bar-row .label {{ width: 90px; color: #555; }}
  .bar-row .bar-bg {{ flex: 1; background: #eef1f5; height: 16px; border-radius: 8px;
                     overflow: hidden; margin: 0 10px; }}
  .bar-row .bar-fill {{ height: 100%; background: #3f51b5; border-radius: 8px; }}
  .bar-row .num {{ width: 80px; text-align: right; color: #666; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th, td {{ padding: 8px 10px; text-align: left; border-bottom: 1px solid #eee; }}
  th {{ background: #fafafa; color: #666; font-weight: 600; }}
</style>
</head>
<body>
  <h1>🌸 花店多 Agent 运营仪表盘</h1>

  <div class="cards">
    <div class="card"><div class="l">总订单</div><div class="v">{total_orders}</div></div>
    <div class="card"><div class="l">完成 / 拒绝</div>
      <div class="v">{done} / {refused}</div></div>
    <div class="card"><div class="l">总营收</div><div class="v">¥{revenue:.0f}</div></div>
    <div class="card"><div class="l">利润（毛利率 {margin:.1f}%）</div>
      <div class="v" style="color:{'#4caf50' if profit>0 else '#f44336'}">¥{profit:.0f}</div></div>
  </div>

  <div class="grid">
    <div class="panel">
      <h3>📦 当前库存</h3>
      {''.join(inv_rows)}
    </div>
    <div class="panel">
      <h3>🌹 花材销量排行</h3>
      {''.join(flower_bars)}
    </div>
  </div>

  <div class="panel">
    <h3>👥 客户消费 TOP 6</h3>
    {''.join(cust_bars)}
  </div>

  <div class="panel">
    <h3>📋 订单明细</h3>
    <table>
      <tr><th>单号</th><th>客户</th><th>花材</th><th>金额</th><th>状态</th></tr>
      {''.join(order_rows)}
    </table>
  </div>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return os.path.abspath(output_path)
