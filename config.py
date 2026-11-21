"""项目配置：全部通过环境变量读取，支持 python-dotenv 加载 .env 文件。"""
import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # 未安装 python-dotenv 时退化为纯环境变量读取
    pass


class Config:
    """数据库与 Flask 服务配置。生产环境请务必用环境变量注入密码。"""

    HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
    PORT = int(os.getenv("MYSQL_PORT", "3306"))
    USER = os.getenv("MYSQL_USER", "root")
    PASSWORD = os.getenv("MYSQL_PASSWORD", "your_password")
    DATABASE = os.getenv("MYSQL_DATABASE", "cha_analysis")
    CHARSET = "utf8mb4"

    FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "true").lower() in ("1", "true", "yes")
