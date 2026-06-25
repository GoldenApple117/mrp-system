"""CRP产能需求计划 API"""
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.order import WorkOrder
from app.models.routing import WorkCenter, RoutingHeader, RoutingOperation
from app.services.crp_calculator import CrpCalculator

router = APIRouter(prefix="/api/crp", tags=["CRP产能计划"])


@router.post("/calculate")
def calculate_crp(data: dict, db: Session = Depends(get_db)):
    """执行CRP产能计算"""
    horizon_days = data.get("horizon_days", 60)

    # 读取工作中心
    wc_raw = db.query(WorkCenter).filter(WorkCenter.is_active == True).all()
    work_centers = [
        {
            "id": w.id, "center_code": w.center_code, "center_name": w.center_name,
            "capacity_per_day": w.capacity_per_day, "efficiency": w.efficiency,
            "machines_count": w.machines_count, "workers_count": w.workers_count,
        }
        for w in wc_raw
    ]

    if not work_centers:
        return {"success": False, "message": "没有工作中心，请先创建", "data": None}

    # 读取工单（计划中、进行中的）
    wo_raw = db.query(WorkOrder).filter(
        WorkOrder.status.in_(["待下达", "已下达", "进行中"])
    ).all()
    work_orders = [
        {
            "id": w.id, "wo_number": w.wo_number, "item_id": w.item_id,
            "plan_qty": w.plan_qty,
            "start_date": w.start_date.isoformat() if w.start_date else date.today().isoformat(),
            "end_date": w.end_date.isoformat() if w.end_date else date.today().isoformat(),
            "work_center_id": w.work_center_id, "routing_id": w.routing_id,
        }
        for w in wo_raw
    ]

    # 读取工艺路线
    routing_raw = db.query(RoutingHeader).filter(RoutingHeader.is_active == True).all()
    routings = [
        {"id": r.id, "item_id": r.item_id, "routing_code": r.routing_code}
        for r in routing_raw
    ]

    # 读取工序
    op_raw = db.query(RoutingOperation).all()
    operations = [
        {
            "id": o.id, "routing_header_id": o.routing_header_id,
            "seq_no": o.seq_no, "work_center_id": o.work_center_id,
            "operation_name": o.operation_name,
            "setup_time": o.setup_time,
            "run_time_per_unit": o.run_time_per_unit,
        }
        for o in op_raw
    ]

    calculator = CrpCalculator(horizon_days)
    result = calculator.calculate(work_orders, work_centers, routings, operations)
    return result
