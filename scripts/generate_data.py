"""生成模拟订单数据 data/order_data.csv。

相比原教程的改进：
  1) 门店固定属于某座城市（原教程每单随机城市，同一家店会「瞬移」到不同城市，不合业务逻辑）；
  2) 产品固定分类与单价，并写入 CSV，维度信息可复用；
  3) 数据日期锚定到「最近 180 天」而不是写死 2024 年，保证趋势图开箱即用；
  4) 订单时间集中在早晚高峰，更贴近真实茶饮消费规律。

仅用于学习与面试展示，不代表任何品牌真实经营数据。
"""
import os
import random
from datetime import datetime, timedelta

import pandas as pd

random.seed(42)

# 门店 -> 固定城市/商圈（一家店只属于一座城市）
STORE_CITIES = [
    ("成都", "春熙路商圈"), ("成都", "太古里商圈"), ("成都", "高新商圈"),
    ("成都", "锦里商圈"), ("成都", "天府广场商圈"),
    ("武汉", "楚河汉街商圈"), ("武汉", "光谷商圈"), ("武汉", "江汉路商圈"),
    ("武汉", "武昌商圈"), ("武汉", "汉口商圈"),
    ("南京", "新街口商圈"), ("南京", "夫子庙商圈"), ("南京", "河西商圈"),
    ("南京", "仙林商圈"), ("南京", "鼓楼商圈"),
    ("杭州", "湖滨商圈"), ("杭州", "钱江新城商圈"), ("杭州", "武林商圈"),
    ("杭州", "滨江商圈"), ("杭州", "西溪商圈"),
]
STORES = [(f"门店{i + 1:02d}店", city, region)
          for i, (city, region) in enumerate(STORE_CITIES)]

# 产品 -> 固定分类/单价
PRODUCTS = [
    ("伯牙绝弦", "原叶鲜奶茶", 18),
    ("万里木兰", "原叶鲜奶茶", 20),
    ("桂馥兰香", "原叶鲜奶茶", 21),
    ("花田乌龙", "原叶鲜奶茶", 19),
    ("青青糯山", "原叶鲜奶茶", 16),
    ("寻香遇桂", "鲜果茶", 22),
    ("桃香乌龙", "鲜果茶", 20),
    ("栀子绿茶", "纯茶", 15),
    ("茉莉毛尖", "纯茶", 15),
]

# 下单小时权重：早高峰(9-11)、午间(13-14)、晚高峰(17-20) 更高
HOUR_WEIGHTS = {
    9: 5, 10: 6, 11: 5, 12: 6, 13: 7, 14: 5, 15: 4,
    16: 5, 17: 8, 18: 9, 19: 9, 20: 7, 21: 3,
}
HOURS = list(HOUR_WEIGHTS)
HOUR_CDF = []
_total = sum(HOUR_WEIGHTS.values())
_acc = 0
for h in HOURS:
    _acc += HOUR_WEIGHTS[h]
    HOUR_CDF.append(_acc / _total)


def pick_hour():
    r = random.random()
    for hour, cdf in zip(HOURS, HOUR_CDF):
        if r <= cdf:
            return hour
    return HOURS[-1]


def main():
    rows = []
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=179)

    for day in range(180):
        current = start_date + timedelta(days=day)
        is_weekend = current.weekday() >= 5
        for store_name, city, region in STORES:
            # 周末订单量上浮，模拟商圈客流规律
            base = random.randint(20, 60) * (2 if is_weekend else 1)
            for _ in range(base):
                product_name, category, unit_price = random.choice(PRODUCTS)
                quantity = random.choices([1, 2, 3], weights=[7, 2, 1])[0]
                rows.append({
                    "order_id": f"{current:%Y%m%d}{random.randint(10000, 99999):05d}",
                    "order_time": datetime.combine(
                        current,
                        datetime.min.time().replace(hour=pick_hour(), minute=random.randint(0, 59)),
                    ),
                    "store_name": store_name,
                    "city": city,
                    "region": region,
                    "product_name": product_name,
                    "category": category,
                    "unit_price": unit_price,
                    "quantity": quantity,
                    "amount": round(unit_price * quantity, 2),
                })

    df = pd.DataFrame(rows)
    # 极小概率的订单号碰撞去重，避免主键冲突
    df = df.drop_duplicates(subset="order_id")
    output = os.path.join(os.path.dirname(__file__), "..", "data", "order_data.csv")
    output = os.path.abspath(output)
    df.to_csv(output, index=False, encoding="utf-8-sig")
    print(f"生成 {len(df)} 条订单数据 -> {output}")
    print(df.head(3).to_string(index=False))


if __name__ == "__main__":
    main()
