"""MPS主生产计划模型"""
from datetime import datetime, date
from sqlalchemy import Column, BigInteger, Integer, String, Float, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class MpsEntry(Base):
    __tablename__ = "mps_entry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("material_master.id"), nullable=False, comment="成品物料")
    plan_date = Column(Date, nullable=False, comment="计划日期")
    quantity = Column(Float, nullable=False, default=0, comment="计划数量")
    source_type = Column(String(20), default="手动", comment="来源：销售订单/预测/手动")
    source_id = Column(String(50), default="", comment="来源单号")
    status = Column(String(20), default="进行中", comment="状态：进行中/已完成")
    is_frozen = Column(Boolean, default=False, comment="是否冻结")
    frozen_until = Column(Date, nullable=True, comment="冻结至")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    item = relationship("MaterialMaster", lazy="selectin")
