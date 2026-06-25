"""到货检验模型"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base


class InspectionRecord(Base):
    """到货检验记录"""
    __tablename__ = "inspection_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    inspection_no = Column(String(50), unique=True, nullable=False, comment="检验单号")
    purchase_order_id = Column(Integer, ForeignKey("purchase_order.id"), nullable=False, comment="关联采购单")
    item_id = Column(Integer, ForeignKey("material_master.id"), nullable=False, comment="物料")
    inspect_qty = Column(Float, nullable=False, comment="检验数量")
    pass_qty = Column(Float, default=0, comment="合格数量")
    reject_qty = Column(Float, default=0, comment="不合格数量")
    inspector = Column(String(50), default="", comment="检验员")
    result = Column(String(20), default="待检", comment="结果：待检/合格/部分合格/不合格")
    remark = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    purchase_order = relationship("PurchaseOrder", lazy="selectin")
    item = relationship("MaterialMaster", lazy="selectin")


class StockCount(Base):
    """盘点记录"""
    __tablename__ = "stock_count"

    id = Column(Integer, primary_key=True, autoincrement=True)
    count_no = Column(String(50), unique=True, nullable=False, comment="盘点单号")
    warehouse_id = Column(Integer, ForeignKey("warehouse.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("material_master.id"), nullable=False)
    system_qty = Column(Float, default=0, comment="系统库存")
    actual_qty = Column(Float, default=0, comment="实际盘点数量")
    difference = Column(Float, default=0, comment="差异(实际-系统)")
    status = Column(String(20), default="待盘点", comment="状态：待盘点/已盘点/已调整")
    counter = Column(String(50), default="", comment="盘点人")
    count_date = Column(Date, default=date.today, comment="盘点日期")
    remark = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    warehouse = relationship("Warehouse", lazy="selectin")
    item = relationship("MaterialMaster", lazy="selectin")
