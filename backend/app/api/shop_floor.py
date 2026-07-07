"""生产看板与安灯系统 API"""
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional

from app.core.database import get_db
from app.models.order import WorkOrder, WorkOrderOperation, WorkOrderReport
from app.models.routing import WorkCenter
from app.models.andon import AndonEvent

router = APIRouter(prefix="/api/shop-floor", tags=["生产看板"])


# ====== 安灯系统 ======

@router.get("/andon")
def list_andon(
    status: str = Query(None), severity: str = Query(None),
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """安灯事件列表"""
    q = db.query(AndonEvent)
    if status: q = q.filter(AndonEvent.status == status)
    if severity: q = q.filter(AndonEvent.severity == severity)
    total = q.count()
    items = q.order_by(AndonEvent.created_at.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()
    return {
        "items": [{
            "id": e.id, "event_no": e.event_no, "event_type": e.event_type,
            "severity": e.severity, "description": e.description,
            "handler": e.handler, "status": e.status,
            "work_order_id": e.work_order_id,
            "wo_number": e.work_order.wo_number if e.work_order else "",
            "work_center_name": e.work_center.center_name if e.work_center else "",
            "response_time": e.response_time.isoformat() if e.response_time else None,
            "resolve_time": e.resolve_time.isoformat() if e.resolve_time else None,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        } for e in items],
        "total": total, "page": page, "page_size": page_size,
    }


@router.post("/andon")
def create_andon(data: dict, db: Session = Depends(get_db)):
    """触发安灯事件"""
    now = datetime.now()
    count = db.query(AndonEvent).count() + 1
    event = AndonEvent(
        event_no=f"ANDON-{now.strftime('%Y%m%d')}-{count:04d}",
        work_order_id=data.get("work_order_id"),
        operation_id=data.get("operation_id"),
        work_center_id=data.get("work_center_id"),
        event_type=data.get("event_type", "其他"),
        severity=data.get("severity", "黄色"),
        description=data.get("description", ""),
        status="待响应",
    )
    db.add(event); db.commit()
    return {"success": True, "data": {"id": event.id, "event_no": event.event_no}}


@router.put("/andon/{event_id}/respond")
def respond_andon(event_id: int, data: dict, db: Session = Depends(get_db)):
    """响应安灯（接单）"""
    e = db.query(AndonEvent).filter(AndonEvent.id == event_id).first()
    if not e: raise HTTPException(404, "安灯事件不存在")
    if e.status != "待响应": raise HTTPException(400, f"当前状态({e.status})不能响应")
    e.status = "处理中"
    e.handler = data.get("handler", e.handler)
    e.response_time = datetime.now()
    db.commit()
    return {"success": True, "message": f"已响应: {e.handler}"}


@router.put("/andon/{event_id}/resolve")
def resolve_andon(event_id: int, data: dict, db: Session = Depends(get_db)):
    """解决安灯"""
    e = db.query(AndonEvent).filter(AndonEvent.id == event_id).first()
    if not e: raise HTTPException(404, "安灯事件不存在")
    e.status = "已解决"
    e.resolve_time = datetime.now()
    if data.get("description"): e.description = data["description"]
    db.commit()
    return {"success": True, "message": "安灯已解决"}


# ====== OEE ======

@router.get("/oee")
def calculate_oee(
    work_center_id: int = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """OEE 计算：时间利用率 × 性能效率 × 合格率"""
    now = datetime.now()
    since = now - timedelta(days=days)

    wcs = db.query(WorkCenter).filter(WorkCenter.is_active == True)
    if work_center_id: wcs = wcs.filter(WorkCenter.id == work_center_id)
    wcs = wcs.all()

    results = []
    for wc in wcs:
        # 找到该工作中心在时间范围内的工单
        wos = db.query(WorkOrder).filter(
            WorkOrder.work_center_id == wc.id,
            WorkOrder.actual_start >= since if WorkOrder.actual_start.is_not else True,
        ).all()

        if not wos:
            results.append({
                "work_center_id": wc.id, "center_name": wc.center_name,
                "total_orders": 0, "oee": 0,
                "availability": 0, "performance": 0, "quality": 0,
            })
            continue

        total_plan = sum(w.plan_qty or 0 for w in wos)
        total_completed = sum(w.completed_qty or 0 for w in wos)
        total_rejected = sum(w.rejected_qty or 0 for w in wos)
        total_labor = sum(w.labor_hours or 0 for w in wos)
        total_orders = len(wos)

        # 时间利用率: 计划每天 8h，计算实际 vs 计划
        planned_hours = wc.capacity_per_day or 8
        availability = min(1.0, total_labor / (planned_hours * days)) if days > 0 else 0

        # 性能效率: 实际产出 / 理论产出
        theoretical_hours = total_completed * 0.5  # 假设每件 0.5h 标准
        performance = min(1.0, theoretical_hours / total_labor) if total_labor > 0 else 0

        # 合格率: 良品 / 总产量
        good = total_completed - total_rejected
        quality = good / total_completed if total_completed > 0 else 0

        oee = round(availability * performance * quality * 100, 1)

        results.append({
            "work_center_id": wc.id,
            "center_name": wc.center_name,
            "total_orders": total_orders,
            "total_completed": total_completed,
            "total_rejected": total_rejected,
            "total_labor_hours": round(total_labor, 1),
            "availability": round(availability * 100, 1),
            "performance": round(performance * 100, 1),
            "quality": round(quality * 100, 1),
            "oee": oee,
        })

    return {"items": results, "period_days": days}


# ====== 生产看板 ======

@router.get("/kanban")
def production_kanban(db: Session = Depends(get_db)):
    """生产看板 — 工单按状态的卡片视图"""
    statuses = ["已下达", "进行中", "已完成"]
    columns = {}
    for s in statuses:
        wos = db.query(WorkOrder).filter(WorkOrder.status == s).order_by(
            WorkOrder.priority.desc(), WorkOrder.end_date.asc()
        ).limit(20).all()
        columns[s] = [{
            "id": w.id, "wo_number": w.wo_number,
            "material_name": w.item.material_name if w.item else "",
            "plan_qty": w.plan_qty, "completed_qty": w.completed_qty or 0,
            "rejected_qty": w.rejected_qty or 0,
            "progress": round((w.completed_qty or 0) / w.plan_qty * 100, 0) if w.plan_qty > 0 else 0,
            "start_date": w.start_date.isoformat() if w.start_date else None,
            "end_date": w.end_date.isoformat() if w.end_date else None,
            "priority": w.priority or 0,
            "work_center_name": w.work_center.center_name if w.work_center else "",
        } for w in wos]

    return {"columns": columns}


@router.get("/work-center-load")
def work_center_load(db: Session = Depends(get_db)):
    """工作中心负荷看板 — 当前在制 + 已下达的负荷"""
    wcs = db.query(WorkCenter).filter(WorkCenter.is_active == True).all()
    results = []
    for wc in wcs:
        active = db.query(WorkOrder).filter(
            WorkOrder.work_center_id == wc.id,
            WorkOrder.status.in_(["已下达", "进行中"]),
        ).all()
        total_qty = sum(w.plan_qty for w in active)
        total_completed = sum(w.completed_qty or 0 for w in active)
        load_pct = min(100, round(total_qty / (wc.capacity_per_day or 8) * 100, 0)) if wc.capacity_per_day else 0

        results.append({
            "work_center_id": wc.id, "center_name": wc.center_name,
            "active_orders": len(active),
            "total_plan_qty": total_qty,
            "total_completed": total_completed,
            "load_pct": load_pct,
            "capacity_per_day": wc.capacity_per_day,
        })

    return {"items": results}


@router.get("/summary")
def shop_floor_summary(db: Session = Depends(get_db)):
    """车间概况 — 顶部 KPI"""
    total_active = db.query(WorkOrder).filter(
        WorkOrder.status.in_(["已下达", "进行中"])).count()
    in_progress = db.query(WorkOrder).filter(
        WorkOrder.status == "进行中").count()
    today_reports = db.query(WorkOrderReport).filter(
        func.date(WorkOrderReport.created_at) == date.today()).count()
    pending_andon = db.query(AndonEvent).filter(
        AndonEvent.status == "待响应").count()

    return {
        "active_orders": total_active,
        "in_progress": in_progress,
        "today_reports": today_reports,
        "pending_andon": pending_andon,
        "today": date.today().isoformat(),
    }
