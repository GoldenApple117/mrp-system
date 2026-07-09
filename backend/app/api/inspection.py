"""质量管理 API — 检验标准 / IQC-PQC-OQC / NCR 不合格品处理 / 盘点"""
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
import json
import logging

logger = logging.getLogger(__name__)

from app.core.database import get_db
from app.models.order import PurchaseOrder, WorkOrder
from app.models.inventory import InventoryRecord, InventoryTransaction
from app.models.inspection import InspectionRecord, InspectionStandard, InspectionDefect, NcrRecord, StockCount

router = APIRouter(prefix="/api/inspection", tags=["质量管理"])


# ====== 兼容旧路径 ======

@router.get("")
def legacy_list_inspections(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    result: str = Query(None), db: Session = Depends(get_db),
):
    """兼容旧版前端 — 重定向到 inspections"""
    try:
        q = db.query(InspectionRecord).options(joinedload(InspectionRecord.item))
        if result: q = q.filter(InspectionRecord.result == result)
        total = q.count()
        items = q.order_by(InspectionRecord.id.desc()).offset(
            (page - 1) * page_size).limit(page_size).all()
        return {
            "items": [{
                "id": i.id, "inspection_no": i.inspection_no,
                "inspection_type": i.inspection_type,
                "po_number": getattr(i.purchase_order, 'po_number', '') if hasattr(i, 'purchase_order') else "",
                "material_code": i.item.material_code if i.item else "",
                "material_name": i.item.material_name if i.item else "",
                "inspect_qty": i.inspect_qty, "pass_qty": i.pass_qty,
                "reject_qty": i.reject_qty, "result": i.result,
                "inspector": i.inspector, "remark": i.remark,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            } for i in items],
            "total": total, "page": page, "page_size": page_size,
        }
    except Exception as e:
        import traceback
        logger.error(f"检验列表500: {e}\n{traceback.format_exc()}")
        raise HTTPException(500, detail=f"数据库查询异常: {str(e)}")


# ====== 检验标准 ======

@router.get("/standards")
def list_standards(
    item_id: int = Query(None), inspection_type: str = Query(None),
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """检验标准列表"""
    q = db.query(InspectionStandard)
    if item_id: q = q.filter(InspectionStandard.item_id == item_id)
    if inspection_type: q = q.filter(InspectionStandard.inspection_type == inspection_type)
    total = q.count()
    items = q.order_by(InspectionStandard.id.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()
    return {
        "items": [{
            "id": s.id, "standard_code": s.standard_code, "standard_name": s.standard_name,
            "item_id": s.item_id,
            "material_name": s.item.material_name if s.item else "",
            "inspection_type": s.inspection_type,
            "sampling_method": s.sampling_method, "aql_level": s.aql_level,
            "sample_size": s.sample_size, "accept_level": s.accept_level,
            "characteristics": json.loads(s.characteristics) if s.characteristics else [],
            "is_active": s.is_active,
        } for s in items],
        "total": total, "page": page, "page_size": page_size,
    }


@router.post("/standards")
def create_standard(data: dict, db: Session = Depends(get_db)):
    """创建检验标准"""
    std = InspectionStandard(
        item_id=data["item_id"],
        standard_code=data["standard_code"],
        standard_name=data.get("standard_name", ""),
        inspection_type=data.get("inspection_type", "IQC"),
        sampling_method=data.get("sampling_method", "全检"),
        aql_level=data.get("aql_level", ""),
        sample_size=data.get("sample_size", 0),
        accept_level=data.get("accept_level", 0),
        characteristics=json.dumps(data.get("characteristics", []), ensure_ascii=False),
    )
    db.add(std); db.commit()
    return {"success": True, "data": {"id": std.id}}


@router.put("/standards/{std_id}")
def update_standard(std_id: int, data: dict, db: Session = Depends(get_db)):
    """更新检验标准"""
    std = db.query(InspectionStandard).filter(InspectionStandard.id == std_id).first()
    if not std: raise HTTPException(404, "标准不存在")
    for k in ("standard_code", "standard_name", "inspection_type", "sampling_method",
              "aql_level", "sample_size", "accept_level", "is_active"):
        if k in data: setattr(std, k, data[k])
    if "characteristics" in data:
        std.characteristics = json.dumps(data["characteristics"], ensure_ascii=False)
    db.commit()
    return {"success": True}


@router.delete("/standards/{std_id}")
def delete_standard(std_id: int, db: Session = Depends(get_db)):
    std = db.query(InspectionStandard).filter(InspectionStandard.id == std_id).first()
    if not std: raise HTTPException(404, "标准不存在")
    db.delete(std); db.commit()
    return {"success": True}


# ====== 检验记录 (IQC / PQC / OQC) ======

@router.get("/inspections")
def list_inspections(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    inspection_type: str = Query(None), result: str = Query(None),
    source_type: str = Query(None), db: Session = Depends(get_db),
):
    """检验记录列表（含类型过滤）"""
    try:
        # 使用 joinedload 替代 selectin 加载，兼容云 MySQL
        q = db.query(InspectionRecord).options(joinedload(InspectionRecord.item))
        if inspection_type: q = q.filter(InspectionRecord.inspection_type == inspection_type)
        if result: q = q.filter(InspectionRecord.result == result)
        if source_type: q = q.filter(InspectionRecord.source_type == source_type)
        total = q.count()
        items = q.order_by(InspectionRecord.id.desc()).offset(
            (page - 1) * page_size).limit(page_size).all()
        return {
            "items": [{
                "id": i.id, "inspection_no": i.inspection_no,
                "inspection_type": i.inspection_type,
                "source_type": i.source_type, "source_id": i.source_id,
                "item_id": i.item_id,
                "material_code": i.item.material_code if i.item else "",
                "material_name": i.item.material_name if i.item else "",
                "inspect_qty": i.inspect_qty, "pass_qty": i.pass_qty,
                "reject_qty": i.reject_qty, "result": i.result,
                "inspector": i.inspector, "remark": i.remark,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            } for i in items],
            "total": total, "page": page, "page_size": page_size,
        }
    except Exception as e:
        import traceback
        logger.error(f"检验列表500: {e}\n{traceback.format_exc()}")
        raise HTTPException(500, detail=f"数据库查询异常: {str(e)}")


@router.post("/inspections")
def create_inspection(data: dict, db: Session = Depends(get_db)):
    """创建检验（自动判断类型，支持 IQC/PQC/OQC）
    来源类型: 采购单 / 工单 / 工单工序 / 出货单
    """
    now = datetime.now()
    insp_type = data.get("inspection_type", "IQC")
    prefix = {"IQC": "IQC", "PQC": "PQC", "OQC": "OQC"}
    insp = InspectionRecord(
        inspection_no=data.get("inspection_no",
            f"{prefix.get(insp_type, 'QC')}-{now.strftime('%Y%m%d%H%M%S')}"),
        inspection_type=insp_type,
        source_type=data.get("source_type", "采购单"),
        source_id=data["source_id"],
        standard_id=data.get("standard_id"),
        item_id=data["item_id"],
        inspect_qty=data["inspect_qty"],
        pass_qty=data.get("pass_qty", 0),
        reject_qty=data.get("reject_qty", 0),
        inspector=data.get("inspector", ""),
        result=data.get("result", "待检"),
        remark=data.get("remark", ""),
    )
    db.add(insp); db.commit(); db.refresh(insp)
    return {"success": True, "data": {"id": insp.id, "inspection_no": insp.inspection_no}}


@router.get("/inspections/{inspection_id}")
def get_inspection(inspection_id: int, db: Session = Depends(get_db)):
    """检验记录详情"""
    try:
        insp = db.query(InspectionRecord).options(
            joinedload(InspectionRecord.item),
            joinedload(InspectionRecord.standard),
        ).filter(InspectionRecord.id == inspection_id).first()
        if not insp: raise HTTPException(404, "检验记录不存在")
        return {
            "data": {
                "id": insp.id, "inspection_no": insp.inspection_no,
                "inspection_type": insp.inspection_type,
                "source_type": insp.source_type, "source_id": insp.source_id,
                "item_id": insp.item_id,
                "material_code": insp.item.material_code if insp.item else "",
                "material_name": insp.item.material_name if insp.item else "",
                "inspect_qty": insp.inspect_qty, "pass_qty": insp.pass_qty,
                "reject_qty": insp.reject_qty, "result": insp.result,
                "inspector": insp.inspector, "remark": insp.remark,
                "standard_code": insp.standard.standard_code if insp.standard else "",
                "created_at": insp.created_at.isoformat() if insp.created_at else None,
            },
        }
    except Exception as e:
        import traceback
        logger.error(f"检验详情500: {e}\n{traceback.format_exc()}")
        raise HTTPException(500, detail=f"查询异常: {str(e)}")


# ====== NCR 不合格品处理 ======

@router.get("/ncr")
def list_ncr(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """不合格品处理记录列表"""
    q = db.query(NcrRecord).order_by(NcrRecord.id.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [{
            "id": n.id, "ncr_no": n.ncr_no,
            "inspection_id": n.inspection_id,
            "inspection_no": n.inspection.inspection_no if n.inspection else "",
            "defect_description": n.defect_description,
            "disposition": n.disposition,
            "disposition_qty": n.disposition_qty,
            "status": n.status,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        } for n in items],
        "total": total,
    }


# ====== 检验缺陷明细 ======

@router.get("/inspections/{inspection_id}/defects")
def list_defects(inspection_id: int, db: Session = Depends(get_db)):
    """检验缺陷明细"""
    defects = db.query(InspectionDefect).filter(
        InspectionDefect.inspection_id == inspection_id).all()
    return {"items": [{
        "id": d.id, "defect_code": d.defect_code,
        "defect_description": d.defect_description,
        "defect_qty": d.defect_qty,
    } for d in defects]}


# ====== 库存盘点 ======

@router.get("/stock-counts")
def list_stock_counts(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(StockCount).order_by(StockCount.id.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [{
            "id": s.id, "count_no": s.count_no,
            "warehouse_id": s.warehouse_id,
            "item_id": s.item_id,
            "book_qty": s.book_qty, "actual_qty": s.actual_qty,
            "diff_qty": s.diff_qty,
            "status": s.status,
            "counted_at": s.counted_at.isoformat() if s.counted_at else None,
            "remark": s.remark,
        } for s in items],
        "total": total,
    }
