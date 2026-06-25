"""应用配置"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# MySQL 数据库连接（默认）  /  SQLite 备用
MYSQL_CONFIG = {
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "root"),
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "database": os.getenv("MYSQL_DATABASE", "mrp_system"),
    "charset": "utf8mb4",
}

SQLITE_PATH = os.path.join(BASE_DIR, "mrp_system_data.db")

# 默认使用 MySQL，可通过环境变量切换
DB_BACKEND = os.getenv("DB_BACKEND", "mysql")

if DB_BACKEND == "mysql":
    DATABASE_URL = (
        f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}"
        f"@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}"
        f"?charset={MYSQL_CONFIG['charset']}"
    )
else:
    DATABASE_URL = f"sqlite:///{SQLITE_PATH}"

UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MRP_DEFAULT_HORIZON_DAYS = 90
MRP_DEFAULT_TIME_FENCE_DAYS = 7
MRP_MAX_BOM_LEVELS = 10
