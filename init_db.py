"""Railway 启动前数据库初始化脚本 — 独立运行，不依赖后端启动"""
import sys
import os
import time

# 确保 backend/ 目录在 Python 路径中
BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
sys.path.insert(0, BACKEND_DIR)

from sqlalchemy import create_engine


def wait_for_mysql(database_url: str, max_attempts: int = 30) -> bool:
    """等待 MySQL 就绪"""
    if "mysql" not in database_url:
        return True
    print("Waiting for MySQL to become available...")
    for i in range(max_attempts):
        try:
            engine = create_engine(database_url, connect_args={"connect_timeout": 3})
            conn = engine.connect()
            conn.close()
            print(f"MySQL connection OK (attempt {i+1})")
            return True
        except Exception as e:
            print(f"  Attempt {i+1}/{max_attempts}: {e}")
            time.sleep(2)
    print("ERROR: MySQL not available after max attempts")
    return False


def main():
    import app.core.config as cfg
    print(f"DB_BACKEND={cfg.DB_BACKEND}")
    print(f"DATABASE_URL={cfg.DATABASE_URL[:50]}...")

    # Step 1: Wait for MySQL
    if not wait_for_mysql(cfg.DATABASE_URL):
        sys.exit(1)

    # Step 2: Import all models so they register with Base.metadata
    print("Loading data models...")
    import app.models  # noqa: F401 — registers models with SQLAlchemy Base

    # Step 3: Init tables
    print("Initializing database tables...")
    from app.core.database import init_db, SessionLocal
    init_db()
    print("Tables initialized")

    # Step 3: Seed demo data if empty
    db = SessionLocal()
    try:
        from app.models.material import MaterialMaster
        count = db.query(MaterialMaster).count()
        if count == 0:
            print("Empty database, seeding demo data...")
            # 直接调用 seed_data — 它也在 backend/ 下
            import importlib
            seed = importlib.import_module("seed_data")
            seed.seed_demo_data()
        else:
            print(f"Database already has {count} materials, skipping seed")
    finally:
        db.close()

    print("Database init complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
