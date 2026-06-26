#!/bin/bash
# Railway 启动脚本：等待 MySQL 就绪 + 初始化数据库 + 启动后端
set -e

cd backend

# ====== 等待 MySQL 就绪（最多重试 30 次，间隔 2 秒） ======
echo "=== Waiting for MySQL to be ready ==="
for i in $(seq 1 30); do
    python -c "
import os
from app.core.config import DB_BACKEND, DATABASE_URL
print(f'DB_BACKEND={DB_BACKEND}')
try:
    from sqlalchemy import create_engine
    engine = create_engine(DATABASE_URL, connect_args={'connect_timeout': 3})
    conn = engine.connect()
    conn.close()
    print('MySQL connection OK')
    exit(0)
except Exception as e:
    print(f'Attempt $i: {e}')
    exit(1)
" 2>/dev/null && break

    echo "  Retry $i/30 - MySQL not ready yet, waiting 2s..."
    sleep 2
done

echo "=== Initializing database ==="
python -c "
from app.core.config import DB_BACKEND
print(f'DB_BACKEND={DB_BACKEND}')
from app.core.database import init_db
from app.models.material import MaterialMaster
from app.core.database import SessionLocal
init_db()
db = SessionLocal()
count = db.query(MaterialMaster).count()
db.close()
if count == 0:
    print('Empty database, seeding demo data...')
    import seed_data
    seed_data.seed_demo_data()
else:
    print(f'Database already has {count} materials, skipping seed')
" || echo "WARNING: DB init/seed failed, starting anyway..."

echo "=== Starting backend ==="
exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
