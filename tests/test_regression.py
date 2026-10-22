"""真实业务边界与回归验证，兼容unittest和pytest。"""
import contextlib
import io
import json
import random
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from flower_shop.services.config_loader import load_config
from flower_shop.services.repository import OrderRepository
from flower_shop.services.dashboard import generate_dashboard
from flower_shop.core.state import ShopState
from flower_shop.core.models import Customer, FlowerItem, Order
from flower_shop.core.enums import FlowerType as F, OrderStatus as S, EventType as E
from flower_shop.core.events import Message, MessageBus
from flower_shop.simulation import Simulation


class RegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.config = load_config()
        self.state = ShopState(self.config)
        self.sim = Simulation(self.state, seed=42, output_dir=self.path)

    def order(self, **kwargs):
        return self.sim.sales.place_order(Customer('演示', 'DEMO', 2), {F.ROSE: 5}, **kwargs)

    def run_sim(self, sim=None, days=7):
        with contextlib.redirect_stdout(io.StringIO()):
            return (sim or self.sim).run(days)

    def test_seven_agents(self):
        self.assertEqual(len(self.sim.agents), 7)
        self.assertEqual(len(set(a.name for a in self.sim.agents)), 7)

    def test_order_delivery_and_pickup(self):
        for delivery in (False, True):
            order = self.order(is_delivery=delivery)
            self.assertEqual(order.status, S.COMPLETED)
            states = [e['action'] for e in self.state.timeline if e['order_id']==order.order_id]
            self.assertIn('CONFIRMED', states)
            self.assertIn('READY', states)
            self.assertEqual('DELIVERING' in states, delivery)

    def test_duplicate_order_messages(self):
        order = self.order()
        before = (self.state.cash,self.state.revenue,self.state.total_cost,
                  self.state.inventory[F.ROSE].stock)
        for event in (E.ORDER_RECEIVED,E.INVENTORY_CHECK_REQUEST,E.MAKING_REQUEST,E.DELIVERY_REQUEST):
            self.sim.bus.publish(Message(event,'test',{'order_id':order.order_id}))
        self.state.settle_order(order)
        self.assertEqual(before,(self.state.cash,self.state.revenue,self.state.total_cost,
                                 self.state.inventory[F.ROSE].stock))

    def test_invalid_quantities(self):
        for qty in (0,-1,1.5,True,'3'):
            with self.subTest(qty=qty), self.assertRaises(ValueError):
                self.sim.sales.place_order(Customer('演示','DEMO'),{F.ROSE:qty})
        self.assertFalse(self.state.orders)

    def test_empty_unknown_items(self):
        for items in ({},{'ROSE':2}):
            with self.assertRaises(ValueError):
                self.sim.sales.place_order(Customer('演示','DEMO'),items)

    def test_invalid_customer(self):
        for name,vip in (('',0),('演示',3)):
            with self.assertRaises(ValueError):
                self.sim.sales.place_order(Customer(name,'DEMO',vip),{F.ROSE:1})

    def test_insufficient_order_no_side_effect(self):
        before=self.state.cash
        order=self.sim.sales.place_order(Customer('演示','DEMO'),{F.ROSE:999})
        self.assertEqual(order.status,S.REFUSED)
        self.assertEqual(self.state.cash,before)
        self.assertEqual(self.state.inventory[F.ROSE].stock,60)

    def test_input_copy(self):
        items={F.ROSE:1}
        order=self.sim.sales.place_order(Customer('演示','DEMO'),items)
        items[F.ROSE]=999
        self.assertEqual(order.items[F.ROSE],1)

    def test_fefo_and_no_rejuvenation(self):
        flower=FlowerItem(F.ROSE,8,4,10,5,shelf_life=3)
        flower.age_one_day()
        flower.restock(10)
        flower.deduct(12)
        self.assertEqual(flower.stock,8)
        self.assertEqual(flower.batches,[{'qty':8,'expires_day':3}])
        flower.age_one_day()
        self.assertEqual(flower.age_one_day(),0)
        self.assertEqual(flower.age_one_day(),8)

    def test_partial_old_batch_expires(self):
        flower=FlowerItem(F.ROSE,8,4,10,5,shelf_life=2)
        flower.age_one_day()
        flower.restock(20)
        self.assertEqual(flower.age_one_day(),10)
        self.assertEqual(flower.stock,20)
        self.assertEqual(flower.freshness,1)

    def test_atomic_insufficient_deduction(self):
        with self.assertRaises(ValueError):
            self.state.deduct_materials({F.ROSE:2,F.LILY:999})
        self.assertEqual(self.state.inventory[F.ROSE].stock,60)

    def test_cash_and_cost(self):
        order=self.order()
        self.assertEqual(self.state.total_cost,order.cost)
        self.assertTrue(self.state.spend(100))
        self.assertEqual(self.state.total_cost,order.cost)
        self.state.record_spoilage(F.ROSE,2,4)
        self.assertEqual(self.state.total_cost,order.cost+8)
        self.assertAlmostEqual(self.state.cash,5000+order.total_price-100)

    def test_reserve_cash(self):
        self.assertFalse(self.state.spend(4001))
        self.assertEqual(self.state.cash,5000)
        with self.assertRaises(ValueError):
            self.state.spend(-1)

    def test_duplicate_purchase(self):
        message=Message(E.LOW_STOCK_WARNING,'test',{'flower_type':F.ROSE,'suggest_qty':10})
        self.sim.bus.publish(message)
        before=self.state.cash
        self.sim.bus.publish(message)
        self.assertEqual(self.state.cash,before)
        self.assertEqual(self.state.inventory[F.ROSE].stock,70)

    def test_duplicate_day_end(self):
        message=Message(E.DAILY_REPORT_REQUEST,'test',{'day':1})
        self.sim.bus.publish(message)
        before=[(v.stock,v.freshness) for v in self.state.inventory.values()]
        self.sim.bus.publish(message)
        self.assertEqual(before,[(v.stock,v.freshness) for v in self.state.inventory.values()])

    def test_reproducibility_and_isolation(self):
        original=random.getstate()
        first=self.run_sim()
        second_state=ShopState(self.config)
        second=Simulation(second_state,seed=42,output_dir=self.path/'second')
        self.assertEqual(first,self.run_sim(second))
        self.assertEqual(self.state.daily_metrics,second_state.daily_metrics)
        self.assertEqual(self.config.inventory[F.ROSE].stock,60)
        self.assertEqual(random.getstate(),original)
        with self.assertRaises(ValueError):
            self.sim.run()

    def test_invalid_days(self):
        for days in (0,-1,True,1.2):
            with self.assertRaises(ValueError):
                self.sim.run(days)

    def test_transition_rejects_jump(self):
        order=Order('x',Customer('演示','DEMO'),{F.ROSE:1})
        with self.assertRaises(ValueError):
            self.state.transition(order,S.PENDING,S.COMPLETED,'test')

    def test_bus_error_visible(self):
        bus=MessageBus()
        def broken(message):
            raise RuntimeError('故障')
        bus.subscribe(E.ORDER_RECEIVED,broken)
        with self.assertRaises(RuntimeError):
            bus.publish(Message(E.ORDER_RECEIVED,'test'))

    def test_sqlite_runs_days_timeline_inventory(self):
        repos=[OrderRepository(self.path/'shared.db') for _ in range(2)]
        for repo in repos:
            sim=Simulation(ShopState(self.config),repo,seed=7,output_dir=self.path/repo.run_id)
            result=self.run_sim(sim,days=3)
            self.assertEqual(len(repo.list_orders()),result.total_orders)
        with contextlib.closing(sqlite3.connect(self.path/'shared.db')) as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM simulation_runs').fetchone()[0],2)
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM run_inventory').fetchone()[0],42)
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM run_daily').fetchone()[0],6)
            self.assertGreater(conn.execute('SELECT COUNT(*) FROM run_timeline').fetchone()[0],0)
            self.assertEqual(conn.execute('SELECT COUNT(DISTINCT day) FROM run_orders').fetchone()[0],3)

    def test_daily_reconciles_after_restock(self):
        result=self.run_sim()
        self.assertAlmostEqual(sum(d['revenue'] for d in self.state.daily_metrics),result.revenue)
        self.assertAlmostEqual(sum(d['profit'] for d in self.state.daily_metrics),result.profit)
        self.assertEqual(self.state.daily_metrics[-1]['cash'],self.state.cash)
        self.assertEqual(self.state.daily_metrics[-1]['inventory'],
                         {k.value:v.stock for k,v in self.state.inventory.items()})
        self.assertAlmostEqual(self.state.cash,5000+self.state.revenue-self.state.purchase_spend)
        for v in self.state.inventory.values():
            self.assertEqual(v.stock,sum(b['qty'] for b in v.batches))
            self.assertGreaterEqual(v.stock,0)

    def test_dashboard_escapes_and_sections(self):
        order=self.order(note='<script>alert(1)</script>')
        order.customer.name='<img src=x onerror=alert(1)>'
        path=generate_dashboard(self.state,self.path/'dashboard.html')
        content=path.read_text(encoding='utf-8')
        self.assertNotIn('<script>',content)
        self.assertNotIn('<img',content)
        self.assertIn('&lt;script&gt;',content)
        for label in ('每日趋势','库存与批次','订单明细','Agent协作时间线'):
            self.assertIn(label,content)

    def test_cli_invalid_days(self):
        result=subprocess.run([sys.executable,str(ROOT/'main.py'),'--days','0'],
                              capture_output=True)
        self.assertEqual(result.returncode,2)

    def test_cli_bare_paths(self):
        result=subprocess.run([sys.executable,str(ROOT/'main.py'),'--days','1',
                               '--db','shop.db','--csv','orders.csv','--summary','summary.json',
                               '--dashboard','dashboard.html','--output-dir','data'],
                              cwd=self.path,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        summary=json.loads((self.path/'summary.json').read_text(encoding='utf-8'))
        self.assertEqual(summary['agent_count'],7)
        for name in ('shop.db','orders.csv','summary.json','dashboard.html'):
            self.assertTrue((self.path/name).is_file())

    def test_invalid_config(self):
        path=self.path/'bad.json'
        for changes in ({'initial_cash':-1},{'reserve_cash':99999},{'package_fee':float('nan')}):
            raw=json.loads((ROOT/'config/shop_config.json').read_text(encoding='utf-8'))
            raw.update(changes)
            path.write_text(json.dumps(raw),encoding='utf-8')
            with self.assertRaises(Exception):
                load_config(path)


if __name__=='__main__':
    unittest.main()
