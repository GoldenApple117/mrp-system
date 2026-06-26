"""应用配置"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Railway MySQL 注入的完整连接字符串（优先级最高）
# Railway MySQL 插件导出的是 MYSQL_URL，DATABASE_URL 是备用
RAILWAY_MYSQL_URL = os.getenv("MYSQL_URL", "") or os.getenv("DATABASE_URL", "")

# MySQL 数据库连接（默认） / SQLite 备用
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
    if RAILWAY_MYSQL_URL and RAILWAY_MYSQL_URL.startswith("mysql://"):
        # Railway MySQL 模式：DATABASE_URL => mysql://user:pass@host:port/db
        # 转为 pymysql 驱动的格式
        DATABASE_URL = RAILWAY_MYSQL_URL.replace("mysql://", "mysql+pymysql://", 1) + "?charset=utf8mb4"
    else:
        # 本地 MySQL 模式
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
