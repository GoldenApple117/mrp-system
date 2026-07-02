"""物料管理 API"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.material import MaterialMaster
from app.models.bom import BomHeader, BomLine
from app.schemas import MaterialCreate, MaterialUpdate, MaterialResponse

router = APIRouter(prefix="/api/materials", tags=["物料管理"])


def generate_material_code(db: Session) -> str:
    """自动生成物料编码：MAT-YYYYMMDD-XXXXX（当日序号）"""
    today_str = datetime.now().strftime("%Y%m%d")
    prefix = f"MAT-{today_str}-"
    last = db.query(MaterialMaster).filter(
        MaterialMaster.material_code.like(f"{prefix}%")
    ).order_by(MaterialMaster.material_code.desc()).first()
    if last:
        seq = int(last.material_code.split("-")[-1]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:05d}"

router = APIRouter(prefix="/api/materials", tags=["物料管理"])


@router.get("", response_model=dict)
def list_materials(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None, description="搜索关键词(编码/名称)"),
    material_type: Optional[str] = Query(None, description="物料类型筛选"),
    level_type: Optional[str] = Query(None, description="层级类型筛选"),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """获取物料列表（分页+搜索+筛选）"""
    query = db.query(MaterialMaster)

    if keyword:
        query = query.filter(
            (MaterialMaster.material_code.ilike(f"%{keyword}%")) |
            (MaterialMaster.material_name.ilike(f"%{keyword}%"))
        )
    if material_type:
        query = query.filter(MaterialMaster.material_type == material_type)
    if level_type:
        query = query.filter(MaterialMaster.level_type == level_type)
    if is_active is not None:
        query = query.filter(MaterialMaster.is_active == is_active)

    total = query.count()
    items = query.order_by(MaterialMaster.material_code).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "items": [
            {
                "id": m.id, "material_code": m.material_code, "classification_code": m.classification_code or "",
                "material_name": m.material_name,
                "specification": m.specification, "unit": m.unit, "material_type": m.material_type,
                "level_type": m.level_type or "零件",
                "lead_time": m.lead_time, "safety_stock": m.safety_stock,
                "lot_size_rule": m.lot_size_rule, "lot_size_qty": m.lot_size_qty,
                "min_order_qty": m.min_order_qty, "max_order_qty": m.max_order_qty,
                "scrap_rate": m.scrap_rate, "is_purchased": m.is_purchased,
                "is_active": m.is_active, "remark": m.remark,
                "reference_unit_price": m.reference_unit_price or 0,
                "reference_submitter": m.reference_submitter or "",
                "reference_link": m.reference_link or "",
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in items
        ],
        "total": total, "page": page, "page_size": page_size,
    }


@router.get("/all")
def list_all_materials(
    material_type: Optional[str] = Query(None),
    level_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """获取所有物料（用于下拉选择）"""
    query = db.query(MaterialMaster).filter(MaterialMaster.is_active == True)
    if material_type:
        query = query.filter(MaterialMaster.material_type == material_type)
    if level_type:
        query = query.filter(MaterialMaster.level_type == level_type)

    items = query.order_by(MaterialMaster.material_code).all()
    return {
        "items": [
            {"id": m.id, "material_code": m.material_code, "classification_code": m.classification_code or "",
             "material_name": m.material_name, "level_type": m.level_type or "零件",
             "unit": m.unit, "material_type": m.material_type, "is_purchased": m.is_purchased}
            for m in items
        ]
    }


@router.get("/tree")
def material_tree(db: Session = Depends(get_db)):
    """获取项目→模块→零件的层级结构"""
    products = db.query(MaterialMaster).filter(
        MaterialMaster.level_type == "产品", MaterialMaster.is_active == True
    ).all()
    result = []
    for product in products:
        proj_bom = db.query(BomHeader).filter(BomHeader.product_id == product.id).order_by(BomHeader.id.desc()).first()
        if not proj_bom: continue
        module_lines = db.query(BomLine).filter(BomLine.bom_header_id == proj_bom.id).order_by(BomLine.sort_order).all()
        modules = []
        for ml in module_lines:
            mod = db.query(MaterialMaster).filter(MaterialMaster.id == ml.item_id, MaterialMaster.level_type == "模块").first()
            if not mod: continue
            mod_bom = db.query(BomHeader).filter(BomHeader.product_id == mod.id).order_by(BomHeader.id.desc()).first()
            if not mod_bom: continue
            part_lines = db.query(BomLine).filter(BomLine.bom_header_id == mod_bom.id).order_by(BomLine.sort_order).all()
            parts = []
            for pl in part_lines:
                part = db.query(MaterialMaster).filter(MaterialMaster.id == pl.item_id, MaterialMaster.level_type == "零件").first()
                if part:
                    parts.append({"id": part.id, "material_code": part.material_code, "material_name": part.material_name,
                        "specification": part.specification or "", "unit": part.unit, "is_purchased": part.is_purchased,
                        "lead_time": part.lead_time, "safety_stock": part.safety_stock,
                        "reference_unit_price": part.reference_unit_price or 0})
            modules.append({"id": mod.id, "module_code": mod.material_code, "module_name": mod.material_name,
                "part_count": len(parts), "parts": parts})
        result.append({"id": product.id, "product_code": product.material_code, "product_name": product.material_name,
            "module_count": len(modules), "total_parts": sum(m["part_count"] for m in modules), "modules": modules})
    return {"projects": result}


@router.get("/{material_id}")
def get_material(material_id: int, db: Session = Depends(get_db)):
    """获取单个物料详情"""
    m = db.query(MaterialMaster).filter(MaterialMaster.id == material_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="物料不存在")
    return {"item": {
        "id": m.id, "material_code": m.material_code, "classification_code": m.classification_code or "",
        "material_name": m.material_name,
        "specification": m.specification, "unit": m.unit, "material_type": m.material_type,
        "level_type": m.level_type or "零件",
        "lead_time": m.lead_time, "safety_stock": m.safety_stock,
        "lot_size_rule": m.lot_size_rule, "lot_size_qty": m.lot_size_qty,
        "min_order_qty": m.min_order_qty, "max_order_qty": m.max_order_qty,
        "scrap_rate": m.scrap_rate, "is_purchased": m.is_purchased,
        "is_active": m.is_active, "remark": m.remark,
    }}


@router.post("")
def create_material(data: MaterialCreate, db: Session = Depends(get_db)):
    """新增物料（物料编码为空时自动生成）"""
    material_code = data.material_code.strip() if data.material_code else ""
    if not material_code:
        material_code = generate_material_code(db)
    else:
        existing = db.query(MaterialMaster).filter(
            MaterialMaster.material_code == material_code
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"物料编码 {material_code} 已存在")

    mat_data = data.model_dump()
    mat_data["material_code"] = material_code
    mat = MaterialMaster(**mat_data)
    db.add(mat)
    db.commit()
    db.refresh(mat)
    return {"success": True, "message": "创建成功", "data": {"id": mat.id, "material_code": mat.material_code}}


@router.put("/{material_id}")
def update_material(material_id: int, data: MaterialUpdate, db: Session = Depends(get_db)):
    """更新物料"""
    mat = db.query(MaterialMaster).filter(MaterialMaster.id == material_id).first()
    if not mat:
        raise HTTPException(status_code=404, detail="物料不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(mat, key, value)

    db.commit()
    return {"success": True, "message": "更新成功"}


@router.delete("/{material_id}")
def delete_material(material_id: int, db: Session = Depends(get_db)):
    """删除物料（软删除）"""
    mat = db.query(MaterialMaster).filter(MaterialMaster.id == material_id).first()
    if not mat:
        raise HTTPException(status_code=404, detail="物料不存在")
    mat.is_active = False
    db.commit()
    return {"success": True, "message": "已停用"}


@router.put("/batch/safety-stock")
def batch_update_safety_stock(data: dict, db: Session = Depends(get_db)):
    """批量更新安全库存"""
    item_ids = data.get("item_ids", [])
    new_value = data.get("safety_stock", 0)
    
    if not item_ids:
        raise HTTPException(status_code=400, detail="请提供物料ID列表")
    
    updated = 0
    for item_id in item_ids:
        mat = db.query(MaterialMaster).filter(MaterialMaster.id == item_id).first()
        if mat:
            mat.safety_stock = new_value
            updated += 1
    
    db.commit()
    return {
        "success": True,
        "message": f"已更新 {updated} 个物料的安全库存为 {new_value}",
        "data": {"updated": updated},
    }


@router.put("/batch/update")
def batch_update_materials(data: dict, db: Session = Depends(get_db)):
    """批量更新物料字段（单价/提交人/链接等）"""
    item_ids = data.get("item_ids", [])
    fields = data.get("fields", {})
    if not item_ids:
        raise HTTPException(status_code=400, detail="请提供物料ID列表")
    if not fields:
        raise HTTPException(status_code=400, detail="请提供要更新的字段")
    updated = 0
    for item_id in item_ids:
        mat = db.query(MaterialMaster).filter(MaterialMaster.id == item_id).first()
        if mat:
            for key, val in fields.items():
                if hasattr(mat, key):
                    setattr(mat, key, val)
            updated += 1
    db.commit()
    return {
        "success": True,
        "message": f"已更新 {updated} 个物料",
        "data": {"updated": updated},
    }
