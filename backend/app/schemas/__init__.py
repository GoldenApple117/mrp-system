"""Pydantic schemas"""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ====== 物料 ======
class MaterialCreate(BaseModel):
    material_code: str = ""
    classification_code: str = ""
    material_name: str
    specification: str = ""
    unit: str = "个"
    material_type: str = "原材料"
    level_type: str = "零件"
    lead_time: int = 0
    safety_stock: float = 0
    lot_size_rule: str = "LFL"
    lot_size_qty: float = 1
    min_order_qty: float = 0
    max_order_qty: float = 0
    scrap_rate: float = 0
    is_purchased: bool = True
    is_active: bool = True
    remark: str = ""


class MaterialUpdate(BaseModel):
    classification_code: Optional[str] = None
    material_name: Optional[str] = None
    specification: Optional[str] = None
    unit: Optional[str] = None
    material_type: Optional[str] = None
    level_type: Optional[str] = None
    lead_time: Optional[int] = None
    safety_stock: Optional[float] = None
    lot_size_rule: Optional[str] = None
    lot_size_qty: Optional[float] = None
    min_order_qty: Optional[float] = None
    max_order_qty: Optional[float] = None
    scrap_rate: Optional[float] = None
    is_purchased: Optional[bool] = None
    is_active: Optional[bool] = None
    remark: Optional[str] = None


class MaterialResponse(BaseModel):
    id: int
    material_code: str
    classification_code: str
    material_name: str
    specification: str
    unit: str
    material_type: str
    level_type: str
    lead_time: int
    safety_stock: float
    lot_size_rule: str
    lot_size_qty: float
    is_purchased: bool
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ====== BOM ======
class BomLineCreate(BaseModel):
    parent_item_id: Optional[int] = None
    item_id: int
    quantity: float = 1
    position: str = ""
    is_substitute: bool = False
    substitute_for_id: Optional[int] = None
    substitute_group: str = ""
    scrap_rate: float = 0
    sort_order: int = 0
    remark: str = ""


class BomHeaderCreate(BaseModel):
    bom_code: str
    product_id: int
    version: str = "A"
    status: str = "草稿"
    effective_date: Optional[date] = None
    lines: List[BomLineCreate] = []


class BomImportResult(BaseModel):
    success: bool
    message: str
    imported_count: int = 0
    errors: List[str] = []


# ====== MPS ======
class MpsCreate(BaseModel):
    item_id: int
    plan_date: date
    quantity: float
    source_type: str = "手动"
    source_id: str = ""


class MpsBatchCreate(BaseModel):
    entries: List[MpsCreate]


# ====== MRP ======
class MrpRunRequest(BaseModel):
    horizon_days: int = Field(default=90, ge=1, le=365)
    time_fence_days: int = Field(default=7, ge=0, le=30)


class MrpResultResponse(BaseModel):
    planned_orders: List[dict]
    exceptions: List[dict]
    run_time: str


# ====== 采购 ======
class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    item_id: int
    order_qty: float
    due_date: date
    priority: int = 0
    remark: str = ""


class PurchaseOrderStatusUpdate(BaseModel):
    status: str
    received_qty: Optional[float] = None


# ====== 生产工单 ======
class WorkOrderCreate(BaseModel):
    item_id: int
    plan_qty: float
    start_date: date
    end_date: date
    work_center_id: Optional[int] = None
    routing_id: Optional[int] = None
    priority: int = 0
    remark: str = ""


# ====== 库存 ======
class InventoryTransactionCreate(BaseModel):
    item_id: int
    warehouse_id: int
    transaction_type: str  # 入库/出库/调拨/盘点调整
    quantity: float
    reference_no: str = ""
    batch_no: str = ""
    location_code: str = ""
    operator: str = ""
    remark: str = ""


# ====== 供应商 ======
class SupplierCreate(BaseModel):
    supplier_code: str
    supplier_name: str
    contact_person: str = ""
    contact_phone: str = ""
    address: str = ""
    lead_time_days: float = 0
    remark: str = ""


class ApiResponse(BaseModel):
    success: bool = True
    message: str = ""
    data: Optional[dict] = None


class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    page_size: int
