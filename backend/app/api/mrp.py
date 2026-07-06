"""MRP运算 API — 核心引擎接口"""
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text
import logging

from app.core.database import get_db
from app.models.material import MaterialMaster
from app.models.bom import BomHeader, BomLine
from app.models.inventory import InventoryRecord
from app.models.mps import MpsEntry
from app.models.order import PurchaseOrder, WorkOrder
from app.models.mrp_run_record import MrpRunRecord
from app.services.mrp_calculator import MrpCalculator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mrp", tags=["MRP运算"])


def run_mrp_logic(db: Session, horizon_days: int = 90, time_fence_days: int = 7) -> dict:
    """
    MRP运算核心逻辑（可被API和定时任务共用）
    
    返回：{"planned_orders": [...], "exceptions": [...]}
    """
    start_time = datetime.now()

    # 1. 读取MPS（仅产品层级物料作为MRP起点）
    mps_entries_raw = db.query(MpsEntry).filter(
        MpsEntry.plan_date >= date.today()
    ).all()

    mps_entries = []
    for e in mps_entries_raw:
        if not e.item:
            logger.warning(f"MPS#{e.id}: 关联物料为空，跳过")
            continue
        if e.item.level_type != "产品":
            continue
        mps_entries.append({
            "item_code": e.item.material_code,
            "plan_date": e.plan_date,
            "quantity": e.quantity,
        })

    if not mps_entries:
        return {
            "success": False,
            "message": "无MPS数据。请先在MPS模块中录入成品计划！",
            "planned_orders": [],
            "exceptions": [],
        }

    # 2. 读取BOM行（仅生效状态的BOM）
    bom_lines_raw = db.query(BomLine).join(BomHeader).filter(
        BomHeader.status.in_(["生效", "草稿"])
    ).all()

    # 3. 读取物料主数据（必须在BOM之前，供N+1优化用）
    materials_raw = db.query(MaterialMaster).filter(MaterialMaster.is_active == True).all()

    # 预加载物料索引，避免 N+1 查询
    material_by_id = {m.id: m for m in materials_raw}
    bom_lines = []
    for bl in bom_lines_raw:
        parent_mat = material_by_id.get(bl.parent_item_id)
        child_mat = material_by_id.get(bl.item_id)
        if parent_mat and child_mat:
            bom_lines.append({
                "parent_code": parent_mat.material_code,
                "child_code": child_mat.material_code,
                "quantity_per": bl.quantity,
                "scrap_rate": bl.scrap_rate,
                "is_substitute": bl.is_substitute,
                "substitute_group": bl.substitute_group or "",
                "substitute_for_id": bl.substitute_for_id,
            })

    # 3. 构建物料主数据字典
    material_masters = [
        {
            "code": m.material_code,
            "level_type": m.level_type,
            "lead_time": m.lead_time,
            "safety_stock": m.safety_stock,
            "lot_size_rule": m.lot_size_rule,
            "lot_size_qty": m.lot_size_qty,
            "min_order_qty": m.min_order_qty,
            "max_order_qty": m.max_order_qty,
            "is_purchased": m.is_purchased,
        }
        for m in materials_raw
    ]

    # 3b. 为产品物料附加工艺路线数据（用于自动计算提前期）
    from app.models.routing import RoutingHeader
    routings = {r.item_id: r for r in db.query(RoutingHeader).filter(RoutingHeader.is_active == True).all()}
    for mm in material_masters:
        if mm["level_type"] == "产品":
            m_id = next((m.id for m in materials_raw if m.material_code == mm["code"]), None)
            route = routings.get(m_id) if m_id else None
            if route and route.operations:
                total_setup = sum(op.setup_time or 0 for op in route.operations)
                total_run = sum(op.run_time_per_unit or 0 for op in route.operations)
                avg_eff = sum(op.work_center.efficiency or 85 for op in route.operations if op.work_center) / max(len(route.operations), 1)
                mm["_routing"] = {
                    "total_setup": total_setup,
                    "total_run": total_run,
                    "efficiency": avg_eff,
                }

    # 4. 读取库存快照
    inventory_records = db.query(InventoryRecord).all()
    inventory_snapshot = {}
    for r in inventory_records:
        code = r.item.material_code if r.item else ""
        if code not in inventory_snapshot:
            inventory_snapshot[code] = {"on_hand": 0, "allocated": 0, "reserved": 0}
        inventory_snapshot[code]["on_hand"] += r.on_hand_qty
        inventory_snapshot[code]["allocated"] += r.allocated_qty
        inventory_snapshot[code]["reserved"] += r.reserved_qty

    # 5. 读取在途/在制（采购单+生产工单）
    scheduled_receipts = {}

    # 采购在途
    po_entries = db.query(PurchaseOrder).filter(
        PurchaseOrder.status.in_(["已下单", "部分收货"])
    ).all()
    for po in po_entries:
        code = po.item.material_code if po.item else ""
        remaining = po.order_qty - (po.received_qty or 0)
        if remaining > 0:
            if code not in scheduled_receipts:
                scheduled_receipts[code] = []
            scheduled_receipts[code].append({
                "date": po.due_date,
                "quantity": remaining,
                "ref_no": po.po_number,
            })

    # 生产在制
    wo_entries = db.query(WorkOrder).filter(
        WorkOrder.status.in_(["已下达", "进行中"])
    ).all()
    for wo in wo_entries:
        code = wo.item.material_code if wo.item else ""
        remaining = wo.plan_qty - (wo.completed_qty or 0)
        if remaining > 0:
            if code not in scheduled_receipts:
                scheduled_receipts[code] = []
            scheduled_receipts[code].append({
                "date": wo.end_date,
                "quantity": remaining,
                "ref_no": wo.wo_number,
            })

    # 6. 构建替代料组索引
    substitute_groups = {}
    sub_lines = [bl for bl in bom_lines if bl.get("is_substitute") and bl.get("substitute_group")]
    for bl in sub_lines:
        grp = bl["substitute_group"]
        child_code = bl["child_code"]
        inv = inventory_snapshot.get(child_code, {"on_hand": 0, "allocated": 0, "reserved": 0})
        if grp not in substitute_groups:
            substitute_groups[grp] = []
        substitute_groups[grp].append({
            "item_code": child_code,
            "on_hand": inv["on_hand"],
            "allocated": inv["allocated"],
            "reserved": inv["reserved"],
        })

    # 7. 执行MRP计算
    calculator = MrpCalculator(db, horizon_days, time_fence_days)
    planned_orders, exceptions = calculator.calculate(
        mps_entries=mps_entries,
        material_masters=material_masters,
        bom_lines=bom_lines,
        inventory_snapshot=inventory_snapshot,
        scheduled_receipts=scheduled_receipts,
        substitute_groups=substitute_groups if substitute_groups else None,
    )

    # 补充物料名称
    code_to_name = {m.material_code: m.material_name for m in materials_raw}
    for po in planned_orders:
        po["material_name"] = code_to_name.get(po["item_code"], "")
    for ex in exceptions:
        ex["material_name"] = code_to_name.get(ex["item_code"], "")

    elapsed = (datetime.now() - start_time).total_seconds()

    # 持久化例外到数据库
    run_id = f"MRP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    from app.models.mrp_exception import MrpException
    for ex in exceptions:
        db.add(MrpException(
            run_id=run_id,
            exception_type=ex.get("type", ""),
            item_code=ex.get("item_code", ""),
            material_name=ex.get("material_name", ""),
            message=ex.get("message", ""),
            severity=ex.get("severity", "INFO"),
        ))
    db.commit()

    return {
        "success": True,
        "message": f"MRP运算完成（仅零件层），耗时 {elapsed:.2f}s",
        "data": {
            "planned_orders": planned_orders,
            "exceptions": exceptions,
            "summary": {
                "total_orders": len(planned_orders),
                "purchase_orders": len([o for o in planned_orders if o["order_type"] == "PURCHASE"]),
                "production_orders": len([o for o in planned_orders if o["order_type"] == "PRODUCTION"]),
                "exceptions_count": len(exceptions),
                "error_count": len([e for e in exceptions if e.get("severity") == "ERROR"]),
                "warning_count": len([e for e in exceptions if e.get("severity") == "WARNING"]),
                "run_time_ms": round(elapsed * 1000, 2),
                "horizon_days": horizon_days,
                "module_layer_skipped": len([m for m in materials_raw if m.level_type == "模块"]),
            },
        },
    }


@router.post("/run")
def run_mrp(data: dict, db: Session = Depends(get_db)):
    """执行MRP运算（API入口）"""
    import traceback
    try:
        horizon_days = max(1, min(data.get("horizon_days", 90), 365))
        time_fence_days = max(0, min(data.get("time_fence_days", 7), 30))
        result = run_mrp_logic(db, horizon_days, time_fence_days)
        if not result.get("success"):
            return result

        # 持久化到数据库，替代全局变量缓存
        mrp_data = result.get("data", {})
        run_id = f"MRP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        record = MrpRunRecord(
            run_id=run_id,
            planned_orders=mrp_data.get("planned_orders", []),
            summary=mrp_data.get("summary", {}),
        )
        db.add(record)
        db.commit()

        # 在返回结果中附带 run_id 供前端消费
        result["data"]["run_id"] = run_id
        return result
    except Exception as e:
        logger.exception("MRP运算失败")
        return {
            "success": False,
            "message": str(e),
            "traceback": traceback.format_exc(),
        }


@router.post("/batch-merge")
def batch_merge_planned_orders(data: dict, db: Session = Depends(get_db)):
    """采购计划批量合并 — 同物料不同日期需求合并/按周合并/按供应商合并

    合并策略选项:
    - weekly: 按周合并（默认）
    - monthly: 按月合并
    - supplier: 按供应商合并
    - none: 不合并（只排序）
    """
    from collections import defaultdict
    from app.models.material import MaterialMaster

    strategy = data.get("strategy", "weekly")
    planned_orders = data.get("planned_orders", [])

    # 如果没有传入，从最近一次MRP结果读取
    if not planned_orders:
        last = db.query(MrpRunRecord).order_by(MrpRunRecord.id.desc()).first()
        if not last:
            return {"success": False, "message": "没有MRP结果，请先运行MRP运算"}
        planned_orders = last.planned_orders

    if not planned_orders:
        return {"success": False, "message": "没有待合并的计划订单"}

    # 只处理采购类（PURCHASE）
    purchase_orders = [o for o in planned_orders if o.get("order_type") == "PURCHASE"]
    if not purchase_orders:
        return {"success": False, "message": "没有采购类计划订单需要合并"}

    # 按物料编码分组
    groups = defaultdict(list)
    for po in purchase_orders:
        groups[po["item_code"]].append(po)

    merged = []
    merge_details = []

    for item_code, orders in groups.items():
        mat = db.query(MaterialMaster).filter(
            MaterialMaster.material_code == item_code
        ).first()
        lot_size = mat.lot_size_qty if mat and mat.lot_size_qty else 0
        min_qty = mat.min_order_qty if mat else 0
        max_qty = mat.max_order_qty if mat else 999999

        if strategy == "weekly":
            # 按ISO周合并
            week_groups = defaultdict(list)
            for o in orders:
                import datetime
                d = datetime.date.fromisoformat(o["required_date"])
                week_key = f"{d.isocalendar()[0]}-W{d.isocalendar()[1]:02d}"
                week_groups[week_key].append(o)
            for wk, wk_orders in sorted(week_groups.items()):
                total_qty = sum(o["quantity"] for o in wk_orders)
                # 应用批量规则
                if lot_size > 0 and total_qty < lot_size:
                    total_qty = lot_size
                if min_qty > 0 and total_qty < min_qty:
                    total_qty = min_qty
                if max_qty > 0 and total_qty > max_qty:
                    total_qty = max_qty
                merged.append({
                    "item_code": item_code,
                    "material_name": o["material_name"],
                    "merged_qty": total_qty,
                    "original_count": len(wk_orders),
                    "week": wk,
                    "earliest_date": min(o["required_date"] for o in wk_orders),
                    "latest_date": max(o["required_date"] for o in wk_orders),
                })

        elif strategy == "supplier":
            # 按供应商 + 日期合并（简单汇总）
            total_qty = sum(o["quantity"] for o in orders)
            if lot_size > 0 and total_qty < lot_size:
                total_qty = lot_size
            merged.append({
                "item_code": item_code,
                "material_name": orders[0]["material_name"],
                "merged_qty": total_qty,
                "original_count": len(orders),
                "earliest_date": min(o["required_date"] for o in orders),
                "latest_date": max(o["required_date"] for o in orders),
            })

        else:  # none
            for o in orders:
                merged.append({
                    "item_code": o["item_code"],
                    "material_name": o["material_name"],
                    "merged_qty": o["quantity"],
                    "original_count": 1,
                    "required_date": o["required_date"],
                })

    return {
        "success": True,
        "strategy": strategy,
        "summary": {
            "original_count": len(purchase_orders),
            "merged_count": len(merged),
            "reduction": len(purchase_orders) - len(merged),
            "reduction_pct": round((len(purchase_orders) - len(merged)) / len(purchase_orders) * 100, 1),
        },
        "merged_orders": merged[:100],  # 最多返回100条
    }


@router.post("/convert-to-orders")
def convert_mrp_to_orders(data: dict = None, db: Session = Depends(get_db)):
    """
    将MRP计划建议转换为实际订单
    优先使用请求中传入的 planned_orders，否则从数据库读取最近一次 MRP 运算结果
    """
    data = data or {}
    planned_orders = data.get("planned_orders", [])

    # 如果前端没传 planned_orders，从数据库读取最近一次结果
    if not planned_orders:
        last_record = db.query(MrpRunRecord).order_by(MrpRunRecord.id.desc()).first()
        if not last_record:
            return {
                "success": False,
                "message": "没有待转换的计划订单，请先运行 MRP 运算",
                "data": {"purchase_orders": 0, "work_orders": 0, "errors": []},
            }
        planned_orders = last_record.planned_orders
    
    created_po = 0
    created_wo = 0
    errors = []

    # 自动缓存模式下限制转换数量（避免超时），前端可传完整列表覆盖
    max_auto = 200
    if not data.get("planned_orders") and len(planned_orders) > max_auto:
        errors.append(f"计划订单过多({len(planned_orders)}条)，自动转换仅处理前{max_auto}条。如需全部转换请通过前端页面操作。")
        planned_orders = planned_orders[:max_auto]

    # 使用时间戳+序号确保编号唯一（seq从数据库实时读取，同一请求内自增）
    from datetime import datetime
    today_str = date.today().strftime("%Y%m%d")
    time_part = datetime.now().strftime("%H%M%S")
    po_base = f"PR-{today_str}-{time_part}"
    wo_base = f"WO-{today_str}-{time_part}"
    po_seq = 0
    wo_seq = 0

    for order in planned_orders:
        try:
            # 查找物料
            mat = db.query(MaterialMaster).filter(
                MaterialMaster.material_code == order["item_code"]
            ).first()
            if not mat:
                errors.append(f"物料 {order['item_code']} 不存在")
                continue

            if order["order_type"] == "PURCHASE":
                po_seq += 1
                # 采购申请，同步物料主数据
                unit_price = mat.reference_unit_price or 0
                order_qty = order["quantity"]
                # 查找物料默认供应商，无则使用第一个供应商（如无则自动创建）
                supplier_id = mat.default_supplier_id if hasattr(mat, 'default_supplier_id') and mat.default_supplier_id else None
                if not supplier_id:
                    from app.models.supplier import Supplier
                    first_sup = db.query(Supplier).first()
                    if not first_sup:
                        first_sup = Supplier(
                            supplier_code="DEF-SUP",
                            supplier_name="默认供应商",
                            contact_person="系统自动创建",
                            contact_phone="00000000",
                        )
                        db.add(first_sup)
                        db.flush()
                    supplier_id = first_sup.id
                po = PurchaseOrder(
                    po_number=f"{po_base}-{po_seq:04d}",
                    supplier_id=supplier_id,
                    item_id=mat.id,
                    order_qty=order_qty,
                    unit_price=unit_price,
                    total_amount=round(unit_price * order_qty, 2),
                    due_date=date.fromisoformat(order["required_date"]),
                    status="申请",
                    source_type="MRP建议",
                    priority=order.get("level", 0),
                    brand=mat.specification.split(" / ")[-1] if " / " in (mat.specification or "") else (mat.specification or ""),
                    submitter=mat.reference_submitter or "",
                    supplier_link=mat.reference_link or "",
                )
                db.add(po)
                created_po += 1

            elif order["order_type"] == "PRODUCTION":
                wo_seq += 1
                # 自动关联工艺路线和工作中心
                from app.models.routing import RoutingHeader
                routing = db.query(RoutingHeader).filter(
                    RoutingHeader.item_id == mat.id, RoutingHeader.is_active == True
                ).first()
                wc_id = routing.operations[0].work_center_id if routing and routing.operations else None
                
                wo = WorkOrder(
                    wo_number=f"{wo_base}-{wo_seq:04d}",
                    item_id=mat.id,
                    plan_qty=order["quantity"],
                    start_date=date.fromisoformat(order["release_date"]),
                    end_date=date.fromisoformat(order["required_date"]),
                    status="待下达",
                    source_type="MRP建议",
                    priority=order.get("level", 0),
                    routing_id=routing.id if routing else None,
                    work_center_id=wc_id,
                )
                db.add(wo)
                created_wo += 1

        except Exception as e:
            errors.append(f"{order['item_code']}: {str(e)}")

    db.commit()

    return {
        "success": True,
        "message": f"采购申请 {created_po} 笔，生产工单 {created_wo} 笔",
        "data": {
            "purchase_orders": created_po,
            "work_orders": created_wo,
            "errors": errors,
        },
    }


@router.post("/fix-column-types")
def fix_column_types(db: Session = Depends(get_db)):
    """
    [临时修复] 将 mrp_run_record 的 JSON 列从 TEXT 改为 LONGTEXT
    仅在紧急修复时调用，后续将通过正常部署流程解决
    """
    results = {}
    for col in ["planned_orders_json", "summary_json"]:
        try:
            db.execute(text(
                f"ALTER TABLE mrp_run_record MODIFY COLUMN {col} LONGTEXT"
            ))
            db.commit()
            results[col] = "LONGTEXT ✅"
        except Exception as e:
            db.rollback()
            results[col] = f"失败: {e}"
    return {"success": True, "results": results}
