"""Alembic 迁移环境配置 — 从 app.core.config 读取数据库连接"""
import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, create_engine
from sqlalchemy import pool

from alembic import context

# 确保 backend/ 在路径中
BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Alembic Config 对象
config = context.config

# 日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 从应用配置获取数据库 URL
from app.core.config import DATABASE_URL
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# 导入所有模型以注册到 Base.metadata
import app.models  # noqa: F401
from app.core.database import Base
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式 — 只生成 SQL 脚本，不连接数据库"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式 — 连接数据库执行迁移"""
    # 使用应用的 engine（兼容 SQLite 的 check_same_thread 设置）
    from app.core.database import engine
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
