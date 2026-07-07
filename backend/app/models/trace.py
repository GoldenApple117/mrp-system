"""批次追溯与序列号管理模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class BatchRecord(Base):
    """批次主档 — 记录每个批次的来源与状态"""
    __tablename__ = "batch_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_no = Column(String(50), unique=True, nullable=False, comment="批次号")
    item_id = Column(Integer, ForeignKey("material_master.id"), nullable=False, comment="物料")
    supplier_id = Column(Integer, ForeignKey("supplier.id"), nullable=True, comment="供应商")
    po_id = Column(Integer, ForeignKey("purchase_order.id"), nullable=True, comment="来源采购单")
    received_date = Column(DateTime, nullable=True, comment="入库日期")
    expiry_date = Column(DateTime, nullable=True, comment="有效期/过期日期")
    qty = Column(Float, default=0, comment="批次总量")
    remaining_qty = Column(Float, default=0, comment="剩余库存")
    status = Column(String(20), default="在库", comment="状态: 在库/已用尽/已冻结/已过期")
    remark = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    item = relationship("MaterialMaster", lazy="selectin")
    supplier = relationship("Supplier", lazy="selectin")


class SerialNumber(Base):
    """序列号追踪 — 每个单品唯一的身份标识"""
    __tablename__ = "serial_number"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sn = Column(String(100), unique=True, nullable=False, comment="序列号")
    item_id = Column(Integer, ForeignKey("material_master.id"), nullable=False, comment="物料")
    batch_no = Column(String(50), nullable=True, comment="关联批次")
    status = Column(String(20), default="在库", comment="状态: 在库/已出库/在制/已发货/已退货/已报废")
    current_location = Column(String(200), default="", comment="当前位置描述")
    customer_id = Column(Integer, nullable=True, comment="最终客户")
    wo_id = Column(Integer, ForeignKey("work_order.id"), nullable=True, comment="生产工单")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    item = relationship("MaterialMaster", lazy="selectin")


class SerialNumberLog(Base):
    """序列号流转日志 — 记录每次状态变更"""
    __tablename__ = "serial_number_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    serial_number_id = Column(Integer, ForeignKey("serial_number.id"), nullable=False, comment="关联序列号")
    sn = Column(String(100), nullable=False, comment="序列号")
    event_type = Column(String(20), nullable=False, comment="事件: 入库/领料/上机/完工/出货/退货/报废")
    reference_no = Column(String(50), default="", comment="关联单号")
    operator = Column(String(50), default="", comment="操作人")
    remark = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)

    serial_number = relationship("SerialNumber", lazy="selectin")
