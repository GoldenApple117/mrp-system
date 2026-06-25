"""工艺路线和工作中心模型"""
from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Float, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class WorkCenter(Base):
    __tablename__ = "work_center"

    id = Column(Integer, primary_key=True, autoincrement=True)
    center_code = Column(String(20), unique=True, nullable=False, comment="工作中心编码")
    center_name = Column(String(100), nullable=False, comment="工作中心名称")
    capacity_per_day = Column(Float, default=8, comment="日产能(小时)")
    efficiency = Column(Float, default=100, comment="效率(%)")
    machines_count = Column(Integer, default=1, comment="设备数量")
    workers_count = Column(Integer, default=1, comment="工人数量")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class RoutingHeader(Base):
    __tablename__ = "routing_header"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("material_master.id"), nullable=False, comment="适用物料")
    routing_code = Column(String(50), unique=True, nullable=False, comment="工艺编码")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    item = relationship("MaterialMaster", lazy="selectin")
    operations = relationship("RoutingOperation", back_populates="header", cascade="all, delete-orphan", lazy="selectin")


class RoutingOperation(Base):
    __tablename__ = "routing_operation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    routing_header_id = Column(Integer, ForeignKey("routing_header.id"), nullable=False)
    seq_no = Column(Integer, nullable=False, comment="工序序号")
    work_center_id = Column(Integer, ForeignKey("work_center.id"), nullable=False)
    operation_name = Column(String(100), nullable=False, comment="工序名称")
    setup_time = Column(Float, default=0, comment="准备时间(小时)")
    run_time_per_unit = Column(Float, default=0, comment="单件工时(小时)")
    queue_time = Column(Float, default=0, comment="排队时间(小时)")

    header = relationship("RoutingHeader", back_populates="operations")
    work_center = relationship("WorkCenter", lazy="selectin")
