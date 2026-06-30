"""MRP运算 API — 核心引擎接口"""
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.material import MaterialMaster
from app.models.bom import BomHeader, BomLine
from app.models.inventory import InventoryRecord
from app.models.mps import MpsEntry
from app.models.order import PurchaseOrder, WorkOrder
from app.services.mrp_calculator import MrpCalculator

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

    mps_entries = [
        {
            "item_code": e.item.material_code,
            "plan_date": e.plan_date,
            "quantity": e.quantity,
        }
        for e in mps_entries_raw
        if e.item and e.item.level_type == "产品"
    ]

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

    bom_lines = []
    for bl in bom_lines_raw:
        parent_mat = db.query(MaterialMaster).filter(MaterialMaster.id == bl.parent_item_id).first()
        child_mat = db.query(MaterialMaster).filter(MaterialMaster.id == bl.item_id).first()
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

    # 3. 读取物料主数据
    materials_raw = db.query(MaterialMaster).filter(MaterialMaster.is_active == True).all()
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
    horizon_days = data.get("horizon_days", 90)
    time_fence_days = data.get("time_fence_days", 7)
    result = run_mrp_logic(db, horizon_days, time_fence_days)
    if not result.get("success"):
        return result
    return result


@router.post("/convert-to-orders")
def convert_mrp_to_orders(data: dict, db: Session = Depends(get_db)):
    """
    将MRP计划建议转换为实际订单
    采购建议 → 采购申请(PR)
    生产建议 → 工单
    """
    planned_orders = data.get("planned_orders", [])
    created_po = 0
    created_wo = 0
    errors = []

    # 计算当天已生成的PR/WO数量，避免编号冲突
    today_str = date.today().strftime("%Y%m%d")
    last_pr = db.query(PurchaseOrder).filter(
        PurchaseOrder.po_number.like(f"PR-{today_str}-%")
    ).order_by(PurchaseOrder.po_number.desc()).first()
    last_wo = db.query(WorkOrder).filter(
        WorkOrder.wo_number.like(f"WO-{today_str}-%")
    ).order_by(WorkOrder.wo_number.desc()).first()

    po_seq = int(last_pr.po_number.split("-")[-1]) + 1 if last_pr else 1
    wo_seq = int(last_wo.wo_number.split("-")[-1]) + 1 if last_wo else 1

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
                # 创建采购申请
                po = PurchaseOrder(
                    po_number=f"PR-{today_str}-{po_seq:04d}",
                    supplier_id=1,
                    item_id=mat.id,
                    order_qty=order["quantity"],
                    due_date=date.fromisoformat(order["required_date"]),
                    status="申请",
                    source_type="MRP建议",
                    priority=order.get("level", 0),
                )
                db.add(po)
                po_seq += 1
                created_po += 1

            elif order["order_type"] == "PRODUCTION":
                wo = WorkOrder(
                    wo_number=f"WO-{today_str}-{wo_seq:04d}",
                    item_id=mat.id,
                    plan_qty=order["quantity"],
                    start_date=date.fromisoformat(order["release_date"]),
                    end_date=date.fromisoformat(order["required_date"]),
                    status="待下达",
                    source_type="MRP建议",
                    priority=order.get("level", 0),
                )
                db.add(wo)
                wo_seq += 1
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
