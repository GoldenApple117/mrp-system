"""层级BOM模型 — 父子结构"""
from datetime import datetime, date
from sqlalchemy import Column, BigInteger, String, Float, Boolean, Integer, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class BomHeader(Base):
    """BOM 头表 — 一个成品/半成品对应一个BOM版本"""
    __tablename__ = "bom_header"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bom_code = Column(String(50), unique=True, nullable=False, comment="BOM编号")
    product_id = Column(Integer, ForeignKey("material_master.id"), nullable=False, comment="成品/父物料ID")
    version = Column(String(20), default="A", comment="版本号")
    revision = Column(String(10), default="0", comment="修订号(ECN)")
    status = Column(String(20), default="草稿", comment="状态：草稿/生效/失效")
    effective_date = Column(Date, default=date.today, comment="生效日期")
    expire_date = Column(Date, nullable=True, comment="失效日期")
    change_reason = Column(Text, default="", comment="ECN变更原因")
    created_by = Column(String(50), default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    product = relationship("MaterialMaster", foreign_keys=[product_id], lazy="selectin")
    lines = relationship("BomLine", back_populates="header", cascade="all, delete-orphan", lazy="selectin")


class BomLine(Base):
    """BOM 行表 — 每行记录一对父子物料关系"""
    __tablename__ = "bom_line"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bom_header_id = Column(Integer, ForeignKey("bom_header.id"), nullable=False, comment="所属BOM头")
    parent_item_id = Column(Integer, ForeignKey("material_master.id"), nullable=True, comment="父物料ID(NULL=顶层成品)")
    item_id = Column(Integer, ForeignKey("material_master.id"), nullable=False, comment="子物料ID")
    quantity = Column(Float, nullable=False, default=1, comment="单位用量")
    position = Column(String(10), default="", comment="位号")
    is_substitute = Column(Boolean, default=False, comment="是否替代料")
    substitute_for_id = Column(Integer, nullable=True, comment="替代哪个物料")
    substitute_group = Column(String(20), default="", comment="替代组(同组可替换)")
    scrap_rate = Column(Float, default=0, comment="工序损耗率")
    level = Column(Integer, default=0, comment="层级深度(0=成品直接下级)")
    sort_order = Column(Integer, default=0, comment="排序")
    remark = Column(String(500), default="")

    header = relationship("BomHeader", back_populates="lines")
    parent_item = relationship("MaterialMaster", foreign_keys=[parent_item_id], lazy="selectin")
    item = relationship("MaterialMaster", foreign_keys=[item_id], lazy="selectin")


class BomEcn(Base):
    """ECN工程变更记录"""
    __tablename__ = "bom_ecn"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ecn_number = Column(String(50), unique=True, nullable=False, comment="ECN编号")
    bom_header_id = Column(Integer, ForeignKey("bom_header.id"), nullable=False, comment="关联BOM")
    change_type = Column(String(20), default="修订", comment="变更类型：新建/修订/替代/停用")
    reason = Column(Text, default="", comment="变更原因")
    old_content = Column(Text, default="", comment="变更前内容(JSON)")
    new_content = Column(Text, default="", comment="变更后内容(JSON)")
    status = Column(String(20), default="申请", comment="状态：申请/已审批/已执行/已驳回")
    applicant = Column(String(50), default="", comment="申请人")
    approver = Column(String(50), default="", comment="审批人")
    approved_at = Column(DateTime, nullable=True, comment="审批时间")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

