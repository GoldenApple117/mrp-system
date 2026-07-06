"""MRP运行记录 — 替代全局变量缓存，持久化到数据库"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.mysql import LONGTEXT
from app.core.database import Base
from datetime import datetime
import json


class MrpRunRecord(Base):
    """每次MRP运算的结果快照"""
    __tablename__ = "mrp_run_record"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(50), unique=True, nullable=False, comment="MRP运行批次ID")
    planned_orders_json = Column(LONGTEXT, default="[]", comment="计划订单列表(JSON)")
    summary_json = Column(LONGTEXT, default="{}", comment="运算摘要(JSON)")
    created_at = Column(DateTime, default=datetime.now, comment="运算时间")

    @property
    def planned_orders(self) -> list:
        return json.loads(self.planned_orders_json) if self.planned_orders_json else []

    @planned_orders.setter
    def planned_orders(self, value: list):
        self.planned_orders_json = json.dumps(value, default=str)

    @property
    def summary(self) -> dict:
        return json.loads(self.summary_json) if self.summary_json else {}

    @summary.setter
    def summary(self, value: dict):
        self.summary_json = json.dumps(value, default=str)
