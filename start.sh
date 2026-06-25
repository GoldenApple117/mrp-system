#!/bin/bash
# Railway 启动脚本：启动后端（前端在构建阶段已编译）

echo "=== Starting backend ==="
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
