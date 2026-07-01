"""项目财务管理 — 收款记录"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Payment(Base):
    __tablename__ = "payment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    payment_number = Column(String(50), unique=True, nullable=False, comment="收款单号")
    sales_order_id = Column(Integer, ForeignKey("sales_order.id"), nullable=False, comment="关联销售订单")
    customer_id = Column(Integer, ForeignKey("customer.id"), nullable=False, comment="客户")
    amount = Column(Float, nullable=False, default=0, comment="收款金额")
    payment_date = Column(Date, nullable=True, comment="收款日期")
    status = Column(String(20), default="未到账", comment="状态: 未到账/已到账/部分到账")
    payment_method = Column(String(30), default="", comment="付款方式")
    remark = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    sales_order = relationship("SalesOrder", lazy="selectin")
    customer = relationship("Customer", lazy="selectin")
