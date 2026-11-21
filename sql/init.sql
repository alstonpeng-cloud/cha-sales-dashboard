-- 建库建表：门店/产品两张维度表，订单事实表
-- 统一用 utf8mb4，避免中文乱码

CREATE DATABASE IF NOT EXISTS cha_analysis
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE cha_analysis;

-- 门店维度表
DROP TABLE IF EXISTS fact_order;
DROP TABLE IF EXISTS dim_store;
DROP TABLE IF EXISTS dim_product;

CREATE TABLE dim_store (
  store_id    INT PRIMARY KEY AUTO_INCREMENT COMMENT '门店ID',
  store_name  VARCHAR(64)  NOT NULL COMMENT '门店名称',
  city        VARCHAR(32)  NOT NULL COMMENT '所属城市',
  region      VARCHAR(32)  DEFAULT '' COMMENT '区域/商圈',
  open_date   DATE         DEFAULT NULL COMMENT '开业日期',
  status      TINYINT      NOT NULL DEFAULT 1 COMMENT '状态：1营业，0关闭',
  UNIQUE KEY uk_store_name (store_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='门店维度表';

-- 产品维度表
CREATE TABLE dim_product (
  product_id   INT PRIMARY KEY AUTO_INCREMENT COMMENT '产品ID',
  product_name VARCHAR(64)  NOT NULL COMMENT '产品名称',
  category     VARCHAR(32)  DEFAULT '' COMMENT '产品分类（鲜奶茶/果茶/纯茶…）',
  unit_price   DECIMAL(10,2) NOT NULL COMMENT '单价（元）',
  UNIQUE KEY uk_product_name (product_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='产品维度表';

-- 订单事实表：一行是一条订单明细（订单 × 单品）
CREATE TABLE fact_order (
  order_id    VARCHAR(64)  PRIMARY KEY COMMENT '订单号',
  order_time  DATETIME     NOT NULL COMMENT '下单时间',
  store_id    INT          NOT NULL COMMENT '门店ID',
  product_id  INT          NOT NULL COMMENT '产品ID',
  quantity    INT          NOT NULL COMMENT '购买数量（杯）',
  amount      DECIMAL(10,2) NOT NULL COMMENT '订单金额（元）',
  KEY idx_order_time (order_time),
  KEY idx_store_id (store_id),
  KEY idx_product_id (product_id),
  KEY idx_store_time (store_id, order_time),
  CONSTRAINT fk_order_store   FOREIGN KEY (store_id)   REFERENCES dim_store(store_id),
  CONSTRAINT fk_order_product FOREIGN KEY (product_id) REFERENCES dim_product(product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单事实表';
