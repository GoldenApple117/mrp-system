"""设备台账 + 模具管理 + 保养计划 API"""
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.equipment import Equipment, Tooling, MaintenancePlan

router = APIRouter(prefix="/api/equipment", tags=["设备与模具"])


# ====== 设备台账 ======

@router.get("")
def list_equipment(
    status: str = Query(None), work_center_id: int = Query(None),
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(Equipment)
    if status: q = q.filter(Equipment.status == status)
    if work_center_id: q = q.filter(Equipment.work_center_id == work_center_id)
    total = q.count()
    items = q.order_by(Equipment.id.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()
    return {"items": [{
        "id": e.id, "equipment_code": e.equipment_code, "equipment_name": e.equipment_name,
        "model_spec": e.model_spec,
        "work_center_id": e.work_center_id,
        "work_center_name": e.work_center.center_name if e.work_center else "",
        "manufacturer": e.manufacturer, "status": e.status,
        "purchase_date": e.purchase_date.isoformat() if e.purchase_date else None,
        "warranty_expiry": e.warranty_expiry.isoformat() if e.warranty_expiry else None,
        "location": e.location,
    } for e in items], "total": total, "page": page, "page_size": page_size}


@router.post("")
def create_equipment(data: dict, db: Session = Depends(get_db)):
    eq = Equipment(**{k: data[k] for k in data if hasattr(Equipment, k)})
    if data.get("purchase_date"): eq.purchase_date = date.fromisoformat(data["purchase_date"])
    if data.get("warranty_expiry"): eq.warranty_expiry = date.fromisoformat(data["warranty_expiry"])
    db.add(eq); db.commit()
    return {"success": True, "data": {"id": eq.id}}


@router.put("/{eq_id}")
def update_equipment(eq_id: int, data: dict, db: Session = Depends(get_db)):
    eq = db.query(Equipment).filter(Equipment.id == eq_id).first()
    if not eq: raise HTTPException(404, "设备不存在")
    for k in ("equipment_code", "equipment_name", "model_spec", "work_center_id",
              "manufacturer", "status", "location", "remark"):
        if k in data: setattr(eq, k, data[k])
    if data.get("purchase_date"): eq.purchase_date = date.fromisoformat(data["purchase_date"])
    if data.get("warranty_expiry"): eq.warranty_expiry = date.fromisoformat(data["warranty_expiry"])
    db.commit()
    return {"success": True}


@router.delete("/{eq_id}")
def delete_equipment(eq_id: int, db: Session = Depends(get_db)):
    eq = db.query(Equipment).filter(Equipment.id == eq_id).first()
    if not eq: raise HTTPException(404, "设备不存在")
    db.delete(eq); db.commit()
    return {"success": True}


# ====== 模具管理 ======

@router.get("/toolings")
def list_toolings(
    status: str = Query(None), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(Tooling)
    if status: q = q.filter(Tooling.status == status)
    total = q.count()
    items = q.order_by(Tooling.id.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()
    return {"items": [{
        "id": t.id, "tooling_code": t.tooling_code, "tooling_name": t.tooling_name,
        "item_id": t.item_id,
        "material_name": t.item.material_name if t.item else "",
        "max_life": t.max_life, "current_life": t.current_life,
        "life_pct": round(t.current_life / t.max_life * 100, 0) if t.max_life > 0 else 0,
        "status": t.status,
        "last_maintenance_date": t.last_maintenance_date.isoformat() if t.last_maintenance_date else None,
        "next_maintenance_date": t.next_maintenance_date.isoformat() if t.next_maintenance_date else None,
        "location": t.location,
    } for t in items], "total": total, "page": page, "page_size": page_size}


@router.post("/toolings")
def create_tooling(data: dict, db: Session = Depends(get_db)):
    tl = Tooling(**{k: data[k] for k in data if hasattr(Tooling, k)})
    if data.get("last_maintenance_date"): tl.last_maintenance_date = date.fromisoformat(data["last_maintenance_date"])
    if data.get("next_maintenance_date"): tl.next_maintenance_date = date.fromisoformat(data["next_maintenance_date"])
    db.add(tl); db.commit()
    return {"success": True, "data": {"id": tl.id}}


@router.put("/toolings/{tl_id}/life")
def record_tooling_life(tl_id: int, data: dict, db: Session = Depends(get_db)):
    """记录模具使用次数"""
    tl = db.query(Tooling).filter(Tooling.id == tl_id).first()
    if not tl: raise HTTPException(404, "模具不存在")
    add_life = int(data.get("add_life", 0))
    tl.current_life = (tl.current_life or 0) + add_life
    if tl.max_life > 0 and tl.current_life >= tl.max_life:
        tl.status = "报废"
    elif tl.current_life > 0:
        tl.status = "使用中"
    db.commit()
    return {"success": True, "message": f"已使用{add_life}次，累计{tl.current_life}/{tl.max_life}"}


@router.delete("/toolings/{tl_id}")
def delete_tooling(tl_id: int, db: Session = Depends(get_db)):
    tl = db.query(Tooling).filter(Tooling.id == tl_id).first()
    if not tl: raise HTTPException(404, "模具不存在")
    db.delete(tl); db.commit()
    return {"success": True}


# ====== 保养计划 ======

@router.get("/maintenance")
def list_maintenance(
    status: str = Query(None), target_type: str = Query(None),
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(MaintenancePlan)
    if status: q = q.filter(MaintenancePlan.status == status)
    if target_type: q = q.filter(MaintenancePlan.target_type == target_type)
    total = q.count()
    items = q.order_by(MaintenancePlan.id.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()
    result = []
    for m in items:
        eq_name = ""
        if m.equipment_id:
            eq = db.query(Equipment).filter(Equipment.id == m.equipment_id).first()
            eq_name = eq.equipment_name if eq else ""
        tl_name = ""
        if m.tooling_id:
            tl = db.query(Tooling).filter(Tooling.id == m.tooling_id).first()
            tl_name = tl.tooling_name if tl else ""
        result.append({
            "id": m.id, "plan_no": m.plan_no, "target_type": m.target_type,
            "plan_type": m.plan_type, "description": m.description,
            "equipment_id": m.equipment_id, "equipment_name": eq_name,
            "tooling_id": m.tooling_id, "tooling_name": tl_name,
            "scheduled_date": m.scheduled_date.isoformat() if m.scheduled_date else None,
            "completed_date": m.completed_date.isoformat() if m.completed_date else None,
            "status": m.status, "handler": m.handler,
        })
    return {"items": result, "total": total, "page": page, "page_size": page_size}


@router.post("/maintenance")
def create_maintenance(data: dict, db: Session = Depends(get_db)):
    now = datetime.now()
    count = db.query(MaintenancePlan).count() + 1
    mp = MaintenancePlan(
        plan_no=f"MT-{now.strftime('%Y%m%d')}-{count:04d}",
        target_type=data.get("target_type", "设备"),
        equipment_id=data.get("equipment_id"),
        tooling_id=data.get("tooling_id"),
        plan_type=data.get("plan_type", "月保"),
        description=data.get("description", ""),
        scheduled_date=date.fromisoformat(data["scheduled_date"]) if data.get("scheduled_date") else None,
        status="待执行",
    )
    db.add(mp); db.commit()
    return {"success": True, "data": {"id": mp.id, "plan_no": mp.plan_no}}


@router.put("/maintenance/{mp_id}/complete")
def complete_maintenance(mp_id: int, data: dict, db: Session = Depends(get_db)):
    mp = db.query(MaintenancePlan).filter(MaintenancePlan.id == mp_id).first()
    if not mp: raise HTTPException(404, "保养计划不存在")
    mp.status = "已完成"
    mp.completed_date = date.today()
    mp.handler = data.get("handler", mp.handler)
    if data.get("remark"): mp.remark = data["remark"]
    db.commit()
    return {"success": True, "message": f"保养 {mp.plan_no} 已完成"}
