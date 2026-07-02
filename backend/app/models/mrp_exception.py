"""MRP例外看板 — 持久化模型"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from app.core.database import Base
from datetime import datetime


class MrpException(Base):
    """MRP运算产生的例外信息"""
    __tablename__ = "mrp_exception"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(50), default="", comment="MRP运行批次ID")
    exception_type = Column(String(30), default="", comment="例外类型: SHORTAGE/OVERDUE_ORDER/SAFETY_STOCK_ALERT/SUBSTITUTE")
    item_code = Column(String(100), default="", comment="物料编码")
    material_name = Column(String(200), default="", comment="物料型号")
    message = Column(String(500), default="", comment="例外描述")
    severity = Column(String(20), default="INFO", comment="严重程度: ERROR/WARNING/INFO")
    is_resolved = Column(Boolean, default=False, comment="是否已处理")
    resolved_at = Column(DateTime, nullable=True, comment="处理时间")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
