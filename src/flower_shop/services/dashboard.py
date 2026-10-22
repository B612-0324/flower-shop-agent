"""完全离线、安全转义的运营仪表盘。"""
from html import escape
from pathlib import Path


def generate_dashboard(state, output_path='data/dashboard.html'):
    def text(value):
        return escape(str(value), quote=True)
    def table(headers, rows):
        return '<table><thead><tr>' + ''.join('<th>'+text(h)+'</th>' for h in headers) + \
            '</tr></thead><tbody>' + ''.join('<tr>'+''.join('<td>'+text(c)+'</td>' for c in row)+
                                           '</tr>' for row in rows) + '</tbody></table>'
    daily = table(['天', '订单', '完成', '拒绝', '营收', '成本含报损', '利润', '采购现金', '现金'],
                  [[d[k] for k in ('day','orders','completed','refused','revenue','cost',
                                   'profit','purchases','cash')] for d in state.daily_metrics])
    orders = table(['单号','天','客户','花材','金额','成本','状态','备注','拒绝原因'],
                   [[o.order_id,o.day,o.customer.name,
                     ', '.join(f'{k.label}×{v}' for k,v in o.items.items()),
                     o.total_price,o.cost,o.status.label,o.note,o.refuse_reason]
                    for o in state.orders.values()])
    inventory = table(['品类','库存','安全线','最短剩余保鲜天数','批次（数量/剩余天）'],
                      [[k.label,v.stock,v.safety_stock,v.freshness,
                        ', '.join(f"{b['qty']}/{b['expires_day']}" for b in v.batches)]
                       for k,v in state.inventory.items()])
    timeline = table(['序号','天','订单','Agent','协作事件'],
                     [[e[k] for k in ('seq','day','order_id','agent','action')]
                      for e in state.timeline])
    peak = max((d['revenue'] for d in state.daily_metrics), default=1) or 1
    bars = ''.join(f'<div class="trend">第{d["day"]}天 <meter min="0" max="{peak}" '
                   f'value="{d["revenue"]}"></meter> {d["revenue"]:.2f}元</div>'
                   for d in state.daily_metrics)
    html = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>花店运营仪表盘</title>
<style>body{font:15px "Microsoft YaHei",sans-serif;background:#f2f5f4;color:#243b35;margin:24px}
section{background:white;padding:22px;margin:18px 0;border-radius:12px;overflow:auto}
table{width:100%;border-collapse:collapse;white-space:nowrap}th,td{padding:9px;text-align:left;
border-bottom:1px solid #e5ece9}th{background:#edf4f0}meter{width:55%;height:22px}
.cards{display:flex;gap:24px;flex-wrap:wrap}.cards strong{font-size:24px}.trend{margin:8px 0}
summary{cursor:pointer;font-size:20px}</style><h1>花店多Agent协作运营模拟系统</h1>
<p>七个规则驱动Agent · 离线模拟 · 非LLM · 演示客户均为合成数据</p>'''
    html += '<section class="cards">' + ''.join(
        f'<div>{label}<br><strong>{text(value)}</strong></div>' for label,value in
        [('总订单',len(state.orders)),('营收',f'{state.revenue:.2f}'),
         ('利润（扣销售成本与报损）',f'{state.profit:.2f}'),('现金',f'{state.cash:.2f}')])+'</section>'
    for title, content in [('每日趋势与日报',bars+daily),('库存与批次',inventory),
                           ('订单明细',orders),('Agent协作时间线',timeline)]:
        html += '<section><details open><summary>'+title+'</summary>'+content+'</details></section>'
    html += '</html>'
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding='utf-8')
    return path.resolve()
