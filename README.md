# 🍵 茶息 · 门店销售数据分析可视化系统

> 一个面向秋招/练手的完整数据链路项目：**MySQL 建模 → Python 清洗入库 → Flask REST API → Echarts 可视化看板**。
> 用模拟的新式茶饮门店销售数据，回答「卖了多少、在哪卖、卖什么、什么时候卖」四类业务问题。

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3-green)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange)](https://www.mysql.com/)
[![Echarts](https://img.shields.io/badge/Echarts-5.5-purple)](https://echarts.apache.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 一、项目亮点

- **完整数据链路**：不是「前端写死数据」的 Demo，从建表、造数、清洗入库到接口、图表全覆盖。
- **规范星型模型**：2 张维度表（门店/产品）+ 1 张事实表（订单），带索引、外键与唯一约束。
- **统一接口格式**：所有接口返回 `{"code": 0, "message": "ok", "data": ...}`，错误处理也有统一出口。
- **更真实的模拟数据**：门店固定归属城市（不会「瞬移」）、产品固定分类单价、下单时间集中在早晚高峰、周末客流上浮。
- **开箱即用的趋势图**：趋势接口以「事实表最大订单日期」为基准，而不是 `CURDATE()`，历史数据也能出图。
- **8 个分析视角**：总览、趋势、城市分布、单品排行、门店排行、品类占比、时段分布、工作日/周末对比。
- **深色茶饮风格看板**：响应式布局，移动端也能看。

> 相比参考教程，本项目额外修复了 `db.py` 与 `db/` 目录同名导致的导入冲突，并补充了维度唯一键、批量入库、连接上下文管理等工程细节。

---

## 二、技术栈

| 层次 | 技术 |
|---|---|
| 数据库 | MySQL 8.0（utf8mb4） |
| 数据处理 | Python + pandas |
| 后端 | Flask + PyMySQL |
| 前端 | HTML + CSS + JavaScript fetch |
| 可视化 | Echarts 5.x（CDN 引入） |

---

## 三、目录结构

```text
cha-sales-dashboard/
├── app.py                      # Flask 入口 + 全部 REST API
├── config.py                   # 环境变量配置
├── db.py                       # 数据库连接工具（上下文管理 + 通用查询）
├── requirements.txt            # 依赖清单
├── .env.example                # 环境变量示例（复制为 .env 使用）
├── sql/
│   ├── init.sql                # 建库建表：星型模型 + 索引 + 外键
│   └── analytics.sql           # 8 条分析 SQL，可直接粘贴到 MySQL 验证
├── scripts/
│   ├── generate_data.py        # 生成模拟订单 CSV
│   └── import_data.py          # CSV 批量导入 MySQL
├── data/
│   └── order_data.csv          # 运行 generate_data.py 后生成（已 gitignore）
├── templates/
│   └── index.html              # 看板页面
├── static/
│   ├── css/style.css           # 深色茶饮风格
│   └── js/dashboard.js         # Echarts 渲染 + 异步请求
└── LICENSE                     # MIT
```

---

## 四、数据库设计（星型模型）

```text
        dim_store                    dim_product
        ├─ store_id (PK)             ├─ product_id (PK)
        ├─ store_name (UK)           ├─ product_name (UK)
        ├─ city / region             ├─ category / unit_price
        └─ status
              │                            │
              └─────── fact_order ─────────┘
                      ├─ order_id (PK)
                      ├─ order_time   [idx_order_time]
                      ├─ store_id     [idx_store_id, FK]
                      ├─ product_id   [idx_product_id, FK]
                      ├─ quantity
                      └─ amount
```

**聚合粒度**：事实表一行 = 一条「订单 × 单品」明细。所有指标都从这张表按维度聚合而来。

**索引设计**：
- `idx_order_time`：支撑趋势查询的时间范围过滤与分组；
- `idx_store_id` / `idx_product_id`：支撑两路外键 JOIN；
- `idx_store_time (store_id, order_time)`：支撑门店维度 + 时间的组合查询（复合索引，遵循最左前缀原则）。

---

## 五、快速开始

### 1. 环境要求

- Python 3.10+
- MySQL 8.0+
- Chrome / Edge 浏览器

### 2. 安装依赖

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. 配置数据库连接

```bash
cp .env.example .env
# 编辑 .env，把 MYSQL_PASSWORD 改成你自己的密码
```

### 4. 建库建表

```bash
mysql -uroot -p < sql/init.sql
```

### 5. 生成并导入数据

```bash
python scripts/generate_data.py   # 生成最近 180 天、约 10 万级订单的 CSV
python scripts/import_data.py     # 维护维度表 + 批量写入事实表
```

### 6. 启动服务

```bash
python app.py
```

浏览器打开 <http://127.0.0.1:5000> 即可看到看板。

---

## 六、API 接口

所有接口统一返回 `{"code": 0, "message": "ok", "data": ...}`。

| 接口 | 说明 | 参数 |
|---|---|---|
| `GET /api/health` | 健康检查（数据库连通性） | — |
| `GET /api/dashboard/summary` | 总览：销售额/订单数/门店数/客单价/杯数 | — |
| `GET /api/dashboard/trend` | 近 N 天销售趋势 | `days`（默认 30，范围 1–365） |
| `GET /api/dashboard/region` | 城市销售分布 | — |
| `GET /api/dashboard/product_top` | 单品销量/销售额 Top N | `limit`（默认 10） |
| `GET /api/dashboard/store_top` | 门店销售额 Top N（增强） | `limit`（默认 10） |
| `GET /api/dashboard/category` | 品类销售占比（增强） | — |
| `GET /api/dashboard/hourly` | 24 小时订单分布（增强） | — |
| `GET /api/dashboard/daytype` | 工作日 vs 周末对比（增强） | — |

示例：

```bash
curl http://127.0.0.1:5000/api/dashboard/summary
```

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "store_count": 20,
    "order_count": 118432,
    "total_amount": 2387654.0,
    "avg_order_amount": 20.16,
    "total_cups": 145203
  }
}
```

---

## 七、业务问题与图表的对应

| 业务问题 | 图表 | 数据来源 |
|---|---|---|
| 整体卖了多少？ | 4 张总览卡片 | `fact_order` 聚合 |
| 最近生意走势如何？ | 销售趋势折线图（可切换 7/30/90/180 天） | `fact_order` 按日期聚合 |
| 哪些城市贡献大？ | 城市销售柱状图 | `fact_order ⋈ dim_store` |
| 哪些单品最好卖？ | 单品销量横向排行 | `fact_order ⋈ dim_product` |
| 哪些门店是头部？ | 门店销售额横向排行 | `fact_order ⋈ dim_store` |
| 品类结构如何？ | 品类占比环形图 | `fact_order ⋈ dim_product` |
| 一天中什么时候忙？ | 24 小时订单分布 | `fact_order` 按 HOUR 聚合 |
| 周末生意更好吗？ | 工作日/周末双轴对比 | `fact_order` 按 WEEKDAY 聚合 |

---

## 八、SQL 聚合查询摘录

```sql
-- 总览指标
SELECT COUNT(DISTINCT store_id) AS store_count,
       COUNT(*) AS order_count,
       SUM(amount) AS total_amount,
       ROUND(SUM(amount) / COUNT(*), 2) AS avg_order_amount
FROM fact_order;

-- 城市销售分布
SELECT s.city, SUM(f.amount) AS total_amount
FROM fact_order f
JOIN dim_store s ON f.store_id = s.store_id
GROUP BY s.city
ORDER BY total_amount DESC;
```

更多查询见 [`sql/analytics.sql`](sql/analytics.sql)。

---

## 九、数据说明与免责声明

- `data/order_data.csv` 由 `generate_data.py` **程序化模拟生成**，随机种子固定（42），可复现。
- 门店名、产品名仅借用大众熟知的茶饮品类作为业务语境，**不代表任何品牌的真实经营数据**，与任何商业主体无关。
- 本项目仅用于学习、面试作品展示与技术交流，请勿用于商业决策。

---

## 十、简历写法参考

```text
门店销售数据分析可视化系统        2024.xx – 2024.xx
技术栈：Python、Flask、MySQL、Echarts、pandas
- 设计门店/产品维度表与订单事实表构成的星型模型，建立索引与外键约束；
- 编写 Python 脚本完成模拟数据生成、清洗与批量入库（executemany 分批事务提交）；
- 开发 9 个 REST API，统一 JSON 响应与异常处理，聚合查询覆盖时间/区域/品类等维度；
- 使用 Echarts 实现响应式数据看板，通过 fetch 异步加载完成图表动态渲染与联动。
```

---

## License

[MIT](LICENSE) © cha-sales-dashboard contributors
