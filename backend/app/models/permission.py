"""权限请求模型 + 模块权限模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from app.core.database import Base


class PermissionRequest(Base):
    __tablename__ = "permission_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(16), default="pending", nullable=False)  # pending / approved / rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)


class UserModulePermission(Base):
    """用户 → 可访问模块的关联表（参考设备出机系统的 user_stage_permissions）"""
    __tablename__ = "user_module_permission"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    module_name = Column(String(50), nullable=False, comment="模块标识: materials / bom / purchase ...")
    granted_by = Column(String(50), default="", comment="授权人")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "module_name"),)
