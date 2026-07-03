"""用户模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(32), default="admin", nullable=False)
    is_approved = Column(Integer, default=1, nullable=False)  # 1=已授权, 0=待审批(仅normal用户)
    created_at = Column(DateTime, default=datetime.utcnow)
