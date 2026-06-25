#!/bin/bash
# Railway 启动脚本：初始化数据库 + 启动后端
set -e

cd backend

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
"

echo "=== Starting backend ==="
python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
