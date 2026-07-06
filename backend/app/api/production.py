"""生产管理 API — 工单 + 工作中心 + 工艺路线 + 报工"""
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.order import WorkOrder, WorkOrderMaterial, WorkOrderReport
from app.models.routing import WorkCenter, RoutingHeader, RoutingOperation
from app.models.material import MaterialMaster
from app.models.inventory import InventoryRecord, InventoryTransaction, Warehouse
from app.models.bom import BomLine, BomHeader

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/production", tags=["生产管理"])


@router.get("/orders")
def list_work_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """生产工单列表"""
    query = db.query(WorkOrder)

    if status:
        query = query.filter(WorkOrder.status == status)
    if keyword:
        query = query.filter(WorkOrder.wo_number.ilike(f"%{keyword}%"))

    total = query.count()
    orders = query.order_by(WorkOrder.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "items": [
            {
                "id": o.id, "wo_number": o.wo_number,
                "item_id": o.item_id,
                "material_code": o.item.material_code if o.item else "",
                "material_name": o.item.material_name if o.item else "",
                "unit": o.item.unit if o.item else "",
                "plan_qty": o.plan_qty, "completed_qty": o.completed_qty,
                "rejected_qty": getattr(o, 'rejected_qty', 0),
                "labor_hours": getattr(o, 'labor_hours', 0),
                "start_date": o.start_date.isoformat() if o.start_date else None,
                "end_date": o.end_date.isoformat() if o.end_date else None,
                "actual_start": o.actual_start.isoformat() if o.actual_start else None,
                "actual_end": o.actual_end.isoformat() if o.actual_end else None,
                "status": o.status, "work_center_id": o.work_center_id,
                "work_center_name": o.work_center.center_name if o.work_center else "",
                "priority": o.priority, "source_type": o.source_type,
                "remark": o.remark,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in orders
        ],
        "total": total, "page": page, "page_size": page_size,
    }


@router.post("/orders")
def create_work_order(data: dict, db: Session = Depends(get_db)):
    """创建生产工单"""
    if "wo_number" not in data or not data.get("wo_number"):
        today_str = date.today().strftime("%Y%m%d")
        last_wo = db.query(WorkOrder).filter(
            WorkOrder.wo_number.like(f"WO-{today_str}-%")
        ).order_by(WorkOrder.wo_number.desc()).first()
        if last_wo:
            last_seq = int(last_wo.wo_number.split("-")[-1])
            seq = last_seq + 1
        else:
            seq = 1
        wo_number = f"WO-{today_str}-{seq:04d}"
    else:
        wo_number = data["wo_number"]

    wo = WorkOrder(
        wo_number=wo_number,
        item_id=data["item_id"],
        plan_qty=data["plan_qty"],
        start_date=date.fromisoformat(data["start_date"]) if isinstance(data["start_date"], str) else data["start_date"],
        end_date=date.fromisoformat(data["end_date"]) if isinstance(data["end_date"], str) else data["end_date"],
        status=data.get("status", "待下达"),
        work_center_id=data.get("work_center_id"),
        routing_id=data.get("routing_id"),
        priority=data.get("priority", 0),
        source_type=data.get("source_type", "手动"),
        remark=data.get("remark", ""),
    )
    db.add(wo)
    db.commit()
    return {"success": True, "data": {"id": wo.id, "wo_number": wo.wo_number}}


@router.put("/orders/{order_id}")
def update_work_order(order_id: int, data: dict, db: Session = Depends(get_db)):
    """更新工单（含路由/工作中心/数量等）"""
    wo = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="工单不存在")
    if wo.status not in ("待下达", "已下达"):
        raise HTTPException(status_code=400, detail=f"当前状态({wo.status})不允许修改")

    if "routing_id" in data:
        wo.routing_id = data["routing_id"]
    if "work_center_id" in data:
        wo.work_center_id = data["work_center_id"]
    if "plan_qty" in data and data["plan_qty"] is not None:
        wo.plan_qty = data["plan_qty"]
    if "start_date" in data:
        wo.start_date = date.fromisoformat(data["start_date"]) if isinstance(data["start_date"], str) else data["start_date"]
    if "end_date" in data:
        wo.end_date = date.fromisoformat(data["end_date"]) if isinstance(data["end_date"], str) else data["end_date"]
    if "priority" in data:
        wo.priority = data["priority"]
    if "remark" in data:
        wo.remark = data["remark"]

    db.commit()
    return {"success": True, "message": "工单已更新"}


@router.put("/orders/{order_id}/status")
def update_wo_status(order_id: int, data: dict, db: Session = Depends(get_db)):
    """更新工单状态"""
    wo = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="工单不存在")

    wo.status = data["status"]
    if "completed_qty" in data and data["completed_qty"] is not None:
        wo.completed_qty = data["completed_qty"]
    if wo.status == "已完成" and wo.completed_qty == 0:
        wo.completed_qty = wo.plan_qty

    db.commit()
    return {"success": True, "message": f"状态更新为: {wo.status}"}


@router.post("/orders/{order_id}/start")
def start_work_order(order_id: int, db: Session = Depends(get_db)):
    """开工 — 缺料检查 + 自动领料 + 记录实际开工时间"""
    wo = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="工单不存在")
    if wo.status != "已下达":
        raise HTTPException(status_code=400, detail=f"当前状态({wo.status})不能开工，需先下达")

    # 0. 缺料检查
    bom_lines = _get_bom_lines(db, wo.item_id)
    shortages = []
    if bom_lines:
        for bl in bom_lines:
            req = bl.quantity * wo.plan_qty
            inv = db.query(InventoryRecord).filter(InventoryRecord.item_id == bl.item_id).first()
            on_hand = inv.on_hand_qty if inv else 0
            if on_hand < req:
                shortages.append({
                    "material_code": bl.item.material_code if bl.item else "",
                    "material_name": bl.item.material_name if bl.item else "",
                    "required": req,
                    "on_hand": on_hand,
                    "shortage": req - on_hand,
                })

    if shortages:
        return {
            "success": False,
            "message": f"缺料{len(shortages)}种，无法开工",
            "shortages": shortages[:20],
        }

    now = datetime.now()
    wo.status = "进行中"
    wo.actual_start = now

    # 根据 BOM 自动生成物料需求并扣减库存
    if bom_lines:
        for bl in bom_lines:
            required = bl.quantity * wo.plan_qty
            wom = db.query(WorkOrderMaterial).filter(
                WorkOrderMaterial.work_order_id == wo.id,
                WorkOrderMaterial.item_id == bl.item_id,
            ).first()
            if not wom:
                wom = WorkOrderMaterial(
                    work_order_id=wo.id,
                    item_id=bl.item_id,
                    required_qty=required,
                    bom_line_id=bl.id,
                )
                db.add(wom)

            # 扣减库存
            inv = db.query(InventoryRecord).filter(
                InventoryRecord.item_id == bl.item_id,
            ).first()
            if inv and inv.on_hand_qty >= required:
                inv.on_hand_qty -= required
                wom.issued_qty = required
                db.add(InventoryTransaction(
                    item_id=bl.item_id,
                    warehouse_id=inv.warehouse_id,
                    transaction_type="生产发料",
                    quantity=-required,
                    reference_no=wo.wo_number,
                    operator="系统",
                    remark=f"工单{wo.wo_number}自动领料",
                ))

    # 更新在制量
    _update_on_production_qty(db, wo.item_id, wo.plan_qty)

    db.commit()
    issued_count = len(wo.materials) if hasattr(wo, 'materials') else 0
    return {
        "success": True,
        "message": f"工单已开工，{issued_count}种物料已发料",
        "actual_start": now.isoformat(),
    }


@router.post("/orders/{order_id}/report")
def report_progress(order_id: int, data: dict, db: Session = Depends(get_db)):
    """工单报工 — 记录每次报工详情，累计到工单"""
    wo = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="工单不存在")
    if wo.status not in ("进行中",):
        raise HTTPException(status_code=400, detail=f"当前状态({wo.status})不能报工")

    completed = float(data.get("completed_qty", 0))
    rejected = float(data.get("rejected_qty", 0))
    labor = float(data.get("labor_hours", 0))
    operator = data.get("operator", "")
    remark = data.get("remark", "")

    if completed <= 0 and rejected <= 0 and labor <= 0:
        raise HTTPException(status_code=422, detail="请至少填报一项数据")

    # 累计到工单
    if completed > 0:
        wo.completed_qty = (wo.completed_qty or 0) + completed
    if rejected > 0:
        wo.rejected_qty = (wo.rejected_qty or 0) + rejected
    if labor > 0:
        wo.labor_hours = (wo.labor_hours or 0) + labor

    # 保存报工记录（独立记录，保留历史）
    report = WorkOrderReport(
        work_order_id=wo.id,
        wo_number=wo.wo_number,
        completed_qty=completed,
        rejected_qty=rejected,
        labor_hours=labor,
        operator=operator or "系统",
        remark=remark or "",
    )
    db.add(report)

    db.commit()

    return {
        "success": True,
        "message": f"报工完成：良品+{completed}，不合格{rejected}，工时{labor}h",
        "data": {
            "report_id": report.id,
            "completed_qty": wo.completed_qty,
            "rejected_qty": wo.rejected_qty or 0,
            "labor_hours": wo.labor_hours or 0,
            "total_reports": db.query(WorkOrderReport).filter(
                WorkOrderReport.work_order_id == wo.id).count(),
        },
    }


@router.get("/orders/{order_id}/reports")
def get_order_reports(order_id: int, db: Session = Depends(get_db)):
    """工单报工历史"""
    reports = db.query(WorkOrderReport).filter(
        WorkOrderReport.work_order_id == order_id
    ).order_by(WorkOrderReport.report_time.desc()).all()
    return {
        "items": [
            {
                "id": r.id,
                "report_time": r.report_time.isoformat() if r.report_time else None,
                "completed_qty": r.completed_qty,
                "rejected_qty": r.rejected_qty,
                "labor_hours": r.labor_hours,
                "operator": r.operator or "",
                "remark": r.remark or "",
            }
            for r in reports
        ],
        "total": len(reports),
    }


@router.get("/orders/{order_id}/readiness")
def check_order_readiness(order_id: int, db: Session = Depends(get_db)):
    """检查工单完工就绪状态 — 物料是否全部领完、报工是否完成"""
    wo = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="工单不存在")

    checks = []

    # 检查物料
    materials = db.query(WorkOrderMaterial).filter(
        WorkOrderMaterial.work_order_id == wo.id
    ).all()
    if materials:
        unfinished_mats = [m for m in materials if (m.issued_qty or 0) < m.required_qty]
        if unfinished_mats:
            checks.append({
                "name": "物料领料",
                "status": "WARNING",
                "detail": f"{len(unfinished_mats)}/{len(materials)} 种物料未领完",
                "items": [
                    {"code": m.item.material_code if m.item else "", "name": m.item.material_name if m.item else "",
                     "required": m.required_qty, "issued": m.issued_qty or 0}
                    for m in unfinished_mats[:5]
                ],
            })
        else:
            checks.append({"name": "物料领料", "status": "OK", "detail": "全部领完"})
    else:
        checks.append({"name": "物料领料", "status": "OK", "detail": "无物料需求"})

    # 检查报工
    total_reports = db.query(WorkOrderReport).filter(
        WorkOrderReport.work_order_id == wo.id
    ).count()
    if wo.completed_qty and wo.completed_qty >= wo.plan_qty:
        checks.append({"name": "报工进度", "status": "OK",
                       "detail": f"已完成 {wo.completed_qty}/{wo.plan_qty}，报工{total_reports}次"})
    else:
        checks.append({"name": "报工进度", "status": "INFO",
                       "detail": f"已完成 {wo.completed_qty or 0}/{wo.plan_qty}，报工{total_reports}次"})

    # 综合判断
    can_complete = all(c["status"] == "OK" for c in checks)
    completion_blockers = [c for c in checks if c["status"] != "OK"]

    return {
        "wo_number": wo.wo_number,
        "status": wo.status,
        "can_complete": can_complete,
        "checks": checks,
        "summary": {
            "plan_qty": wo.plan_qty,
            "completed_qty": wo.completed_qty or 0,
            "rejected_qty": wo.rejected_qty or 0,
            "labor_hours": wo.labor_hours or 0,
            "total_reports": total_reports,
            "material_count": len(materials),
        },
    }


@router.post("/orders/{order_id}/complete")
def complete_work_order(order_id: int, data: dict = None, db: Session = Depends(get_db)):
    """完工入库 — 良品入库 + 标记完成时间
    可选传 force=true 跳过就绪检查
    """
    wo = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="工单不存在")
    if wo.status != "进行中":
        raise HTTPException(status_code=400, detail=f"当前状态({wo.status})不能完工")

    data = data or {}
    force = data.get("force", False)

    # 就绪检查（除非 force）
    if not force:
        materials = db.query(WorkOrderMaterial).filter(
            WorkOrderMaterial.work_order_id == wo.id
        ).all()
        unfinished_mats = [m for m in materials if (m.issued_qty or 0) < m.required_qty]
        if unfinished_mats:
            return {
                "success": False,
                "message": f"有 {len(unfinished_mats)} 种物料未领完，请先领料或传 force=true 强制完工",
                "unfinished_materials": [
                    {"code": m.item.material_code if m.item else "",
                     "name": m.item.material_name if m.item else "",
                     "required": m.required_qty, "issued": m.issued_qty or 0}
                    for m in unfinished_mats[:10]
                ],
            }

    now = datetime.now()
    wo.status = "已完成"
    wo.actual_end = now
    if wo.completed_qty <= 0:
        wo.completed_qty = wo.plan_qty
    rejected = wo.rejected_qty or 0
    good_qty = wo.completed_qty - rejected
    if good_qty > 0:
        # 找到该物料的库存记录或默认仓库
        inv = db.query(InventoryRecord).filter(
            InventoryRecord.item_id == wo.item_id,
        ).first()
        wh_id = inv.warehouse_id if inv else 1

        # 增加库存
        if inv:
            inv.on_hand_qty += good_qty
        else:
            db.add(InventoryRecord(
                item_id=wo.item_id,
                warehouse_id=wh_id,
                on_hand_qty=good_qty,
            ))

        # 记录库存流水
        db.add(InventoryTransaction(
            item_id=wo.item_id,
            warehouse_id=wh_id,
            transaction_type="生产入库",
            quantity=good_qty,
            reference_no=wo.wo_number,
            operator="系统",
            remark=f"工单{wo.wo_number}完工入库，良品{good_qty}，不合格{rejected}",
        ))

    # 减少在制量
    _update_on_production_qty(db, wo.item_id, -wo.plan_qty)

    db.commit()
    return {
        "success": True,
        "message": f"完工入库完成：良品{good_qty}，不合格{rejected}，工时{wo.labor_hours or 0}h",
        "actual_end": now.isoformat(),
    }


@router.get("/orders/{order_id}/materials")
def get_order_materials(order_id: int, db: Session = Depends(get_db)):
    """查看工单物料需求及发料情况"""
    woms = db.query(WorkOrderMaterial).filter(
        WorkOrderMaterial.work_order_id == order_id
    ).all()
    return {
        "items": [
            {
                "id": w.id,
                "material_code": w.item.material_code if w.item else "",
                "material_name": w.item.material_name if w.item else "",
                "unit": w.item.unit if w.item else "",
                "required_qty": w.required_qty,
                "issued_qty": w.issued_qty,
            }
            for w in woms
        ]
    }


@router.post("/orders/{order_id}/issue-material")
def issue_material_to_work_order(order_id: int, data: dict, db: Session = Depends(get_db)):
    """工单领料 — 按物料逐项发料，自动扣减库存"""
    wo = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="工单不存在")
    if wo.status not in ("已下达", "进行中"):
        raise HTTPException(status_code=400, detail=f"当前状态({wo.status})不能领料")

    item_id = data.get("item_id")
    issue_qty = float(data.get("issue_qty", 0))
    operator = data.get("operator", "系统")

    if not item_id or issue_qty <= 0:
        raise HTTPException(status_code=422, detail="请提供物料ID (item_id) 和发料数量 (issue_qty>0)")

    # 查找工单物料记录
    wom = db.query(WorkOrderMaterial).filter(
        WorkOrderMaterial.work_order_id == wo.id,
        WorkOrderMaterial.item_id == item_id,
    ).first()
    if not wom:
        raise HTTPException(status_code=404, detail="该物料不在工单需求清单中")

    # 检查是否超发
    remaining = wom.required_qty - (wom.issued_qty or 0)
    if issue_qty > remaining:
        return {"success": False, "message": f"超出发料上限：可发 {remaining}，请求 {issue_qty}"}

    # 检查库存
    inv = db.query(InventoryRecord).filter(
        InventoryRecord.item_id == item_id,
    ).first()
    on_hand = inv.on_hand_qty if inv else 0
    if on_hand < issue_qty:
        return {"success": False, "message": f"库存不足：需要 {issue_qty}，可用 {on_hand}"}

    # 扣减库存
    inv.on_hand_qty -= issue_qty
    wom.issued_qty = (wom.issued_qty or 0) + issue_qty

    # 记录物料单价与总成本
    unit_price = (wom.item.reference_unit_price if wom.item else 0) or 0
    if wom.unit_cost == 0 and unit_price > 0:
        wom.unit_cost = unit_price
    wom.total_cost = (wom.issued_qty or 0) * (wom.unit_cost or 0)

    # 记录流水
    db.add(InventoryTransaction(
        item_id=item_id,
        warehouse_id=inv.warehouse_id,
        transaction_type="生产发料",
        quantity=-issue_qty,
        reference_no=wo.wo_number,
        operator=operator,
        remark=f"工单{wo.wo_number}领料 {issue_qty}，物料{wom.item.material_name if wom.item else ''}",
    ))

    db.commit()

    mat_name = wom.item.material_name if wom.item else ""
    return {
        "success": True,
        "message": f"已发料 {issue_qty} ({mat_name})，已发总计 {wom.issued_qty}/{wom.required_qty}",
        "data": {
            "item_id": item_id,
            "material_name": mat_name,
            "issue_qty": issue_qty,
            "issued_qty": wom.issued_qty,
            "required_qty": wom.required_qty,
            "remaining": wom.required_qty - wom.issued_qty,
            "on_hand_after": inv.on_hand_qty,
        },
    }


@router.post("/orders/{order_id}/return-material")
def return_material_from_work_order(order_id: int, data: dict, db: Session = Depends(get_db)):
    """工单退料 — 未用完的物料退回仓库"""
    wo = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="工单不存在")
    if wo.status not in ("进行中", "已完成"):
        raise HTTPException(status_code=400, detail=f"当前状态({wo.status})不能退料")

    item_id = data.get("item_id")
    return_qty = float(data.get("return_qty", 0))
    operator = data.get("operator", "系统")

    if not item_id or return_qty <= 0:
        raise HTTPException(status_code=422, detail="请提供物料ID (item_id) 和退料数量 (return_qty>0)")

    wom = db.query(WorkOrderMaterial).filter(
        WorkOrderMaterial.work_order_id == wo.id,
        WorkOrderMaterial.item_id == item_id,
    ).first()
    if not wom:
        raise HTTPException(status_code=404, detail="该物料不在工单需求清单中")

    # 检查退料数量不超过已发数量
    if return_qty > (wom.issued_qty or 0):
        return {"success": False, "message": f"超出已发数量：已发 {wom.issued_qty}，请求退 {return_qty}"}

    # 增加库存
    inv = db.query(InventoryRecord).filter(
        InventoryRecord.item_id == item_id,
    ).first()
    if inv:
        inv.on_hand_qty += return_qty
    else:
        # 没有库存记录则创建一条
        from app.models.inventory import Warehouse
        wh = db.query(Warehouse).filter(Warehouse.warehouse_code == "WH01").first()
        if not wh:
            wh = Warehouse(warehouse_code="WH01", warehouse_name="主仓库")
            db.add(wh)
            db.flush()
        inv = InventoryRecord(item_id=item_id, warehouse_id=wh.id, on_hand_qty=return_qty)
        db.add(inv)

    wom.issued_qty = (wom.issued_qty or 0) - return_qty

    # 记录流水
    db.add(InventoryTransaction(
        item_id=item_id,
        warehouse_id=inv.warehouse_id,
        transaction_type="生产退料",
        quantity=return_qty,
        reference_no=wo.wo_number,
        operator=operator,
        remark=f"工单{wo.wo_number}退料 {return_qty}，物料{wom.item.material_name if wom.item else ''}",
    ))

    db.commit()

    mat_name = wom.item.material_name if wom.item else ""
    return {
        "success": True,
        "message": f"已退料 {return_qty} ({mat_name})，剩余已发 {wom.issued_qty}",
        "data": {
            "item_id": item_id,
            "material_name": mat_name,
            "return_qty": return_qty,
            "issued_qty": wom.issued_qty,
            "required_qty": wom.required_qty,
            "on_hand_after": inv.on_hand_qty,
        },
    }


@router.delete("/orders/{order_id}")
def delete_work_order(order_id: int, db: Session = Depends(get_db)):
    """删除工单"""
    wo = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if wo and wo.status == "待下达":
        db.delete(wo)
        db.commit()
        return {"success": True}
    raise HTTPException(status_code=400, detail="只能删除'待下达'状态的工单")


# ====== 内部辅助函数 ======

def _get_bom_lines(db: Session, item_id: int):
    """获取某物料 BOM 的全部零件层子物料（穿透模块层）"""
    from app.models.material import MaterialMaster
    all_parts = []
    visited = set()
    
    def expand(parent_id, multiplier=1.0):
        direct = db.query(BomLine).filter(BomLine.parent_item_id == parent_id).all()
        for bl in direct:
            child = db.query(MaterialMaster).filter(MaterialMaster.id == bl.item_id).first()
            qty = bl.quantity * multiplier
            
            if child and child.level_type == "模块":
                # 模块层：穿透继续展开
                expand(bl.item_id, qty)
            else:
                # 零件层或产品层：收集
                if (parent_id, bl.item_id) not in visited:
                    visited.add((parent_id, bl.item_id))
                    bl.quantity = qty  # 累积用量
                    all_parts.append(bl)
    
    expand(item_id)
    return all_parts


def _update_on_production_qty(db: Session, item_id: int, delta: float):
    """更新在制量"""
    inv = db.query(InventoryRecord).filter(
        InventoryRecord.item_id == item_id
    ).first()
    if inv:
        inv.on_production_qty = (inv.on_production_qty or 0) + delta


# ====== 工作中心 ======
@router.get("/work-centers")
def list_work_centers(db: Session = Depends(get_db)):
    """工作中心列表"""
    wcs = db.query(WorkCenter).filter(WorkCenter.is_active == True).all()
    return {
        "items": [
            {
                "id": w.id, "center_code": w.center_code, "center_name": w.center_name,
                "capacity_per_day": w.capacity_per_day, "efficiency": w.efficiency,
                "machines_count": w.machines_count, "workers_count": w.workers_count,
            }
            for w in wcs
        ]
    }


@router.post("/work-centers")
def create_work_center(data: dict, db: Session = Depends(get_db)):
    """创建工作中心"""
    wc = WorkCenter(**data)
    db.add(wc)
    db.commit()
    return {"success": True, "data": {"id": wc.id}}


# ====== 工艺路线 ======
@router.get("/routings")
def list_routings(db: Session = Depends(get_db)):
    """工艺路线列表"""
    routings = db.query(RoutingHeader).filter(RoutingHeader.is_active == True).all()
    return {
        "items": [
            {
                "id": r.id, "routing_code": r.routing_code,
                "item_id": r.item_id,
                "material_code": r.item.material_code if r.item else "",
                "material_name": r.item.material_name if r.item else "",
                "operations_count": len(r.operations),
            }
            for r in routings
        ]
    }


@router.get("/routings/{routing_id}")
def get_routing_detail(routing_id: int, db: Session = Depends(get_db)):
    """工艺路线详情（含工序）"""
    routing = db.query(RoutingHeader).filter(RoutingHeader.id == routing_id).first()
    if not routing:
        raise HTTPException(status_code=404, detail="工艺路线不存在")

    return {
        "header": {
            "id": routing.id, "routing_code": routing.routing_code,
            "item_id": routing.item_id,
            "material_code": routing.item.material_code if routing.item else "",
        },
        "operations": [
            {
                "id": op.id, "seq_no": op.seq_no, "operation_name": op.operation_name,
                "work_center_id": op.work_center_id,
                "work_center_name": op.work_center.center_name if op.work_center else "",
                "setup_time": op.setup_time, "run_time_per_unit": op.run_time_per_unit,
                "queue_time": op.queue_time,
            }
            for op in sorted(routing.operations, key=lambda o: o.seq_no)
        ],
    }


@router.post("/routings")
def create_routing(data: dict, db: Session = Depends(get_db)):
    """创建工艺路线"""
    routing = RoutingHeader(
        item_id=data["item_id"],
        routing_code=data["routing_code"],
    )
    db.add(routing)
    db.flush()

    for i, op_data in enumerate(data.get("operations", [])):
        op = RoutingOperation(
            routing_header_id=routing.id,
            seq_no=op_data.get("seq_no", i + 1),
            work_center_id=op_data["work_center_id"],
            operation_name=op_data["operation_name"],
            setup_time=op_data.get("setup_time", 0),
            run_time_per_unit=op_data.get("run_time_per_unit", 0),
            queue_time=op_data.get("queue_time", 0),
        )
        db.add(op)

    db.commit()
    return {"success": True, "data": {"id": routing.id}}


# ====== 成本配置 ======

# 默认人工费率（元/小时）
_DEFAULT_LABOR_RATE = 45.0
_labor_rate: float = _DEFAULT_LABOR_RATE


@router.get("/cost-rates")
def get_cost_rates():
    """获取成本费率"""
    return {
        "labor_rate_per_hour": _labor_rate,
        "unit": "元/小时",
    }


@router.put("/cost-rates")
def update_cost_rates(data: dict):
    """更新成本费率"""
    global _labor_rate
    if "labor_rate_per_hour" in data:
        _labor_rate = max(0, float(data["labor_rate_per_hour"]))
    return {"success": True, "message": f"人工费率已更新: {_labor_rate}元/小时"}


# ====== 工单成本核算 ======

@router.get("/orders/{order_id}/cost")
def get_order_cost(order_id: int, db: Session = Depends(get_db)):
    """工单成本核算 — 物料成本 + 人工成本 + 对比标准成本"""
    wo = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="工单不存在")

    # 1. 物料成本（实际领料 * 单价）
    materials = db.query(WorkOrderMaterial).filter(
        WorkOrderMaterial.work_order_id == wo.id
    ).all()

    material_items = []
    actual_material_cost = 0.0
    standard_material_cost = 0.0

    for m in materials:
        unit_price = m.unit_cost or (m.item.reference_unit_price if m.item else 0) or 0
        issued = m.issued_qty or 0
        required = m.required_qty or 0

        actual_cost = unit_price * issued
        standard_cost = unit_price * required
        actual_material_cost += actual_cost
        standard_material_cost += standard_cost

        material_items.append({
            "material_code": m.item.material_code if m.item else "",
            "material_name": m.item.material_name if m.item else "",
            "unit_price": unit_price,
            "required_qty": required,
            "issued_qty": issued,
            "actual_cost": actual_cost,
            "standard_cost": standard_cost,
        })

    # 2. 人工成本（累计工时 * 费率）
    labor_hours = wo.labor_hours or 0
    labor_cost = labor_hours * _labor_rate

    # 3. 汇总
    actual_total = actual_material_cost + labor_cost
    standard_total = standard_material_cost + labor_cost  # 标准工时用实际工时替代

    # 产出成本（分摊到良品）
    good_qty = (wo.completed_qty or 0) - (wo.rejected_qty or 0)
    unit_actual_cost = round(actual_total / good_qty, 2) if good_qty > 0 else 0

    return {
        "wo_number": wo.wo_number,
        "status": wo.status,
        "product_name": wo.item.material_name if wo.item else "",
        "plan_qty": wo.plan_qty,
        "completed_qty": wo.completed_qty or 0,
        "rejected_qty": wo.rejected_qty or 0,
        "good_qty": good_qty,
        "labor_hours": labor_hours,
        "cost_rates": {
            "labor_rate_per_hour": _labor_rate,
        },
        "material_costs": {
            "items": material_items,
            "actual_total": round(actual_material_cost, 2),
            "standard_total": round(standard_material_cost, 2),
        },
        "labor_cost": round(labor_cost, 2),
        "summary": {
            "actual_material_cost": round(actual_material_cost, 2),
            "labor_cost": round(labor_cost, 2),
            "actual_total": round(actual_total, 2),
            "standard_total": round(standard_total, 2),
            "variance": round(actual_total - standard_total, 2),
            "variance_pct": round((actual_total - standard_total) / standard_total * 100, 1) if standard_total > 0 else 0,
            "unit_actual_cost": unit_actual_cost,
        },
    }
