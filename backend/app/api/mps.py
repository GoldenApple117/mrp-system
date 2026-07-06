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
    # 兼容两种字段名：item_id（后端标准）和 product_id（前端/外部常用）
    item_id = data.get("item_id") or data.get("product_id")
    if not item_id:
        raise HTTPException(status_code=422, detail="缺少物料ID (item_id / product_id)")
    plan_date_raw = data.get("plan_date") or data.get("start_date")
    if not plan_date_raw:
        raise HTTPException(status_code=422, detail="缺少计划日期 (plan_date / start_date)")

    entry = MpsEntry(
        item_id=item_id,
        plan_date=date.fromisoformat(plan_date_raw) if isinstance(plan_date_raw, str) else plan_date_raw,
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

    for key in ["quantity", "plan_date", "is_frozen", "source_type", "status"]:
        if key in data:
            if key == "plan_date" and isinstance(data[key], str):
                setattr(entry, key, date.fromisoformat(data[key]))
            else:
                setattr(entry, key, data[key])

    # 双向同步：MPS变更 → 回写关联销售订单
    if entry.source_type == "销售订单" and entry.source_id:
        from app.models.sales import SalesOrder
        so = db.query(SalesOrder).filter(
            SalesOrder.order_number == entry.source_id
        ).first()
        if so and so.ship_status == "待出货":
            if "quantity" in data:
                so.order_qty = data["quantity"]
                so.total_amount = so.order_qty * (so.unit_price or 0)
            if "plan_date" in data and data["plan_date"]:
                so.delivery_date = date.fromisoformat(data["plan_date"]) if isinstance(data["plan_date"], str) else data["plan_date"]

    db.commit()
    return {"success": True, "message": "已更新" + ("，已同步销售订单" if entry.source_type == "销售订单" else "")}


@router.delete("/{entry_id}")
def delete_mps(entry_id: int, db: Session = Depends(get_db)):
    """删除MPS（关联销售订单时恢复为待出货）"""
    entry = db.query(MpsEntry).filter(MpsEntry.id == entry_id).first()
    if entry:
        # 如果关联销售订单，回退订单信息
        if entry.source_type == "销售订单" and entry.source_id:
            from app.models.sales import SalesOrder
            so = db.query(SalesOrder).filter(
                SalesOrder.order_number == entry.source_id
            ).first()
            if so and so.ship_status == "待出货":
                so.order_qty = entry.quantity
        db.delete(entry)
        db.commit()
    return {"success": True}


@router.get("/atp")
def calculate_atp(db: Session = Depends(get_db)):
    """ATP 可承诺量 — 当前可用库存 + 计划产出 - 已承诺订单"""
    from app.models.material import MaterialMaster
    from app.models.inventory import InventoryRecord
    from app.models.order import PurchaseOrder, WorkOrder
    from app.models.mps import MpsEntry
    from datetime import date

    today = date.today()

    # 获取所有成品物料
    products = db.query(MaterialMaster).filter(
        MaterialMaster.level_type == "产品"
    ).all()

    results = []
    for prod in products:
        # 当前库存
        inv = db.query(InventoryRecord).filter(
            InventoryRecord.item_id == prod.id
        ).first()
        on_hand = inv.on_hand_qty if inv else 0

        # 计划产出（MPS未来30天）
        mps_qty = db.query(func.coalesce(func.sum(MpsEntry.quantity), 0)).filter(
            MpsEntry.item_id == prod.id,
            MpsEntry.plan_date >= today,
            MpsEntry.status == "进行中",
        ).scalar() or 0

        # 在途采购（未来30天）
        po_qty = db.query(func.coalesce(func.sum(PurchaseOrder.order_qty - func.coalesce(PurchaseOrder.received_qty, 0)), 0)).filter(
            PurchaseOrder.item_id == prod.id,
            PurchaseOrder.due_date >= today,
            PurchaseOrder.status.in_(["已下单", "部分收货"]),
        ).scalar() or 0

        # 在制工单（未来30天）
        wo_qty = db.query(func.coalesce(func.sum(WorkOrder.plan_qty - func.coalesce(WorkOrder.completed_qty, 0)), 0)).filter(
            WorkOrder.item_id == prod.id,
            WorkOrder.status.in_(["已下达", "进行中"]),
        ).scalar() or 0

        # 已承诺（未出货销售订单）
        from app.models.sales import SalesOrder
        committed = db.query(func.coalesce(func.sum(SalesOrder.order_qty - func.coalesce(SalesOrder.shipped_qty, 0)), 0)).filter(
            SalesOrder.item_id == prod.id,
            SalesOrder.ship_status.in_(["待出货", "部分出货"]),
        ).scalar() or 0

        available = on_hand + mps_qty + po_qty + wo_qty - committed

        results.append({
            "material_id": prod.id,
            "material_code": prod.material_code,
            "material_name": prod.material_name,
            "on_hand": on_hand,
            "mps_planned": mps_qty,
            "po_in_transit": po_qty,
            "wo_in_progress": wo_qty,
            "total_supply": on_hand + mps_qty + po_qty + wo_qty,
            "committed": committed,
            "atp": available,
            "atp_label": f"可承诺 {available}" if available >= 0 else f"超卖 {abs(available)}",
        })

    results.sort(key=lambda x: x["atp"])

    return {
        "items": results,
        "total": len(results),
        "summary": {
            "products_with_stock": len([r for r in results if r["atp"] >= 0]),
            "over_sold": len([r for r in results if r["atp"] < 0]),
            "total_atp": sum(r["atp"] for r in results),
        },
    }
