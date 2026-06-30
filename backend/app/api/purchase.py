"""采购管理 API"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
import os, uuid

from app.core.database import get_db
from app.core.config import UPLOAD_DIR
from app.models.order import PurchaseOrder
from app.models.supplier import Supplier
from app.models.material import MaterialMaster

router = APIRouter(prefix="/api/purchase", tags=["采购管理"])


@router.get("/orders")
def list_purchase_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """采购订单列表"""
    query = db.query(PurchaseOrder)

    if status:
        query = query.filter(PurchaseOrder.status == status)
    if keyword:
        query = query.filter(PurchaseOrder.po_number.ilike(f"%{keyword}%"))

    total = query.count()
    orders = query.order_by(PurchaseOrder.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "items": [
            {
                "id": o.id, "po_number": o.po_number,
                "supplier_id": o.supplier_id,
                "supplier_name": o.supplier.supplier_name if o.supplier else "",
                "item_id": o.item_id,
                "material_code": o.item.material_code if o.item else "",
                "material_name": o.item.material_name if o.item else "",
                "unit": o.item.unit if o.item else "",
                "order_qty": o.order_qty, "received_qty": o.received_qty,
                "due_date": o.due_date.isoformat() if o.due_date else None,
                "status": o.status, "source_type": o.source_type,
                "priority": o.priority, "remark": o.remark,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in orders
        ],
        "total": total, "page": page, "page_size": page_size,
    }


@router.post("/orders")
def create_purchase_order(data: dict, db: Session = Depends(get_db)):
    """创建采购订单"""
    # 自动生成唯一单号
    if "po_number" not in data or not data.get("po_number"):
        today_str = date.today().strftime("%Y%m%d")
        last_po = db.query(PurchaseOrder).filter(
            PurchaseOrder.po_number.like(f"PO-{today_str}-%")
        ).order_by(PurchaseOrder.po_number.desc()).first()
        if last_po:
            last_seq = int(last_po.po_number.split("-")[-1])
            seq = last_seq + 1
        else:
            seq = 1
        po_number = f"PO-{today_str}-{seq:04d}"
    else:
        po_number = data["po_number"]

    po = PurchaseOrder(
        po_number=po_number,
        supplier_id=data["supplier_id"],
        item_id=data["item_id"],
        order_qty=data["order_qty"],
        due_date=date.fromisoformat(data["due_date"]) if isinstance(data["due_date"], str) else data["due_date"],
        status=data.get("status", "申请"),
        source_type=data.get("source_type", "手动"),
        priority=data.get("priority", 0),
        remark=data.get("remark", ""),
    )
    db.add(po)
    db.commit()
    return {"success": True, "data": {"id": po.id, "po_number": po.po_number}}


@router.put("/orders/{order_id}/status")
def update_po_status(order_id: int, data: dict, db: Session = Depends(get_db)):
    """更新采购单状态"""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="采购单不存在")

    po.status = data["status"]
    if "received_qty" in data and data["received_qty"] is not None:
        po.received_qty = data["received_qty"]
    if po.status == "已完成" and po.received_qty == 0:
        po.received_qty = po.order_qty

    db.commit()
    return {"success": True, "message": f"状态更新为: {po.status}"}


@router.delete("/orders/{order_id}")
def delete_purchase_order(order_id: int, db: Session = Depends(get_db)):
    """删除采购单"""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if po and po.status == "申请":
        db.delete(po)
        db.commit()
        return {"success": True}
    raise HTTPException(status_code=400, detail="只能删除'申请'状态的采购单")


@router.post("/orders/import/excel")
async def import_purchase_orders(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Excel批量导入采购订单"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="仅支持 .xlsx / .xls 文件")

    import openpyxl
    file_path = os.path.join(UPLOAD_DIR, f"po_import_{uuid.uuid4().hex}.xlsx")
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    wb = openpyxl.load_workbook(file_path)
    ws = wb.active
    header_row = [cell.value for cell in ws[1]]
    expected = ["物料编码", "数量", "供应商编码", "交货日期", "备注"]
    col_map = {h: i for i, h in enumerate(header_row)}

    missing = [h for h in expected if h not in col_map]
    if missing:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"缺少列: {', '.join(missing)}")

    imported = 0
    errors = []
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        try:
            material_code = str(row[col_map["物料编码"]]).strip()
            qty = float(row[col_map["数量"]])
            supplier_code = str(row[col_map["供应商编码"]]).strip()
            due = str(row[col_map["交货日期"]]).strip()
            remark = str(row[col_map.get("备注", 4)]).strip() if col_map.get("备注", 4) < len(row) else ""

            material = db.query(MaterialMaster).filter(MaterialMaster.material_code == material_code).first()
            if not material:
                errors.append(f"第{i}行: 物料编码 {material_code} 不存在")
                continue
            supplier = db.query(Supplier).filter(Supplier.supplier_code == supplier_code).first()
            if not supplier:
                errors.append(f"第{i}行: 供应商编码 {supplier_code} 不存在")
                continue

            # 自动生成单号
            today_str = date.today().strftime("%Y%m%d")
            last_po = db.query(PurchaseOrder).filter(
                PurchaseOrder.po_number.like(f"PO-{today_str}-%")
            ).order_by(PurchaseOrder.po_number.desc()).first()
            seq = int(last_po.po_number.split("-")[-1]) + 1 if last_po else 1
            po_number = f"PO-{today_str}-{seq:04d}"

            po = PurchaseOrder(
                po_number=po_number,
                supplier_id=supplier.id,
                item_id=material.id,
                order_qty=qty,
                due_date=date.fromisoformat(due),
                status="申请",
                source_type="导入",
                remark=remark,
            )
            db.add(po)
            imported += 1
        except Exception as e:
            errors.append(f"第{i}行: {str(e)}")

    if imported:
        db.commit()
    os.remove(file_path)
    return {
        "success": True,
        "message": f"成功导入 {imported} 条采购订单",
        "errors": errors[:10],
        "total_errors": len(errors),
    }


@router.get("/orders/import/template")
def download_import_template():
    """下载采购订单导入模板"""
    import openpyxl
    from fastapi.responses import FileResponse

    file_path = os.path.join(UPLOAD_DIR, "po_import_template.xlsx")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "采购订单导入"
    ws.append(["物料编码", "数量", "供应商编码", "交货日期", "备注"])
    ws.append(["RM-001", 100, "SUP001", "2026-07-15", "急用"])
    ws.append(["RM-002", 200, "SUP001", "2026-07-20", ""])
    ws.column_dimensions['A'].width = 16
    ws.column_dimensions['B'].width = 10
    ws.column_dimensions['C'].width = 16
    ws.column_dimensions['D'].width = 14
    ws.column_dimensions['E'].width = 20
    wb.save(file_path)
    return FileResponse(file_path, filename="采购订单导入模板.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ====== 供应商管理 ======
@router.get("/suppliers")
def list_suppliers(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1),
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """供应商列表"""
    query = db.query(Supplier).filter(Supplier.is_active == True)
    if keyword:
        query = query.filter(
            (Supplier.supplier_code.ilike(f"%{keyword}%")) |
            (Supplier.supplier_name.ilike(f"%{keyword}%"))
        )
    total = query.count()
    suppliers = query.offset((page-1)*page_size).limit(page_size).all()

    return {
        "items": [
            {"id": s.id, "supplier_code": s.supplier_code, "supplier_name": s.supplier_name,
             "contact_person": s.contact_person, "contact_phone": s.contact_phone,
             "lead_time_days": s.lead_time_days}
            for s in suppliers
        ],
        "total": total,
    }


@router.post("/suppliers")
def create_supplier(data: dict, db: Session = Depends(get_db)):
    """创建供应商"""
    s = Supplier(**data)
    db.add(s)
    db.commit()
    return {"success": True, "data": {"id": s.id}}
