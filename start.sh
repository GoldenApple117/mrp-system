#!/bin/bash
# Railway 启动脚本
set -e

echo "=== MRP II System Starting ==="

# 初始化数据库（含 MySQL 等待逻辑）
python /app/init_db.py || echo "WARNING: DB init failed, starting anyway..."

# 启动后端（必须在 backend/ 目录下，uvicorn 才能找到 app 包）
cd /app/backend
echo "=== Starting backend on port ${PORT:-8000} ==="
exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
