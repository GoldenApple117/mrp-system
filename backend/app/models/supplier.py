"""供应商模型"""
from datetime import datetime
from sqlalchemy import Column, BigInteger, Integer, String, Float, DateTime, Text, Boolean
from app.core.database import Base


class Supplier(Base):
    __tablename__ = "supplier"

    id = Column(Integer, primary_key=True, autoincrement=True)
    supplier_code = Column(String(50), unique=True, nullable=False, comment="供应商编码")
    supplier_name = Column(String(200), nullable=False, comment="供应商名称")
    contact_person = Column(String(50), default="")
    contact_phone = Column(String(30), default="")
    address = Column(String(500), default="")
    lead_time_days = Column(Float, default=0, comment="平均交货天数")
    quality_rating = Column(Float, default=100, comment="质量评分")
    is_active = Column(Boolean, default=True)
    remark = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
