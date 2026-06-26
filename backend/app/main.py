"""MRP II 系统 — FastAPI 主入口"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.core.database import init_db
from app.core.config import UPLOAD_DIR
from app.api import materials, bom, inventory, mps, mrp, purchase, production, crp, inspection, system as system_api


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIST = os.path.join(os.path.dirname(BASE_DIR), "frontend", "dist")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    init_db()
    yield


app = FastAPI(
    title="MRP II 系统",
    description="物料需求计划管理系统 — MPS + BOM + 库存 + MRP引擎 + 采购 + 生产",
    version="1.2.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由（API 路由优先于静态文件）
app.include_router(materials.router)
app.include_router(bom.router)
app.include_router(inventory.router)
app.include_router(mps.router)
app.include_router(mrp.router)
app.include_router(purchase.router)
app.include_router(production.router)
app.include_router(crp.router)
app.include_router(inspection.router)
app.include_router(system_api.router)

# 上传文件静态访问
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# 健康检查 — 必须在 /{full_path:path} 之前注册，否则被 catch-all 截获
@app.get("/api/health")
def health():
    return {"status": "ok"}


# 生产环境：托管前端静态文件
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # 排除 API 路径和文档路径
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi"):
            return {"name": "MRP II 系统", "version": "1.2.0", "docs": "/docs", "status": "running"}
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        index_path = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path, media_type="text/html")
        return {"name": "MRP II 系统", "version": "1.2.0", "docs": "/docs", "status": "running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
