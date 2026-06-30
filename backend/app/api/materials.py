"""物料管理 API"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.material import MaterialMaster
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
