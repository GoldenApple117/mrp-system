"""MPS主生产计划 API"""
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List

from app.core.database import get_db
from app.models.mps import MpsEntry
from app.models.material import MaterialMaster

router = APIRouter(prefix="/api/mps", tags=["MPS"])


@router.get("")
def list_mps(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    item_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """MPS计划列表"""
    query = db.query(MpsEntry)

    if start_date:
        query = query.filter(MpsEntry.plan_date >= date.fromisoformat(start_date))
    if end_date:
        query = query.filter(MpsEntry.plan_date <= date.fromisoformat(end_date))
    if item_id:
        query = query.filter(MpsEntry.item_id == item_id)

    total = query.count()
    entries = query.order_by(MpsEntry.plan_date, MpsEntry.item_id).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "items": [
            {
                "id": e.id, "item_id": e.item_id,
                "material_code": e.item.material_code if e.item else "",
                "material_name": e.item.material_name if e.item else "",
                "unit": e.item.unit if e.item else "",
                "plan_date": e.plan_date.isoformat() if e.plan_date else None,
                "quantity": e.quantity, "source_type": e.source_type,
                "source_id": e.source_id, "is_frozen": e.is_frozen,
                "status": e.status or "进行中",
            }
            for e in entries
        ],
        "total": total, "page": page, "page_size": page_size,
    }


@router.post("")
def create_mps(data: dict, db: Session = Depends(get_db)):
    """新增MPS计划"""
    entry = MpsEntry(
        item_id=data["item_id"],
        plan_date=date.fromisoformat(data["plan_date"]) if isinstance(data["plan_date"], str) else data["plan_date"],
        quantity=data["quantity"],
        source_type=data.get("source_type", "手动"),
        source_id=data.get("source_id", ""),
    )
    db.add(entry)
    db.commit()
    return {"success": True, "data": {"id": entry.id}}


@router.post("/batch")
def batch_create_mps(data: dict, db: Session = Depends(get_db)):
    """批量创建MPS"""
    count = 0
    for entry_data in data.get("entries", []):
        entry = MpsEntry(
            item_id=entry_data["item_id"],
            plan_date=date.fromisoformat(entry_data["plan_date"]) if isinstance(entry_data["plan_date"], str) else entry_data["plan_date"],
            quantity=entry_data["quantity"],
            source_type=entry_data.get("source_type", "手动"),
            source_id=entry_data.get("source_id", ""),
        )
        db.add(entry)
        count += 1
    db.commit()
    return {"success": True, "message": f"已创建 {count} 条MPS计划"}


@router.put("/{entry_id}")
def update_mps(entry_id: int, data: dict, db: Session = Depends(get_db)):
    """更新MPS"""
    entry = db.query(MpsEntry).filter(MpsEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="不存在")

    for key in ["quantity", "plan_date", "is_frozen", "source_type"]:
        if key in data:
            if key == "plan_date" and isinstance(data[key], str):
                setattr(entry, key, date.fromisoformat(data[key]))
            else:
                setattr(entry, key, data[key])

    db.commit()
    return {"success": True}


@router.delete("/{entry_id}")
def delete_mps(entry_id: int, db: Session = Depends(get_db)):
    """删除MPS"""
    entry = db.query(MpsEntry).filter(MpsEntry.id == entry_id).first()
    if entry:
        db.delete(entry)
        db.commit()
    return {"success": True}
