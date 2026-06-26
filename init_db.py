"""Railway 启动前数据库初始化脚本"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

import time
from sqlalchemy import create_engine

def main():
    from app.core.config import DB_BACKEND, DATABASE_URL
    print(f"DB_BACKEND={DB_BACKEND}")

    # Step 1: Wait for MySQL
    if "mysql" in DATABASE_URL:
        print("Waiting for MySQL to become available...")
        for i in range(30):
            try:
                engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 3})
                conn = engine.connect()
                conn.close()
                print(f"MySQL connection OK (attempt {i+1})")
                break
            except Exception as e:
                print(f"  Attempt {i+1}/30: {e}")
                time.sleep(2)
        else:
            print("ERROR: MySQL not available after 30 attempts")
            sys.exit(1)

    # Step 2: Init tables
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
            import seed_data
            seed_data.seed_demo_data()
        else:
            print(f"Database already has {count} materials, skipping seed")
    finally:
        db.close()

    print("Database init complete")
    return 0

if __name__ == "__main__":
    sys.exit(main())
