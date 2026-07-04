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


@router.get("/health/pip")
def health_check_pip():
    """健康检查：列出已安装的关键包"""
    import importlib, sys
    pkgs = ["openpyxl", "pandas", "fastapi", "sqlalchemy", "pymysql", "pydantic"]
    result = {"python": sys.version}
    for p in pkgs:
        try:
            m = importlib.import_module(p)
            result[p] = getattr(m, "__version__", "installed")
        except ImportError:
            result[p] = "NOT_INSTALLED"
    return result

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


# ====== Excel 导出 ======
def _make_excel_response(rows: list, filename: str):
    """生成 Excel 文件并返回 StreamingResponse"""
    import traceback, sys
    try:
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = filename[:31]
        if rows:
            headers = list(rows[0].keys())
            ws.append(headers)
            for row in rows:
                ws.append([str(row.get(h, "")) for h in headers])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        from urllib.parse import quote
        safe_name = quote(f"{filename}.xlsx")
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{safe_name}"},
        )
    except Exception as e:
        err_msg = f"Excel export error (type={type(e).__name__}): {str(e)}\n"
        err_msg += f"Python: {sys.version}\n"
        err_msg += f"Traceback: {traceback.format_exc()}"
        return {"error": err_msg, "python_version": sys.version}


@router.get("/export-excel/materials")
def export_materials_excel(db: Session = Depends(get_db)):
    """导出物料表为 Excel"""
    from app.models.material import MaterialMaster
    rows = db.query(MaterialMaster).all()
    data = [{"物料编码": r.material_code, "物料名称": r.material_name,
             "物料类型": r.material_type, "层级": r.level_type,
             "单位": r.unit, "提前期(天)": r.lead_time,
             "安全库存": r.safety_stock, "批量规则": r.lot_size_rule,
             "是否外购": "是" if r.is_purchased else "否",
             "损耗率(%)": r.scrap_rate} for r in rows]
    return _make_excel_response(data, "物料主数据")


@router.get("/export-excel/inventory")
def export_inventory_excel(db: Session = Depends(get_db)):
    """导出库存表为 Excel"""
    from app.models.inventory import InventoryRecord
    rows = db.query(InventoryRecord).all()
    data = [{"物料编码": r.item.material_code if r.item else "",
             "物料名称": r.item.material_name if r.item else "",
             "仓库": r.warehouse.warehouse_name if r.warehouse else "",
             "库位": r.location_code, "现有库存": r.on_hand_qty,
             "已分配": r.allocated_qty, "已预留": r.reserved_qty,
             "在途": r.on_order_qty, "在制": r.on_production_qty,
             "可用量": r.on_hand_qty - r.allocated_qty - r.reserved_qty if hasattr(r, 'allocated_qty') else r.on_hand_qty}
            for r in rows]
    return _make_excel_response(data, "库存数据")


@router.get("/export-excel/work-orders")
def export_work_orders_excel(db: Session = Depends(get_db)):
    """导出工单表为 Excel"""
    from app.models.order import WorkOrder
    rows = db.query(WorkOrder).all()
    data = [{"工单号": r.wo_number, "物料编码": r.item.material_code if r.item else "",
             "物料名称": r.item.material_name if r.item else "",
             "计划产量": r.plan_qty, "完成数": r.completed_qty,
             "不合格": getattr(r, 'rejected_qty', 0),
             "工时(h)": getattr(r, 'labor_hours', 0),
             "开始": r.start_date.isoformat() if r.start_date else "",
             "完成": r.end_date.isoformat() if r.end_date else "",
             "状态": r.status,
             "工作中心": r.work_center.center_name if r.work_center else "",
             "来源": r.source_type} for r in rows]
    return _make_excel_response(data, "生产工单")


@router.get("/export-excel/bom")
def export_bom_excel(db: Session = Depends(get_db)):
    """导出BOM表为 Excel"""
    from app.models.bom import BomLine, BomHeader
    from app.models.material import MaterialMaster
    lines = db.query(BomLine).all()
    data = []
    for l in lines:
        parent = db.query(MaterialMaster).filter(MaterialMaster.id == l.parent_item_id).first()
        child = db.query(MaterialMaster).filter(MaterialMaster.id == l.item_id).first()
        bom_header = db.query(BomHeader).filter(BomHeader.id == l.bom_header_id).first()
        data.append({
            "BOM编号": bom_header.bom_code if bom_header else "",
            "父物料编码": parent.material_code if parent else "",
            "父物料名称": parent.material_name if parent else "",
            "子物料编码": child.material_code if child else "",
            "子物料名称": child.material_name if child else "",
            "单位用量": l.quantity, "位号": l.position,
            "层级": l.level, "损耗率(%)": l.scrap_rate,
        })
    return _make_excel_response(data, "BOM清单")


# ====== BOM 完整性校验 ======
@router.get("/bom-check")
def check_bom_integrity(db: Session = Depends(get_db)):
    """BOM完整性校验：循环引用、缺失物料、孤儿物料"""
    from app.models.bom import BomLine, BomHeader
    from app.models.material import MaterialMaster
    from app.services.bom_exploder import BomExploder

    issues = []

    # 1. 所有 BOM 行中的物料必须存在于 material_master
    all_materials = {m.id: m for m in db.query(MaterialMaster).all()}
    all_lines = db.query(BomLine).all()
    for l in all_lines:
        if l.parent_item_id and l.parent_item_id not in all_materials:
            issues.append({"type": "缺失父物料", "detail": f"BOM行#{l.id}: parent_item_id={l.parent_item_id} 不存在"})
        if l.item_id not in all_materials:
            issues.append({"type": "缺失子物料", "detail": f"BOM行#{l.id}: item_id={l.item_id} 不存在"})

    # 2. 计算高低码，检查循环引用
    try:
        from app.services.mrp_calculator import MrpCalculator
        calc = MrpCalculator(db_session=db)
        llc_map = calc._compute_llc(db, list(all_materials.keys()))
    except Exception as e:
        issues.append({"type": "循环引用", "detail": str(e)[:200]})

    # 3. 检查是否有物料没有关联 BOM（零件级、无子物料的是正常的）
    items_with_children = set()
    for l in all_lines:
        if l.parent_item_id:
            items_with_children.add(l.parent_item_id)
    
    orphan_products = []
    for mid, mat in all_materials.items():
        if mat.level_type in ("产品", "模块") and mid not in items_with_children:
            orphan_products.append(mat.material_code)

    if orphan_products:
        issues.append({"type": "产品/模块无BOM", "detail": f"无BOM: {', '.join(orphan_products[:10])}"})

    # 4. 统计
    return {
        "total_issues": len(issues),
        "issues": issues,
        "summary": {
            "total_materials": len(all_materials),
            "total_bom_lines": len(all_lines),
            "products_with_bom": len([h for h in db.query(BomHeader).all()]),
        },
    }


# ====== Dashboard 增强 ======
@router.get("/dashboard/alerts")
def dashboard_alerts(db: Session = Depends(get_db)):
    """Dashboard告警卡片：安全库存预警、逾期工单、呆滞料"""
    from app.models.material import MaterialMaster
    from app.models.inventory import InventoryRecord
    from app.models.order import WorkOrder

    alerts = []

    # 1. 安全库存预警（库存低于安全库存）
    mats = db.query(MaterialMaster).all()
    low_stock = []
    for mat in mats:
        if not mat.safety_stock or mat.safety_stock <= 0:
            continue
        inv = db.query(InventoryRecord).filter(InventoryRecord.item_id == mat.id).first()
        on_hand = inv.on_hand_qty if inv else 0
        if on_hand < mat.safety_stock:
            low_stock.append({
                "material_code": mat.material_code,
                "material_name": mat.material_name,
                "on_hand": on_hand,
                "safety_stock": mat.safety_stock,
                "gap": mat.safety_stock - on_hand,
            })
    if low_stock:
        alerts.append({"type": "warning", "title": "安全库存预警",
                        "count": len(low_stock),
                        "detail": f"{len(low_stock)}种物料低于安全库存",
                        "items": low_stock[:5]})

    # 2. 逾期工单
    today = datetime.now().date()
    overdue = db.query(WorkOrder).filter(
        WorkOrder.end_date < today,
        WorkOrder.status.in_(["已下达", "进行中"])
    ).all()
    if overdue:
        alerts.append({"type": "danger", "title": "逾期工单",
                        "count": len(overdue),
                        "detail": f"{len(overdue)}个工单已超期",
                        "items": [{"wo": o.wo_number, "due": o.end_date.isoformat()} for o in overdue[:5]]})

    # 3. 呆滞料预警（30天无变动且库存>0）
    import datetime as _dt
    cutoff = _dt.datetime.now() - _dt.timedelta(days=30)
    slow_moving = db.query(InventoryRecord).filter(
        InventoryRecord.on_hand_qty > 0,
        InventoryRecord.last_count_date < cutoff if hasattr(InventoryRecord, 'last_count_date') and InventoryRecord.last_count_date else True
    ).limit(5).all()
    if slow_moving:
        alerts.append({"type": "info", "title": "呆滞料预警",
                        "count": len(slow_moving),
                        "detail": "长期未变动物料",
                        "items": [{"code": s.item.material_code if s.item else "", "qty": s.on_hand_qty} for s in slow_moving]})

    # 4. 今日待办
    from app.models.bom import BomHeader
    pending = db.query(WorkOrder).filter(
        WorkOrder.status.in_(["待下达", "已下达"])
    ).count()

    return {
        "alerts": alerts,
        "pending_orders": pending,
        "total_materials": len(mats),
        "total_bom": db.query(BomHeader).count(),
    }
