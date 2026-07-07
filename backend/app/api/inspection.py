"""质量管理 API — 检验标准 / IQC-PQC-OQC / NCR 不合格品处理 / 盘点"""
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import json

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
    q = db.query(InspectionRecord)
    if result: q = q.filter(InspectionRecord.result == result)
    total = q.count()
    items = q.order_by(InspectionRecord.id.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()
    return {
        "items": [{
            "id": i.id, "inspection_no": i.inspection_no,
            "inspection_type": i.inspection_type,
            "po_number": i.purchase_order.po_number if hasattr(i, 'purchase_order') and i.purchase_order else "",
            "material_code": i.item.material_code if i.item else "",
            "material_name": i.item.material_name if i.item else "",
            "inspect_qty": i.inspect_qty, "pass_qty": i.pass_qty,
            "reject_qty": i.reject_qty, "result": i.result,
            "inspector": i.inspector, "remark": i.remark,
            "created_at": i.created_at.isoformat() if i.created_at else None,
        } for i in items],
        "total": total, "page": page, "page_size": page_size,
    }


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
            "material_code": s.item.material_code if s.item else "",
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
    q = db.query(InspectionRecord)
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
        inspector=data.get("inspector", ""),
        remark=data.get("remark", ""),
    )
    db.add(insp); db.commit()
    return {"success": True, "data": {"id": insp.id, "inspection_no": insp.inspection_no}}


@router.put("/inspections/{inspection_id}/result")
def update_inspection_result(inspection_id: int, data: dict, db: Session = Depends(get_db)):
    """提报检验结果 — 合格入库 / 不合格触发 NCR"""
    insp = db.query(InspectionRecord).filter(InspectionRecord.id == inspection_id).first()
    if not insp: raise HTTPException(404, "检验单不存在")

    pass_qty = float(data.get("pass_qty", 0))
    reject_qty = float(data.get("reject_qty", 0))

    if pass_qty + reject_qty > insp.inspect_qty:
        raise HTTPException(400, "合格+不合格数量超过检验数量")

    insp.pass_qty = pass_qty
    insp.reject_qty = reject_qty
    if reject_qty == 0 and pass_qty >= insp.inspect_qty:
        insp.result = "合格"
    elif reject_qty > 0 and pass_qty > 0:
        insp.result = "部分合格"
    elif reject_qty >= insp.inspect_qty:
        insp.result = "不合格"
    else:
        insp.result = "合格"
    insp.inspector = data.get("inspector", insp.inspector)

    # 合格 → 入库（仅 IQC 采购入库场景）
    if pass_qty > 0 and insp.source_type == "采购单":
        wh_id = data.get("warehouse_id", 1)
        rec = db.query(InventoryRecord).filter(
            InventoryRecord.item_id == insp.item_id,
            InventoryRecord.warehouse_id == wh_id,
        ).first()
        if not rec:
            rec = InventoryRecord(item_id=insp.item_id, warehouse_id=wh_id)
            db.add(rec); db.flush()
        rec.on_hand_qty += pass_qty

        db.add(InventoryTransaction(
            item_id=insp.item_id, warehouse_id=wh_id,
            transaction_type="采购入库", quantity=pass_qty,
            reference_no=insp.inspection_no, operator=data.get("inspector", ""),
        ))

        # 更新采购单
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == insp.source_id).first()
        if po:
            po.received_qty = (po.received_qty or 0) + pass_qty
            if po.received_qty >= po.order_qty: po.status = "已完成"

    # 不合格 → 自动创建 NCR
    if reject_qty > 0:
        ncr_count = db.query(NcrRecord).count() + 1
        ncr = NcrRecord(
            ncr_no=f"NCR-{datetime.now().strftime('%Y%m%d')}-{ncr_count:04d}",
            source_type=insp.source_type, source_id=insp.source_id,
            inspection_id=insp.id, item_id=insp.item_id,
            qty=reject_qty, description=data.get("ncr_reason", ""),
            severity=data.get("severity", "一般"),
            status="待处理",
        )
        db.add(ncr)

    db.commit()
    return {
        "success": True,
        "message": f"检验完成：合格{pass_qty}件，不合格{reject_qty}件" +
                   ("，已创建NCR" if reject_qty > 0 else ""),
    }


# ====== 缺陷明细 ======

@router.get("/inspections/{inspection_id}/defects")
def list_defects(inspection_id: int, db: Session = Depends(get_db)):
    """查看检验缺陷明细"""
    defects = db.query(InspectionDefect).filter(
        InspectionDefect.inspection_id == inspection_id).all()
    return {"items": [{
        "id": d.id, "defect_code": d.defect_code, "defect_name": d.defect_name,
        "severity": d.severity, "qty": d.qty,
    } for d in defects]}


@router.post("/inspections/{inspection_id}/defects")
def add_defect(inspection_id: int, data: dict, db: Session = Depends(get_db)):
    """添加缺陷明细"""
    d = InspectionDefect(
        inspection_id=inspection_id,
        defect_code=data.get("defect_code", ""),
        defect_name=data["defect_name"],
        severity=data.get("severity", "一般"),
        qty=data.get("qty", 0),
    )
    db.add(d); db.commit()
    return {"success": True}


# ====== NCR 不合格品处理 ======

@router.get("/ncr")
def list_ncr(
    status: str = Query(None), severity: str = Query(None),
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """NCR 列表"""
    q = db.query(NcrRecord)
    if status: q = q.filter(NcrRecord.status == status)
    if severity: q = q.filter(NcrRecord.severity == severity)
    total = q.count()
    items = q.order_by(NcrRecord.id.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()
    return {
        "items": [{
            "id": n.id, "ncr_no": n.ncr_no,
            "source_type": n.source_type, "source_id": n.source_id,
            "item_id": n.item_id,
            "material_code": n.item.material_code if n.item else "",
            "material_name": n.item.material_name if n.item else "",
            "qty": n.qty, "defect_type": n.defect_type,
            "severity": n.severity, "disposition": n.disposition,
            "description": n.description, "reviewer": n.reviewer,
            "approver": n.approver, "status": n.status,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        } for n in items],
        "total": total, "page": page, "page_size": page_size,
    }


@router.post("/ncr")
def create_ncr(data: dict, db: Session = Depends(get_db)):
    """手动创建 NCR"""
    now = datetime.now()
    count = db.query(NcrRecord).count() + 1
    ncr = NcrRecord(
        ncr_no=f"NCR-{now.strftime('%Y%m%d')}-{count:04d}",
        source_type=data["source_type"],
        source_id=data["source_id"],
        inspection_id=data.get("inspection_id"),
        item_id=data["item_id"],
        qty=data.get("qty", 0),
        defect_type=data.get("defect_type", ""),
        severity=data.get("severity", "一般"),
        description=data.get("description", ""),
        status="待处理",
    )
    db.add(ncr); db.commit()
    return {"success": True, "data": {"id": ncr.id, "ncr_no": ncr.ncr_no}}


@router.put("/ncr/{ncr_id}/dispose")
def dispose_ncr(ncr_id: int, data: dict, db: Session = Depends(get_db)):
    """NCR 评审处置"""
    ncr = db.query(NcrRecord).filter(NcrRecord.id == ncr_id).first()
    if not ncr: raise HTTPException(404, "NCR 不存在")

    ncr.disposition = data.get("disposition", ncr.disposition)
    ncr.disposition_qty = data.get("disposition_qty", ncr.qty)
    ncr.reviewer = data.get("reviewer", ncr.reviewer)
    ncr.approver = data.get("approver", ncr.approver)

    if ncr.disposition in ("退货", "报废"):
        ncr.status = "已处理"
        ncr.resolved_at = datetime.now()
    elif ncr.disposition in ("让步接收", "返工"):
        ncr.status = "已处理"
        ncr.resolved_at = datetime.now()
        # 让步接收 → 更新库存
        if ncr.disposition == "让步接收" and ncr.source_type == "采购单":
            pass_qty = ncr.disposition_qty or ncr.qty
            wh_id = data.get("warehouse_id", 1)
            rec = db.query(InventoryRecord).filter(
                InventoryRecord.item_id == ncr.item_id,
                InventoryRecord.warehouse_id == wh_id,
            ).first()
            if rec:
                rec.on_hand_qty += pass_qty
    else:
        ncr.status = "评审中"

    db.commit()
    return {"success": True, "message": f"NCR 处置完成: {ncr.disposition}"}


# ====== 质量看板 ======

@router.get("/dashboard")
def quality_dashboard(db: Session = Depends(get_db)):
    """质量看板 — 合格率趋势 / 缺陷分布 / 待处理 NCR"""
    total_inspections = db.query(InspectionRecord).count()
    total_pass = db.query(InspectionRecord).with_entities(
        InspectionRecord.pass_qty).all()
    total_reject = db.query(InspectionRecord).with_entities(
        InspectionRecord.reject_qty).all()
    total_pass_qty = sum(p[0] or 0 for p in total_pass)
    total_reject_qty = sum(r[0] or 0 for r in total_reject)
    total_qty = total_pass_qty + total_reject_qty
    pass_rate = round(total_pass_qty / total_qty * 100, 1) if total_qty > 0 else 100

    pending_ncr = db.query(NcrRecord).filter(NcrRecord.status == "待处理").count()
    pending_insp = db.query(InspectionRecord).filter(InspectionRecord.result == "待检").count()

    # 按类型统计
    type_stats = {}
    for insp_type in ("IQC", "PQC", "OQC"):
        records = db.query(InspectionRecord).filter(
            InspectionRecord.inspection_type == insp_type).all()
        p = sum(r.pass_qty or 0 for r in records)
        rj = sum(r.reject_qty or 0 for r in records)
        total = p + rj
        type_stats[insp_type] = {
            "count": len(records), "pass_qty": p, "reject_qty": rj,
            "pass_rate": round(p / total * 100, 1) if total > 0 else 100,
        }

    return {
        "total_inspections": total_inspections,
        "total_pass_qty": total_pass_qty,
        "total_reject_qty": total_reject_qty,
        "pass_rate": pass_rate,
        "pending_ncr": pending_ncr,
        "pending_inspections": pending_insp,
        "by_type": type_stats,
    }


# ====== 盘点管理 ======

@router.get("/stock-counts")
def list_stock_counts(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None), db: Session = Depends(get_db),
):
    """盘点列表"""
    q = db.query(StockCount)
    if status: q = q.filter(StockCount.status == status)
    total = q.count()
    items = q.order_by(StockCount.id.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()
    return {
        "items": [{
            "id": s.id, "count_no": s.count_no,
            "warehouse_id": s.warehouse_id,
            "warehouse_name": s.warehouse.warehouse_name if s.warehouse else "",
            "material_code": s.item.material_code if s.item else "",
            "material_name": s.item.material_name if s.item else "",
            "system_qty": s.system_qty, "actual_qty": s.actual_qty,
            "difference": s.difference, "status": s.status,
            "counter": s.counter, "count_date": s.count_date.isoformat() if s.count_date else None,
        } for s in items],
        "total": total, "page": page, "page_size": page_size,
    }


@router.post("/stock-counts")
def create_stock_count(data: dict, db: Session = Depends(get_db)):
    """创建盘点计划"""
    now = datetime.now()
    rec = db.query(InventoryRecord).filter(
        InventoryRecord.item_id == data["item_id"],
        InventoryRecord.warehouse_id == data.get("warehouse_id", 1),
    ).first()
    sc = StockCount(
        count_no=f"COUNT-{now.strftime('%Y%m%d%H%M%S')}",
        warehouse_id=data.get("warehouse_id", 1),
        item_id=data["item_id"],
        system_qty=rec.on_hand_qty if rec else 0,
        status="待盘点", counter=data.get("counter", ""),
        remark=data.get("remark", ""),
    )
    db.add(sc); db.commit()
    return {"success": True, "data": {"id": sc.id, "count_no": sc.count_no}}


@router.put("/stock-counts/{count_id}/result")
def submit_stock_count(count_id: int, data: dict, db: Session = Depends(get_db)):
    """提交盘点结果"""
    sc = db.query(StockCount).filter(StockCount.id == count_id).first()
    if not sc: raise HTTPException(404, "盘点记录不存在")
    sc.actual_qty = data["actual_qty"]
    sc.difference = sc.actual_qty - sc.system_qty
    sc.status = "已盘点"
    sc.counter = data.get("counter", sc.counter)
    db.commit()
    return {"success": True, "message": f"盘点完成，差异{sc.difference:+.0f}件"}


@router.post("/stock-counts/{count_id}/adjust")
def adjust_stock(count_id: int, data: dict, db: Session = Depends(get_db)):
    """确认盘点差异，调整库存"""
    sc = db.query(StockCount).filter(StockCount.id == count_id).first()
    if not sc: raise HTTPException(404, "盘点记录不存在")
    if sc.status != "已盘点": raise HTTPException(400, "请先提交盘点结果")
    rec = db.query(InventoryRecord).filter(
        InventoryRecord.item_id == sc.item_id,
        InventoryRecord.warehouse_id == sc.warehouse_id,
    ).first()
    if rec:
        rec.on_hand_qty += sc.difference
        db.add(InventoryTransaction(
            item_id=sc.item_id, warehouse_id=sc.warehouse_id,
            transaction_type="盘点调整", quantity=sc.difference,
            reference_no=sc.count_no, operator=data.get("operator", "系统"),
            remark=f"盘点调整: 系统{sc.system_qty}→实盘{sc.actual_qty}",
        ))
    sc.status = "已调整"
    db.commit()
    return {"success": True, "message": f"库存已调整，差异{sc.difference:+.0f}件"}
