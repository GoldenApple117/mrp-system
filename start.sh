#!/bin/bash
# Railway 启动脚本：构建前端 + 启动后端

echo "=== Building frontend ==="
cd frontend
npm install
npm run build
cd ..

echo "=== Starting backend ==="
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
