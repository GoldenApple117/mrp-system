"""库存模型 — 多仓库/库位/批次"""
from datetime import datetime, date
from sqlalchemy import Column, BigInteger, String, Float, Integer, Boolean, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Warehouse(Base):
    __tablename__ = "warehouse"

    id = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_code = Column(String(20), unique=True, nullable=False, comment="仓库编码")
    warehouse_name = Column(String(100), nullable=False, comment="仓库名称")
    location = Column(String(200), default="", comment="位置")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Warehouse {self.warehouse_name}>"


class InventoryRecord(Base):
    """库存记录 — 按物料+仓库+库位+批次维度"""
    __tablename__ = "inventory_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("material_master.id"), nullable=False, comment="物料ID")
    warehouse_id = Column(Integer, ForeignKey("warehouse.id"), nullable=False, comment="仓库ID")
    location_code = Column(String(50), default="", comment="库位编码")
    batch_no = Column(String(50), default="", comment="批次号")
    on_hand_qty = Column(Float, default=0, comment="现有库存")
    allocated_qty = Column(Float, default=0, comment="已分配量")
    reserved_qty = Column(Float, default=0, comment="已预留量")
    on_order_qty = Column(Float, default=0, comment="在途量(采购中)")
    on_production_qty = Column(Float, default=0, comment="在制量(生产中)")
    last_count_date = Column(Date, nullable=True, comment="上次盘点日期")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    item = relationship("MaterialMaster", lazy="selectin")
    warehouse = relationship("Warehouse", lazy="selectin")

    @property
    def available_qty(self):
        """可用量 = 现有库存 - 已分配 - 已预留"""
        return self.on_hand_qty - self.allocated_qty - self.reserved_qty


class InventoryTransaction(Base):
    """库存流水 — 出入库记录"""
    __tablename__ = "inventory_transaction"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("material_master.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouse.id"), nullable=False)
    transaction_type = Column(String(20), nullable=False, comment="类型：入库/出库/调拨/盘点调整")
    quantity = Column(Float, nullable=False, comment="数量(正=入库, 负=出库)")
    reference_no = Column(String(50), default="", comment="关联单号(采购单/工单)")
    batch_no = Column(String(50), default="")
    location_code = Column(String(50), default="")
    operator = Column(String(50), default="")
    remark = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)

    item = relationship("MaterialMaster", lazy="selectin")
    warehouse = relationship("Warehouse", lazy="selectin")
