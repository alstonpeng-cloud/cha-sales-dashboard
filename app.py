"""Flask 入口：首页渲染 + 数据看板 REST API。

统一响应格式：{"code": 0, "message": "ok", "data": ...}
"""
from datetime import date, datetime
from decimal import Decimal

from flask import Flask, jsonify, render_template, request

from config import Config
from db import query_all, query_one

app = Flask(__name__)


# 通用工具
def convert(value):
    """把 Decimal / date / datetime 转成 jsonify 可序列化的类型。"""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def normalize(rows):
    """把 [{col: value}] 中的不可序列化值统一转换。"""
    if rows is None:
        return None
    if isinstance(rows, dict):
        return {k: convert(v) for k, v in rows.items()}
    return [{k: convert(v) for k, v in row.items()} for row in rows]


def success(data):
    return jsonify({"code": 0, "message": "ok", "data": data})


def failure(message, status=500):
    return jsonify({"code": 1, "message": message, "data": None}), status


@app.errorhandler(Exception)
def handle_error(err):
    """异常处理：统一返回 JSON。"""
    app.logger.exception("接口异常: %s", err)
    return failure(f"服务器内部错误: {err}", 500)


# 页面
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health")
def health():
    """健康检查：确认数据库可连通。"""
    try:
        query_one("SELECT 1 AS ok")
        return success({"status": "up", "database": "connected"})
    except Exception as err:
        return failure(f"数据库连接失败: {err}", 503)


# 核心指标
@app.route("/api/dashboard/summary")
def summary():
    row = query_one("""
        SELECT
          COUNT(DISTINCT store_id)         AS store_count,
          COUNT(*)                         AS order_count,
          SUM(amount)                      AS total_amount,
          ROUND(SUM(amount) / COUNT(*), 2) AS avg_order_amount,
          SUM(quantity)                    AS total_cups
        FROM fact_order
    """)
    return success(normalize(row))


@app.route("/api/dashboard/trend")
def trend():
    """近 N 天销售趋势。以事实表中最新的订单日期为基准向前取 N 天。"""
    days = request.args.get("days", 30, type=int)
    days = max(1, min(days, 365))
    rows = query_all("""
        SELECT d.order_date,
               COALESCE(t.total_amount, 0) AS total_amount,
               COALESCE(t.order_count, 0)  AS order_count
        FROM (
            SELECT DATE_ADD(anchor.max_day, INTERVAL -seq.n DAY) AS order_date
            FROM (SELECT MAX(DATE(order_time)) AS max_day FROM fact_order) anchor
            JOIN (
                SELECT a.n + b.n * 10 AS n
                FROM (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3
                      UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6
                      UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) a
                CROSS JOIN (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3
                      UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6
                      UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) b
            ) seq ON seq.n < %s
        ) d
        LEFT JOIN (
            SELECT DATE(order_time) AS order_date,
                   SUM(amount)      AS total_amount,
                   COUNT(*)         AS order_count
            FROM fact_order
            GROUP BY DATE(order_time)
        ) t ON t.order_date = d.order_date
        ORDER BY d.order_date
    """, (days,))
    return success(normalize(rows))


@app.route("/api/dashboard/region")
def region():
    rows = query_all("""
        SELECT s.city,
               SUM(f.amount) AS total_amount,
               COUNT(*)      AS order_count
        FROM fact_order f
        JOIN dim_store s ON f.store_id = s.store_id
        GROUP BY s.city
        ORDER BY total_amount DESC
    """)
    return success(normalize(rows))


@app.route("/api/dashboard/product_top")
def product_top():
    limit = request.args.get("limit", 10, type=int)
    limit = max(1, min(limit, 50))
    rows = query_all("""
        SELECT p.product_name,
               SUM(f.quantity) AS total_quantity,
               SUM(f.amount)   AS total_amount
        FROM fact_order f
        JOIN dim_product p ON f.product_id = p.product_id
        GROUP BY p.product_name
        ORDER BY total_amount DESC
        LIMIT %s
    """, (limit,))
    return success(normalize(rows))


# 更多维度
@app.route("/api/dashboard/store_top")
def store_top():
    """门店销售额 Top N（带城市信息）。"""
    limit = request.args.get("limit", 10, type=int)
    limit = max(1, min(limit, 50))
    rows = query_all("""
        SELECT s.store_name, s.city,
               SUM(f.amount)   AS total_amount,
               SUM(f.quantity) AS total_quantity
        FROM fact_order f
        JOIN dim_store s ON f.store_id = s.store_id
        GROUP BY s.store_id, s.store_name, s.city
        ORDER BY total_amount DESC
        LIMIT %s
    """, (limit,))
    return success(normalize(rows))


@app.route("/api/dashboard/category")
def category():
    """品类销售占比（饼图数据）。"""
    rows = query_all("""
        SELECT p.category,
               SUM(f.amount)   AS total_amount,
               SUM(f.quantity) AS total_quantity
        FROM fact_order f
        JOIN dim_product p ON f.product_id = p.product_id
        GROUP BY p.category
        ORDER BY total_amount DESC
    """)
    return success(normalize(rows))


@app.route("/api/dashboard/hourly")
def hourly():
    """24 小时时段分布，用于分析早晚高峰。"""
    rows = query_all("""
        SELECT HOUR(order_time) AS order_hour,
               COUNT(*)         AS order_count,
               SUM(amount)      AS total_amount
        FROM fact_order
        GROUP BY HOUR(order_time)
        ORDER BY order_hour
    """)
    return success(normalize(rows))


@app.route("/api/dashboard/daytype")
def daytype():
    """工作日 vs 周末对比。"""
    rows = query_all("""
        SELECT CASE WHEN WEEKDAY(order_time) < 5 THEN '工作日' ELSE '周末' END AS day_type,
               SUM(amount)                    AS total_amount,
               COUNT(*)                       AS order_count,
               ROUND(SUM(amount) / COUNT(*), 2) AS avg_order_amount
        FROM fact_order
        GROUP BY day_type
    """)
    return success(normalize(rows))


if __name__ == "__main__":
    app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=Config.FLASK_DEBUG)
