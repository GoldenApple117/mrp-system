"""销售订单服务 — 统一状态更新逻辑"""
from sqlalchemy.orm import Session


class SalesOrderService:
    """所有销售订单状态变更的唯一入口"""

    @staticmethod
    def update_ship_status(db: Session, order, shipped_qty: float):
        """更新出货数量和出货状态，自动重算综合状态"""
        from app.models.sales import SalesOrder
        order.shipped_qty = shipped_qty
        if shipped_qty <= 0:
            order.ship_status = "待出货"
        elif shipped_qty >= (order.order_qty or 1):
            order.ship_status = "全部出货"
        else:
            order.ship_status = "部分出货"
        SalesOrderService._recalc_composite_status(db, order)

    @staticmethod
    def update_pay_status(db: Session, order, paid_amount: float):
        """更新收款金额和收款状态，自动重算综合状态"""
        order.paid_amount = paid_amount
        order_total = order.total_amount or (order.order_qty or 1) * (order.unit_price or 0)
        if paid_amount <= 0:
            order.pay_status = "未收款"
        elif paid_amount >= order_total:
            order.pay_status = "全部收款"
        else:
            order.pay_status = "部分收款"
        SalesOrderService._recalc_composite_status(db, order)

    @staticmethod
    def sync_payment(db: Session, order_id: int):
        """从付款记录汇总已收款金额并更新订单"""
        from sqlalchemy import func
        from app.models.payment import Payment
        from app.models.sales import SalesOrder
        order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
        if not order:
            return
        total_paid = db.query(func.sum(Payment.amount)).filter(
            Payment.sales_order_id == order_id,
            Payment.status == "已到账",
        ).scalar() or 0
        SalesOrderService.update_pay_status(db, order, float(total_paid))

    @staticmethod
    def allocate_shipment(db: Session, item_id: int, qty: float):
        """将出货数量分配给最早未完成出货的订单"""
        from app.models.sales import SalesOrder
        orders = db.query(SalesOrder).filter(
            SalesOrder.item_id == item_id,
            SalesOrder.ship_status.in_(["待出货", "部分出货"]),
        ).order_by(SalesOrder.delivery_date.asc(), SalesOrder.id.asc()).all()

        remaining = qty
        for order in orders:
            if remaining <= 0:
                break
            need = (order.order_qty or 0) - (order.shipped_qty or 0)
            if need <= 0:
                continue
            allocate = min(remaining, need)
            SalesOrderService.update_ship_status(
                db, order, (order.shipped_qty or 0) + allocate
            )
            remaining -= allocate

    @staticmethod
    def _recalc_composite_status(db: Session, order):
        """综合状态：全部出货 + 全部收款 → 已完成"""
        if order.ship_status == "全部出货" and order.pay_status == "全部收款":
            order.status = "已完成"

    @staticmethod
    def mark_mps_completed(db: Session, order):
        """全部出货时标记对应的MPS为已完成"""
        from app.models.mps import MpsEntry
        mps = db.query(MpsEntry).filter(
            MpsEntry.source_type == "销售订单",
            MpsEntry.source_id == order.order_number,
            MpsEntry.status == "进行中",
        ).first()
        if mps:
            mps.status = "已完成"
