"""SMTP邮件配置模型 — 单行配置表，永久存储在数据库"""
from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base


class SmtpConfig(Base):
    __tablename__ = "smtp_config"

    id = Column(Integer, primary_key=True, default=1)
    host = Column(String(256), default="")
    port = Column(Integer, default=587)
    username = Column(String(256), default="")
    password = Column(String(256), default="")  # 授权码
    from_addr = Column(String(256), default="")
    to_email = Column(String(1024), default="")  # 逗号分隔多个收件人
    use_tls = Column(Boolean, default=True)
