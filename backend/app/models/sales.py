"""销售模块模型 — 客户 + 销售订单"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Customer(Base):
    __tablename__ = "customer"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_code = Column(String(50), unique=True, nullable=False, comment="客户编码")
    customer_name = Column(String(200), nullable=False, comment="客户名称")
    contact_person = Column(String(50), default="")
    contact_phone = Column(String(30), default="")
    address = Column(String(500), default="")
    is_active = Column(Boolean, default=True)
    remark = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class SalesOrder(Base):
    __tablename__ = "sales_order"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_number = Column(String(50), unique=True, nullable=False, comment="销售订单号")
    customer_id = Column(Integer, ForeignKey("customer.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("material_master.id"), nullable=False, comment="产品物料")
    order_qty = Column(Float, nullable=False, default=1, comment="订单数量")
    shipped_qty = Column(Float, default=0, comment="已出货数量")
    unit_price = Column(Float, default=0, comment="单价")
    total_amount = Column(Float, default=0, comment="订单总金额")
    paid_amount = Column(Float, default=0, comment="已收款金额")
    delivery_date = Column(Date, nullable=False, comment="交期")
    ship_status = Column(String(20), default="待出货", comment="出货状态: 待出货/部分出货/全部出货")
    pay_status = Column(String(20), default="未收款", comment="收款状态: 未收款/部分收款/全部收款")
    status = Column(String(20), default="进行中", comment="综合状态: 进行中/已完成/已取消")
    priority = Column(Integer, default=0, comment="优先级")
    source_type = Column(String(20), default="手动", comment="来源")
    remark = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    customer = relationship("Customer", lazy="selectin")
    item = relationship("MaterialMaster", lazy="selectin")
