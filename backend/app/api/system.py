"""系统管理 API — 初始化/维护"""
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import inspect
import io

from app.core.database import get_db, init_db, SessionLocal, engine, Base

router = APIRouter(prefix="/api/system", tags=["系统管理"])


@router.get("/export")
def export_all_data(db: Session = Depends(get_db)):
    """导出全部数据为JSON"""
    result = {"exported_at": datetime.now().isoformat(), "tables": {}}

    # 遍历所有模型表
    for table_name, table in Base.metadata.tables.items():
        if table_name.startswith("_"):
            continue
        rows = db.execute(table.select()).fetchall()
        columns = [c.name for c in table.columns]
        result["tables"][table_name] = [
            {c: str(getattr(r, c)) if isinstance(getattr(r, c), datetime) else getattr(r, c)
             for c in columns}
            for r in rows
        ]
        result["tables"][table_name + "_count"] = len(rows)

    json_str = json.dumps(result, ensure_ascii=False, default=str)
    return StreamingResponse(
        io.BytesIO(json_str.encode("utf-8")),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=mrp_backup_{}.json".format(
            datetime.now().strftime("%Y%m%d_%H%M%S"))}
    )


@router.post("/import")
def import_all_data(data: dict, db: Session = Depends(get_db)):
    """从JSON恢复全部数据（先清空再导入）"""
    tables = data.get("tables", {})
    if not tables:
        raise HTTPException(status_code=400, detail="无效的数据格式")

    count = 0
    # 先清空所有表（逆序删除，避免外键约束）
    inspector = inspect(engine)
    all_tables = inspector.get_table_names()
    for t in reversed(all_tables):
        if t in tables and t != "_count":
            db.execute(Base.metadata.tables[t].delete())

    # 再写入数据
    for table_name, rows in tables.items():
        if table_name.endswith("_count") or table_name.startswith("_"):
            continue
        if table_name not in Base.metadata.tables:
            continue
        table = Base.metadata.tables[table_name]
        for row in rows:
            db.execute(table.insert().values(**row))
            count += 1

    db.commit()
    return {"success": True, "message": f"已导入 {count} 条记录，共 {len(tables)} 张表"}


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
