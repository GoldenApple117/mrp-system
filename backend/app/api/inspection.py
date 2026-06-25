"""到货检验 + 盘点管理 API"""
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.order import PurchaseOrder
from app.models.inventory import InventoryRecord, InventoryTransaction
from app.models.inspection import InspectionRecord, StockCount

router = APIRouter(prefix="/api/inspection", tags=["检验与盘点"])


# ====== 到货检验 ======

@router.get("")
def list_inspections(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    result: str = Query(None), db: Session = Depends(get_db),
):
    """检验记录列表"""
    query = db.query(InspectionRecord)
    if result:
        query = query.filter(InspectionRecord.result == result)
    total = query.count()
    items = query.order_by(InspectionRecord.id.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()
    return {
        "items": [{
            "id": i.id, "inspection_no": i.inspection_no,
            "purchase_order_id": i.purchase_order_id,
            "po_number": i.purchase_order.po_number if i.purchase_order else "",
            "material_code": i.item.material_code if i.item else "",
            "material_name": i.item.material_name if i.item else "",
            "inspect_qty": i.inspect_qty, "pass_qty": i.pass_qty,
            "reject_qty": i.reject_qty, "result": i.result,
            "inspector": i.inspector, "remark": i.remark,
            "created_at": i.created_at.isoformat() if i.created_at else None,
        } for i in items],
        "total": total, "page": page, "page_size": page_size,
    }


@router.post("")
def create_inspection(data: dict, db: Session = Depends(get_db)):
    """创建到货检验"""
    now = datetime.now()
    insp = InspectionRecord(
        inspection_no=data.get("inspection_no", f"QC-{now.strftime('%Y%m%d%H%M%S')}"),
        purchase_order_id=data["purchase_order_id"],
        item_id=data["item_id"],
        inspect_qty=data["inspect_qty"],
        inspector=data.get("inspector", ""),
        remark=data.get("remark", ""),
    )
    db.add(insp)
    db.commit()
    return {"success": True, "message": "检验单已创建", "data": {"id": insp.id, "inspection_no": insp.inspection_no}}


@router.put("/{inspection_id}/result")
def update_inspection_result(inspection_id: int, data: dict, db: Session = Depends(get_db)):
    """更新检验结果（合格/不合格），自动入库或退货"""
    insp = db.query(InspectionRecord).filter(InspectionRecord.id == inspection_id).first()
    if not insp:
        raise HTTPException(status_code=404, detail="检验单不存在")

    insp.pass_qty = data.get("pass_qty", 0)
    insp.reject_qty = data.get("reject_qty", 0)
    insp.result = data.get("result", "合格")
    insp.remark = data.get("remark", insp.remark)

    # 合格 → 自动入库
    if insp.pass_qty > 0:
        warehouse_id = data.get("warehouse_id", 1)
        record = db.query(InventoryRecord).filter(
            InventoryRecord.item_id == insp.item_id,
            InventoryRecord.warehouse_id == warehouse_id,
        ).first()
        if not record:
            record = InventoryRecord(item_id=insp.item_id, warehouse_id=warehouse_id)
            db.add(record)
            db.flush()
        record.on_hand_qty += insp.pass_qty

        db.add(InventoryTransaction(
            item_id=insp.item_id, warehouse_id=warehouse_id,
            transaction_type="采购入库", quantity=insp.pass_qty,
            reference_no=insp.inspection_no, operator=data.get("inspector", ""),
        ))

        # 更新采购单已收数量
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == insp.purchase_order_id).first()
        if po:
            po.received_qty = (po.received_qty or 0) + insp.pass_qty
            if po.received_qty >= po.order_qty:
                po.status = "已完成"

    db.commit()
    return {"success": True, "message": f"检验结果已提交，合格{insp.pass_qty}件，不合格{insp.reject_qty}件"}


# ====== 盘点管理 ======

@router.get("/stock-counts")
def list_stock_counts(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None), db: Session = Depends(get_db),
):
    """盘点列表"""
    query = db.query(StockCount)
    if status:
        query = query.filter(StockCount.status == status)
    total = query.count()
    items = query.order_by(StockCount.id.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()
    return {
        "items": [{
            "id": s.id, "count_no": s.count_no,
            "warehouse_id": s.warehouse_id,
            "warehouse_name": s.warehouse.warehouse_name if s.warehouse else "",
            "material_code": s.item.material_code if s.item else "",
            "material_name": s.item.material_name if s.item else "",
            "system_qty": s.system_qty, "actual_qty": s.actual_qty,
            "difference": s.difference, "status": s.status,
            "counter": s.counter, "count_date": s.count_date.isoformat() if s.count_date else None,
        } for s in items],
        "total": total, "page": page, "page_size": page_size,
    }


@router.post("/stock-counts")
def create_stock_count(data: dict, db: Session = Depends(get_db)):
    """创建盘点计划"""
    now = datetime.now()
    # 读取系统库存
    rec = db.query(InventoryRecord).filter(
        InventoryRecord.item_id == data["item_id"],
        InventoryRecord.warehouse_id == data.get("warehouse_id", 1),
    ).first()
    system_qty = rec.on_hand_qty if rec else 0

    sc = StockCount(
        count_no=f"COUNT-{now.strftime('%Y%m%d%H%M%S')}",
        warehouse_id=data.get("warehouse_id", 1),
        item_id=data["item_id"],
        system_qty=system_qty,
        status="待盘点",
        counter=data.get("counter", ""),
        remark=data.get("remark", ""),
    )
    db.add(sc)
    db.commit()
    return {"success": True, "data": {"id": sc.id, "count_no": sc.count_no}}


@router.put("/stock-counts/{count_id}/result")
def submit_stock_count(count_id: int, data: dict, db: Session = Depends(get_db)):
    """提交盘点结果并自动调整库存"""
    sc = db.query(StockCount).filter(StockCount.id == count_id).first()
    if not sc:
        raise HTTPException(status_code=404, detail="盘点记录不存在")

    sc.actual_qty = data["actual_qty"]
    sc.difference = sc.actual_qty - sc.system_qty
    sc.status = "已盘点"
    sc.counter = data.get("counter", sc.counter)

    db.commit()
    return {
        "success": True, "message": f"盘点完成，差异{sc.difference:+.0f}件",
        "data": {"difference": sc.difference, "system_qty": sc.system_qty, "actual_qty": sc.actual_qty},
    }


@router.post("/stock-counts/{count_id}/adjust")
def adjust_stock(count_id: int, data: dict, db: Session = Depends(get_db)):
    """确认盘点差异，调整库存"""
    sc = db.query(StockCount).filter(StockCount.id == count_id).first()
    if not sc:
        raise HTTPException(status_code=404, detail="盘点记录不存在")
    if sc.status != "已盘点":
        raise HTTPException(status_code=400, detail="请先提交盘点结果")

    # 调整库存
    rec = db.query(InventoryRecord).filter(
        InventoryRecord.item_id == sc.item_id,
        InventoryRecord.warehouse_id == sc.warehouse_id,
    ).first()
    if rec:
        diff = sc.difference
        rec.on_hand_qty += diff

        db.add(InventoryTransaction(
            item_id=sc.item_id, warehouse_id=sc.warehouse_id,
            transaction_type="盘点调整", quantity=diff,
            reference_no=sc.count_no, operator=data.get("operator", "系统"),
            remark=f"盘点调整: 系统{sc.system_qty}→实盘{sc.actual_qty}",
        ))

    sc.status = "已调整"
    db.commit()
    return {"success": True, "message": f"库存已调整，差异{sc.difference:+.0f}件"}
