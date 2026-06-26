"""系统管理 API — 初始化/维护"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db, init_db, SessionLocal

router = APIRouter(prefix="/api/system", tags=["系统管理"])


@router.post("/seed-demo")
def seed_demo_api():
    """一键初始化全部演示数据"""
    try:
        init_db()
        db = SessionLocal()

        # 导入 seed_data 模块并执行（它会自行管理 session）
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        import seed_data
        seed_data.seed_demo_data()

        return {"success": True, "message": "✅ 演示数据初始化完成！所有物料、BOM、工作中心、工艺路线、库存、MPS数据已就绪。"}
    except Exception as e:
        return {"success": False, "message": f"❌ 初始化失败: {str(e)}"}
