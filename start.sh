#!/bin/bash
# Railway 启动脚本
set -e

echo "=== MRP II System Starting (v1.4.0) ==="

# 验证前端构建产物
FRONTEND_DIST="/app/frontend/dist"
if [ -d "$FRONTEND_DIST" ]; then
    echo "✅ 前端文件目录: $FRONTEND_DIST"
    ls -la "$FRONTEND_DIST/"
    if [ -f "$FRONTEND_DIST/index.html" ]; then
        echo "✅ index.html 存在"
    else
        echo "⚠️ index.html 不存在于 $FRONTEND_DIST"
    fi
else
    echo "⚠️ 前端文件目录不存在: $FRONTEND_DIST"
    echo "   文件列表: $(ls -la /app/frontend/ 2>/dev/null || echo '无')"
fi

# 初始化数据库
python /app/init_db.py || echo "WARNING: DB init failed, starting anyway..."

# 启动后端（必须在 backend/ 目录下，uvicorn 才能找到 app 包）
cd /app/backend
echo "=== 启动后端 on port ${PORT:-8000} ==="
exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
