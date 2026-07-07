"""订单模型 — 采购订单 + 生产工单"""
from datetime import datetime, date
from sqlalchemy import Column, BigInteger, String, Float, Integer, Boolean, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class PurchaseOrder(Base):
    __tablename__ = "purchase_order"

    id = Column(Integer, primary_key=True, autoincrement=True)
    po_number = Column(String(50), unique=True, nullable=False, comment="采购单号")
    supplier_id = Column(Integer, ForeignKey("supplier.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("material_master.id"), nullable=False)
    order_qty = Column(Float, nullable=False, default=0, comment="订购数量")
    received_qty = Column(Float, default=0, comment="已收数量")
    due_date = Column(Date, nullable=False, comment="预计到货日期")
    status = Column(String(20), default="申请", comment="状态：申请/已审批/已下单/部分收货/已完成/已取消")
    source_type = Column(String(20), default="手动", comment="来源：MRP建议/手动")
    mrp_plan_id = Column(BigInteger, nullable=True, comment="关联MRP计划ID")
    unit_price = Column(Float, default=0, comment="单价")
    total_amount = Column(Float, default=0, comment="总金额")
    brand = Column(String(100), default="", comment="品牌")
    supplier_link = Column(String(1000), default="", comment="供应商/采购链接")
    submitter = Column(String(50), default="", comment="采购提交人")
    priority = Column(Integer, default=0, comment="优先级")
    remark = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    supplier = relationship("Supplier", lazy="selectin")
    item = relationship("MaterialMaster", lazy="selectin")


class WorkOrder(Base):
    __tablename__ = "work_order"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wo_number = Column(String(50), unique=True, nullable=False, comment="工单号")
    item_id = Column(Integer, ForeignKey("material_master.id"), nullable=False, comment="生产物料")
    plan_qty = Column(Float, nullable=False, default=0, comment="计划产量")
    completed_qty = Column(Float, default=0, comment="完成数量")
    start_date = Column(Date, nullable=False, comment="计划开始日期")
    end_date = Column(Date, nullable=False, comment="计划完成日期")
    actual_start = Column(DateTime, nullable=True, comment="实际开始")
    actual_end = Column(DateTime, nullable=True, comment="实际完成")
    rejected_qty = Column(Float, default=0, comment="不合格数量")
    labor_hours = Column(Float, default=0, comment="累计工时")
    status = Column(String(20), default="待下达", comment="状态：待下达/已下达/进行中/已完成/已关闭")
    work_center_id = Column(Integer, ForeignKey("work_center.id"), nullable=True)
    routing_id = Column(Integer, ForeignKey("routing_header.id"), nullable=True)
    priority = Column(Integer, default=0, comment="优先级")
    source_type = Column(String(20), default="手动", comment="来源：MRP建议/手动")
    mrp_plan_id = Column(BigInteger, nullable=True, comment="关联MRP计划ID")
    remark = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    item = relationship("MaterialMaster", lazy="selectin")
    work_center = relationship("WorkCenter", lazy="selectin")
    routing = relationship("RoutingHeader", lazy="selectin")
    materials = relationship("WorkOrderMaterial", lazy="selectin", cascade="all, delete-orphan")


class WorkOrderReport(Base):
    """工单报工记录 — 每次报工独立记录，保留报工历史"""
    __tablename__ = "work_order_report"

    id = Column(Integer, primary_key=True, autoincrement=True)
    work_order_id = Column(Integer, ForeignKey("work_order.id"), nullable=False, comment="工单ID")
    wo_number = Column(String(50), default="", comment="工单号（冗余，方便查询）")
    report_time = Column(DateTime, default=datetime.now, comment="报工时间")
    completed_qty = Column(Float, default=0, comment="本次完成数量")
    rejected_qty = Column(Float, default=0, comment="本次不合格数量")
    labor_hours = Column(Float, default=0, comment="本次工时")
    operator = Column(String(50), default="", comment="操作人")
    remark = Column(String(500), default="", comment="备注")
    created_at = Column(DateTime, default=datetime.now)

    work_order = relationship("WorkOrder", lazy="selectin")


class WorkOrderMaterial(Base):
    """工单物料需求 — 记录每个工单需要的原材料及其发料/消耗情况"""
    __tablename__ = "work_order_material"

    id = Column(Integer, primary_key=True, autoincrement=True)
    work_order_id = Column(Integer, ForeignKey("work_order.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("material_master.id"), nullable=False)
    required_qty = Column(Float, nullable=False, default=0, comment="需求数量")
    issued_qty = Column(Float, default=0, comment="已发料数量")
    unit_cost = Column(Float, default=0, comment="物料单价")
    total_cost = Column(Float, default=0, comment="物料总成本(unit_cost * issued_qty)")
    bom_line_id = Column(Integer, ForeignKey("bom_line.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    item = relationship("MaterialMaster", lazy="selectin")


class WorkOrderOperation(Base):
    """工单工序执行记录 — 将工单按工艺路线展开为逐序执行"""
    __tablename__ = "work_order_operation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    work_order_id = Column(Integer, ForeignKey("work_order.id"), nullable=False, comment="工单ID")
    routing_operation_id = Column(Integer, ForeignKey("routing_operation.id"), nullable=True, comment="关联工艺工序")
    seq_no = Column(Integer, nullable=False, comment="工序序号")
    operation_name = Column(String(100), nullable=False, comment="工序名称")
    work_center_id = Column(Integer, ForeignKey("work_center.id"), nullable=True, comment="执行工作中心")
    status = Column(String(20), default="待开工", comment="状态：待开工/进行中/待检验/已完成/跳过")
    plan_start = Column(Date, nullable=True, comment="计划开始")
    plan_end = Column(Date, nullable=True, comment="计划完成")
    actual_start = Column(DateTime, nullable=True, comment="实际开始时间")
    actual_end = Column(DateTime, nullable=True, comment="实际完成时间")
    completed_qty = Column(Float, default=0, comment="本工序完成数量")
    rejected_qty = Column(Float, default=0, comment="本工序不合格数量")
    labor_hours = Column(Float, default=0, comment="本工序总工时")
    setup_hours = Column(Float, default=0, comment="换线/准备工时")
    operator = Column(String(50), default="", comment="操作人")
    remark = Column(String(500), default="", comment="备注")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    work_order = relationship("WorkOrder", lazy="selectin")
    routing_operation = relationship("RoutingOperation", lazy="selectin")
    work_center = relationship("WorkCenter", lazy="selectin")
