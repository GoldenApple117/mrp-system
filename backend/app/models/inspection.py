"""质量管理模型 — 检验标准 / 检验记录 / 不合格品处理 (NCR)"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base


class InspectionStandard(Base):
    """检验标准 — 定义某物料在某个环节需要检什么、怎么检"""
    __tablename__ = "inspection_standard"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("material_master.id"), nullable=False, comment="物料")
    standard_code = Column(String(50), nullable=False, comment="标准编码")
    standard_name = Column(String(200), default="", comment="标准名称")
    inspection_type = Column(String(10), nullable=False, comment="类型: IQC / PQC / OQC")
    sampling_method = Column(String(20), default="全检", comment="抽样方式: 全检 / AQL / 百分比")
    aql_level = Column(String(10), default="", comment="AQL 等级")
    sample_size = Column(Float, default=0, comment="抽检数量")
    accept_level = Column(Float, default=0, comment="允收标准（不合格数上限）")
    characteristics = Column(Text, default="", comment="检验特性（JSON：名称/规格/方法/量具）")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    item = relationship("MaterialMaster", lazy="selectin")


class InspectionRecord(Base):
    """检验记录 — 支持 IQC / PQC / OQC 三种类型"""
    __tablename__ = "inspection_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    inspection_no = Column(String(50), unique=True, nullable=False, comment="检验单号")
    inspection_type = Column(String(10), default="IQC", comment="类型: IQC / PQC / OQC")
    source_type = Column(String(20), default="采购单", comment="来源类型: 采购单 / 工单 / 工单工序 / 出货单")
    source_id = Column(Integer, nullable=False, comment="关联单号ID")
    standard_id = Column(Integer, ForeignKey("inspection_standard.id"), nullable=True, comment="检验标准")
    item_id = Column(Integer, ForeignKey("material_master.id"), nullable=False, comment="物料")
    inspect_qty = Column(Float, nullable=False, comment="检验数量")
    pass_qty = Column(Float, default=0, comment="合格数量")
    reject_qty = Column(Float, default=0, comment="不合格数量")
    inspector = Column(String(50), default="", comment="检验员")
    result = Column(String(20), default="待检", comment="结果: 待检 / 合格 / 部分合格 / 不合格")
    remark = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    standard = relationship("InspectionStandard", lazy="selectin")
    item = relationship("MaterialMaster", lazy="selectin")


class InspectionDefect(Base):
    """检验缺陷明细 — 每条不合格品记录一条"""
    __tablename__ = "inspection_defect"

    id = Column(Integer, primary_key=True, autoincrement=True)
    inspection_id = Column(Integer, ForeignKey("inspection_record.id"), nullable=False, comment="关联检验")
    defect_code = Column(String(50), default="", comment="缺陷编码")
    defect_name = Column(String(200), default="", comment="缺陷名称")
    severity = Column(String(10), default="一般", comment="严重度: 致命 / 严重 / 一般 / 轻微")
    qty = Column(Float, default=0, comment="缺陷数量")
    created_at = Column(DateTime, default=datetime.now)

    inspection = relationship("InspectionRecord", lazy="selectin")


class NcrRecord(Base):
    """不合格品处理单 (NCR) — 对不合格品的评审与处置"""
    __tablename__ = "ncr_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ncr_no = Column(String(50), unique=True, nullable=False, comment="NCR 编号")
    source_type = Column(String(20), nullable=False, comment="来源类型")
    source_id = Column(Integer, nullable=False, comment="来源单号ID")
    inspection_id = Column(Integer, ForeignKey("inspection_record.id"), nullable=True, comment="关联检验")
    item_id = Column(Integer, ForeignKey("material_master.id"), nullable=False, comment="物料")
    qty = Column(Float, default=0, comment="不合格数量")
    defect_type = Column(String(100), default="", comment="缺陷分类")
    severity = Column(String(10), default="一般", comment="严重度: 致命 / 严重 / 一般 / 轻微")
    disposition = Column(String(20), default="待处理", comment="处理方式: 待处理 / 退货 / 让步接收 / 返工 / 报废 / 降级")
    disposition_qty = Column(Float, default=0, comment="处置数量")
    description = Column(Text, default="", comment="问题描述")
    reviewer = Column(String(50), default="", comment="评审人")
    approver = Column(String(50), default="", comment="批准人")
    status = Column(String(20), default="待处理", comment="状态: 待处理 / 评审中 / 已处理 / 已关闭")
    resolved_at = Column(DateTime, nullable=True, comment="处理完成时间")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    inspection = relationship("InspectionRecord", lazy="selectin")
    item = relationship("MaterialMaster", lazy="selectin")


class StockCount(Base):
    """盘点记录"""
    __tablename__ = "stock_count"

    id = Column(Integer, primary_key=True, autoincrement=True)
    count_no = Column(String(50), unique=True, nullable=False, comment="盘点单号")
    warehouse_id = Column(Integer, ForeignKey("warehouse.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("material_master.id"), nullable=False)
    system_qty = Column(Float, default=0, comment="系统库存")
    actual_qty = Column(Float, default=0, comment="实际盘点数量")
    difference = Column(Float, default=0, comment="差异(实际-系统)")
    status = Column(String(20), default="待盘点", comment="状态：待盘点/已盘点/已调整")
    counter = Column(String(50), default="", comment="盘点人")
    count_date = Column(Date, default=date.today, comment="盘点日期")
    remark = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    warehouse = relationship("Warehouse", lazy="selectin")
    item = relationship("MaterialMaster", lazy="selectin")
