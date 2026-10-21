# 运维手册

## 改价格 / 库存

编辑 `config/shop_config.json`，重启模拟即可。无需改代码。

## 看日志

```bash
tail -f logs/flower_shop.log
```

## 查历史订单

```bash
sqlite3 data/shop.db "SELECT * FROM orders WHERE status='REFUSED'"
```

## 导出 CSV

程序运行结束自动生成 `data/orders.csv`，可用 Excel 直接打开。

## 重置数据库

```bash
rm -f data/shop.db data/orders.csv
```
