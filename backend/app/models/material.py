"""物料主数据模型"""
from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Integer, Float, Boolean, DateTime, Text
from app.core.database import Base
import enum


class MaterialType(str, enum.Enum):
    FINISHED = "成品"
    SEMI = "半成品"
    PART = "零件"
    RAW = "原材料"


class LotSizeRule(str, enum.Enum):
    LFL = "LFL"      # 按需定货
    FOQ = "FOQ"      # 固定批量
    EOQ = "EOQ"      # 经济批量
    MULT = "MULT"    # 倍数批量


class MaterialMaster(Base):
    __tablename__ = "material_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    material_code = Column(String(50), unique=True, nullable=False, index=True, comment="物料编码")
    material_name = Column(String(200), nullable=False, comment="物料名称")
    specification = Column(String(500), default="", comment="规格型号")
    unit = Column(String(20), default="个", comment="单位")
    material_type = Column(String(20), default=MaterialType.RAW.value, comment="物料类型：成品/半成品/零件/原材料")
    lead_time = Column(Integer, default=0, comment="提前期(天)")
    safety_stock = Column(Float, default=0, comment="安全库存")
    lot_size_rule = Column(String(20), default=LotSizeRule.LFL.value, comment="批量规则：LFL/FOQ/EOQ/MULT")
    lot_size_qty = Column(Float, default=1, comment="批量数量")
    min_order_qty = Column(Float, default=0, comment="最小订货量")
    max_order_qty = Column(Float, default=0, comment="最大订货量")
    scrap_rate = Column(Float, default=0, comment="损耗率(%)")
    is_purchased = Column(Boolean, default=True, comment="是否外购件(False=自制件)")
    is_active = Column(Boolean, default=True, comment="是否启用")
    remark = Column(Text, default="", comment="备注")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
