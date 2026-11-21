# 茶息 · 门店销售数据分析看板

一个练手用的小项目：用脚本生成一批茶饮门店的模拟订单数据，导入 MySQL，再用 Flask 写几个聚合接口，前端用 Echarts 把结果画出来。

项目想回答几个简单的业务问题：总体卖了多少、最近走势如何、哪些城市和门店贡献大、哪些产品好卖、一天里什么时候忙、周末和工作日有没有差别。

## 技术栈

- Python 3.10+
- Flask 2.3 / PyMySQL / pandas
- MySQL 8.0（utf8mb4）
- Echarts 5.x（CDN 引入，无需构建）

## 目录结构

```
cha-sales-dashboard/
├── app.py                  Flask 入口和全部接口
├── config.py               环境变量配置
├── db.py                   数据库连接和查询工具
├── requirements.txt
├── .env.example            环境变量示例
├── sql/
│   ├── init.sql            建库建表
│   └── analytics.sql       常用聚合查询
├── scripts/
│   ├── generate_data.py    生成模拟订单 CSV
│   └── import_data.py      CSV 导入 MySQL
├── data/                   生成的 CSV 放这里（已 gitignore）
├── templates/index.html
├── static/
│   ├── css/style.css
│   └── js/dashboard.js
└── LICENSE
```

## 数据库设计

用的是最简单的星型模型，两张维度表加一张事实表：

```
   dim_store              dim_product
   store_id (PK)          product_id (PK)
   store_name (UK)        product_name (UK)
   city / region          category / unit_price
        │                       │
        └─────── fact_order ────┘
                order_id (PK)
                order_time
                store_id (FK)
                product_id (FK)
                quantity
                amount
```

事实表一行是一条订单明细（订单 × 单品）。建了几个索引：`idx_order_time` 用于按时间聚合，`idx_store_id`、`idx_product_id` 用于 JOIN，`idx_store_time` 是门店和时间的组合查询用的复合索引。

## 本地运行

```bash
# 1. 装依赖
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS / Linux
pip install -r requirements.txt

# 2. 配置数据库
cp .env.example .env           # 把 MYSQL_PASSWORD 改成自己的密码

# 3. 建表
mysql -uroot -p < sql/init.sql

# 4. 生成数据并导入
python scripts/generate_data.py
python scripts/import_data.py

# 5. 启动
python app.py
```

然后打开 http://127.0.0.1:5000 。

`generate_data.py` 会生成最近 180 天、十多万条订单，随机种子固定，重复运行结果一致。门店固定归属于某座城市，产品固定分类和单价，下单时间集中在早晚高峰，周末单量上浮一点——主要是为了让图表看起来符合常识。

## 接口

统一返回 `{"code": 0, "message": "ok", "data": ...}`。

| 接口 | 说明 | 参数 |
|---|---|---|
| `/api/health` | 数据库连通性检查 | — |
| `/api/dashboard/summary` | 总览指标 | — |
| `/api/dashboard/trend` | 销售趋势 | `days`，默认 30 |
| `/api/dashboard/region` | 城市销售分布 | — |
| `/api/dashboard/product_top` | 单品销量排行 | `limit`，默认 10 |
| `/api/dashboard/store_top` | 门店销售额排行 | `limit`，默认 10 |
| `/api/dashboard/category` | 品类占比 | — |
| `/api/dashboard/hourly` | 24 小时订单分布 | — |
| `/api/dashboard/daytype` | 工作日 / 周末对比 | — |

试一下：

```bash
curl http://127.0.0.1:5000/api/dashboard/summary
```

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "store_count": 20,
    "order_count": 183533,
    "total_amount": 3700000.5,
    "avg_order_amount": 20.16,
    "total_cups": 220000
  }
}
```

几个聚合查询的例子在 [sql/analytics.sql](sql/analytics.sql)，可以直接复制到 MySQL 里跑。

## 关于数据

订单数据全部由脚本模拟生成，随机种子固定（42）。门店名和产品名只是借用常见的茶饮品类做业务场景，不代表任何品牌的真实经营数据。项目只用于学习和交流。

## License

MIT
