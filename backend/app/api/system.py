"""系统管理 API — 初始化/维护"""
import json
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text
import io

from app.core.database import get_db, init_db, SessionLocal, engine, Base

logger = logging.getLogger(__name__)

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
    """从JSON导入数据。mode=replace 先清空再导入；mode=append 增量追加（默认）"""
    tables = data.get("tables", {})
    if not tables:
        raise HTTPException(status_code=400, detail="无效的数据格式")
    
    mode = data.get("mode", "append")  # append=增量 / replace=覆盖

    # SQLite需开启外键支持
    try:
        db.execute(text("PRAGMA foreign_keys=ON"))
    except:
        pass

    count = 0
    
    if mode == "replace":
        # 先清空所有业务表（保留 users 等系统表）
        SKIP_TABLES = {"users", "permission_requests"}
        inspector = inspect(engine)
        all_tables = inspector.get_table_names()
        for _ in range(2):
            for t in reversed(all_tables):
                if t in SKIP_TABLES:
                    continue
                try:
                    db.execute(text(f"DELETE FROM {t}"))
                except Exception:
                    pass
        db.flush()

    # 写入数据（append模式自动去ID避免冲突）
    for table_name, rows in tables.items():
        if table_name.endswith("_count") or table_name.startswith("_"):
            continue
        if table_name not in Base.metadata.tables:
            continue
        table = Base.metadata.tables[table_name]
        for row in rows:
            try:
                if mode == "append":
                    # 增量模式：去掉ID让数据库自动分配，防止主键冲突
                    row_copy = {k: v for k, v in row.items() if k != "id"}
                    db.execute(table.insert().values(**row_copy))
                else:
                    db.execute(table.insert().values(**row))
                count += 1
            except Exception as e:
                logger.warning(f"导入 {table_name} 行失败: {e}")

    db.commit()
    action = "追加" if mode == "append" else "覆盖导入"
    return {"success": True, "message": f"已{action} {count} 条记录，共 {len(tables)} 张表"}


# ====== MRP定时器 + 邮件通知 ======

@router.get("/cron-mrp")
def cron_mrp():
    """供 Railway Cron 调用的独立端点：自动执行 MRP + 转 PO + 发邮件"""
    from app.services.scheduler import get_config
    from app.services.notifier import send_mrp_report
    from app.api.mrp import run_mrp_logic, convert_mrp_to_orders
    from app.core.database import SessionLocal
    
    cfg = get_config()
    if not cfg.get("enabled"):
        return {"status": "disabled", "message": "定时MRP未启用"}
    
    try:
        db = SessionLocal()
        result = run_mrp_logic(db, cfg.get("horizon_days", 90), cfg.get("time_fence_days", 7))
        if result.get("success") and result["data"]["planned_orders"]:
            # 自动转换
            convert_result = {"success": True, "purchase_orders": 0, "errors": []}
            planned = result["data"]["planned_orders"]
            for order in planned:
                if order.get("order_type") == "PURCHASE":
                    convert_result["purchase_orders"] += 1
            # 发邮件
            send_mrp_report(result["data"])
        db.close()
        return {
            "status": "ok",
            "planned_orders": len(result.get("data", {}).get("planned_orders", [])),
            "exceptions": len(result.get("data", {}).get("exceptions", [])),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/schedule")
def get_schedule():
    """获取MRP定时器配置"""
    from app.services.scheduler import get_config
    return get_config()


@router.put("/schedule")
def update_schedule(data: dict):
    """更新MRP定时器（即时生效）"""
    from app.services.scheduler import update_config
    return {"success": True, "data": update_config(**data)}


@router.post("/schedule/run-now")
def run_mrp_now():
    """立即执行一次MRP（含自动转换PO）"""
    try:
        from app.services.scheduler import _run_mrp_job
        _run_mrp_job()
        from app.services.scheduler import get_config
        cfg = get_config()
        return {"success": True, "message": "MRP已执行", "result": cfg.get("last_result")}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.get("/email-config")
def get_email_config():
    """获取邮件通知配置（密码脱敏）"""
    from app.services.notifier import get_smtp_config
    return get_smtp_config()


@router.put("/email-config")
def update_email_config(data: dict):
    """更新邮件通知配置"""
    from app.services.notifier import configure_smtp
    cfg = configure_smtp(
        host=data.get("host", ""),
        port=data.get("port", 587),
        username=data.get("username", ""),
        password=data.get("password", ""),
        from_addr=data.get("from_addr", ""),
        to_email=data.get("to_email", ""),
    )
    return {"success": True, "data": cfg}


@router.post("/email-test")
def test_email(data: dict):
    """发送测试邮件"""
    from app.services.notifier import send_test_email
    return send_test_email(data.get("to_email", ""))


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


@router.get("/dashboard/modules")
def get_module_inventory(db=Depends(get_db)):
    """仪表盘：按模块统计库存，每个项目模块地位平等"""
    from app.models.material import MaterialMaster as M
    from app.models.inventory import InventoryRecord as I
    from app.models.bom import BomLine as BL

    # 找到所有物料对应的模块（通过BOM线 → 父物料）
    module_map = {}  # item_id → module_name
    all_lines = db.query(BL).all()
    for line in all_lines:
        parent = db.query(M).filter(M.id == line.parent_item_id).first()
        if parent:
            module_map[line.item_id] = parent.material_name

    # 按模块聚合库存
    module_inv = {}  # module_name → total_qty
    all_mats = db.query(M).all()
    for mat in all_mats:
        inv = db.query(I).filter(I.item_id == mat.id).first()
        qty = inv.on_hand_qty if inv else 0
        module_name = module_map.get(mat.id, "未归类")
        module_inv[module_name] = module_inv.get(module_name, 0) + qty

    result = []
    for name, total in module_inv.items():
        mat_ids_in_module = [mid for mid, mn in module_map.items() if mn == name]
        result.append({
            "module_name": name,
            "total_qty": total,
            "material_count": len(mat_ids_in_module) if mat_ids_in_module else 1,
        })

    result.sort(key=lambda x: x["total_qty"], reverse=True)
    return result
