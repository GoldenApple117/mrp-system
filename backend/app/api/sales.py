"""销售管理 API — 客户 + 销售订单"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.sales import Customer, SalesOrder
from app.models.material import MaterialMaster
from app.models.mps import MpsEntry

router = APIRouter(prefix="/api/sales", tags=["销售管理"])


class SalesOrderCreate(BaseModel):
    """创建销售订单请求体"""
    customer_id: int
    item_id: int
    order_qty: float = 1
    unit_price: float = 0
    delivery_date: str  # ISO format: 2026-09-01
    priority: int = 0
    remark: str = ""

    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": 1,
                "item_id": 415,
                "order_qty": 100,
                "unit_price": 5000,
                "delivery_date": "2026-09-01",
            }
        }


# ====== 客户管理 ======

@router.get("/customers")
def list_customers(db: Session = Depends(get_db)):
    """客户列表"""
    customers = db.query(Customer).filter(Customer.is_active == True).all()
    return {
        "items": [
            {
                "id": c.id, "customer_code": c.customer_code, "customer_name": c.customer_name,
                "contact_person": c.contact_person, "contact_phone": c.contact_phone, "address": c.address,
            }
            for c in customers
        ]
    }


@router.post("/customers")
def create_customer(data: dict, db: Session = Depends(get_db)):
    """创建客户"""
    c = Customer(**{k: v for k, v in data.items() if hasattr(Customer, k)})
    db.add(c)
    db.commit()
    return {"success": True, "data": {"id": c.id, "customer_code": c.customer_code}}


# ====== 销售订单 ======

@router.get("/orders")
def list_sales_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """销售订单列表"""
    query = db.query(SalesOrder)
    if status:
        query = query.filter(SalesOrder.status == status)
    if keyword:
        query = query.filter(
            SalesOrder.order_number.ilike(f"%{keyword}%")
        )

    total = query.count()
    orders = query.order_by(SalesOrder.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "items": [
            {
                "id": o.id, "order_number": o.order_number,
                "customer_id": o.customer_id,
                "customer_name": o.customer.customer_name if o.customer else "",
                "item_id": o.item_id,
                "material_code": o.item.material_code if o.item else "",
                "material_name": o.item.material_name if o.item else "",
                "unit": o.item.unit if o.item else "",
                "order_qty": o.order_qty, "shipped_qty": o.shipped_qty or 0,
                "unit_price": o.unit_price or 0, "total_amount": o.total_amount or 0,
                "paid_amount": o.paid_amount or 0,
                "delivery_date": o.delivery_date.isoformat() if o.delivery_date else None,
                "ship_status": o.ship_status or "待出货",
                "pay_status": o.pay_status or "未收款",
                "status": o.status or "进行中",
                "priority": o.priority, "remark": o.remark,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in orders
        ],
        "total": total, "page": page, "page_size": page_size,
    }


@router.post("/orders")
def create_sales_order(data: SalesOrderCreate, db: Session = Depends(get_db)):
    """创建销售订单"""
    today_str = date.today().strftime("%Y%m%d")
    last = db.query(SalesOrder).filter(
        SalesOrder.order_number.like(f"SO-{today_str}-%")
    ).order_by(SalesOrder.order_number.desc()).first()
    seq = int(last.order_number.split("-")[-1]) + 1 if last else 1
    order_number = f"SO-{today_str}-{seq:04d}"

    so = SalesOrder(
        order_number=order_number,
        customer_id=data.customer_id,
        item_id=data.item_id,
        order_qty=data.order_qty,
        unit_price=data.unit_price,
        total_amount=data.order_qty * data.unit_price,
        delivery_date=date.fromisoformat(data.delivery_date),
        ship_status="待出货",
        pay_status="未收款",
        status="进行中",
        priority=data.priority,
        remark=data.remark or "",
    )
    db.add(so)
    db.commit()
    return {"success": True, "data": {"id": so.id, "order_number": so.order_number}}


@router.put("/orders/{order_id}")
def update_sales_order(order_id: int, data: dict, db: Session = Depends(get_db)):
    so = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not so:
        raise HTTPException(status_code=404, detail="订单不存在")
    for field in ["order_qty", "unit_price", "total_amount", "delivery_date", "remark"]:
        if field in data:
            if field == "delivery_date" and isinstance(data[field], str) and data[field]:
                setattr(so, field, date.fromisoformat(data[field]))
            else:
                setattr(so, field, data[field])
    # 如果改了数量和单价，重新算总金额
    if "order_qty" in data or "unit_price" in data:
        so.total_amount = (so.order_qty or 1) * (so.unit_price or 0)
    db.commit()
    return {"success": True, "message": "已更新"}


@router.put("/orders/{order_id}/status")
def update_so_status(order_id: int, data: dict, db: Session = Depends(get_db)):
    """更新订单状态"""
    so = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not so:
        raise HTTPException(status_code=404, detail="订单不存在")
    so.status = data["status"]
    db.commit()
    return {"success": True, "message": f"状态更新为: {so.status}"}


@router.delete("/orders/{order_id}")
def delete_sales_order(order_id: int, db: Session = Depends(get_db)):
    """删除销售订单"""
    so = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if so and so.status in ("待出货", "已取消"):
        db.delete(so)
        db.commit()
        return {"success": True}
    raise HTTPException(status_code=400, detail="只能删除'待处理'或'已取消'状态的订单")


@router.post("/orders/{order_id}/to-mps")
def sales_order_to_mps(order_id: int, db: Session = Depends(get_db)):
    """将销售订单转化为MPS计划"""
    so = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not so:
        raise HTTPException(status_code=404, detail="订单不存在")

    existing = db.query(MpsEntry).filter(
        MpsEntry.item_id == so.item_id,
        MpsEntry.plan_date == so.delivery_date,
        MpsEntry.source_type == "销售订单",
    ).first()

    if existing:
        return {"success": False, "message": f"该产品在 {so.delivery_date} 已有MPS计划，请勿重复生成"}

    mps = MpsEntry(
        item_id=so.item_id,
        plan_date=so.delivery_date,
        quantity=so.order_qty,
        source_type="销售订单",
        source_id=so.order_number,
        status="进行中",
    )
    db.add(mps)
    db.commit()

    return {
        "success": True,
        "message": f"已生成MPS计划: {so.item.material_name if so.item else ''} x{so.order_qty} @ {so.delivery_date}",
    }


@router.post("/orders/{order_id}/ship")
def ship_sales_order(order_id: int, data: dict = None, db: Session = Depends(get_db)):
    """销售出库 — 从成品库存扣减并更新出货状态"""
    from app.models.inventory import InventoryRecord, InventoryTransaction
    from datetime import datetime

    so = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not so:
        raise HTTPException(status_code=404, detail="订单不存在")
    if so.ship_status == "已出货":
        raise HTTPException(status_code=400, detail="该订单已出货")

    data = data or {}
    ship_qty = data.get("shipped_qty", so.order_qty - (so.shipped_qty or 0))

    # 查成品库存
    inv = db.query(InventoryRecord).filter(InventoryRecord.item_id == so.item_id).first()
    if not inv or inv.on_hand_qty < ship_qty:
        raise HTTPException(
            status_code=400,
            detail=f"库存不足：需求{ship_qty}，可用{inv.on_hand_qty if inv else 0}"
        )

    # 扣减库存
    inv.on_hand_qty -= ship_qty

    # 记录流水
    db.add(InventoryTransaction(
        item_id=so.item_id,
        warehouse_id=inv.warehouse_id,
        transaction_type="销售出库",
        quantity=-ship_qty,
        reference_no=so.order_number,
        operator="系统",
        remark=f"订单{so.order_number}出货{ship_qty}，客户{so.customer.customer_name if so.customer else ''}",
    ))

    # 更新订单
    so.shipped_qty = (so.shipped_qty or 0) + ship_qty
    if so.shipped_qty >= so.order_qty:
        so.ship_status = "已出货"
        so.status = "已完成"
    else:
        so.ship_status = "部分出货"

    db.commit()

    return {
        "success": True,
        "message": f"出货{ship_qty}，库存剩余{inv.on_hand_qty}，订单状态{so.ship_status}",
        "data": {
            "shipped_qty": so.shipped_qty,
            "order_qty": so.order_qty,
            "ship_status": so.ship_status,
            "remaining_stock": inv.on_hand_qty,
        }
    }
