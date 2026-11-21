"""数据库连接工具。

注意：原教程把连接工具命名为 db.py，同时又有 db/ 目录存放脚本，
这会导致 Python 导入冲突（同名包覆盖模块）。本仓库将脚本统一放到 scripts/ 目录，
彻底规避这个问题。
"""
import contextlib

import pymysql

from config import Config


def get_conn():
    """返回一个新的数据库连接，游标类型为 DictCursor（结果直接是字典）。"""
    return pymysql.connect(
        host=Config.HOST,
        port=Config.PORT,
        user=Config.USER,
        password=Config.PASSWORD,
        database=Config.DATABASE,
        charset=Config.CHARSET,
        cursorclass=pymysql.cursors.DictCursor,
    )


@contextlib.contextmanager
def connection():
    """上下文管理器：自动提交/回滚并关闭连接，避免异常时连接泄漏。"""
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def query_all(sql, params=None):
    """执行查询并返回字典列表，自动管理连接。"""
    with connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()


def query_one(sql, params=None):
    """执行查询并返回单条字典记录，自动管理连接。"""
    with connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchone()
