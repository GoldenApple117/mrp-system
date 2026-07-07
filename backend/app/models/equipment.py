"""设备台账 + 模具管理 + 保养计划模型"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base


class Equipment(Base):
    """设备台账"""
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    equipment_code = Column(String(50), unique=True, nullable=False, comment="设备编码")
    equipment_name = Column(String(200), nullable=False, comment="设备名称")
    model_spec = Column(String(200), default="", comment="型号规格")
    work_center_id = Column(Integer, ForeignKey("work_center.id"), nullable=True, comment="所属工作中心")
    manufacturer = Column(String(200), default="", comment="制造商")
    purchase_date = Column(Date, nullable=True, comment="购买日期")
    warranty_expiry = Column(Date, nullable=True, comment="保修到期")
    status = Column(String(20), default="运行中", comment="状态: 运行中/停机/维修中/报废")
    location = Column(String(200), default="", comment="位置")
    remark = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    work_center = relationship("WorkCenter", lazy="selectin")


class Tooling(Base):
    """模具/工装管理"""
    __tablename__ = "tooling"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tooling_code = Column(String(50), unique=True, nullable=False, comment="模具编码")
    tooling_name = Column(String(200), nullable=False, comment="模具名称")
    item_id = Column(Integer, ForeignKey("material_master.id"), nullable=True, comment="关联物料")
    max_life = Column(Integer, default=0, comment="额定寿命(次数)")
    current_life = Column(Integer, default=0, comment="已用寿命(次数)")
    status = Column(String(20), default="可用", comment="状态: 可用/使用中/维修中/报废")
    last_maintenance_date = Column(Date, nullable=True, comment="上次保养日期")
    next_maintenance_date = Column(Date, nullable=True, comment="下次保养日期")
    location = Column(String(200), default="", comment="存放位置")
    remark = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    item = relationship("MaterialMaster", lazy="selectin")


class MaintenancePlan(Base):
    """保养计划"""
    __tablename__ = "maintenance_plan"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_no = Column(String(50), unique=True, nullable=False, comment="计划编号")
    target_type = Column(String(10), nullable=False, comment="保养对象: 设备/模具")
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=True, comment="关联设备")
    tooling_id = Column(Integer, ForeignKey("tooling.id"), nullable=True, comment="关联模具")
    plan_type = Column(String(20), default="月保", comment="保养类型: 日保/周保/月保/年保")
    description = Column(String(500), default="", comment="保养内容")
    scheduled_date = Column(Date, nullable=True, comment="计划日期")
    completed_date = Column(Date, nullable=True, comment="完成日期")
    status = Column(String(20), default="待执行", comment="状态: 待执行/执行中/已完成/延期")
    handler = Column(String(50), default="", comment="执行人")
    remark = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    equipment = relationship("Equipment", lazy="selectin")
    tooling = relationship("Tooling", lazy="selectin")
