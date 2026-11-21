"""将 CSV 数据导入 MySQL：维护维度表 + 批量写入事实表。

相比原教程的改进：
  1) 用 executemany 批量插入事实表，速度远快于逐行 execute；
  2) 门店/产品维度信息（城市、分类）来自 CSV，不再只写名称；
  3) 支持重复运行（先清空事实表再导入），避免主键冲突；
  4) 使用 with 连接上下文，异常自动回滚，不留半截数据。
"""
import os
import sys

import pandas as pd
import pymysql

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import Config  # noqa: E402
from db import connection  # noqa: E402

BATCH_SIZE = 5000


def load_csv():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "order_data.csv"))
    if not os.path.exists(path):
        raise FileNotFoundError(f"未找到数据文件：{path}，请先运行 python scripts/generate_data.py")
    return pd.read_csv(path)


def upsert_dimensions(cursor, df):
    """维护门店、产品两张维度表，返回 name -> id 的映射。"""
    store_map = {}
    for store_name, city, region in df[["store_name", "city", "region"]].drop_duplicates().itertuples(index=False):
        cursor.execute(
            "INSERT INTO dim_store(store_name, city, region) VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE city=VALUES(city), region=VALUES(region)",
            (store_name, city, region),
        )
        cursor.execute("SELECT store_id FROM dim_store WHERE store_name=%s", (store_name,))
        store_map[store_name] = cursor.fetchone()[0]

    product_map = {}
    for product_name, category, unit_price in df[
        ["product_name", "category", "unit_price"]
    ].drop_duplicates().itertuples(index=False):
        cursor.execute(
            "INSERT INTO dim_product(product_name, category, unit_price) VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE category=VALUES(category), unit_price=VALUES(unit_price)",
            (product_name, category, float(unit_price)),
        )
        cursor.execute("SELECT product_id FROM dim_product WHERE product_name=%s", (product_name,))
        product_map[product_name] = cursor.fetchone()[0]

    return store_map, product_map


def main():
    df = load_csv()
    print(f"读取到 {len(df)} 条订单记录，开始导入...")

    with connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE fact_order")
            store_map, product_map = upsert_dimensions(cursor, df)

            batch = []
            for row in df.itertuples(index=False):
                batch.append((
                    row.order_id,
                    row.order_time,
                    store_map[row.store_name],
                    product_map[row.product_name],
                    int(row.quantity),
                    float(row.amount),
                ))
                if len(batch) >= BATCH_SIZE:
                    cursor.executemany(
                        "INSERT INTO fact_order"
                        "(order_id, order_time, store_id, product_id, quantity, amount) "
                        "VALUES (%s, %s, %s, %s, %s, %s)",
                        batch,
                    )
                    conn.commit()
                    batch.clear()
                    print(f"已导入 {cursor.rowcount} 条（批次提交）")

            if batch:
                cursor.executemany(
                    "INSERT INTO fact_order"
                    "(order_id, order_time, store_id, product_id, quantity, amount) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    batch,
                )

    print(f"数据导入完成：门店 {len(store_map)} 家，产品 {len(product_map)} 款。")


if __name__ == "__main__":
    main()
