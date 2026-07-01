"""项目财务管理 API"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.core.database import get_db
from app.models.payment import Payment
from app.models.sales import SalesOrder, Customer
from app.models.material import MaterialMaster

def sync_order_pay_status(order_id: int, db: Session):
    """同步销售订单的收款状态"""
    from app.models.sales import SalesOrder
    so = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not so: return
    total_paid = db.query(func.sum(Payment.amount)).filter(
        Payment.sales_order_id == order_id, Payment.status == "已到账"
    ).scalar() or 0
    so.paid_amount = total_paid
    order_total = so.total_amount or so.order_qty * so.unit_price or 0
    if total_paid <= 0:
        so.pay_status = "未收款"
    elif total_paid >= order_total:
        so.pay_status = "全部收款"
    else:
        so.pay_status = "部分收款"
    if so.ship_status == "全部出货" and so.pay_status == "全部收款":
        so.status = "已完成"


router = APIRouter(prefix="/api/finance", tags=["财务管理"])


@router.get("/payments")
def list_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Payment)
    if status:
        query = query.filter(Payment.status == status)
    if keyword:
        query = query.filter(
            (Payment.payment_number.ilike(f"%{keyword}%"))
        )
    total = query.count()
    payments = query.order_by(Payment.id.desc()).offset((page-1)*page_size).limit(page_size).all()

    return {
        "items": [
            {
                "id": p.id, "payment_number": p.payment_number,
                "sales_order_id": p.sales_order_id,
                "order_number": p.sales_order.order_number if p.sales_order else "",
                "order_qty": p.sales_order.order_qty if p.sales_order else 0,
                "shipped_qty": p.sales_order.shipped_qty or 0 if p.sales_order else 0,
                "customer_id": p.customer_id,
                "customer_name": p.customer.customer_name if p.customer else "",
                "product_name": p.sales_order.item.material_name if p.sales_order and p.sales_order.item else "",
                "amount": p.amount, "payment_date": p.payment_date.isoformat() if p.payment_date else None,
                "status": p.status, "payment_method": p.payment_method,
                "remark": p.remark,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in payments
        ],
        "total": total, "page": page, "page_size": page_size,
    }


@router.post("/payments")
def create_payment(data: dict, db: Session = Depends(get_db)):
    today = date.today().strftime("%Y%m%d")
    last = db.query(Payment).filter(Payment.payment_number.like(f"PAY-{today}-%")).order_by(Payment.id.desc()).first()
    seq = int(last.payment_number.split("-")[-1]) + 1 if last else 1
    p = Payment(
        payment_number=f"PAY-{today}-{seq:04d}",
        sales_order_id=data["sales_order_id"],
        customer_id=data["customer_id"],
        amount=data.get("amount", 0),
        payment_date=date.fromisoformat(data["payment_date"]) if data.get("payment_date") else None,
        status=data.get("status", "未到账"),
        payment_method=data.get("payment_method", ""),
        remark=data.get("remark", ""),
    )
    db.add(p)
    db.flush()
    sync_order_pay_status(p.sales_order_id, db)
    db.commit()
    return {"success": True, "data": {"id": p.id, "payment_number": p.payment_number}}


@router.put("/payments/{payment_id}")
def update_payment(payment_id: int, data: dict, db: Session = Depends(get_db)):
    p = db.query(Payment).filter(Payment.id == payment_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="收款记录不存在")
    for k in ["status", "payment_date", "amount", "payment_method", "remark"]:
        if k in data:
            if k == "payment_date" and isinstance(data[k], str) and data[k]:
                setattr(p, k, date.fromisoformat(data[k]))
            else:
                setattr(p, k, data[k])
    db.commit()
    sync_order_pay_status(p.sales_order_id, db)
    db.commit()
    return {"success": True, "message": "已更新"}


@router.delete("/payments/{payment_id}")
def delete_payment(payment_id: int, db: Session = Depends(get_db)):
    p = db.query(Payment).filter(Payment.id == payment_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="不存在")
    so_id = p.sales_order_id
    db.delete(p)
    db.commit()
    sync_order_pay_status(so_id, db)
    db.commit()
    return {"success": True, "message": "已删除"}


@router.get("/summary")
def finance_summary(db: Session = Depends(get_db)):
    """收款汇总"""
    from sqlalchemy import func
    from app.models.sales import SalesOrder
    # 总应收 = 所有销售订单金额
    total_receivable = db.query(func.sum(SalesOrder.total_amount)).filter(
        SalesOrder.status != "已取消"
    ).scalar() or 0
    # 已到账 = 所有已到账付款金额
    total_paid = db.query(func.sum(Payment.amount)).filter(Payment.status == "已到账").scalar() or 0
    total_pending = total_receivable - total_paid
    statuses = db.query(Payment.status, func.sum(Payment.amount), func.count()).group_by(Payment.status).all()

    return {
        "total_amount": float(total_receivable),
        "total_paid": float(total_paid),
        "total_pending": float(total_pending),
        "by_status": [{"status": s, "amount": float(a), "count": c} for s, a, c in statuses],
    }
