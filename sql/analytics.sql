-- ============================================================
-- 常用聚合分析 SQL 合集
-- 对应 Flask 各个 /api/dashboard/* 接口，可直接复制到 MySQL 客户端验证。
-- 面试时可重点讲：星型模型 JOIN、时间维度聚合、复合索引命中。
-- ============================================================
USE cha_analysis;

-- 1) 总览指标：门店数 / 订单数 / 总销售额 / 客单价
SELECT
  COUNT(DISTINCT store_id)                  AS store_count,
  COUNT(*)                                  AS order_count,
  SUM(amount)                               AS total_amount,
  ROUND(SUM(amount) / COUNT(*), 2)          AS avg_order_amount,
  SUM(quantity)                             AS total_cups
FROM fact_order;

-- 2) 近 N 天销售趋势（N 由应用层参数传入，此处以 30 为例）
SELECT
  DATE(order_time) AS order_date,
  SUM(amount)      AS total_amount,
  COUNT(*)         AS order_count
FROM fact_order
WHERE order_time >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY DATE(order_time)
ORDER BY order_date;

-- 3) 城市销售分布（事实表 JOIN 门店维度表）
SELECT
  s.city,
  SUM(f.amount) AS total_amount,
  COUNT(*)      AS order_count
FROM fact_order f
JOIN dim_store s ON f.store_id = s.store_id
GROUP BY s.city
ORDER BY total_amount DESC;

-- 4) 品类销量 / 销售额排行（事实表 JOIN 产品维度表）
SELECT
  p.category,
  SUM(f.quantity) AS total_quantity,
  SUM(f.amount)   AS total_amount
FROM fact_order f
JOIN dim_product p ON f.product_id = p.product_id
GROUP BY p.category
ORDER BY total_amount DESC;

-- 5) 单品销售额 Top 10
SELECT
  p.product_name,
  SUM(f.quantity) AS total_quantity,
  SUM(f.amount)   AS total_amount
FROM fact_order f
JOIN dim_product p ON f.product_id = p.product_id
GROUP BY p.product_name
ORDER BY total_amount DESC
LIMIT 10;

-- 6) 【增强】门店销售额 Top 10（带城市信息）
SELECT
  s.store_name,
  s.city,
  SUM(f.amount) AS total_amount,
  SUM(f.quantity) AS total_quantity
FROM fact_order f
JOIN dim_store s ON f.store_id = s.store_id
GROUP BY s.store_id, s.store_name, s.city
ORDER BY total_amount DESC
LIMIT 10;

-- 7) 【增强】工作日 vs 周末对比（WEEKDAY: 0=周一 … 6=周日）
SELECT
  CASE WHEN WEEKDAY(order_time) < 5 THEN '工作日' ELSE '周末' END AS day_type,
  SUM(amount)              AS total_amount,
  COUNT(*)                 AS order_count,
  ROUND(SUM(amount) / COUNT(*), 2) AS avg_order_amount
FROM fact_order
GROUP BY day_type;

-- 8) 【增强】24 小时时段分布（分析早晚高峰）
SELECT
  HOUR(order_time) AS order_hour,
  COUNT(*)         AS order_count,
  SUM(amount)      AS total_amount
FROM fact_order
GROUP BY HOUR(order_time)
ORDER BY order_hour;
