# ===== Stage 1: Build frontend =====
FROM node:20-alpine AS frontend

WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ===== Stage 2: Python backend =====
FROM python:3.11-slim

WORKDIR /app

# 复制前端构建产物
COPY --from=frontend /build/frontend/dist ./frontend/dist

# 复制后端代码
COPY backend/ ./backend/

# 安装后端依赖
RUN pip install --no-cache-dir -r backend/requirements.txt

# 健康检查
EXPOSE 8000

# 复制启动脚本和初始化脚本
COPY start.sh init_db.py /app/
RUN sed -i 's/\r$//' /app/start.sh && chmod +x /app/start.sh

# 启动
CMD ["bash", "/app/start.sh"]
