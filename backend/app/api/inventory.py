"""库存管理 API"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional

from app.core.database import get_db
from app.models.inventory import InventoryRecord, InventoryTransaction, Warehouse
from app.models.material import MaterialMaster

router = APIRouter(prefix="/api/inventory", tags=["库存管理"])


@router.get("")
def list_inventory(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    keyword: Optional[str] = Query(None),
    warehouse_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """库存列表"""
    query = db.query(InventoryRecord)

    if warehouse_id:
        query = query.filter(InventoryRecord.warehouse_id == warehouse_id)

    if keyword:
        query = query.join(MaterialMaster).filter(
            (MaterialMaster.material_code.ilike(f"%{keyword}%")) |
            (MaterialMaster.material_name.ilike(f"%{keyword}%"))
        )

    total = query.count()
    records = query.order_by(InventoryRecord.item_id).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "items": [
            {
                "id": r.id, "item_id": r.item_id,
                "material_code": r.item.material_code if r.item else "",
                "material_name": r.item.material_name if r.item else "",
                "unit": r.item.unit if r.item else "",
                "warehouse_id": r.warehouse_id,
                "warehouse_name": r.warehouse.warehouse_name if r.warehouse else "",
                "location_code": r.location_code, "batch_no": r.batch_no,
                "on_hand_qty": r.on_hand_qty, "allocated_qty": r.allocated_qty,
                "reserved_qty": r.reserved_qty, "on_order_qty": r.on_order_qty,
                "on_production_qty": r.on_production_qty,
                "available_qty": r.available_qty,
            }
            for r in records
        ],
        "total": total, "page": page, "page_size": page_size,
    }


@router.get("/summary")
def inventory_summary(
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """库存汇总（按物料汇总所有仓库）"""
    query = db.query(
        MaterialMaster.id,
        MaterialMaster.material_code,
        MaterialMaster.material_name,
        MaterialMaster.material_type,
        MaterialMaster.unit,
        MaterialMaster.safety_stock,
        func.sum(InventoryRecord.on_hand_qty).label("total_on_hand"),
        func.sum(InventoryRecord.allocated_qty).label("total_allocated"),
        func.sum(InventoryRecord.on_order_qty).label("total_on_order"),
    ).join(InventoryRecord, MaterialMaster.id == InventoryRecord.item_id, isouter=True
    ).filter(MaterialMaster.is_active == True,
             MaterialMaster.level_type != "模块")
    
    if keyword:
        query = query.filter(
            (MaterialMaster.material_code.ilike(f"%{keyword}%")) |
            (MaterialMaster.material_name.ilike(f"%{keyword}%"))
        )
    
    results = query.group_by(MaterialMaster.id).all()

    # 构建基础结果
    result_items = []
    for r in results:
        result_items.append({
            "item_id": r.id, "material_code": r.material_code,
            "material_name": r.material_name, "material_type": r.material_type,
            "unit": r.unit,
            "safety_stock": r.safety_stock,
            "on_hand": float(r.total_on_hand or 0),
            "allocated": float(r.total_allocated or 0),
            "on_order": float(r.total_on_order or 0),
            "available": float(r.total_on_hand or 0) - float(r.total_allocated or 0),
            "is_low": (float(r.total_on_hand or 0) - float(r.total_allocated or 0)) < r.safety_stock if r.safety_stock else False,
            "last_received_qty": 0,
            "last_received_date": None,
        })

    # 批量查询最近入库记录
    item_ids = [r.id for r in results]
    if item_ids:
        last_txs = {}
        for item_id in item_ids:
            tx = db.query(InventoryTransaction).filter(
                InventoryTransaction.item_id == item_id,
                InventoryTransaction.transaction_type.ilike("%入库%")
            ).order_by(desc(InventoryTransaction.created_at)).first()
            if tx:
                last_txs[item_id] = (tx.quantity, tx.created_at)
        
        for item in result_items:
            if item["item_id"] in last_txs:
                qty, dt = last_txs[item["item_id"]]
                item["last_received_qty"] = qty
                item["last_received_date"] = dt.isoformat() if dt else None

    return {"items": result_items}


@router.post("/transaction")
def create_transaction(data: dict, db: Session = Depends(get_db)):
    """创建出入库记录"""
    item_id = data["item_id"]
    warehouse_id = data["warehouse_id"]
    qty = data["quantity"]
    tx_type = data.get("transaction_type", "入库")

    # 更新库存记录
    record = db.query(InventoryRecord).filter(
        InventoryRecord.item_id == item_id,
        InventoryRecord.warehouse_id == warehouse_id,
    ).first()

    if not record:
        record = InventoryRecord(item_id=item_id, warehouse_id=warehouse_id)
        db.add(record)
        db.flush()

    if tx_type in ("入库", "采购入库", "生产入库"):
        record.on_hand_qty += abs(qty)
    elif tx_type in ("出库", "领料出库", "销售出库"):
        record.on_hand_qty -= abs(qty)
        if record.on_hand_qty < 0:
            raise HTTPException(status_code=400, detail="库存不足")
    elif tx_type == "盘点调整":
        record.on_hand_qty = qty

    # 记录流水
    tx = InventoryTransaction(
        item_id=item_id,
        warehouse_id=warehouse_id,
        transaction_type=tx_type,
        quantity=qty,
        reference_no=data.get("reference_no", ""),
        batch_no=data.get("batch_no", ""),
        location_code=data.get("location_code", ""),
        operator=data.get("operator", ""),
        remark=data.get("remark", ""),
    )
    db.add(tx)
    db.flush()

    # 如果是产品出库，自动关联销售订单
    item = db.query(MaterialMaster).filter(MaterialMaster.id == item_id).first()
    if item and item.level_type == "产品" and tx_type in ("出库", "销售出库"):
        from app.models.sales import SalesOrder
        abs_qty = abs(qty)
        # 找最早的未全部出货的订单
        orders = db.query(SalesOrder).filter(
            SalesOrder.item_id == item_id,
            SalesOrder.ship_status.in_(["待出货", "部分出货"])
        ).order_by(SalesOrder.delivery_date.asc(), SalesOrder.id.asc()).all()
        remaining = abs_qty
        for order in orders:
            if remaining <= 0:
                break
            need = order.order_qty - (order.shipped_qty or 0)
            if need <= 0:
                continue
            allocate = min(remaining, need)
            order.shipped_qty = (order.shipped_qty or 0) + allocate
            order.ship_status = "全部出货" if order.shipped_qty >= order.order_qty else "部分出货"
            # 更新综合状态
            if order.ship_status == "全部出货" and order.pay_status == "全部收款":
                order.status = "已完成"
            remaining -= allocate
            # 全部出货 → 标记MPS完成
            if order.ship_status == "全部出货":
                from app.models.mps import MpsEntry
                mps = db.query(MpsEntry).filter(
                    MpsEntry.source_type == "销售订单",
                    MpsEntry.source_id == order.order_number,
                    MpsEntry.status == "进行中"
                ).first()
                if mps:
                    mps.status = "已完成"

    db.commit()

    return {"success": True, "message": f"{tx_type}成功"}


@router.get("/transactions")
def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    item_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """库存流水"""
    query = db.query(InventoryTransaction)
    if item_id:
        query = query.filter(InventoryTransaction.item_id == item_id)

    total = query.count()
    txs = query.order_by(InventoryTransaction.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "items": [
            {
                "id": t.id, "item_id": t.item_id,
                "material_code": t.item.material_code if t.item else "",
                "material_name": t.item.material_name if t.item else "",
                "transaction_type": t.transaction_type, "quantity": t.quantity,
                "reference_no": t.reference_no, "operator": t.operator,
                "remark": t.remark,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in txs
        ],
        "total": total, "page": page, "page_size": page_size,
    }


# ====== 仓库管理 ======
@router.get("/warehouses")
def list_warehouses(db: Session = Depends(get_db)):
    """仓库列表"""
    warehouses = db.query(Warehouse).filter(Warehouse.is_active == True).all()
    return {
        "items": [
            {"id": w.id, "warehouse_code": w.warehouse_code, "warehouse_name": w.warehouse_name}
            for w in warehouses
        ]
    }


@router.post("/warehouses")
def create_warehouse(data: dict, db: Session = Depends(get_db)):
    """创建仓库"""
    wh = Warehouse(**data)
    db.add(wh)
    db.commit()
    return {"success": True, "data": {"id": wh.id}}
