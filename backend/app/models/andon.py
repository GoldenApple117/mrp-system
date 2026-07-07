"""安灯系统 + 生产看板模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class AndonEvent(Base):
    """安灯事件 — 生产异常报警与响应"""
    __tablename__ = "andon_event"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_no = Column(String(50), unique=True, nullable=False, comment="事件编号")
    work_order_id = Column(Integer, ForeignKey("work_order.id"), nullable=True, comment="关联工单")
    operation_id = Column(Integer, ForeignKey("work_order_operation.id"), nullable=True, comment="关联工序")
    work_center_id = Column(Integer, ForeignKey("work_center.id"), nullable=True, comment="关联工作中心")
    event_type = Column(String(20), nullable=False, comment="类型: 缺料/设备故障/质量问题/安全/其他")
    severity = Column(String(10), default="黄色", comment="严重度: 红色(停线)/黄色(预警)/蓝色(请求)")
    description = Column(Text, default="", comment="问题描述")
    handler = Column(String(50), default="", comment="响应人")
    response_time = Column(DateTime, nullable=True, comment="响应时间")
    resolve_time = Column(DateTime, nullable=True, comment="解决时间")
    status = Column(String(20), default="待响应", comment="状态: 待响应/处理中/已解决")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    work_order = relationship("WorkOrder", lazy="selectin")
    operation = relationship("WorkOrderOperation", lazy="selectin")
    work_center = relationship("WorkCenter", lazy="selectin")
