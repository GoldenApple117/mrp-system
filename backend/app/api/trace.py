"""批次追溯与序列号管理 API"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional

from app.core.database import get_db
from app.models.trace import BatchRecord, SerialNumber, SerialNumberLog
from app.models.inventory import InventoryRecord, InventoryTransaction
from app.models.order import PurchaseOrder, WorkOrder
from app.models.material import MaterialMaster
from app.models.supplier import Supplier

router = APIRouter(prefix="/api/trace", tags=["追溯管理"])


# ====== 批次管理 ======

@router.get("/batches")
def list_batches(
    item_id: int = Query(None), status: str = Query(None),
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """批次列表"""
    q = db.query(BatchRecord)
    if item_id: q = q.filter(BatchRecord.item_id == item_id)
    if status: q = q.filter(BatchRecord.status == status)
    total = q.count()
    items = q.order_by(BatchRecord.id.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()
    return {
        "items": [{
            "id": b.id, "batch_no": b.batch_no,
            "item_id": b.item_id,
            "material_code": b.item.material_code if b.item else "",
            "material_name": b.item.material_name if b.item else "",
            "supplier_id": b.supplier_id,
            "supplier_name": b.supplier.supplier_name if b.supplier else "",
            "qty": b.qty, "remaining_qty": b.remaining_qty,
            "status": b.status,
            "received_date": b.received_date.isoformat() if b.received_date else None,
            "expiry_date": b.expiry_date.isoformat() if b.expiry_date else None,
        } for b in items],
        "total": total, "page": page, "page_size": page_size,
    }


@router.post("/batches")
def create_batch(data: dict, db: Session = Depends(get_db)):
    """创建批次记录（采购入库时调用）"""
    batch = BatchRecord(
        batch_no=data["batch_no"],
        item_id=data["item_id"],
        supplier_id=data.get("supplier_id"),
        po_id=data.get("po_id"),
        qty=data.get("qty", 0),
        remaining_qty=data.get("qty", 0),
        status="在库",
        remark=data.get("remark", ""),
    )
    if data.get("received_date"):
        batch.received_date = datetime.fromisoformat(data["received_date"])
    if data.get("expiry_date"):
        batch.expiry_date = datetime.fromisoformat(data["expiry_date"])
    db.add(batch); db.commit()
    return {"success": True, "data": {"id": batch.id, "batch_no": batch.batch_no}}


@router.get("/batches/{batch_no}/flow")
def batch_flow(batch_no: str, db: Session = Depends(get_db)):
    """正向追溯：批次 → 所有出库去向（工单/客户等）"""
    batch = db.query(BatchRecord).filter(BatchRecord.batch_no == batch_no).first()
    if not batch: raise HTTPException(404, "批次不存在")

    # 查询该批次的所有库存流水
    transactions = db.query(InventoryTransaction).filter(
        InventoryTransaction.batch_no == batch_no
    ).order_by(InventoryTransaction.created_at.asc()).all()

    flow = []
    total_in = 0; total_out = 0
    for t in transactions:
        qty = t.quantity or 0
        item = {
            "transaction_type": t.transaction_type,
            "quantity": qty,
            "reference_no": t.reference_no,
            "operator": t.operator,
            "remark": t.remark,
            "time": t.created_at.isoformat() if t.created_at else None,
        }
        flow.append(item)
        if qty > 0: total_in += qty
        else: total_out += abs(qty)

    return {
        "batch_no": batch_no,
        "material_code": batch.item.material_code if batch.item else "",
        "material_name": batch.item.material_name if batch.item else "",
        "supplier_name": batch.supplier.supplier_name if batch.supplier else "",
        "total_qty": batch.qty,
        "remaining_qty": batch.remaining_qty,
        "total_in": total_in,
        "total_out": total_out,
        "flow": flow,
    }


# ====== 序列号管理 ======

@router.get("/serial-numbers")
def list_serial_numbers(
    item_id: int = Query(None), status: str = Query(None),
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """序列号列表"""
    q = db.query(SerialNumber)
    if item_id: q = q.filter(SerialNumber.item_id == item_id)
    if status: q = q.filter(SerialNumber.status == status)
    total = q.count()
    items = q.order_by(SerialNumber.id.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()
    return {
        "items": [{
            "id": s.id, "sn": s.sn,
            "item_id": s.item_id,
            "material_code": s.item.material_code if s.item else "",
            "material_name": s.item.material_name if s.item else "",
            "batch_no": s.batch_no,
            "status": s.status,
            "current_location": s.current_location,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        } for s in items],
        "total": total, "page": page, "page_size": page_size,
    }


@router.post("/serial-numbers")
def create_serial_number(data: dict, db: Session = Depends(get_db)):
    """创建序列号（成品完工入库时调用）"""
    try:
        sn_str = data.get("sn", "").strip()
        if not sn_str:
            raise HTTPException(422, "序列号不能为空")
        existing = db.query(SerialNumber).filter(SerialNumber.sn == sn_str).first()
        if existing:
            raise HTTPException(400, f"序列号 {sn_str} 已存在")

        item_id = int(data.get("item_id", 0))
        if item_id <= 0:
            raise HTTPException(422, "请提供有效的物料ID")

        sn = SerialNumber(
            sn=sn_str,
            item_id=item_id,
            batch_no=data.get("batch_no", ""),
            status="在库",
            wo_id=data.get("wo_id"),
        )
        db.add(sn)
        db.flush()

        db.add(SerialNumberLog(
            serial_number_id=sn.id,
            sn=sn.sn,
            event_type="入库",
            reference_no=data.get("reference_no", ""),
            operator=data.get("operator", "系统"),
        ))
        db.commit()
        return {"success": True, "data": {"id": sn.id, "sn": sn.sn}}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, detail=f"{type(e).__name__}: {str(e)}")


@router.put("/serial-numbers/{sn_id}/status")
def update_sn_status(sn_id: int, data: dict, db: Session = Depends(get_db)):
    """更新序列号状态并记录日志"""
    sn = db.query(SerialNumber).filter(SerialNumber.id == sn_id).first()
    if not sn: raise HTTPException(404, "序列号不存在")

    old_status = sn.status
    sn.status = data.get("status", sn.status)
    sn.current_location = data.get("location", sn.current_location)
    if data.get("customer_id"): sn.customer_id = data["customer_id"]

    db.add(SerialNumberLog(
        serial_number_id=sn.id,
        sn=sn.sn,
        event_type=data.get("event_type", "状态变更"),
        reference_no=data.get("reference_no", ""),
        operator=data.get("operator", "系统"),
        remark=f"{old_status} → {sn.status}",
    ))
    db.commit()
    return {"success": True, "message": f"序列号 {sn.sn} 状态已更新: {sn.status}"}


# ====== 逆向追溯 ======

@router.get("/trace-backward")
def trace_backward(sn: str = Query(...), db: Session = Depends(get_db)):
    """逆向追溯：序列号 → 所有历史日志 → 供应商"""
    serial = db.query(SerialNumber).filter(SerialNumber.sn == sn).first()
    if not serial: raise HTTPException(404, "序列号不存在")

    logs = db.query(SerialNumberLog).filter(
        SerialNumberLog.serial_number_id == serial.id
    ).order_by(SerialNumberLog.created_at.asc()).all()

    # 查找批次信息
    batch_info = None
    if serial.batch_no:
        batch = db.query(BatchRecord).filter(
            BatchRecord.batch_no == serial.batch_no
        ).first()
        if batch:
            batch_info = {
                "batch_no": batch.batch_no,
                "supplier_name": batch.supplier.supplier_name if batch.supplier else "",
                "received_date": batch.received_date.isoformat() if batch.received_date else None,
                "qty": batch.qty,
            }

    # 查找关联的采购单和工单
    wo = db.query(WorkOrder).filter(WorkOrder.id == serial.wo_id).first() if serial.wo_id else None

    return {
        "serial_number": sn,
        "material_code": serial.item.material_code if serial.item else "",
        "material_name": serial.item.material_name if serial.item else "",
        "status": serial.status,
        "current_location": serial.current_location,
        "batch": batch_info,
        "work_order": {
            "wo_number": wo.wo_number if wo else "",
            "status": wo.status if wo else "",
        } if wo else None,
        "timeline": [{
            "time": l.created_at.isoformat() if l.created_at else None,
            "event": l.event_type,
            "reference_no": l.reference_no,
            "operator": l.operator,
            "remark": l.remark,
        } for l in logs],
    }


@router.get("/trace-forward")
def trace_forward(batch_no: str = Query(...), db: Session = Depends(get_db)):
    """正向追溯：输入批次号 → 该批次所有序列号 → 各序列号去向"""
    batch = db.query(BatchRecord).filter(BatchRecord.batch_no == batch_no).first()
    if not batch: raise HTTPException(404, "批次不存在")

    serials = db.query(SerialNumber).filter(
        SerialNumber.batch_no == batch_no
    ).all()

    return {
        "batch_no": batch_no,
        "material_code": batch.item.material_code if batch.item else "",
        "material_name": batch.item.material_name if batch.item else "",
        "supplier_name": batch.supplier.supplier_name if batch.supplier else "",
        "total_qty": batch.qty,
        "remaining_qty": batch.remaining_qty,
        "serial_numbers": [{
            "sn": s.sn,
            "status": s.status,
            "current_location": s.current_location,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        } for s in serials],
        "total_serials": len(serials),
    }


# ====== 简易搜索（一个端点查批次或序列号） ======

@router.get("/search")
def trace_search(keyword: str = Query(...), db: Session = Depends(get_db)):
    """智能搜索：自动识别是批次号还是序列号"""
    # 尝试按批次号查
    batch = db.query(BatchRecord).filter(BatchRecord.batch_no == keyword).first()
    if batch:
        return trace_forward(batch_no=keyword, db=db)

    # 尝试按序列号查
    serial = db.query(SerialNumber).filter(SerialNumber.sn == keyword).first()
    if serial:
        return trace_backward(sn=keyword, db=db)

    raise HTTPException(404, f"未找到匹配的批次号或序列号: {keyword}")
