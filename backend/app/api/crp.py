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


@router.get("/rccp")
def rccp_analysis(
    horizon_days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """RCCP 粗能力计划 — MPS下达前校验产能可行性"""
    from app.models.mps import MpsEntry
    from app.models.material import MaterialMaster
    from app.models.order import WorkOrder
    from datetime import date, timedelta
    from collections import defaultdict

    today = date.today()

    # 收集在用工作中心
    wcs = {w.id: w for w in db.query(WorkCenter).filter(WorkCenter.is_active == True).all()}
    if not wcs:
        return {"success": False, "message": "没有工作中心", "data": []}

    # 收集MPS计划（未来horizon_days天）
    mps_list = db.query(MpsEntry).filter(
        MpsEntry.plan_date >= today,
        MpsEntry.plan_date <= today + timedelta(days=horizon_days),
    ).all()

    # 收集现有工单负荷
    existing_wos = db.query(WorkOrder).filter(
        WorkOrder.status.in_(["待下达", "已下达", "进行中"])
    ).all()

    # 按工作中心汇总负荷（简单估算：每个工单1条工序 8h setup + 0.5h/件）
    wc_load = defaultdict(lambda: {"existing_hours": 0, "planned_hours": 0, "mps_count": 0})
    for wc_id in wcs:
        wc_load[wc_id]["existing_hours"] = 0
        wc_load[wc_id]["planned_hours"] = 0
        wc_load[wc_id]["mps_count"] = 0

    for wo in existing_wos:
        if wo.work_center_id and wo.work_center_id in wc_load:
            hours = 8 + (wo.plan_qty * 0.5)  # 8h 准备 + 0.5h/件
            wc_load[wo.work_center_id]["existing_hours"] += hours

    for mps in mps_list:
        # 找工单关联的工作中心
        route = None
        if mps.item_id:
            rh = db.query(RoutingHeader).filter(
                RoutingHeader.item_id == mps.item_id,
                RoutingHeader.is_active == True,
            ).first()
            if rh and rh.operations:
                wc_id = rh.operations[0].work_center_id
                if wc_id in wc_load:
                    hours = 8 + (mps.quantity * 0.5)
                    wc_load[wc_id]["planned_hours"] += hours
                    wc_load[wc_id]["mps_count"] += 1

    # 汇总
    results = []
    for wc_id, wc in wcs.items():
        ld = wc_load[wc_id]
        capacity = (wc.capacity_per_day or 8) * horizon_days
        total_load = ld["existing_hours"] + ld["planned_hours"]
        utilization = round(total_load / capacity * 100, 1) if capacity > 0 else 0

        results.append({
            "work_center_id": wc_id,
            "work_center_name": wc.center_name,
            "capacity_hours": capacity,
            "existing_load": round(ld["existing_hours"], 1),
            "planned_mps_load": round(ld["planned_hours"], 1),
            "total_load": round(total_load, 1),
            "utilization_pct": utilization,
            "status": "OVERLOAD" if utilization > 100 else "WARNING" if utilization > 80 else "OK",
            "mps_affected": ld["mps_count"],
        })

    results.sort(key=lambda x: x["utilization_pct"], reverse=True)

    return {
        "success": True,
        "horizon_days": horizon_days,
        "data": results,
        "summary": {
            "total_work_centers": len(results),
            "overloaded": len([r for r in results if r["status"] == "OVERLOAD"]),
            "warning": len([r for r in results if r["status"] == "WARNING"]),
            "ok": len([r for r in results if r["status"] == "OK"]),
        },
    }
